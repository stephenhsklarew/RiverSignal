"""Recreation data ingestion — multi-source adapter.

Tier 1 (no key, ArcGIS):
  - OSMB Boating Access Sites (1,815 OR sites) — boat ramps, hand launches
  - USFS Recreation Opportunities (2,164 OR sites) — campgrounds, trailheads, picnic areas
  - BLM Recreation Sites (129 OR sites) — campgrounds, day-use
  - SARP Waterfall Database (5,407 sites) — waterfalls with height, fish ladder status
  - Oregon State Parks (422 parcels) — park boundaries
  - Oregon HABs Advisories (245 sites) — harmful algal bloom swim warnings

Tier 2 (free key):
  - RIDB / Recreation.gov — federal campgrounds with reservability, fees, photos
"""

import json
import os
import time

import httpx
from rich.console import Console
from sqlalchemy import text

from pipeline.ingest.base import IngestionAdapter
from pipeline.models import Site

console = Console()

# ── Tier 1: ArcGIS FeatureServer / REST endpoints (no key) ──

OSMB_BOATING_URL = (
    "https://maps.prd.state.or.us/arcgis/rest/services/Framework/"
    "Boat_Access_Sites_Oregon/FeatureServer/0/query"
)

USFS_REC_URL = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/"
    "EDW_RecreationOpportunities_01/MapServer/0/query"
)

BLM_REC_URL = (
    "https://gis.blm.gov/arcgis/rest/services/recreation/"
    "BLM_Natl_Recreation_Sites/FeatureServer/0/query"
)

SARP_WATERFALLS_URL = (
    "https://services2.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/"
    "SARP_Aquatic_Barrier_Prioritization_Waterfalls/FeatureServer/0/query"
)

OR_STATE_PARKS_URL = (
    "https://navigator.state.or.us/arcgis/rest/services/Framework/"
    "Govt_BndPLSSEtc/MapServer/14/query"
)

OR_HABS_URL = (
    "https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/"
    "Oregon_Harmful_Algal_Blooms/FeatureServer/0/query"
)

# ── Tier 2: REST with key ──
RIDB_BASE = "https://ridb.recreation.gov/api/v1"


def _arcgis_bbox_query(client, url, bbox, extra_params=None, max_records=2000):
    """Generic ArcGIS REST query with bounding box envelope.

    bbox can be a dict {west, south, east, north} or a list [west, south, east, north].
    """
    if isinstance(bbox, dict):
        geom_str = f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}"
    else:
        geom_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
    params = {
        "geometry": geom_str,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "where": "1=1",
        "outFields": "*",
        "f": "json",
        "resultRecordCount": str(max_records),
    }
    if extra_params:
        params.update(extra_params)

    for attempt in range(3):
        try:
            resp = client.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("features", [])
        except (httpx.ConnectError, httpx.ReadTimeout):
            time.sleep(3)
    return []


