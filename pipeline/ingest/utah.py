"""Utah state data source adapters for the Green River watershed.

Sources:
  1. Utah AGRC Boat Ramps — ArcGIS FeatureServer
  2. Utah DWQ Assessment Units — 303(d) impaired waters (ArcGIS FeatureServer)
  3. Utah AGRC Trailheads — ArcGIS FeatureServer
  4. Bureau of Reclamation Flaming Gorge HydroData — reservoir storage, inflow, release, elevation
  5. UDWR Fish Stocking — HTML table scrape for Green River / Flaming Gorge
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# ── Endpoints ──

UTAH_BOAT_RAMPS_URL = (
    "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/"
    "BoatRamps/FeatureServer/0/query"
)

UTAH_DWQ_ASSESSMENT_URL = (
    "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/"
    "DWQAssessmentUnits/FeatureServer/0/query"
)

UTAH_TRAILHEADS_URL = (
    "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/"
    "UtahTrailheads/FeatureServer/0/query"
)

BOR_HYDRODATA_URL = (
    "https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/{param_id}.json"
)

UDWR_STOCKING_URL = (
    "https://dwrapps.utah.gov/fishstocking/FishAjax"
    "?y={year}&sort=waterName&sortorder=ASC"
    "&sortspecific={water_name}&whichSpecific=water"
)

# BOR parameter ID → (parameter_name, unit)
BOR_PARAMS = {
    17: ("reservoir_storage_af", "af"),
    29: ("inflow_cfs", "cfs"),
    42: ("release_cfs", "cfs"),
    49: ("pool_elevation_ft", "ft"),
}

# Water names to query for UDWR stocking
UDWR_WATER_NAMES = ["GREEN RIVER", "FLAMING GORGE"]


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
            resp = client.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("features", [])
        except (httpx.ConnectError, httpx.ReadTimeout):
            time.sleep(3)
    return []


class UtahDataAdapter(IngestionAdapter):
    """Combined adapter for Utah state data sources."""
    source_type = "utah"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            return 0, 0

        # Only run for Utah/Green River watersheds
        if site.watershed not in ("green_river",):
            console.print(f"    utah: skipping {site.watershed} (not a UT watershed)")
            return 0, 0

        bbox = site.bbox
        total = 0

        with httpx.Client(timeout=30) as client:
            for name, method in [
                ("AGRC Boat Ramps", self._ingest_boat_ramps),
                ("DWQ Assessment Units", self._ingest_dwq_assessment),
                ("AGRC Trailheads", self._ingest_trailheads),
                ("BOR Flaming Gorge", self._ingest_bor_hydrodata),
                ("UDWR Fish Stocking", self._ingest_udwr_stocking),
            ]:
                try:
                    c = method(client, site, bbox)
                    total += c
                    console.print(f"    {name}: {c} records")
                except Exception as e:
                    console.print(f"    [yellow]{name}: {e}[/yellow]")

        return total, 0

    def _ingest_boat_ramps(self, client, site, bbox) -> int:
        """Utah AGRC boat ramps."""
        features = _arcgis_query(client, UTAH_BOAT_RAMPS_URL, bbox)
        if not features:
            return 0

        created = 0
        with engine.begin() as conn:
            for f in features:
                a = f.get("attributes", {})
                g = f.get("geometry", {})
                lat = g.get("y")
                lon = g.get("x")
                if not lat or not lon:
                    continue
                name = a.get("Name") or a.get("name") or "Unnamed Boat Ramp"
                source_id = str(a.get("OBJECTID") or a.get("FID") or f"{lat}-{lon}")
                amenities = json.dumps({
                    "Water_body": a.get("Water_body") or a.get("Water_Body") or "",
                    "OWNER": a.get("OWNER") or a.get("Owner") or "",
                    "AGENCY": a.get("AGENCY") or a.get("Agency") or "",
                })
                conn.execute(text("""
                    INSERT INTO recreation_sites
                        (site_id, source_type, source_id, name, rec_type,
                         latitude, longitude, geom, amenities)
                    VALUES
                        (:sid, 'utah_agrc', :src_id, :name, 'boat_ramp',
                         :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                         CAST(:amenities AS jsonb))
                    ON CONFLICT (source_type, source_id) DO UPDATE SET
                        name = EXCLUDED.name, amenities = EXCLUDED.amenities
                """), {
                    "sid": site.id,
                    "src_id": source_id,
                    "name": name[:255],
                    "lat": lat,
                    "lon": lon,
                    "amenities": amenities,
                })
                created += 1

        return created

    def _ingest_dwq_assessment(self, client, site, bbox) -> int:
        """Utah DWQ 303(d) assessment units — impaired waters."""
        features = _arcgis_query(client, UTAH_DWQ_ASSESSMENT_URL, bbox)
        if not features:
            return 0

        created = 0
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS utah_impaired_waters (
                    id SERIAL PRIMARY KEY,
                    site_id UUID REFERENCES sites(id),
                    au_name VARCHAR,
                    au_id VARCHAR,
                    waterbody_name VARCHAR,
                    impairment_cause VARCHAR,
                    status VARCHAR,
                    assessment_category VARCHAR,
                    beneficial_use VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(site_id, au_id)
                )
            """))

            for f in features:
                a = f.get("attributes", {})
                au_id = str(
                    a.get("AU_ID") or a.get("AUID") or a.get("OBJECTID") or ""
                )
                if not au_id:
                    continue
                conn.execute(text("""
                    INSERT INTO utah_impaired_waters
                        (site_id, au_name, au_id, waterbody_name, impairment_cause,
                         status, assessment_category, beneficial_use)
                    VALUES (:sid, :au_name, :au_id, :wb_name, :cause,
                            :status, :category, :use)
                    ON CONFLICT (site_id, au_id) DO UPDATE SET
                        impairment_cause = EXCLUDED.impairment_cause,
                        status = EXCLUDED.status,
                        assessment_category = EXCLUDED.assessment_category
                """), {
                    "sid": site.id,
                    "au_name": a.get("AU_NAME") or a.get("AUName") or "",
                    "au_id": au_id,
                    "wb_name": a.get("Water_Body") or a.get("WaterBody") or a.get("AU_NAME") or "",
                    "cause": a.get("Cause") or a.get("CAUSE") or "",
                    "status": a.get("IR_Cat") or a.get("Status") or "",
                    "category": a.get("AU_Category") or a.get("Category") or "",
                    "use": a.get("Beneficial_Use") or a.get("BeneficialUse") or "",
                })
                created += 1

        return created

    def _ingest_trailheads(self, client, site, bbox) -> int:
        """Utah AGRC trailheads."""
        features = _arcgis_query(client, UTAH_TRAILHEADS_URL, bbox)
        if not features:
            return 0

        created = 0
        with engine.begin() as conn:
            for f in features:
                a = f.get("attributes", {})
                g = f.get("geometry", {})
                lat = g.get("y")
                lon = g.get("x")
                if not lat or not lon:
                    continue
                name = a.get("PrimaryName") or a.get("Name") or a.get("name") or "Unnamed Trailhead"
                source_id = str(a.get("OBJECTID") or a.get("FID") or f"{lat}-{lon}")
                amenities = json.dumps({
                    k: v for k, v in a.items()
                    if isinstance(v, (str, int, float, bool, type(None)))
                })
                conn.execute(text("""
                    INSERT INTO recreation_sites
                        (site_id, source_type, source_id, name, rec_type,
                         latitude, longitude, geom, amenities)
                    VALUES
                        (:sid, 'utah_agrc_trailheads', :src_id, :name, 'trailhead',
                         :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                         CAST(:amenities AS jsonb))
                    ON CONFLICT (source_type, source_id) DO UPDATE SET
                        name = EXCLUDED.name, amenities = EXCLUDED.amenities
                """), {
                    "sid": site.id,
                    "src_id": source_id,
                    "name": name[:255],
                    "lat": lat,
                    "lon": lon,
                    "amenities": amenities,
                })
                created += 1

        return created

    def _ingest_bor_hydrodata(self, client, site, bbox) -> int:
        """Bureau of Reclamation Flaming Gorge reservoir data."""
        created = 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        with engine.begin() as conn:
            for param_id, (param_name, unit) in BOR_PARAMS.items():
                url = BOR_HYDRODATA_URL.format(param_id=param_id)
                try:
                    resp = client.get(url, timeout=30)
                    if resp.status_code != 200:
                        console.print(f"      BOR param {param_id}: HTTP {resp.status_code}")
                        continue
                    data = resp.json()
                except Exception as e:
                    console.print(f"      BOR param {param_id}: {e}")
                    continue

                columns = data.get("columns", [])
                rows = data.get("data", [])
                if not rows:
                    continue

                for row in rows:
                    if len(row) < 2:
                        continue
                    ts_str = row[0]
                    value = row[1]
                    if ts_str is None or value is None:
                        continue

                    # Only recent data
                    if ts_str < cutoff_str:
                        continue

                    try:
                        val_float = float(value)
                    except (ValueError, TypeError):
                        continue

                    conn.execute(text("""
                        INSERT INTO time_series
                            (id, site_id, station_id, parameter, timestamp,
                             value, unit, source_type)
                        VALUES
                            (gen_random_uuid(), :sid, 'flaming_gorge_937', :param,
                             :ts, :val, :unit, 'bor_reservoir')
                        ON CONFLICT (site_id, station_id, parameter, timestamp)
                        DO UPDATE SET value = EXCLUDED.value
                    """), {
                        "sid": str(self.site_id),
                        "param": param_name,
                        "ts": ts_str,
                        "val": val_float,
                        "unit": unit,
                    })
                    created += 1

                time.sleep(1)

        return created

    def _ingest_udwr_stocking(self, client, site, bbox) -> int:
        """UDWR fish stocking data — HTML table scrape."""
        created = 0
        current_year = datetime.now().year
        years = range(current_year - 2, current_year + 1)

        with engine.begin() as conn:
            for water_name in UDWR_WATER_NAMES:
                for year in years:
                    url = UDWR_STOCKING_URL.format(
                        year=year, water_name=water_name.replace(" ", "+")
                    )
                    try:
                        resp = client.get(url, timeout=30)
                        if resp.status_code != 200:
                            continue
                    except Exception:
                        continue

                    html = resp.text
                    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

                    # UDWR table columns (verified 2026-05-11):
                    #   0=Location Name, 1=County, 2=Fish Species,
                    #   3=Number Stocked, 4=Size (inches), 5=Date
                    # The ?sortspecific=GREEN+RIVER URL param is a sort key,
                    # not a filter — the server returns every Utah stocking
                    # record. We must post-filter rows to those whose location
                    # name actually matches the watershed we're ingesting for.
                    target_upper = water_name.upper()
                    for row in rows[1:]:  # skip header row
                        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                        if len(cells) < 6:
                            continue

                        waterbody = cells[0]
                        county = cells[1]
                        species = cells[2]
                        quantity_str = cells[3].replace(",", "")
                        avg_length = cells[4]
                        stock_date = cells[5]

                        # Skip rows for waterbodies that aren't in our basin.
                        # Match GREEN RIVER, FLAMING GORGE, and obvious tributaries.
                        if target_upper not in waterbody.upper():
                            continue

                        try:
                            quantity = int(quantity_str)
                        except ValueError:
                            continue

                        if quantity == 0:
                            continue

                        # Parse date
                        parsed_date = None
                        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
                            try:
                                parsed_date = datetime.strptime(stock_date, fmt).strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                        if not parsed_date:
                            parsed_date = f"{year}-01-01"

                        source_id = f"udwr_{waterbody}_{species}_{parsed_date}".replace(" ", "_")[:255]

                        conn.execute(text("""
                            INSERT INTO interventions
                                (id, site_id, type, description, started_at)
                            VALUES
                                (gen_random_uuid(), :sid, 'fish_stocking', :desc, :date)
                            ON CONFLICT DO NOTHING
                        """), {
                            "sid": site.id,
                            "desc": json.dumps({
                                "waterbody": waterbody,
                                "county": county,
                                "species": species,
                                "quantity": quantity,
                                "avg_length": avg_length,
                                "source": "udwr",
                            }),
                            "date": parsed_date,
                        })
                        created += 1

                    time.sleep(1)

        return created
