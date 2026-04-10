"""MTBS (Monitoring Trends in Burn Severity) fire data ingestion adapter.

Downloads fire perimeter polygons and burn severity data from the MTBS
program via USGS/USFS ArcGIS REST services or direct download.
"""

import json
import uuid
from datetime import datetime

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# MTBS ArcGIS REST service (fire occurrence points with perimeters)
MTBS_SERVICE = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer"
# Layer 63 = Burned Area Boundaries (All Years), Layer 62 = Fire Occurrence (All Years)
FIRE_BOUNDARIES_URL = f"{MTBS_SERVICE}/63/query"
FIRE_POINTS_URL = f"{MTBS_SERVICE}/62/query"

# Alternative: MTBS direct download service
MTBS_DIRECT = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/MTBS_Fire/data"

UPSERT_SQL = text("""
    INSERT INTO fire_perimeters (
        id, site_id, fire_name, fire_id, fire_year, acres,
        ig_date, perimeter, source_type, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, :fire_name, :fire_id, :fire_year, :acres,
        :ig_date, ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326),
        'mtbs', CAST(:data_payload AS jsonb)
    )
    ON CONFLICT DO NOTHING
""")


class MTBSAdapter(IngestionAdapter):
    source_type = "mtbs"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        created = 0

        # Query MTBS ArcGIS service for fire boundaries
        # The service uses Web Mercator (3857), so we need to pass the bbox
        # as a geometry envelope in geographic coords
        geometry = json.dumps({
            "xmin": bbox["west"], "ymin": bbox["south"],
            "xmax": bbox["east"], "ymax": bbox["north"],
            "spatialReference": {"wkid": 4326},
        })

        with httpx.Client(timeout=120) as client:
            console.print("    querying MTBS fire boundaries...")

            for attempt in range(3):
                try:
                    # Try polygon boundaries first
                    resp = client.get(FIRE_BOUNDARIES_URL, params={
                        "geometry": geometry,
                        "geometryType": "esriGeometryEnvelope",
                        "inSR": 4326,
                        "outSR": 4326,
                        "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "*",
                        "f": "geojson",
                        "resultRecordCount": 2000,
                    })
                    if resp.status_code == 200:
                        break
                except (httpx.ConnectError, httpx.ReadTimeout):
                    console.print(f"    [yellow]connection error, retry {attempt+1}/3...[/yellow]")
                    import time; time.sleep(5)
            else:
                # Fall back to point data
                console.print("    [yellow]boundary service unavailable, trying point data...[/yellow]")
                resp = self._fetch_points(client, geometry)

            if resp is None or resp.status_code != 200:
                console.print(f"    [yellow]MTBS service unavailable ({resp.status_code if resp else 'no response'})[/yellow]")
                return 0, 0

            data = resp.json()
            features = data.get("features", [])
            console.print(f"    found {len(features)} fire records")

            with engine.connect() as conn:
                for feat in features:
                    props = feat.get("properties", {})
                    geom = feat.get("geometry")

                    fire_name = props.get("FIRE_NAME") or props.get("fireName") or "Unknown"
                    fire_id = props.get("FIRE_ID") or props.get("fireID") or props.get("Event_ID", "")
                    fire_year = props.get("FIRE_YEAR") or props.get("fireYear") or props.get("Year")
                    acres = props.get("ACRES") or props.get("BurnBndAc") or props.get("GIS_ACRES")
                    ig_date_raw = props.get("IG_DATE") or props.get("Ig_Date") or props.get("igDate")

                    # Parse ignition date
                    ig_date = None
                    if ig_date_raw:
                        if isinstance(ig_date_raw, (int, float)):
                            # Epoch milliseconds
                            ig_date = datetime.fromtimestamp(ig_date_raw / 1000).strftime("%Y-%m-%d")
                        elif isinstance(ig_date_raw, str):
                            ig_date = ig_date_raw[:10]

                    # Convert geometry to GeoJSON string
                    geojson_str = None
                    if geom:
                        geom_type = geom.get("type", "")
                        if geom_type == "Polygon":
                            geom["type"] = "MultiPolygon"
                            geom["coordinates"] = [geom["coordinates"]]
                        geojson_str = json.dumps(geom)

                    if not geojson_str:
                        continue

                    try:
                        conn.execute(UPSERT_SQL, {
                            "site_id": str(self.site_id),
                            "fire_name": fire_name,
                            "fire_id": str(fire_id),
                            "fire_year": int(fire_year) if fire_year else None,
                            "acres": float(acres) if acres else None,
                            "ig_date": ig_date,
                            "geojson": geojson_str,
                            "data_payload": json.dumps({
                                k: v for k, v in props.items()
                                if isinstance(v, (str, int, float, bool, type(None)))
                            }),
                        })
                        created += 1
                    except Exception as e:
                        console.print(f"    [dim]skip {fire_name}: {e}[/dim]")
                        continue

                conn.commit()

        return created, 0

    def _fetch_points(self, client, geometry):
        """Fallback: fetch fire occurrence points instead of polygons."""
        try:
            return client.get(FIRE_POINTS_URL, params={
                "geometry": geometry,
                "geometryType": "esriGeometryEnvelope",
                "inSR": 4326,
                "outSR": 4326,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "f": "geojson",
                "resultRecordCount": 2000,
            })
        except Exception:
            return None
