"""Restoration intervention data ingestion from OWRI, NOAA, and PCSRF.

Pulls stream restoration project records from three public ArcGIS services:
1. OWRI (Oregon Watershed Restoration Inventory) -- most comprehensive Oregon source
2. NOAA Restoration Atlas -- federal restoration projects
3. PCSRF (Pacific Coastal Salmon Recovery Fund) -- salmon-specific projects

Each record represents an intervention (restoration action) with location,
type, dates, and outcomes.
"""

import json
import time
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# OWRI (Oregon Watershed Restoration Inventory) -- polygon geometries
OWRI_URL = "https://services1.arcgis.com/CD5mKowwN6nIaqd8/arcgis/rest/services/project_owri_2024/FeatureServer/5/query"
# OWRI related tables
OWRI_ACTIVITIES_URL = "https://services1.arcgis.com/CD5mKowwN6nIaqd8/arcgis/rest/services/project_owri_2024/FeatureServer/18/query"
OWRI_METRICS_URL = "https://services1.arcgis.com/CD5mKowwN6nIaqd8/arcgis/rest/services/project_owri_2024/FeatureServer/23/query"

# NOAA Restoration Atlas -- point geometries
NOAA_URL = "https://services2.arcgis.com/C8EMgrsFcRFL6LrL/arcgis/rest/services/PublishedProjects/FeatureServer/0/query"

# PCSRF -- point geometries
PCSRF_URL = "https://services2.arcgis.com/C8EMgrsFcRFL6LrL/arcgis/rest/services/PCSRF_Projects_Display/FeatureServer/0/query"

# Watershed name filters for OWRI
OWRI_WATERSHED_FILTERS = {
    "klamath": "watershed LIKE '%Klamath%' OR watershed LIKE '%Williamson%' OR watershed LIKE '%Sprague%'",
    "mckenzie": "watershed LIKE '%McKenzie%'",
    "deschutes": "watershed LIKE '%Deschutes%' OR watershed LIKE '%Crooked%' OR watershed LIKE '%Tumalo%'",
    "metolius": "watershed LIKE '%Metolius%'",
}

UPSERT_SQL = text("""
    INSERT INTO interventions (
        id, site_id, type, description, started_at, completed_at, location, created_at
    ) VALUES (
        gen_random_uuid(), :site_id, :type, :description, :started_at, :completed_at,
        CASE WHEN :geojson IS NOT NULL
             THEN ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326)
             ELSE NULL END,
        now()
    )
    ON CONFLICT DO NOTHING
""")

# We also store rich metadata in observations table for LLM reasoning
UPSERT_OBS_SQL = text("""
    INSERT INTO observations (
        id, site_id, source_type, source_id, observed_at,
        taxon_name, iconic_taxon,
        latitude, longitude,
        location,
        quality_grade, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, :source_type, :source_id, :observed_at,
        :taxon_name, :iconic_taxon,
        :latitude, :longitude,
        CASE WHEN :latitude IS NOT NULL AND :longitude IS NOT NULL
             THEN ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
             ELSE NULL END,
        'restoration_project', CAST(:data_payload AS jsonb)
    )
    ON CONFLICT (source_type, source_id) DO UPDATE SET
        data_payload = EXCLUDED.data_payload
""")


