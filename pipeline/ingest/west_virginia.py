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

import json

import httpx
from sqlalchemy import text

from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site


# ── Endpoints ───────────────────────────────────────────────────────────────

WV_DNR_STOCKING_URL = "https://wvdnr.gov/fishing/"
WV_DNR_REGS_URL     = "https://wvdnr.gov/wildlife/fishing-regulations/"
WVGES_ARCGIS_BASE   = "https://www.wvgs.wvnet.edu/"  # discover specific endpoints during impl
WV_STATE_PARKS_URL  = "https://wvstateparks.com/"

# WV DNR stocked-trout-streams data lives in an ArcGIS FeatureServer that
# powers the wvdnr.gov/fishing/fish-stocking/west-virginia-trout-stocking-map/
# page (via mapwv.gov/huntfish). It is a *registry of stocked streams*, not a
# dated stocking-event feed — there is no per-event schedule published as
# structured data. Per-event dates are only released via a phone hotline.
WV_DNR_STOCKED_STREAMS_FS = (
    "https://services9.arcgis.com/SQbkdxLkuQJuLGtx/ArcGIS/rest/services/"
    "West_Virginia_Stocked_Trout_Streams/FeatureServer/33/query"
)

# Shenandoah-drainage waters in WV. The Shenandoah only enters WV in
# Jefferson County (Harpers Ferry confluence), so the stocked-streams list
# is small. Berkeley County streams drain to the Potomac via Opequon /
# Back Creek, NOT the Shenandoah — they are deliberately excluded.
WV_SHENANDOAH_WATERS: tuple[str, ...] = (
    "bullskin run",
    "evitts run",
)


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
        """WV DNR stocked-trout-streams registry (NOT dated events).

        WV DNR exposes a list of stocked streams as an ArcGIS FeatureServer
        (see WV_DNR_STOCKED_STREAMS_FS). The schema has stream name, county,
        regulation type, hatchery, "stock extent" (a prose description of
        the stocked section), and mileage — but no per-event dates and no
        species per event. Dates are only released afterwards via the phone
        hotline (304-558-3399), with no machine-readable feed.

        Approach: pull the registry and upsert rows into `interventions`
        with type='fish_stocking', source='wv_dnr', and started_at=NULL.
        The frontend's gold MV branch for wv_dnr can render these as
        "stocked annually — date TBD". Surfacing them is a follow-on bead;
        this adapter's responsibility is to keep the registry current.
        """
        params = {
            "where": "County_1 IN ('Jefferson') OR County_2 IN ('Jefferson') OR County_3 IN ('Jefferson')",
            "outFields": "Name,RegType,Hatchery,NearCity,County_1,County_2,County_3,StockExtent,Mileage",
            "returnGeometry": "false",
            "f": "json",
        }
        resp = client.get(WV_DNR_STOCKED_STREAMS_FS, params=params)
        resp.raise_for_status()
        features = resp.json().get("features", [])

        existing = self.session.execute(
            text(
                "SELECT description FROM interventions "
                "WHERE site_id = :sid AND type = 'fish_stocking' "
                "AND description LIKE '{%' "
                "AND description::jsonb ->> 'source' = 'wv_dnr'"
            ),
            {"sid": self.site_id},
        ).scalars().all()
        seen: set[str] = set()
        for d in existing:
            try:
                seen.add(json.loads(d).get("waterbody", "").lower())
            except Exception:
                continue

        inserted = 0
        for feat in features:
            attrs = feat.get("attributes", {})
            name = (attrs.get("Name") or "").strip()
            if not name or name.lower() not in WV_SHENANDOAH_WATERS:
                continue
            if name.lower() in seen:
                continue
            seen.add(name.lower())

            counties = [
                c for c in (attrs.get("County_1"), attrs.get("County_2"), attrs.get("County_3"))
                if c and c.strip()
            ]
            desc = json.dumps({
                "source": "wv_dnr",
                "waterbody": name,
                "county": counties[0] if counties else None,
                "counties": counties,
                "regulation": attrs.get("RegType"),
                "hatchery": attrs.get("Hatchery"),
                "nearest_city": attrs.get("NearCity"),
                "stock_extent": attrs.get("StockExtent"),
                "mileage": attrs.get("Mileage"),
                "_data_shape": "stream_registry",
            }, ensure_ascii=False)

            self.session.execute(
                text(
                    "INSERT INTO interventions (id, site_id, type, description, started_at, created_at) "
                    "VALUES (gen_random_uuid(), :sid, 'fish_stocking', :desc, NULL, now())"
                ),
                {"sid": self.site_id, "desc": desc},
            )
            inserted += 1

        return inserted

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
