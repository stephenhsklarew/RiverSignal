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

from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site


# ── Endpoints ───────────────────────────────────────────────────────────────

VA_DWR_STOCKING_URL = "https://dwr.virginia.gov/fishing/trout-stocking-schedule/"
VA_DWR_REGS_URL     = "https://dwr.virginia.gov/fishing/regulations/"
VGS_ARCGIS_BASE     = "https://services.arcgis.com/p5v98VHDX9Atv3l7/ArcGIS/rest/services"
VA_DCR_PARKS_URL    = "https://www.dcr.virginia.gov/state-parks/"


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

        TODO: HTML scrape of VA_DWR_STOCKING_URL.
          - Identify the stocking-table CSS selector (DOM inspection needed).
          - Parse rows: water_name, county, stocking_date, species, fish_count.
          - Map water_name → reach_id heuristically (lookup `silver.river_reaches`
            for the watershed; match by lowercase substring on `name`).
          - Insert into `interventions` table with intervention_type='stocking',
            source_type='va_dwr', site_id=self.site_id.
          - Existing `gold.stocking_schedule` MV will pick up rows automatically.
        Follow-on bead: P1 VA DWR stocking adapter implementation.
        """
        console.print(f"      [dim]_ingest_dwr_stocking: not yet implemented (scaffold)[/dim]")
        return 0

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
        """VGS geologic units intersecting the watershed bbox.

        TODO: ArcGIS REST query against VGS FeatureServer for geologic units
        within site.bbox. Insert into `geologic_units` table (same schema as
        macrostrat + DOGAMI rows). source_type='vgs'.
        Follow-on bead: P2 VGS geology adapter (discover ArcGIS endpoint;
        DMME may have moved to a successor agency in recent VA reorgs).
        """
        console.print(f"      [dim]_ingest_vgs_geology: not yet implemented (scaffold)[/dim]")
        return 0

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
