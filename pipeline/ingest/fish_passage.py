"""ODFW Fish Passage Barriers ingestion adapter.

Downloads fish passage barrier locations and status from the Oregon
Department of Fish & Wildlife ArcGIS FeatureServer. Includes barrier
type, passage status, modification history, and physical dimensions.
"""

import json
import time
import uuid
from datetime import datetime

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# ODFW Fish Passage Barriers FeatureServer
BARRIERS_URL = "https://nrimp.dfw.state.or.us/arcgis/rest/services/OWRI/OregonFishPassageBarriers_OWRI/FeatureServer/0/query"

UPSERT_SQL = text("""
    INSERT INTO observations (
        id, site_id, source_type, source_id, observed_at,
        taxon_name, iconic_taxon,
        latitude, longitude,
        location,
        quality_grade, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, 'fish_barrier', :source_id, :observed_at,
        :taxon_name, 'Actinopterygii',
        :latitude, :longitude,
        CASE WHEN :latitude IS NOT NULL AND :longitude IS NOT NULL
             THEN ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
             ELSE NULL END,
        :quality_grade, CAST(:data_payload AS jsonb)
    )
    ON CONFLICT (source_type, source_id) DO UPDATE SET
        data_payload = EXCLUDED.data_payload,
        quality_grade = EXCLUDED.quality_grade
""")


class FishPassageAdapter(IngestionAdapter):
    source_type = "fish_barrier"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        geometry = f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}"
        created = 0

        with httpx.Client(timeout=120) as client:
            console.print("    fetching ODFW fish passage barriers...")

            offset = 0
            while True:
                for attempt in range(3):
                    try:
                        resp = client.get(BARRIERS_URL, params={
                            "geometry": geometry,
                            "geometryType": "esriGeometryEnvelope",
                            "inSR": "4326",
                            "outSR": "4326",
                            "spatialRel": "esriSpatialRelIntersects",
                            "where": "1=1",
                            "outFields": "*",
                            "f": "json",
                            "resultRecordCount": "2000",
                            "resultOffset": str(offset),
                        })
                        if resp.status_code == 200:
                            break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        console.print(f"    [yellow]retry {attempt+1}/3...[/yellow]")
                        time.sleep(5)
                else:
                    console.print("    [yellow]ODFW service unavailable[/yellow]")
                    break

                data = resp.json()
                features = data.get("features", [])
                if not features:
                    break

                console.print(f"    processing {offset + len(features)} barriers...")

                with engine.connect() as conn:
                    for feat in features:
                        attrs = feat.get("attributes", {})
                        geom = feat.get("geometry", {})

                        barrier_id = attrs.get("fpbID") or attrs.get("OBJECTID")
                        lat = geom.get("y") or attrs.get("fpbLat")
                        lon = geom.get("x") or attrs.get("fpbLong")
                        stream_name = attrs.get("fpbStrNm", "")
                        barrier_type = attrs.get("fpbFtrTy", "")
                        passage_status = attrs.get("fpbFPasSta", "")
                        road_name = attrs.get("fpbRdNm", "")
                        owner = attrs.get("fpbOwn", "")

                        # Modification data (remediation)
                        mod_type = attrs.get("fpbModTy", "")
                        mod_date = attrs.get("fpbModDt")
                        mod_desc = attrs.get("fpbModDesc", "")

                        # Physical dimensions
                        height = attrs.get("fpbHeight")
                        length = attrs.get("fpbLength")
                        width = attrs.get("fpbWidth")
                        slope = attrs.get("fpbSlope")
                        drop = attrs.get("fpbDrop")

                        # Use modification date if available, else use a default
                        observed_at = "2000-01-01"
                        if mod_date and isinstance(mod_date, (int, float)):
                            observed_at = datetime.fromtimestamp(mod_date / 1000).strftime("%Y-%m-%d")
                        elif mod_date:
                            observed_at = str(mod_date)[:10]

                        source_id = f"fpb_{barrier_id}"
                        try:
                            conn.execute(UPSERT_SQL, {
                                "site_id": str(self.site_id),
                                "source_id": source_id,
                                "observed_at": observed_at,
                                "taxon_name": None,
                                "latitude": float(lat) if lat else None,
                                "longitude": float(lon) if lon else None,
                                "quality_grade": passage_status or "unknown",
                                "data_payload": json.dumps({
                                    "barrier_id": str(barrier_id),
                                    "stream_name": stream_name,
                                    "barrier_type": barrier_type,
                                    "passage_status": passage_status,
                                    "road_name": road_name,
                                    "owner": owner,
                                    "modification_type": mod_type,
                                    "modification_date": observed_at if mod_date else None,
                                    "modification_desc": mod_desc,
                                    "height_ft": height,
                                    "length_ft": length,
                                    "width_ft": width,
                                    "slope_pct": slope,
                                    "drop_ft": drop,
                                    "oweb_status": attrs.get("OWEB_status", ""),
                                }),
                            })
                            created += 1
                        except Exception:
                            continue

                    conn.commit()

                if not data.get("exceededTransferLimit") and len(features) < 2000:
                    break
                offset += 2000

        return created, 0
