"""Ohio fish-stocking adapter.

Source: Ohio DNR Division of Wildlife — Trout Stockings.
  https://ohiodnr.gov/buy-and-apply/hunting-fishing-boating/fishing-resources/trout-stockings
License: Public Records (Ohio Revised Code §149.43 — Ohio Public Records Act).
commercial: true (Ohio public records are commercially usable; attribution to
ODNR Division of Wildlife in any commercial surface is good practice but not
legally required).
Attribution: "Stocking data from Ohio DNR Division of Wildlife, https://ohiodnr.gov".

WHAT THIS FEED ACTUALLY IS (verified 2026-05-30): the ODNR trout-stockings
page is the *statewide spring catchable-rainbow put-and-take schedule* — a
single static HTML table of Location / County / District / Release-Date rows
for community ponds and reservoirs. It is fetchable with a browser User-Agent
(the inventory's 404 was pure UA-gating). It does NOT contain the Mad River
brown-trout stream program. This adapter parses that table and attributes the
basin-relevant rows (by an explicit Mad-River waters allowlist) to the
mad_river_oh watershed as `interventions` rows (source='ohio_dnr').

SCAFFOLD STATUS (2026-05-30): adapter class, watershed-scoping guard, source
URL constant, ODNR put-and-take parser, interventions insert, cli.py
registration, SOURCE_REFRESH_HOURS + SOURCE_LABELS entries are all in place.
Run as `python -m pipeline.cli ingest ohio_stocking -w mad_river_oh` to confirm
the ingestion_jobs heartbeat lands and any basin put-and-take rows insert.

Follow-on beads:
  - P1  Mad River brown-trout STREAM stocking (~11,500 yearlings/yr at
        ~500/mile every mid-October in the Champaign/Clark Co. C&R section).
        NOT in the put-and-take table — published as narrative ODNR content.
        Seed via alembic (interventions, source='ohio_dnr',
        needs_review=true) or parse the ODNR coldwater-streams page.
  - P1  Extend gold.stocking_schedule MV to UNION ohio_dnr interventions
        rows. The MV's stocking branch keys on source='udwr'/'va_dwr' shapes;
        ohio_dnr rows won't surface in the RiverPath stocking panel until the
        MV's UNION is extended (same gap virginia.py flagged for va_dwr).
  - P2  DataOhio "Fish Stocking Records" dataset (1970→present). data.ohio.gov
        is not a standard CKAN endpoint; likely a Tableau/PowerBI embed with
        no CSV export — needs discovery before it can be adapted.
"""

import json
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# ── Endpoints ───────────────────────────────────────────────────────────────

ODNR_TROUT_STOCKING_URL = (
    "https://ohiodnr.gov/buy-and-apply/hunting-fishing-boating/"
    "fishing-resources/trout-stockings"
)

# Browser UA — ODNR's CDN 404s the default httpx UA (verified 2026-05-30).
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Waterbodies attributable to the Mad River (OH) watershed. Substring match
# (case-insensitive) on the cleaned location name from the ODNR put-and-take
# table. Conservative: the statewide put-and-take schedule lists community
# ponds; only those genuinely in the Mad River drainage count. Add new entries
# here as ODNR coverage / guide review identifies missed waters.
#
# NOTE: the put-and-take table is rainbow-trout pond stocking, structurally
# distinct from the Mad River brown-trout STREAM fishery (see P1 follow-on
# bead in the module docstring). Most rows here will match nothing today.
MAD_RIVER_WATERS: tuple[str, ...] = (
    "mad river",
    "buck creek",
    "c.j. brown", "cj brown", "c j brown",
)


def _is_mad_river_water(location: str) -> bool:
    """Return True if this put-and-take location is in the Mad River drainage."""
    loc = location.lower()
    return any(name in loc for name in MAD_RIVER_WATERS)


# ── Adapter ─────────────────────────────────────────────────────────────────

class OhioStockingAdapter(IngestionAdapter):
    """ODNR Division of Wildlife fish-stocking adapter for Mad River (OH).

    Mirrors the virginia.py / utah.py pattern — one adapter class per state,
    ingest() iterates over sub-source methods. Each sub-source isolates its
    own errors so one failing source doesn't kill the others.
    """
    source_type = "ohio_stocking"

    SUB_SOURCES: list[tuple[str, str]] = [
        ("ODNR Trout Put-and-Take", "_ingest_odnr_trout_stocking"),
    ]

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site:
            return 0, 0

        # Only run for OH watersheds. Add new OH watersheds to this tuple when
        # onboarding them (runbook §2.2 step 9 — watershed-scoping caveat).
        if site.watershed not in ("mad_river_oh",):
            console.print(f"    ohio_stocking: skipping {site.watershed} (not an OH watershed)")
            return 0, 0

        total = 0
        with httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": _BROWSER_UA},
        ) as client:
            for name, method_name in self.SUB_SOURCES:
                try:
                    c = getattr(self, method_name)(client, site)
                    total += c
                    console.print(f"    {name}: {c} records")
                except Exception as e:
                    console.print(f"    [yellow]{name}: {e}[/yellow]")
        return total, 0

    def _ingest_odnr_trout_stocking(self, client, site) -> int:
        """ODNR statewide catchable-rainbow put-and-take schedule.

        Parses the single static HTML table (columns: Location, County,
        District, [Special Angler Event], Release Date) and inserts
        Mad-River-attributable rows into `interventions` with type=
        'fish_stocking', source='ohio_dnr'. Species is 'Rainbow Trout' (the
        put-and-take species for this schedule). One row per (location, date).
        Idempotent: dedups against existing ohio_dnr rows by (date, location).
        """
        resp = client.get(ODNR_TROUT_STOCKING_URL)
        resp.raise_for_status()
        html = resp.text

        m = re.search(r"<table.*?</table>", html, re.DOTALL | re.IGNORECASE)
        if not m:
            console.print("      [yellow]ODNR: stocking table not found in HTML[/yellow]")
            return 0
        table_html = m.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE)

        existing = self.session.execute(
            text(
                "SELECT description FROM interventions "
                "WHERE site_id = :sid AND type = 'fish_stocking' "
                "AND description::jsonb ->> 'source' = 'ohio_dnr'"
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
        for row in rows:
            cells = [
                re.sub(r"<[^>]+>", "", c).strip()
                for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
            ]
            if len(cells) < 3:
                continue
            location = cells[0]
            county = cells[1]
            # Release date is the last cell that parses as a date.
            started_at = None
            for cell in reversed(cells):
                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"):
                    try:
                        started_at = datetime.strptime(cell.strip(), fmt).replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
                if started_at:
                    break
            if started_at is None:
                continue  # header row or non-data row

            if not _is_mad_river_water(location):
                continue

            date_iso = started_at.date().isoformat()
            key = (date_iso, location.lower())
            if key in seen:
                continue
            seen.add(key)

            desc = json.dumps({
                "source": "ohio_dnr",
                "waterbody": location,
                "county": county,
                "species": "Rainbow Trout",
                "stocking_date": date_iso,
                "program": "put-and-take",
                "needs_review": True,
            }, ensure_ascii=False)

            self.session.execute(
                text(
                    "INSERT INTO interventions (id, site_id, type, description, started_at, created_at) "
                    "VALUES (gen_random_uuid(), :sid, 'fish_stocking', :desc, :sa, now())"
                ),
                {"sid": self.site_id, "desc": desc, "sa": started_at},
            )
            inserted += 1

        self.session.commit()
        return inserted
