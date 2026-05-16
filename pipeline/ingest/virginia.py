"""Virginia state data source adapters.

Source: Virginia Dept of Wildlife Resources (DWR), VA Dept of Environmental
Quality (DEQ), VA Dept of Conservation & Recreation (DCR), VA Dept of Mines,
Minerals & Energy / Virginia Geological Survey (VGS).
License: Public Records (VA Code §2.2-3700 — Virginia Freedom of Information Act).
commercial: true (Public Records are commercially usable; attribution to the
agency in any commercial surface is good practice but not legally required).
Attribution: "Data from <agency name>, <agency URL>".

SCAFFOLD STATUS (2026-05-15): adapter class, watershed-scoping guard, source
URL constants, cli.py registration, SOURCE_REFRESH_HOURS + SOURCE_LABELS
entries are all in place. Per-source parsing methods are TODO — each emits
a `console.print("...not yet implemented")` and returns 0 rows. Run as
`python -m pipeline.cli ingest virginia -w shenandoah` to confirm the
ingestion_jobs heartbeat lands (proves the freshness wiring is correct).

Follow-on beads (one per sub-source):
  - P1  VA DWR weekly trout stocking schedule → interventions table
        Source: https://dwr.virginia.gov/fishing/trout-stocking-schedule/
  - P2  VA DWR fishing regulations (special-reg streams) → static seed
        Source: https://dwr.virginia.gov/fishing/regulations/
  - P2  VGS geologic units → geologic_units table
        Source: https://www.dmme.virginia.gov/dgmr/
  - P3  VA DCR state parks → recreation_sites table
        Source: https://www.dcr.virginia.gov/state-parks/
        (Check RIDB coverage first — most VA state parks may already be there)
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

VA_DWR_STOCKING_URL = "https://dwr.virginia.gov/fishing/trout-stocking-schedule/"
VA_DWR_REGS_URL     = "https://dwr.virginia.gov/fishing/regulations/"
# Virginia Energy DGMR (formerly VGS / DMME) — 1:500k state geologic map.
# Layer 4 = "Map Units, Lithology" (polygons of geologic units with rock-type
# attribution). Lives on the agency's own ArcGIS Server, not the public
# services.arcgis.com tenant.
VGS_GEOLOGY_MAPSERVER = (
    "https://energy.virginia.gov/gis/rest/services/DGMR/Geology/MapServer/4/query"
)
VA_DCR_PARKS_URL    = "https://www.dcr.virginia.gov/state-parks/"

# Waterbodies known to drain into the Shenandoah River. Used to scope VA-wide
# stocking events to the Shenandoah watershed during ingest. Substring match
# (case-insensitive) on the cleaned waterbody name from the DWR stocking page.
# Conservative: omits waters near the Shenandoah valley that actually drain
# elsewhere (e.g., Bullpasture → James, Maury → James, South Branch Potomac →
# Potomac main stem, NOT Shenandoah). Add new entries here as guide review
# identifies missed waters.
SHENANDOAH_WATERS: tuple[str, ...] = (
    # Main forks and main stem
    "north fork shenandoah", "south fork shenandoah",
    # Major tributaries
    "south river", "north river", "middle river",
    "hughes river", "rose river", "robinson river",
    "moormans river", "moorman's river",
    "dry river", "smith creek", "passage creek", "mossy creek", "beaver creek",
    "linville creek", "war branch", "muddy creek",
    "swift run",
    # Mill Creek is ambiguous (multiple VA streams named that); only stocking
    # rows in Shenandoah/Rockingham counties count as Shenandoah
)
SHENANDOAH_COUNTIES: tuple[str, ...] = (
    "augusta", "rockingham", "shenandoah", "page", "warren",
    "frederick", "clarke", "madison", "greene",
    # Northern Albemarle drains into the South Fork via the Moormans + Rockfish
    "albemarle",
)


def _is_shenandoah_water(waterbody: str, county: str) -> bool:
    """Return True if this stocking row should be attributed to Shenandoah.

    Two filters in OR: (a) the waterbody substring matches a known
    Shenandoah water, OR (b) the waterbody is 'Mill Creek' and the county
    is in a Shenandoah-drainage county (Mill Creek is a common name).
    """
    w = waterbody.lower()
    c = county.lower().replace(" county", "").strip()
    for name in SHENANDOAH_WATERS:
        if name in w:
            return True
    # Mill Creek ambiguity guard — only count it when it's in a SR county.
    if "mill creek" in w and c in SHENANDOAH_COUNTIES:
        return True
    return False


# ── Adapter ─────────────────────────────────────────────────────────────────

class VirginiaDataAdapter(IngestionAdapter):
    """Bundled adapter for Virginia state data sources.

    Mirrors the utah.py / washington.py pattern — one adapter class per
    state, each ingest() call iterates over sub-source methods. Each
    sub-source is responsible for its own bronze table writes and
    error isolation (one failing sub-source doesn't kill the others).
    """
    source_type = "virginia"

    # Sub-sources can grow over time. New rows in this list ship one
    # commit at a time; failures here don't short-circuit the others.
    SUB_SOURCES: list[tuple[str, str]] = [
        ("VA DWR Stocking",   "_ingest_dwr_stocking"),
        ("VA DWR Regulations", "_ingest_dwr_regs"),
        ("VGS Geology",       "_ingest_vgs_geology"),
        ("VA DCR State Parks", "_ingest_dcr_parks"),
    ]

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site:
            return 0, 0

        # Only run for VA watersheds. Add new VA watersheds to this tuple
        # when onboarding them (see runbook §2.2 step 9 — watershed-scoping
        # caveat). shenandoah is the v0 VA watershed.
        if site.watershed not in ("shenandoah",):
            console.print(f"    virginia: skipping {site.watershed} (not a VA watershed)")
            return 0, 0

        total = 0
        with httpx.Client(
            timeout=30,
            headers={"User-Agent": "RiverSignal/1.0 (watershed-onboarding; +contact@liquidmarble.com)"},
        ) as client:
            for name, method_name in self.SUB_SOURCES:
                try:
                    method = getattr(self, method_name)
                    c = method(client, site)
                    total += c
                    console.print(f"    {name}: {c} records")
                except Exception as e:
                    console.print(f"    [yellow]{name}: {e}[/yellow]")
        return total, 0

    # ── Sub-source stubs — each returns 0 until follow-on beads implement ──

    def _ingest_dwr_stocking(self, client, site) -> int:
        """VA DWR weekly trout stocking schedule.

        Parses the DataTables HTML at VA_DWR_STOCKING_URL (table id=stocking-table)
        and inserts Shenandoah-attributable rows into `interventions` with
        type='fish_stocking'. The JSONB description matches the UDWR pattern so
        the existing `gold.stocking_schedule` MV's UDWR UNION branch picks rows
        up — source key is 'va_dwr' (the MV's UDWR predicate keys on 'udwr',
        so a follow-on bead must extend `gold.stocking_schedule` to UNION
        va_dwr rows too).
        """
        resp = client.get(VA_DWR_STOCKING_URL)
        resp.raise_for_status()
        html = resp.text

        m = re.search(
            r'<table[^>]*id=["\']stocking-table["\'][^>]*>(.*?)</table>',
            html, re.DOTALL | re.IGNORECASE,
        )
        if not m:
            console.print("      [yellow]VA DWR: stocking-table not found in HTML[/yellow]")
            return 0
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(1), re.DOTALL | re.IGNORECASE)

        # Dedup against existing rows by (date, waterbody, species). One
        # intervention per species, matching the UDWR pattern that
        # `gold.species_by_reach` and the photo-lookup endpoints expect.
        # Previously stored species as a JSON array, which the MV's
        # `description::jsonb ->> 'species'` then returned as the literal
        # string `["Brook Trout","Tiger Trout"]` and propagated to the UI.
        existing = self.session.execute(
            text(
                "SELECT description FROM interventions "
                "WHERE site_id = :sid AND type = 'fish_stocking' "
                "AND description::jsonb ->> 'source' = 'va_dwr'"
            ),
            {"sid": self.site_id},
        ).scalars().all()
        seen: set[tuple[str, str, str]] = set()
        for d in existing:
            try:
                j = json.loads(d)
                sp = j.get("species") or ""
                # Tolerate any legacy array-shape rows during the transition.
                if isinstance(sp, list):
                    for s in sp:
                        seen.add((j.get("stocking_date", ""), j.get("waterbody", "").lower(), (s or "").lower()))
                else:
                    seen.add((j.get("stocking_date", ""), j.get("waterbody", "").lower(), str(sp).lower()))
            except Exception:
                continue

        inserted = 0
        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            if len(cells) < 4:
                continue
            date_raw  = re.sub(r'<[^>]+>', '', cells[0]).strip()
            county    = re.sub(r'<[^>]+>', '', cells[1]).strip()
            waterbody = re.sub(r'<[^>]+>', '', cells[2]).strip()
            category  = re.sub(r'<[^>]+>', '', cells[3]).strip() if len(cells) > 3 else ""
            species_cell = cells[4] if len(cells) > 4 else cells[-1]
            species_list = [
                re.sub(r'<[^>]+>', '', li).strip()
                for li in re.findall(r'<li[^>]*>(.*?)</li>', species_cell, re.DOTALL | re.IGNORECASE)
            ]
            if not species_list:
                txt = re.sub(r'<[^>]+>', '', species_cell).strip()
                species_list = [s.strip() for s in re.split(r'[,;]| and ', txt) if s.strip()]
            # Drop empties; if still none, skip the row (a stocking with no
            # species attribution is uninteresting downstream).
            species_list = [s for s in species_list if s]
            if not species_list:
                continue

            if not _is_shenandoah_water(waterbody, county):
                continue

            started_at = None
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"):
                try:
                    started_at = datetime.strptime(date_raw, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
            if started_at is None:
                continue
            date_iso = started_at.date().isoformat()

            for species in species_list:
                key = (date_iso, waterbody.lower(), species.lower())
                if key in seen:
                    continue
                seen.add(key)

                desc = json.dumps({
                    "source": "va_dwr",
                    "waterbody": waterbody,
                    "county": county,
                    "category": category,
                    "species": species,       # scalar — one row per species
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

    def _ingest_dwr_regs(self, client, site) -> int:
        """VA DWR fishing regulations — special-regulation streams.

        TODO: HTML scrape or hand-curated seed migration of special-regulation
        streams (catch-and-release sections, slot limits, gear restrictions,
        seasonal closures). Update `silver.river_reaches.notes` with regulation
        summary for reaches that have one, so the TQS access sub-score can
        gate scores down on regulated reaches.

        For v0, static seed via alembic migration may be cleaner than a
        scraper — regulations change annually, not weekly.
        Follow-on bead: P2 VA DWR regulations seed migration.
        """
        console.print(f"      [dim]_ingest_dwr_regs: not yet implemented (scaffold)[/dim]")
        return 0

    def _ingest_vgs_geology(self, client, site) -> int:
        """DGMR (formerly VGS) — VA state geologic-unit polygons in bbox.

        Mirrors the DOGAMI pattern in pipeline/ingest/geology.py — ArcGIS
        REST polygons → geologic_units rows. VGS publishes no numeric ages
        (only formation labels like "Ob"/"Cb" that encode period), so
        age_min_ma/age_max_ma stay NULL like DOGAMI rows do.
        """
        bbox = site.bbox
        if not bbox:
            return 0
        features = _arcgis_query_paginated(client, VGS_GEOLOGY_MAPSERVER, bbox, max_per_page=1000)
        if not features:
            return 0

        SQL = text("""
            INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                rock_type, lithology, age_min_ma, age_max_ma, period, description,
                geometry, data_payload)
            VALUES (gen_random_uuid(), 'vgs', :source_id, :unit_name, :formation,
                :rock_type, :lithology, NULL, NULL, NULL, :description,
                ST_GeomFromGeoJSON(:geojson), CAST(:payload AS jsonb))
            ON CONFLICT DO NOTHING
        """)
        SQL_NO_GEOM = text("""
            INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                rock_type, lithology, age_min_ma, age_max_ma, period, description,
                data_payload)
            VALUES (gen_random_uuid(), 'vgs', :source_id, :unit_name, :formation,
                :rock_type, :lithology, NULL, NULL, NULL, :description,
                CAST(:payload AS jsonb))
            ON CONFLICT DO NOTHING
        """)

        # Dedup against any prior vgs rows for this bbox (re-runs are idempotent
        # at the (source, source_id) level since OBJECTID is stable per feature).
        existing_ids = {
            row[0] for row in self.session.execute(
                text("SELECT source_id FROM geologic_units WHERE source = 'vgs'")
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
                unit_name = (attrs.get("Symbol") or "")[:255]
                formation = (attrs.get("Label") or "")[:255]
                rock_type = (attrs.get("RockType1") or "")[:100]
                lithology = (attrs.get("RockType2") or "")[:255]
                description = attrs.get("Notes") or ""

                params = {
                    "source_id": source_id,
                    "unit_name": unit_name,
                    "formation": formation,
                    "rock_type": rock_type,
                    "lithology": lithology,
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

    def _ingest_dcr_parks(self, client, site) -> int:
        """VA DCR state parks within the watershed bbox.

        TODO: HTML scrape (or DCR API if available) for state parks. Insert
        into `recreation_sites` with rec_type='state_park' and
        source_type='va_dcr'.

        IMPORTANT: before authoring, verify whether VA state parks are
        already covered by the federal RIDB feed (the `recreation` adapter
        pulls RIDB and some states opt-in their state parks). If yes, skip
        this sub-source and close the bead as "covered by federal RIDB".
        Follow-on bead: P3 VA DCR state parks adapter (verify RIDB first).
        """
        console.print(f"      [dim]_ingest_dcr_parks: not yet implemented (scaffold)[/dim]")
        return 0
