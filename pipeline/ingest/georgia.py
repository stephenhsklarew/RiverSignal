"""Georgia state data adapters.

ga_trout — GA DNR Wildlife Resources Division weekly trout-stocking report.

Source: https://gadnr.org/sites/default/files/wrd/pdf/trout/Weekly_Stocking_Report.pdf
License: OCGA §50-18-70 (Georgia Open Records Act), commercial:true.
Attribution: "Trout stocking from the Georgia DNR Wildlife Resources Division".

The report is a small ReportLab PDF with no ruled table — lines are
`DATE COUNTY WATERBODY` (COUNTY is one whitespace token, may contain a slash like
"Forsyth/Gwinnett"; WATERBODY is the remainder). There is NO species column (GA
reports stocked "trout" generically), so species is recorded as "Trout".

Only Chattahoochee-system waters are attributed to the watershed (see
CHATT_WATERS); the report is statewide. Mirrors the virginia.py DWR-stocking
dedup + JSONB-description pattern so the stocking surface picks rows up.
"""
import json
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

GA_TROUT_STOCKING_URL = "https://gadnr.org/sites/default/files/wrd/pdf/trout/Weekly_Stocking_Report.pdf"

# Unambiguous Chattahoochee-system waters (substring match, case-insensitive).
# "chattahoochee" catches "Chattahoochee River" + "Chattahoochee River (WMA)".
# "lanier tailwater" is the Buford Dam tailwater — the signature trout reach.
CHATT_WATERS: tuple[str, ...] = (
    "chattahoochee",
    "lanier tailwater",
    "soque",            # Soque River — major Chattahoochee tributary (Habersham)
    "dukes creek",      # White Co (Smithgall Woods) — Chattahoochee headwaters
    "low gap creek",    # White Co — Chattahoochee headwaters
    "jasus creek",      # White Co — Chattahoochee headwaters
)
# Ambiguous names (common statewide) — only count inside a Chattahoochee county.
CHATT_AMBIGUOUS: tuple[str, ...] = (
    "smith creek",      # White Co (Unicoi/Smithgall) Chattahoochee trib; Smith Creeks exist elsewhere
)
CHATT_COUNTIES: tuple[str, ...] = (
    "white", "habersham", "hall", "forsyth", "gwinnett",
    "fulton", "cobb", "dekalb", "douglas", "carroll", "coweta", "heard", "troup",
)


def _is_chattahoochee_water(waterbody: str, county: str) -> bool:
    w = waterbody.lower()
    c = county.lower().strip()
    for name in CHATT_WATERS:
        if name in w:
            return True
    # county may be a slash-pair e.g. "forsyth/gwinnett"
    counties = {p.strip() for p in re.split(r"[/,]", c)}
    for name in CHATT_AMBIGUOUS:
        if name in w and counties & set(CHATT_COUNTIES):
            return True
    return False


_ROW_RE = re.compile(r"^(\d{1,2}/\d{1,2}/\d{4})\s+(\S+)\s+(.+?)\s*$")


class GATroutStockingAdapter(IngestionAdapter):
    source_type = "ga_trout"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site:
            return 0, 0
        # GA-only. Add new GA watersheds here when onboarding them.
        if site.watershed not in ("chattahoochee",):
            console.print(f"    ga_trout: skipping {site.watershed} (not a GA watershed)")
            return 0, 0

        headers = {"User-Agent": "RiverSignal/1.0 (watershed-onboarding; +contact@liquidmarble.com)"}
        try:
            with httpx.Client(timeout=30, headers=headers) as client:
                resp = client.get(GA_TROUT_STOCKING_URL)
                resp.raise_for_status()
                content = resp.content
        except Exception as e:
            # Don't poison last_sync on a transient fetch failure (cf. owdp).
            raise RuntimeError(f"GA trout stocking PDF unavailable: {e}")

        if not content or not content[:4] == b"%PDF":
            raise RuntimeError("GA trout stocking URL did not return a PDF")

        import io

        import pdfplumber

        lines: list[str] = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for pg in pdf.pages:
                txt = pg.extract_text() or ""
                lines.extend(txt.splitlines())

        # Dedup against existing ga_trout rows for this site.
        existing = self.session.execute(
            text(
                "SELECT description FROM interventions "
                "WHERE site_id = :sid AND type = 'fish_stocking' "
                "AND description::jsonb ->> 'source' = 'ga_trout'"
            ),
            {"sid": self.site_id},
        ).scalars().all()
        seen: set[tuple[str, str]] = set()
        for d in existing:
            try:
                j = json.loads(d)
                seen.add((j.get("stocking_date", ""), j.get("waterbody", "").lower()))
            except Exception:
                continue

        inserted = 0
        for line in lines:
            m = _ROW_RE.match(line.strip())
            if not m:
                continue
            date_raw, county, waterbody = m.group(1), m.group(2), m.group(3).strip()
            if not _is_chattahoochee_water(waterbody, county):
                continue

            started_at = None
            for fmt in ("%m/%d/%Y", "%-m/%-d/%Y"):
                try:
                    started_at = datetime.strptime(date_raw, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
            if started_at is None:
                continue
            date_iso = started_at.date().isoformat()

            key = (date_iso, waterbody.lower())
            if key in seen:
                continue
            seen.add(key)

            desc = json.dumps({
                "source": "ga_trout",
                "waterbody": waterbody,
                "county": county,
                "species": "Trout",   # GA report has no species column
                "stocking_date": date_iso,
            }, ensure_ascii=False)
            self.session.execute(
                text(
                    "INSERT INTO interventions (id, site_id, type, description, started_at, created_at) "
                    "VALUES (gen_random_uuid(), :sid, 'fish_stocking', :desc, :sa, now())"
                ),
                {"sid": self.site_id, "desc": desc, "sa": started_at},
            )
            inserted += 1

        return inserted, 0
