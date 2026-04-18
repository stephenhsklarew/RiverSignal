"""Washington state data source adapters.

Covers Washington-specific public data sources that parallel Oregon's
ODFW, OWRI, DOGAMI, OSMB, and Oregon State Parks adapters.

Sources:
  1. WDFW SalmonScape — fish species distribution (ArcGIS MapServer)
  2. WDFW Fish Stocking — release/planting data (Socrata SODA API on data.wa.gov)
  3. WA DNR Surface Geology — 100K state geologic map (ArcGIS MapServer)
  4. SRFB/RCO Salmon Recovery — restoration projects (ArcGIS MapServer)
  5. WA State Parks — park boundaries, boat launches, activities (ArcGIS FeatureServer)
  6. WDFW Water Access — boat ramps, hand launches (ArcGIS FeatureServer)
"""

import time
import uuid
from datetime import datetime, timezone

import httpx
from rich.console import Console
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter
from pipeline.models import Site

console = Console()

# ── Endpoints ──

SALMONSCAPE_URL = (
    "https://geodataservices.wdfw.wa.gov/arcgis/rest/services/"
    "MapServices/SWIFD/MapServer/0/query"
)

WDFW_STOCKING_URL = "https://data.wa.gov/resource/6fex-3r7d.json"

WA_GEOLOGY_URL = (
    "https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/"
    "100K_Surface_Geology_WA_GeMS/MapServer/12/query"
)

SRFB_PROJECTS_URL = (
    "https://gismanager.rco.wa.gov/arcgis/rest/services/"
    "Public_SRP_Primary_Worksites/MapServer/0/query"
)

WA_PARKS_URL = (
    "https://services5.arcgis.com/4LKAHwqnBooVDUlX/arcgis/rest/services/"
    "ParkBoundaries/FeatureServer/2/query"
)

WA_PARK_LAUNCHES_URL = (
    "https://services5.arcgis.com/4LKAHwqnBooVDUlX/arcgis/rest/services/"
    "WAStateParks_BoatLaunches/FeatureServer/0/query"
)

WDFW_WATER_ACCESS_URL = (
    "https://geodataservices.wdfw.wa.gov/arcgis/rest/services/"
    "WP_RealEstate/WaterAccessSites/FeatureServer/1/query"
)

# Skagit-area counties for stocking data filter
SKAGIT_COUNTIES = ["Skagit", "Whatcom", "Snohomish"]
SKAGIT_LOCATIONS = ["Skagit", "Sauk", "Baker", "Cascade", "Suiattle", "Nookachamps"]


def _arcgis_query(client, url, bbox, extra_params=None, max_records=2000):
    """Generic ArcGIS REST query with bounding box."""
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
            resp = client.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("features", [])
        except (httpx.ConnectError, httpx.ReadTimeout):
            time.sleep(3)
    return []


