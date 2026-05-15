"""West Virginia state data source adapters.

Source: WV Division of Natural Resources (WVDNR), WV Dept of Environmental
Protection (WVDEP), WV Geological & Economic Survey (WVGES), WV Division
of Tourism (state parks).
License: Public Records (WV Code §29B-1 — West Virginia Freedom of
Information Act).
commercial: true (Public Records are commercially usable; attribution
to the agency in any commercial surface is good practice).
Attribution: "Data from <agency name>, <agency URL>".

SCAFFOLD STATUS (2026-05-15): adapter class, watershed-scoping guard, source
URL constants, cli.py registration, SOURCE_REFRESH_HOURS + SOURCE_LABELS
entries are all in place. Per-source parsing methods are TODO — each emits
`console.print("...not yet implemented")` and returns 0 rows.

Follow-on beads (one per sub-source):
  - P1  WV DNR weekly trout stocking → interventions table
        Source: https://wvdnr.gov/fishing/
  - P2  WV DNR fishing regulations → static seed
        Source: https://wvdnr.gov/wildlife/fishing-regulations/
  - P3  WVGES geologic units → geologic_units table
        Source: https://www.wvgs.wvnet.edu/
  - P3  WV State Parks → recreation_sites table
        Source: https://wvstateparks.com/
        (Check RIDB coverage first — WV state parks may already be there)
"""

import httpx

from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site


# ── Endpoints ───────────────────────────────────────────────────────────────

WV_DNR_STOCKING_URL = "https://wvdnr.gov/fishing/"
WV_DNR_REGS_URL     = "https://wvdnr.gov/wildlife/fishing-regulations/"
WVGES_ARCGIS_BASE   = "https://www.wvgs.wvnet.edu/"  # discover specific endpoints during impl
WV_STATE_PARKS_URL  = "https://wvstateparks.com/"


# ── Adapter ─────────────────────────────────────────────────────────────────

class WestVirginiaDataAdapter(IngestionAdapter):
    """Bundled adapter for West Virginia state data sources.

    Mirrors the utah.py / washington.py / virginia.py pattern.
    """
    source_type = "west_virginia"

    SUB_SOURCES: list[tuple[str, str]] = [
        ("WV DNR Stocking",     "_ingest_dnr_stocking"),
        ("WV DNR Regulations",  "_ingest_dnr_regs"),
        ("WVGES Geology",       "_ingest_wvges_geology"),
        ("WV State Parks",      "_ingest_state_parks"),
    ]

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site:
            return 0, 0

        # Only run for WV watersheds. Currently shenandoah is the v0 WV-adjacent
        # watershed (its main stem crosses into WV at Harpers Ferry).
        # Add new WV watersheds to this tuple as they're onboarded.
        if site.watershed not in ("shenandoah",):
            console.print(f"    west_virginia: skipping {site.watershed} (not a WV watershed)")
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

    # ── Sub-source stubs ────────────────────────────────────────────────────

    def _ingest_dnr_stocking(self, client, site) -> int:
        """WV DNR weekly trout stocking schedule.
        TODO: HTML scrape of WV_DNR_STOCKING_URL. Same shape as VA DWR
        stocking — water_name, county, date, species, count → interventions.
        Follow-on bead: P1 WV DNR stocking adapter implementation.
        """
        console.print(f"      [dim]_ingest_dnr_stocking: not yet implemented (scaffold)[/dim]")
        return 0

    def _ingest_dnr_regs(self, client, site) -> int:
        """WV DNR fishing regulations.
        TODO: HTML scrape OR static seed migration of special-regulation
        streams + closures. Same pattern as VA.
        Follow-on bead: P2 WV DNR regulations seed migration.
        """
        console.print(f"      [dim]_ingest_dnr_regs: not yet implemented (scaffold)[/dim]")
        return 0

    def _ingest_wvges_geology(self, client, site) -> int:
        """WVGES geologic units within site bbox.
        TODO: discover ArcGIS REST endpoint (or download Shapefile if no
        live service). Insert into geologic_units. source_type='wvges'.
        Follow-on bead: P3 WVGES geology adapter.
        """
        console.print(f"      [dim]_ingest_wvges_geology: not yet implemented (scaffold)[/dim]")
        return 0

    def _ingest_state_parks(self, client, site) -> int:
        """WV state parks within site bbox.
        TODO: HTML scrape of WV_STATE_PARKS_URL or use federal RIDB.
        Insert into recreation_sites with rec_type='state_park',
        source_type='wv_state_parks'.

        IMPORTANT: verify RIDB coverage first (the `recreation` adapter
        pulls RIDB; some states opt-in their state parks). If covered,
        close the bead as "covered by federal RIDB".
        Follow-on bead: P3 WV state parks adapter (verify RIDB first).
        """
        console.print(f"      [dim]_ingest_state_parks: not yet implemented (scaffold)[/dim]")
        return 0
