"""Massachusetts state data source adapters.

Source: MA Division of Fisheries & Wildlife (MassWildlife / "MA DFW") trout
stocking; MA Division of Marine Fisheries (DMF) Diadromous Fisheries Project
(river-herring counts). MassDEP impaired waters and MassGIS geology are
reached through the federal `impaired`/`wqp` and `macrostrat` adapters plus a
follow-on MassGIS bead, not here.
License: Public Records (MGL c.66, Massachusetts Public Records Law).
commercial: true (Public Records are commercially usable; attribution to the
agency in any commercial surface is good practice but not legally required).
Attribution: "Data from <agency name>, mass.gov".

SCAFFOLD STATUS (2026-06-02): adapter class, watershed-scoping guard, source
URL constants, cli.py registration, SOURCE_REFRESH_HOURS + SOURCE_LABELS +
StatusPage SOURCE_META entries are in place. The MassWildlife stocking
sub-source attempts a best-effort HTML-table scrape, but mass.gov UA-gates
automated fetches (returns HTTP 403) and the live "Trout Stocking Report" is a
JS-rendered map/table with no server-rendered table or CSV/API export. So the
stocking sub-source degrades to 0 rows until a headless-browser path or an
ORC-style public-records data request lands. This is the documented v0 posture
(runbook §2.4.5: ship empty stocking + a P2 bead, NEVER placeholder rows —
`gold.stocking_schedule` handles the empty state, verified against Green River).

Follow-on beads (one per sub-source):
  - P2  MassWildlife trout stocking → interventions (source='ma_dfw').
        Needs headless-browser render OR a public-records data request, since
        mass.gov/info-details/trout-stocking-report is JS + UA-gated.
        Source: https://www.mass.gov/info-details/trout-stocking-report
  - P2  MA DMF river-herring counts (Ipswich = a documented run) →
        interventions / a herring-count surface. Annual HTML/PDF reports only.
        Source: https://www.mass.gov/info-details/diadromous-fisheries-project
"""

import json
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.ingest.geology import _arcgis_query_paginated, _esri_rings_to_geojson
from pipeline.models import Site


# ── Endpoints ───────────────────────────────────────────────────────────────

MA_DFW_STOCKING_URL = "https://www.mass.gov/info-details/trout-stocking-report"
MA_DMF_HERRING_URL  = "https://www.mass.gov/info-details/diadromous-fisheries-project"
# MassGIS 1:24k Surficial Geology overlay (glacial drift / till / outwash /
# shallow-bedrock units) — queryable ArcGIS MapServer on the state's own server.
# Surficial (not bedrock) is the high-value layer here: the Ipswich basin is a
# glacially-shaped New-England landscape (drumlins, outwash, salt marsh).
# License: MassGIS open public data, commercial:true.
MASSGIS_SURFGEO_URL = "https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/SurfGeo24k/MapServer/0/query"

# Browser-like UA — mass.gov 403s the default httpx UA. Even with this, the
# stocking report is JS-rendered, so a static fetch will usually find no table;
# the parser degrades to 0 rows in that case (flag-and-continue).
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Waterbodies known to drain the Ipswich River basin. Conservative substring
# match (case-insensitive) on the cleaned waterbody name. Add entries here as
# guide review identifies missed waters. (Note: Pentucket Pond / Georgetown is
# the *Parker* basin, not the Ipswich — deliberately excluded.)
IPSWICH_WATERS: tuple[str, ...] = (
    "ipswich river",
    "boston brook", "fish brook", "martins brook", "howlett brook",
    "norris brook", "miles river",
    "stiles pond", "hood pond",
)
# Essex/Middlesex towns predominantly in the Ipswich drainage. Used as a
# secondary attribution signal when the waterbody name alone is ambiguous.
IPSWICH_TOWNS: tuple[str, ...] = (
    "wilmington", "reading", "north reading", "middleton", "topsfield",
    "boxford", "hamilton", "wenham", "ipswich",
)


def _is_ipswich_water(waterbody: str, town: str) -> bool:
    """True if a stocking row should be attributed to the Ipswich watershed.

    Primary signal: the waterbody substring matches a known Ipswich water.
    Secondary: the town is a core Ipswich-drainage town (covers stocked ponds
    whose names aren't in the curated water list yet).
    """
    w = (waterbody or "").lower()
    t = (town or "").lower().strip()
    if any(name in w for name in IPSWICH_WATERS):
        return True
    return any(t == town_name for town_name in IPSWICH_TOWNS)