class WashingtonDataAdapter(IngestionAdapter):
    """Combined adapter for Washington state data sources."""
    source_type = "washington"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            return 0, 0

        # Only run for Washington watersheds
        if site.watershed not in ("skagit",):
            console.print(f"    washington: skipping {site.watershed} (not a WA watershed)")
            return 0, 0

        bbox = site.bbox
        total = 0

        with httpx.Client(timeout=60) as client:
            for name, method in [
                ("WDFW SalmonScape", self._ingest_salmonscape),
                ("WDFW Stocking", self._ingest_stocking),
                ("WA DNR Geology", self._ingest_wa_geology),
                ("SRFB Restoration", self._ingest_srfb),
                ("WA State Parks", self._ingest_wa_parks),
                ("WDFW Water Access", self._ingest_water_access),
            ]:
                try:
                    c = method(client, site, bbox)
                    total += c
                    console.print(f"    {name}: {c} records")
                except Exception as e:
                    console.print(f"    [yellow]{name}: {e}[/yellow]")

        return total, 0

    def _ingest_salmonscape(self, client, site, bbox) -> int:
        """WDFW SalmonScape fish species distribution."""
        features = _arcgis_query(client, SALMONSCAPE_URL, bbox)
        if not features:
            return 0

        created = 0
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wa_salmonscape (
                    id SERIAL PRIMARY KEY,
                    site_id UUID REFERENCES sites(id),
                    stream_name VARCHAR,
                    species VARCHAR,
                    species_run VARCHAR,
                    distribution_type VARCHAR,
                    use_type VARCHAR,
                    life_history VARCHAR,
                    length_mi FLOAT,
                    llid VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(site_id, llid, species, species_run)
                )
            """))

            for f in features:
                a = f.get("attributes", {})
                stream = a.get("LLID_STRM_NAME") or a.get("StreamName") or ""
                species = a.get("SPECIES") or a.get("Species") or ""
                if not species:
                    continue
                conn.execute(text("""
                    INSERT INTO wa_salmonscape (site_id, stream_name, species, species_run,
                        distribution_type, use_type, life_history, length_mi, llid)
                    VALUES (:sid, :stream, :species, :run, :dist, :use, :life, :len, :llid)
                    ON CONFLICT (site_id, llid, species, species_run) DO UPDATE SET
                        distribution_type = EXCLUDED.distribution_type,
                        use_type = EXCLUDED.use_type
                """), {
                    "sid": site.id, "stream": stream,
                    "species": species,
                    "run": a.get("SPECIESRUN") or a.get("SpeciesRun") or "",
                    "dist": a.get("DISTTYPE_DESC") or a.get("DistType") or "",
                    "use": a.get("USETYPE_DESC") or a.get("UseType") or "",
                    "life": a.get("LIFEHIST_DESC") or a.get("LifeHist") or "",
                    "len": a.get("Length_mi") or a.get("SHAPE.STLength()"),
                    "llid": a.get("LLID") or "",
                })
                created += 1

        return created

    def _ingest_stocking(self, client, site, bbox) -> int:
        """WDFW fish stocking/planting data from data.wa.gov Socrata API."""
        created = 0
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wa_fish_stocking (
                    id SERIAL PRIMARY KEY,
                    site_id UUID REFERENCES sites(id),
                    release_location VARCHAR,
                    county VARCHAR,
                    species VARCHAR,
                    run VARCHAR,
                    number_released INTEGER,
                    release_date DATE,
                    release_year INTEGER,
                    lifestage VARCHAR,
                    origin VARCHAR,
                    stock VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(site_id, release_location, species, run, release_date)
                )
            """))

            # Query by county (Socrata SoQL — county values have trailing spaces)
            county_filter = " OR ".join(
                f"starts_with(county, '{c}')" for c in SKAGIT_COUNTIES
            )
            where = f"({county_filter})"

            offset = 0
            while True:
                url = f"{WDFW_STOCKING_URL}?$where={where}&$limit=1000&$offset={offset}&$order=release_start_date DESC"
                try:
                    resp = client.get(url, timeout=30)
                    if resp.status_code != 200:
                        break
                    rows = resp.json()
                    if not rows:
                        break
                except Exception:
                    break

                for r in rows:
                    release_date = None
                    if r.get("release_start_date"):
                        try:
                            release_date = r["release_start_date"][:10]
                        except Exception:
                            pass
                    num = None
                    try:
                        num = int(float(r.get("number_released", 0)))
                    except (ValueError, TypeError):
                        pass

                    conn.execute(text("""
                        INSERT INTO wa_fish_stocking (site_id, release_location, county,
                            species, run, number_released, release_date, release_year,
                            lifestage, origin, stock)
                        VALUES (:sid, :loc, :county, :species, :run, :num, :date, :year,
                            :stage, :origin, :stock)
                        ON CONFLICT (site_id, release_location, species, run, release_date)
                        DO UPDATE SET number_released = EXCLUDED.number_released
                    """), {
                        "sid": site.id,
                        "loc": r.get("release_location", ""),
                        "county": r.get("county", ""),
                        "species": r.get("species", ""),
                        "run": r.get("run", ""),
                        "num": num,
                        "date": release_date,
                        "year": r.get("release_year"),
                        "stage": r.get("lifestage", ""),
                        "origin": r.get("origin", ""),
                        "stock": r.get("stock", ""),
                    })
                    created += 1

                if len(rows) < 1000:
                    break
                offset += 1000
                time.sleep(0.5)

        return created

    def _ingest_wa_geology(self, client, site, bbox) -> int:
        """WA DNR 100K surface geology map units."""
        features = _arcgis_query(client, WA_GEOLOGY_URL, bbox)
        if not features:
            return 0

        created = 0
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wa_surface_geology (
                    id SERIAL PRIMARY KEY,
                    site_id UUID REFERENCES sites(id),
                    map_unit VARCHAR,
                    map_unit_label VARCHAR,
                    map_unit_notes TEXT,
                    original_unit VARCHAR,
                    quad_name VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(site_id, map_unit, quad_name)
                )
            """))

            for f in features:
                a = f.get("attributes", {})
                unit = a.get("MAP_UNIT_100K") or a.get("map_unit_100k") or ""
                if not unit:
                    continue
                conn.execute(text("""
                    INSERT INTO wa_surface_geology (site_id, map_unit, map_unit_label,
                        map_unit_notes, original_unit, quad_name)
                    VALUES (:sid, :unit, :label, :notes, :orig, :quad)
                    ON CONFLICT (site_id, map_unit, quad_name) DO NOTHING
                """), {
                    "sid": site.id,
                    "unit": unit,
                    "label": a.get("MAP_UNIT_100K_LABEL") or "",
                    "notes": a.get("MAP_UNIT_100K_NOTES") or "",
                    "orig": a.get("MAP_UNIT_ORIGINAL") or "",
                    "quad": a.get("MAP_UNIT_100K_QUAD_NAME") or "",
                })
                created += 1

        return created

    def _ingest_srfb(self, client, site, bbox) -> int:
        """SRFB/RCO salmon recovery restoration projects."""
        features = _arcgis_query(client, SRFB_PROJECTS_URL, bbox)
        if not features:
            return 0

        created = 0
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wa_srfb_projects (
                    id SERIAL PRIMARY KEY,
                    site_id UUID REFERENCES sites(id),
                    project_name VARCHAR,
                    project_description TEXT,
                    project_type VARCHAR,
                    project_status VARCHAR,
                    lead_entity VARCHAR,
                    sponsor VARCHAR,
                    funded_amount FLOAT,
                    start_date VARCHAR,
                    end_date VARCHAR,
                    latitude FLOAT,
                    longitude FLOAT,
                    prism_number VARCHAR,
                    public_url VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(site_id, prism_number)
                )
            """))

            for f in features:
                a = f.get("attributes", {})
                g = f.get("geometry", {})
                name = a.get("ProjectName") or ""
                prism = a.get("PRISMProjectNumber") or a.get("ProjectNumber") or name
                if not prism:
                    continue
                conn.execute(text("""
                    INSERT INTO wa_srfb_projects (site_id, project_name, project_description,
                        project_type, project_status, lead_entity, sponsor, funded_amount,
                        start_date, end_date, latitude, longitude, prism_number, public_url)
                    VALUES (:sid, :name, :desc, :type, :status, :lead, :sponsor, :amt,
                        :start, :end, :lat, :lon, :prism, :url)
                    ON CONFLICT (site_id, prism_number) DO UPDATE SET
                        project_status = EXCLUDED.project_status,
                        funded_amount = EXCLUDED.funded_amount
                """), {
                    "sid": site.id,
                    "name": name,
                    "desc": a.get("ProjectDescription") or "",
                    "type": a.get("ProjectType") or a.get("PRISMProjectCategoryList") or "",
                    "status": a.get("ProjectDetailStatus") or a.get("ProjectStatus") or "",
                    "lead": a.get("LeadEntityName") or "",
                    "sponsor": a.get("PrimarySponsorName") or "",
                    "amt": a.get("ProjectFundedAmt"),
                    "start": a.get("ProjectStartDate") or "",
                    "end": a.get("ProjectEndDate") or "",
                    "lat": g.get("y"),
                    "lon": g.get("x"),
                    "prism": prism,
                    "url": a.get("SRPProjectPublicURL") or "",
                })
                created += 1

        return created

    def _ingest_wa_parks(self, client, site, bbox) -> int:
        """WA State Parks boundaries and boat launches."""
        created = 0

        # Park boundaries
        parks = _arcgis_query(client, WA_PARKS_URL, bbox, max_records=500)
        # Boat launches
        launches = _arcgis_query(client, WA_PARK_LAUNCHES_URL, bbox, max_records=500)

        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wa_state_parks (
                    id SERIAL PRIMARY KEY,
                    site_id UUID REFERENCES sites(id),
                    park_name VARCHAR,
                    category VARCHAR,
                    park_code VARCHAR,
                    web_page VARCHAR,
                    description TEXT,
                    latitude FLOAT,
                    longitude FLOAT,
                    acres FLOAT,
                    region VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(site_id, park_code)
                )
            """))

            for f in parks:
                a = f.get("attributes", {})
                code = a.get("ParkCode") or a.get("PARKCODE") or ""
                if not code:
                    continue
                conn.execute(text("""
                    INSERT INTO wa_state_parks (site_id, park_name, category, park_code,
                        web_page, description, latitude, longitude, acres, region)
                    VALUES (:sid, :name, :cat, :code, :web, :desc, :lat, :lon, :acres, :region)
                    ON CONFLICT (site_id, park_code) DO NOTHING
                """), {
                    "sid": site.id,
                    "name": a.get("ParkName") or "",
                    "cat": a.get("Category") or "",
                    "code": code,
                    "web": a.get("WebPage") or "",
                    "desc": a.get("Description") or "",
                    "lat": a.get("Lat_Entrance"),
                    "lon": a.get("Long_Entrance"),
                    "acres": a.get("Acres"),
                    "region": a.get("ParkRegion") or "",
                })
                created += 1

            # Add boat launches to recreation_sites table
            for f in launches:
                a = f.get("attributes", {})
                lat = a.get("Lat")
                lon = a.get("Long")
                if not lat or not lon:
                    continue
                ident = a.get("Identifier") or f"wapark-{lat}-{lon}"
                conn.execute(text("""
                    INSERT INTO recreation_sites (site_id, source_type, source_id, name, rec_type, latitude, longitude)
                    VALUES (:sid, 'wa_state_parks', :src_id, :name, 'boat_ramp', :lat, :lon)
                    ON CONFLICT DO NOTHING
                """), {
                    "sid": site.id,
                    "src_id": ident,
                    "name": f"WA State Park Launch ({ident})",
                    "lat": lat, "lon": lon,
                })
                created += 1

        return created

    def _ingest_water_access(self, client, site, bbox) -> int:
        """WDFW water access sites — boat ramps, hand launches."""
        features = _arcgis_query(client, WDFW_WATER_ACCESS_URL, bbox)
        if not features:
            return 0

        created = 0
        with engine.begin() as conn:
            for f in features:
                a = f.get("attributes", {})
                g = f.get("geometry", {})
                name = a.get("WaterAccessSiteName") or ""
                if not name:
                    continue
                lat = g.get("y")
                lon = g.get("x")
                if not lat or not lon:
                    continue

                # Determine rec_type from facilities
                ramps = a.get("BoatRamps") or 0
                hand = a.get("HandLaunches") or 0
                fishing = a.get("FishingPlatforms") or 0
                rec_type = "boat_ramp" if ramps else "fishing_access" if fishing else "boat_ramp" if hand else "day_use"

                conn.execute(text("""
                    INSERT INTO recreation_sites (site_id, source_type, source_id, name, rec_type, latitude, longitude)
                    VALUES (:sid, 'wdfw_water_access', :src_id, :name, :type, :lat, :lon)
                    ON CONFLICT DO NOTHING
                """), {
                    "sid": site.id,
                    "src_id": name,
                    "name": name,
                    "type": rec_type,
                    "lat": lat, "lon": lon,
                })
                created += 1

        return created