class RestorationAdapter(IngestionAdapter):
    source_type = "restoration"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        created = 0

        # 1. OWRI (Oregon's restoration inventory)
        c1 = self._ingest_owri(site)
        created += c1

        # 2. NOAA Restoration Atlas
        c2 = self._ingest_noaa(site)
        created += c2

        # 3. PCSRF (salmon recovery projects)
        c3 = self._ingest_pcsrf(site)
        created += c3

        return created, 0

    def _ingest_owri(self, site: Site) -> int:
        """Ingest from OWRI (Oregon Watershed Restoration Inventory)."""
        where = OWRI_WATERSHED_FILTERS.get(
            site.watershed,
            f"watershed LIKE '%{site.name.split()[0]}%'"
        )

        created = 0
        with httpx.Client(timeout=120) as client:
            console.print("    fetching OWRI restoration projects...")

            offset = 0
            while True:
                for attempt in range(3):
                    try:
                        resp = client.get(OWRI_URL, params={
                            "where": where,
                            "outFields": "*",
                            "f": "json",
                            "resultRecordCount": "2000",
                            "resultOffset": str(offset),
                        })
                        if resp.status_code == 200:
                            break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        time.sleep(5)
                else:
                    console.print("    [yellow]OWRI service unavailable[/yellow]")
                    break

                data = resp.json()
                features = data.get("features", [])
                if not features:
                    break

                with engine.connect() as conn:
                    for feat in features:
                        attrs = feat.get("attributes", {})
                        geom = feat.get("geometry")

                        project_id = attrs.get("project_nbr") or attrs.get("OBJECTID")
                        project_name = attrs.get("project_name") or attrs.get("drvd_project_description", "")
                        activity_type = attrs.get("activity_type", "")
                        stream_name = attrs.get("stream_name", "")
                        start_year = attrs.get("start_year")
                        complete_year = attrs.get("complete_year")
                        watershed = attrs.get("watershed", "")
                        county = attrs.get("county", "")

                        # Build start/end dates from years
                        started_at = f"{start_year}-01-01" if start_year else None
                        completed_at = f"{complete_year}-12-31" if complete_year else None
                        observed_at = started_at or "2000-01-01"

                        # Convert ESRI geometry to GeoJSON
                        geojson_str = None
                        lat, lon = None, None
                        if geom and "rings" in geom:
                            geojson_str = json.dumps({
                                "type": "Polygon",
                                "coordinates": geom["rings"],
                            })
                            # Centroid approximation
                            ring = geom["rings"][0]
                            if ring:
                                lon = sum(p[0] for p in ring) / len(ring)
                                lat = sum(p[1] for p in ring) / len(ring)

                        # Store as observation for LLM reasoning
                        source_id = f"owri_{project_id}"
                        try:
                            conn.execute(UPSERT_OBS_SQL, {
                                "site_id": str(self.site_id),
                                "source_type": "owri",
                                "source_id": source_id,
                                "observed_at": observed_at,
                                "taxon_name": None,
                                "iconic_taxon": None,
                                "latitude": lat,
                                "longitude": lon,
                                "data_payload": json.dumps({
                                    "project_id": str(project_id),
                                    "project_name": project_name,
                                    "activity_type": activity_type,
                                    "stream_name": stream_name,
                                    "watershed": watershed,
                                    "county": county,
                                    "start_year": start_year,
                                    "complete_year": complete_year,
                                    "total_cash": attrs.get("total_cash"),
                                    "total_inkind": attrs.get("total_inkind"),
                                    "description": attrs.get("drvd_project_description", ""),
                                }),
                            })
                            created += 1
                        except Exception:
                            continue

                    conn.commit()

                console.print(f"    OWRI: {offset + len(features)} projects so far")
                if not data.get("exceededTransferLimit") and len(features) < 2000:
                    break
                offset += 2000

        return created

    def _ingest_noaa(self, site: Site) -> int:
        """Ingest from NOAA Restoration Atlas."""
        bbox = site.bbox
        created = 0

        with httpx.Client(timeout=60) as client:
            console.print("    fetching NOAA Restoration Atlas...")

            for attempt in range(3):
                try:
                    resp = client.get(NOAA_URL, params={
                        "where": f"State = 'OR' AND Latitude >= {bbox['south']} AND Latitude <= {bbox['north']} AND Longitude >= {bbox['west']} AND Longitude <= {bbox['east']}",
                        "outFields": "*",
                        "f": "json",
                        "resultRecordCount": "2000",
                    })
                    if resp.status_code == 200:
                        break
                except (httpx.ConnectError, httpx.ReadTimeout):
                    time.sleep(5)
            else:
                console.print("    [yellow]NOAA Atlas unavailable[/yellow]")
                return 0

            data = resp.json()
            features = data.get("features", [])

            with engine.connect() as conn:
                for feat in features:
                    attrs = feat.get("attributes", {})

                    project_id = attrs.get("Project_ID") or attrs.get("OBJECTID")
                    lat = attrs.get("Latitude")
                    lon = attrs.get("Longitude")
                    name = attrs.get("Name", "")
                    description = attrs.get("Description", "")
                    start_raw = attrs.get("Construction_Start_Date")

                    start_date = None
                    if start_raw and isinstance(start_raw, (int, float)):
                        start_date = datetime.fromtimestamp(start_raw / 1000).strftime("%Y-%m-%d")
                    elif start_raw:
                        start_date = str(start_raw)[:10]

                    source_id = f"noaa_{project_id}"
                    try:
                        conn.execute(UPSERT_OBS_SQL, {
                            "site_id": str(self.site_id),
                            "source_type": "noaa_restoration",
                            "source_id": source_id,
                            "observed_at": start_date or "2000-01-01",
                            "taxon_name": None,
                            "iconic_taxon": None,
                            "latitude": lat,
                            "longitude": lon,
                            "data_payload": json.dumps({
                                "project_id": str(project_id),
                                "name": name,
                                "description": description[:1000] if description else "",
                                "techniques": attrs.get("Techniques", ""),
                                "strategy": attrs.get("Strategy", ""),
                                "habitats": attrs.get("Habitats", ""),
                                "species_benefited": attrs.get("Species_Benefited", ""),
                                "acres_restored": attrs.get("Acres_Restored"),
                                "acres_protected": attrs.get("Acres_Protected"),
                                "stream_miles_opened": attrs.get("Stream_Miles_Opened"),
                                "status": attrs.get("Project_Status", ""),
                                "program": attrs.get("Program", ""),
                            }),
                        })
                        created += 1
                    except Exception:
                        continue

                conn.commit()

            console.print(f"    NOAA: {created} projects")

        return created

    def _ingest_pcsrf(self, site: Site) -> int:
        """Ingest from PCSRF (Pacific Coastal Salmon Recovery Fund)."""
        bbox = site.bbox
        created = 0

        with httpx.Client(timeout=60) as client:
            console.print("    fetching PCSRF salmon recovery projects...")

            for attempt in range(3):
                try:
                    resp = client.get(PCSRF_URL, params={
                        "where": f"LATITUDE >= {bbox['south']} AND LATITUDE <= {bbox['north']} AND LONGITUDE >= {bbox['west']} AND LONGITUDE <= {bbox['east']}",
                        "outFields": "*",
                        "f": "json",
                        "resultRecordCount": "2000",
                    })
                    if resp.status_code == 200:
                        break
                except (httpx.ConnectError, httpx.ReadTimeout):
                    time.sleep(5)
            else:
                console.print("    [yellow]PCSRF service unavailable[/yellow]")
                return 0

            data = resp.json()
            features = data.get("features", [])

            with engine.connect() as conn:
                for feat in features:
                    attrs = feat.get("attributes", {})

                    project_ref = attrs.get("PROJECT_REF") or attrs.get("OBJECTID")
                    lat = attrs.get("LATITUDE")
                    lon = attrs.get("LONGITUDE")
                    name = attrs.get("PROJECT_NAME", "")
                    description = attrs.get("DESCRIPTION", "")
                    category = attrs.get("CATEGORY", "")
                    subcategory = attrs.get("SUBCATEGORY", "")
                    start_raw = attrs.get("START_DATE")

                    start_date = None
                    if start_raw and isinstance(start_raw, (int, float)):
                        start_date = datetime.fromtimestamp(start_raw / 1000).strftime("%Y-%m-%d")
                    elif start_raw:
                        start_date = str(start_raw)[:10]

                    source_id = f"pcsrf_{project_ref}"
                    try:
                        conn.execute(UPSERT_OBS_SQL, {
                            "site_id": str(self.site_id),
                            "source_type": "pcsrf",
                            "source_id": source_id,
                            "observed_at": start_date or "2000-01-01",
                            "taxon_name": None,
                            "iconic_taxon": None,
                            "latitude": lat,
                            "longitude": lon,
                            "data_payload": json.dumps({
                                "project_ref": str(project_ref),
                                "name": name,
                                "description": description[:1000] if description else "",
                                "category": category,
                                "subcategory": subcategory,
                                "subcategories": attrs.get("SUBCATEGORIES", ""),
                                "lead": attrs.get("PROJECT_LEAD", ""),
                                "subgrantee": attrs.get("PRIMARY_SUBGRANTEE", ""),
                                "status": attrs.get("STATUS", ""),
                                "fiscal_year": attrs.get("FFY"),
                                "pcsrf_funds": attrs.get("PCSRF_FUNDS"),
                                "state_funds": attrs.get("STATE_FUNDS"),
                                "other_funds": attrs.get("OTHER_FUNDS"),
                                "metrics": attrs.get("COMPLETED_METRICS", ""),
                            }),
                        })
                        created += 1
                    except Exception:
                        continue

                conn.commit()

            console.print(f"    PCSRF: {created} projects (total {created} with NOAA)")

        return created