# ── Adapter ─────────────────────────────────────────────────────────────────

class MassachusettsDataAdapter(IngestionAdapter):
    """Bundled adapter for Massachusetts state data sources.

    Mirrors the virginia.py / utah.py pattern — one adapter class per state;
    each ingest() call iterates over sub-source methods with per-source error
    isolation (one failing sub-source doesn't kill the others).
    """
    source_type = "massachusetts"

    SUB_SOURCES: list[tuple[str, str]] = [
        ("MassWildlife Stocking", "_ingest_dfw_stocking"),
        ("MA DMF Herring",        "_ingest_dmf_herring"),
        ("MassGIS Surficial Geology", "_ingest_massgis_geology"),
    ]

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site:
            return 0, 0

        # Only run for MA watersheds. Add new MA watersheds to this tuple when
        # onboarding them (runbook §2.2 step 9 — watershed-scoping caveat).
        if site.watershed not in ("ipswich_river_ma",):
            console.print(f"    massachusetts: skipping {site.watershed} (not a MA watershed)")
            return 0, 0

        total = 0
        with httpx.Client(timeout=30, headers={"User-Agent": _BROWSER_UA},
                          follow_redirects=True) as client:
            for name, method_name in self.SUB_SOURCES:
                try:
                    c = getattr(self, method_name)(client, site)
                    total += c
                    console.print(f"    {name}: {c} records")
                except Exception as e:
                    console.print(f"    [yellow]{name}: {e}[/yellow]")
        return total, 0

    def _ingest_dfw_stocking(self, client, site) -> int:
        """MassWildlife trout stocking → interventions (type='fish_stocking').

        Best-effort scrape of the first HTML <table> on the Trout Stocking
        Report. Columns are detected from the header row (date / water / town /
        species). Ipswich-basin rows are inserted with source='ma_dfw', one row
        per species, matching the UDWR/va_dwr JSONB shape that
        `gold.stocking_schedule` expects. Degrades to 0 rows when mass.gov
        UA-gates the fetch or serves no server-rendered table (the common case).

        NOTE: `gold.stocking_schedule` keys its stocking UNION on specific
        source strings; a follow-on migration must add a `ma_dfw` branch before
        these rows surface in the RiverPath stocking panel.
        """
        resp = client.get(MA_DFW_STOCKING_URL)
        if resp.status_code == 403:
            console.print("      [yellow]MA DFW: mass.gov UA-gated (403) — stocking deferred to P2 bead[/yellow]")
            return 0
        resp.raise_for_status()
        html = resp.text

        m = re.search(r"<table[^>]*>(.*?)</table>", html, re.DOTALL | re.IGNORECASE)
        if not m:
            console.print("      [yellow]MA DFW: no server-rendered stocking table (JS-rendered) — deferred to P2 bead[/yellow]")
            return 0
        table = m.group(1)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL | re.IGNORECASE)
        if len(rows) < 2:
            return 0

        # Detect column indices from the header row.
        header_cells = [
            re.sub(r"<[^>]+>", "", c).strip().lower()
            for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", rows[0], re.DOTALL | re.IGNORECASE)
        ]
        def col(*names: str) -> int | None:
            for i, h in enumerate(header_cells):
                if any(n in h for n in names):
                    return i
            return None
        i_date  = col("date")
        i_water = col("water", "body")
        i_town  = col("town", "city", "location")
        i_spec  = col("species", "fish")
        if i_water is None:
            return 0

        # Dedup against existing ma_dfw rows by (date, waterbody, species).
        existing = self.session.execute(
            text(
                "SELECT description FROM interventions "
                "WHERE site_id = :sid AND type = 'fish_stocking' "
                "AND description::jsonb ->> 'source' = 'ma_dfw'"
            ),
            {"sid": self.site_id},
        ).scalars().all()
        seen: set[tuple[str, str, str]] = set()
        for d in existing:
            try:
                j = json.loads(d)
                seen.add((j.get("stocking_date", ""), j.get("waterbody", "").lower(),
                          str(j.get("species", "")).lower()))
            except Exception:
                continue

        inserted = 0
        for row in rows[1:]:
            cells = [
                re.sub(r"<[^>]+>", "", c).strip()
                for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.DOTALL | re.IGNORECASE)
            ]
            if i_water >= len(cells):
                continue
            waterbody = cells[i_water]
            town = cells[i_town] if (i_town is not None and i_town < len(cells)) else ""
            if not _is_ipswich_water(waterbody, town):
                continue

            date_raw = cells[i_date] if (i_date is not None and i_date < len(cells)) else ""
            started_at = None
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y", "%m/%d/%y"):
                try:
                    started_at = datetime.strptime(date_raw, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
            if started_at is None:
                continue
            date_iso = started_at.date().isoformat()

            spec_raw = cells[i_spec] if (i_spec is not None and i_spec < len(cells)) else "Trout"
            species_list = [s.strip() for s in re.split(r"[,;/]| and ", spec_raw) if s.strip()] or ["Trout"]

            for species in species_list:
                key = (date_iso, waterbody.lower(), species.lower())
                if key in seen:
                    continue
                seen.add(key)
                desc = json.dumps({
                    "source": "ma_dfw",
                    "waterbody": waterbody,
                    "town": town,
                    "species": species,
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
        return inserted

    def _ingest_dmf_herring(self, client, site) -> int:
        """MA DMF river-herring counts (Ipswich is a documented run).

        TODO (P2 bead): the Diadromous Fisheries Project publishes annual
        HTML/PDF reports, not a structured feed. A v0 fill is a hand-curated
        seed of the Ipswich/Parker sentinel-river annual counts. Scaffold only.
        """
        console.print("      [dim]_ingest_dmf_herring: not yet implemented (scaffold)[/dim]")
        return 0

    def _ingest_massgis_geology(self, client, site) -> int:
        """MassGIS 1:24k surficial-geology polygons in the watershed bbox.

        Mirrors the VGS/DOGAMI pattern (ArcGIS REST polygons -> geologic_units).
        SurfGeo24k has no numeric ages (it's Quaternary surficial cover), so
        age_min_ma/age_max_ma/period stay NULL like DOGAMI/VGS rows. Fields:
        LABEL/SYMBOL (unit code), TYPE (unit type), NOTES (description).
        """
        bbox = site.bbox
        if not bbox:
            return 0
        features = _arcgis_query_paginated(client, MASSGIS_SURFGEO_URL, bbox, max_per_page=1000)
        if not features:
            return 0

        SQL = text("""
            INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                rock_type, lithology, age_min_ma, age_max_ma, period, description,
                geometry, data_payload)
            VALUES (gen_random_uuid(), 'massgis', :source_id, :unit_name, :formation,
                :rock_type, :lithology, NULL, NULL, NULL, :description,
                ST_GeomFromGeoJSON(:geojson), CAST(:payload AS jsonb))
            ON CONFLICT DO NOTHING
        """)
        SQL_NO_GEOM = text("""
            INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                rock_type, lithology, age_min_ma, age_max_ma, period, description,
                data_payload)
            VALUES (gen_random_uuid(), 'massgis', :source_id, :unit_name, :formation,
                :rock_type, :lithology, NULL, NULL, NULL, :description,
                CAST(:payload AS jsonb))
            ON CONFLICT DO NOTHING
        """)

        existing_ids = {
            row[0] for row in self.session.execute(
                text("SELECT source_id FROM geologic_units WHERE source = 'massgis'")
            )
        }

        created = 0
        with engine.connect() as conn:
            for f in features:
                attrs = f.get("attributes", {}) or {}
                source_id = str(attrs.get("OBJECTID", ""))
                if not source_id or source_id in existing_ids:
                    continue
                geojson = _esri_rings_to_geojson(f.get("geometry"))
                unit_code = (attrs.get("LABEL") or attrs.get("SYMBOL") or "")[:255]
                unit_type = (attrs.get("TYPE") or "")[:255]
                description = attrs.get("NOTES") or ""
                params = {
                    "source_id": source_id,
                    "unit_name": unit_code,
                    "formation": unit_type,
                    "rock_type": unit_type[:100],
                    "lithology": "",
                    "description": description,
                    "payload": json.dumps(attrs),
                }
                if geojson:
                    params["geojson"] = geojson
                    conn.execute(SQL, params)
                else:
                    conn.execute(SQL_NO_GEOM, params)
                created += 1
            conn.commit()
        return created