class RecreationAdapter(IngestionAdapter):
    """Multi-source recreation site ingestion."""

    source_type = "recreation"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            return 0, 0

        bbox = site.bbox  # [west, south, east, north]
        job = self.create_job()
        self._ensure_table()

        total_created = 0
        total_updated = 0

        try:
            with httpx.Client(timeout=30) as client:
                # Each source is independent — failures don't block others
                for name, method in [
                    ("OSMB boating", self._ingest_osmb),
                    ("USFS recreation", self._ingest_usfs_rec),
                    ("BLM recreation", self._ingest_blm_rec),
                    ("SARP waterfalls", self._ingest_waterfalls),
                    ("Oregon HABs", self._ingest_habs),
                    ("RIDB", self._ingest_ridb),
                ]:
                    try:
                        c, u = method(client, site, bbox)
                        total_created += c; total_updated += u
                    except Exception as e:
                        console.print(f"  [yellow]{name}: skipped ({e})[/yellow]")

            self.session.commit()
            self.complete_job(job, total_created, total_updated)
            console.print(
                f"  [green]Recreation total: {total_created} created, "
                f"{total_updated} updated for {site.watershed}[/green]"
            )

        except Exception as e:
            self.session.rollback()
            job.status = "failed"
            job.error_message = str(e)[:500]
            self.session.commit()
            console.print(f"  [red]Recreation ingestion failed: {e}[/red]")

        return total_created, total_updated

    # ── Tier 1 sources ──

    def _ingest_osmb(self, client, site, bbox) -> tuple[int, int]:
        """Oregon State Marine Board boating access sites."""
        features = _arcgis_bbox_query(client, OSMB_BOATING_URL, bbox)
        console.print(f"  OSMB boating: {len(features)} features")
        created = updated = 0
        for f in features:
            attr = f.get("attributes", {})
            geom = f.get("geometry", {})
            lat = geom.get("y")
            lon = geom.get("x")
            if not lat or not lon:
                continue
            name = attr.get("Waterbody_Name", "") or attr.get("SITE_NAME", "") or "Unnamed"
            site_name = attr.get("SITE_NAME", "")
            if site_name and site_name != name:
                name = f"{site_name} — {name}"
            amenities = {
                "fee": bool(attr.get("Fee")),
                "restrooms": bool(attr.get("Restroom")),
                "parking": bool(attr.get("Parking")),
                "accessible": bool(attr.get("ADA")),
                "pets_allowed": True,  # most boat ramps allow dogs
            }
            c, u = self._upsert(site, "osmb", str(attr.get("OBJECTID", "")),
                                name, "boat_ramp", lat, lon, amenities, attr)
            created += c; updated += u
        return created, updated

    def _ingest_usfs_rec(self, client, site, bbox) -> tuple[int, int]:
        """USFS Recreation Opportunities — campgrounds, trailheads, picnic areas."""
        features = _arcgis_bbox_query(client, USFS_REC_URL, bbox)
        console.print(f"  USFS recreation: {len(features)} features")
        created = updated = 0
        for f in features:
            attr = f.get("attributes", {})
            geom = f.get("geometry", {})
            # USFS provides lat/lon both in attributes and geometry
            lat = attr.get("LATITUDE") or geom.get("y")
            lon = attr.get("LONGITUDE") or geom.get("x")
            if not lat or not lon:
                continue
            name = attr.get("RECAREANAME", "") or "Unnamed"
            activity = (attr.get("MARKERACTIVITY", "") or "").lower()
            activity_group = (attr.get("MARKERACTIVITYGROUP", "") or "").lower()
            rec_type = self._classify_usfs_activity(f"{activity} {activity_group}", name)
            amenities = {
                "fee": bool(attr.get("FEEDESCRIPTION")),
                "accessible": bool(attr.get("ACCESSIBILITY")),
                "reservable": bool(attr.get("RESERVATION_INFO")),
                "pets_allowed": True,
                "forest": attr.get("FORESTNAME", ""),
                "season_start": attr.get("OPEN_SEASON_START", ""),
                "season_end": attr.get("OPEN_SEASON_END", ""),
                "status": attr.get("OPENSTATUS", ""),
            }
            c, u = self._upsert(site, "usfs_rec", str(attr.get("OBJECTID", "")),
                                name, rec_type, lat, lon, amenities, attr)
            created += c; updated += u
        return created, updated

    def _ingest_blm_rec(self, client, site, bbox) -> tuple[int, int]:
        """BLM recreation sites — campgrounds, day-use."""
        features = _arcgis_bbox_query(client, BLM_REC_URL, bbox)
        console.print(f"  BLM recreation: {len(features)} features")
        created = updated = 0
        for f in features:
            attr = f.get("attributes", {})
            geom = f.get("geometry", {})
            lat = geom.get("y")
            lon = geom.get("x")
            if not lat or not lon:
                continue
            name = attr.get("FET_NAME", "") or "Unnamed"
            ftype = (attr.get("FET_TYPE", "") or "").lower()
            rec_type = "campground" if "camp" in ftype else "day_use"
            amenities = {
                "fee": bool(attr.get("FEE_YN")),
                "accessible": bool(attr.get("ACCESSIBLE_YN")),
                "pets_allowed": True,
            }
            c, u = self._upsert(site, "blm_rec", str(attr.get("OBJECTID", "")),
                                name, rec_type, lat, lon, amenities, attr)
            created += c; updated += u
        return created, updated

    def _ingest_waterfalls(self, client, site, bbox) -> tuple[int, int]:
        """SARP waterfall database."""
        features = _arcgis_bbox_query(client, SARP_WATERFALLS_URL, bbox)
        console.print(f"  SARP waterfalls: {len(features)} features")
        created = updated = 0
        for f in features:
            attr = f.get("attributes", {})
            geom = f.get("geometry", {})
            lat = geom.get("y")
            lon = geom.get("x")
            if not lat or not lon:
                continue
            name = attr.get("Name", "") or attr.get("name", "") or "Unnamed Waterfall"
            height_ft = attr.get("Height", None) or attr.get("height", None)
            amenities = {}
            if height_ft:
                amenities["height_ft"] = height_ft
            c, u = self._upsert(site, "sarp", str(attr.get("OBJECTID", attr.get("FID", ""))),
                                name, "waterfall", lat, lon, amenities, attr)
            created += c; updated += u
        return created, updated

    def _ingest_habs(self, client, site, bbox) -> tuple[int, int]:
        """Oregon harmful algal bloom advisories — swim safety."""
        features = _arcgis_bbox_query(client, OR_HABS_URL, bbox)
        console.print(f"  Oregon HABs: {len(features)} features")
        created = updated = 0
        for f in features:
            attr = f.get("attributes", {})
            geom = f.get("geometry", {})
            lat = geom.get("y")
            lon = geom.get("x")
            if not lat or not lon:
                continue
            name = attr.get("Waterbody", "") or attr.get("waterbody", "") or "Unnamed"
            status = attr.get("Advisory_Status", "") or attr.get("Status", "")
            amenities = {"advisory_status": status}
            c, u = self._upsert(site, "habs", str(attr.get("OBJECTID", "")),
                                f"{name} — HABs Advisory", "swim_advisory", lat, lon,
                                amenities, attr)
            created += c; updated += u
        return created, updated

    # ── Tier 2: RIDB (key required) ──

    def _ingest_ridb(self, client, site, bbox) -> tuple[int, int]:
        """USFS RIDB — federal campgrounds with reservation data."""
        api_key = os.environ.get("RIDB_API_KEY")
        if not api_key:
            console.print("  [dim]RIDB: skipped (RIDB_API_KEY not set)[/dim]")
            return 0, 0

        if isinstance(bbox, dict):
            center_lat = (bbox['south'] + bbox['north']) / 2
            center_lon = (bbox['west'] + bbox['east']) / 2
        else:
            center_lat = (bbox[1] + bbox[3]) / 2
            center_lon = (bbox[0] + bbox[2]) / 2
        params = {
            "latitude": center_lat,
            "longitude": center_lon,
            "radius": 50,
            "limit": 200,
            "apikey": api_key,
        }
        try:
            resp = client.get(f"{RIDB_BASE}/facilities", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"  [yellow]RIDB: failed ({e})[/yellow]")
            return 0, 0

        facilities = data.get("RECDATA", [])
        console.print(f"  RIDB: {len(facilities)} facilities")
        created = updated = 0

        for fac in facilities:
            fac_id = str(fac.get("FacilityID", ""))
            name = fac.get("FacilityName", "")
            lat = fac.get("FacilityLatitude")
            lon = fac.get("FacilityLongitude")
            if not lat or not lon:
                continue
            fac_type = (fac.get("FacilityTypeDescription", "") or "").lower()
            rec_type = self._classify_type(fac_type, name)
            amenities = {
                "pets_allowed": fac.get("FacilityPetsAllowed", False),
                "accessible": fac.get("FacilityAdaAccess", "") != "",
                "reservable": fac.get("Reservable", False),
                "fee": fac.get("FacilityUseFeeDescription", "") != "",
            }
            c, u = self._upsert(site, "ridb", fac_id, name, rec_type, lat, lon,
                                amenities, fac)
            created += c; updated += u

        return created, updated

    # ── Shared helpers ──

    def _upsert(self, site, source_type, source_id, name, rec_type,
                lat, lon, amenities, raw_payload) -> tuple[int, int]:
        """Insert or update a recreation site. Returns (created, updated)."""
        amenities_json = json.dumps(amenities)
        payload_json = json.dumps({
            k: v for k, v in (raw_payload or {}).items()
            if isinstance(v, (str, int, float, bool, type(None)))
        })

        result = self.session.execute(text("""
            INSERT INTO recreation_sites
                (site_id, source_type, source_id, name, rec_type,
                 latitude, longitude, geom, amenities, data_payload)
            VALUES
                (:site_id, :src_type, :src_id, :name, :rec_type,
                 :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                 CAST(:amenities AS jsonb), CAST(:payload AS jsonb))
            ON CONFLICT (source_type, source_id) DO UPDATE SET
                name = EXCLUDED.name, rec_type = EXCLUDED.rec_type,
                amenities = EXCLUDED.amenities, data_payload = EXCLUDED.data_payload
            RETURNING (xmax = 0) as inserted
        """), {
            "site_id": site.id,
            "src_type": source_type,
            "src_id": source_id,
            "name": name[:255],
            "rec_type": rec_type,
            "lat": lat, "lon": lon,
            "amenities": amenities_json,
            "payload": payload_json,
        })
        row = result.fetchone()
        if row and row[0]:
            return 1, 0
        return 0, 1

    def _ensure_table(self):
        """Create recreation_sites table if it doesn't exist."""
        self.session.execute(text("""
            CREATE TABLE IF NOT EXISTS recreation_sites (
                id SERIAL PRIMARY KEY,
                site_id UUID REFERENCES sites(id),
                source_type VARCHAR NOT NULL DEFAULT 'unknown',
                source_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                rec_type VARCHAR,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                geom geometry(Point, 4326),
                amenities JSONB DEFAULT '{}',
                family_suitable BOOLEAN,
                difficulty VARCHAR,
                description TEXT,
                url VARCHAR,
                data_payload JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE(source_type, source_id)
            )
        """))
        self.session.commit()

    @staticmethod
    def _classify_type(fac_type: str, name: str) -> str:
        """Map facility type string to normalized recreation category."""
        combined = f"{fac_type} {name}".lower()
        if "campground" in combined or "camping" in combined:
            return "campground"
        if "trailhead" in combined or "trail" in combined:
            return "trailhead"
        if "boat" in combined or "launch" in combined or "ramp" in combined:
            return "boat_ramp"
        if "fishing" in combined or "angler" in combined:
            return "fishing_access"
        if "waterfall" in combined or "falls" in combined:
            return "waterfall"
        if "picnic" in combined:
            return "day_use"
        return "day_use"

    @staticmethod
    def _classify_usfs_activity(activity: str, name: str) -> str:
        """Classify USFS rec opportunity by activity description."""
        combined = f"{activity} {name}".lower()
        if "camping" in combined or "campground" in combined:
            return "campground"
        if "trail" in combined or "hiking" in combined:
            return "trailhead"
        if "boat" in combined or "kayak" in combined or "canoe" in combined:
            return "boat_ramp"
        if "fishing" in combined:
            return "fishing_access"
        if "picnic" in combined or "day use" in combined:
            return "day_use"
        if "swimming" in combined:
            return "swim_area"
        return "day_use"
