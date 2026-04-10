"""NHDPlus stream network ingestion adapter.

Downloads stream flowlines from the National Hydrography Dataset Plus
via the USGS National Map ArcGIS REST services or the NLDI (Network
Linked Data Index) API.
"""

import json
import uuid

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# NHD ArcGIS REST service
NHD_SERVICE = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer"
# Layer 4 = Flowline - Small Scale (works with bbox queries)
FLOWLINE_URL = f"{NHD_SERVICE}/4/query"

# NLDI API (alternative for navigating upstream/downstream)
NLDI_BASE = "https://labs.waterdata.usgs.gov/api/nldi/linked-data"

UPSERT_SQL = text("""
    INSERT INTO stream_flowlines (
        id, site_id, reach_code, gnis_name, stream_order, length_km,
        ftype, flowline, source_type, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, :reach_code, :gnis_name, :stream_order,
        :length_km, :ftype,
        ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326),
        'nhdplus', CAST(:data_payload AS jsonb)
    )
    ON CONFLICT DO NOTHING
""")


class NHDPlusAdapter(IngestionAdapter):
    source_type = "nhdplus"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        created = 0

        geometry = f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}"

        with httpx.Client(timeout=120) as client:
            console.print("    querying NHD flowlines...")

            offset = 0
            while True:
                for attempt in range(3):
                    try:
                        resp = client.get(FLOWLINE_URL, params={
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
                        import time; time.sleep(5)
                else:
                    console.print("    [yellow]NHD service unavailable[/yellow]")
                    break

                data = resp.json()
                features = data.get("features", [])
                if not features:
                    break

                console.print(f"    processing {offset + len(features)} flowlines...")

                with engine.connect() as conn:
                    for feat in features:
                        attrs = feat.get("attributes", feat.get("properties", {}))
                        geom = feat.get("geometry")

                        if not geom:
                            continue

                        # Convert ESRI JSON paths to GeoJSON MultiLineString
                        if "paths" in geom:
                            geojson_geom = {
                                "type": "MultiLineString",
                                "coordinates": geom["paths"],
                            }
                        elif geom.get("type") == "LineString":
                            geojson_geom = {
                                "type": "MultiLineString",
                                "coordinates": [geom["coordinates"]],
                            }
                        elif geom.get("type") == "MultiLineString":
                            geojson_geom = geom
                        else:
                            continue

                        # NHD server returns uppercase field names
                        reach_code = attrs.get("REACHCODE") or attrs.get("reachcode", "")
                        gnis_name = attrs.get("GNIS_NAME") or attrs.get("gnis_name", "")
                        stream_order = attrs.get("StreamOrde") or attrs.get("streamorde")
                        length_km = attrs.get("LENGTHKM") or attrs.get("lengthkm")
                        ftype = str(attrs.get("FTYPE") or attrs.get("ftype", ""))
                        perm_id = attrs.get("Permanent_Identifier") or attrs.get("permanent_identifier", "")

                        try:
                            conn.execute(UPSERT_SQL, {
                                "site_id": str(self.site_id),
                                "reach_code": reach_code,
                                "gnis_name": gnis_name or None,
                                "stream_order": int(stream_order) if stream_order else None,
                                "length_km": float(length_km) if length_km else None,
                                "ftype": ftype,
                                "geojson": json.dumps(geojson_geom),
                                "data_payload": json.dumps({
                                    "permanent_id": perm_id,
                                    "ftype_desc": "StreamRiver" if ftype == "460" else "ArtificialPath" if ftype == "558" else ftype,
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
