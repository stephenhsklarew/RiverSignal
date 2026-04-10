"""Spatial context data: 303(d) impaired waters, NWI wetlands, WBD boundaries.

Three lightweight spatial datasets that provide regulatory and ecological
context for watershed analysis.
"""

import json
import time

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# EPA ATTAINS Assessment GIS service (303d impaired waters)
ATTAINS_URL = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer"

# USFWS NWI Wetlands MapServer
NWI_URL = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query"

# USGS WBD MapServer
WBD_URL = "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/6/query"


def _esri_to_geojson(geom: dict) -> str | None:
    """Convert ESRI JSON geometry to GeoJSON string."""
    if not geom:
        return None
    if "paths" in geom:
        return json.dumps({"type": "MultiLineString", "coordinates": geom["paths"]})
    if "rings" in geom:
        return json.dumps({"type": "MultiPolygon", "coordinates": [geom["rings"]]})
    return None


def _insert_with_optional_geom(conn, sql_no_geom, sql_with_geom, params, geojson_str):
    """Insert with or without geometry, avoiding psycopg AmbiguousParameter."""
    if geojson_str:
        params["geojson"] = geojson_str
        conn.execute(sql_with_geom, params)
    else:
        conn.execute(sql_no_geom, params)


def _arcgis_query(client, url, bbox, extra_params=None, max_records=2000):
    """Generic ArcGIS REST query with bbox."""
    params = {
        "geometry": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326", "outSR": "4326",
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
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json().get("features", [])
        except (httpx.ConnectError, httpx.ReadTimeout):
            time.sleep(5)
    return []


class ImpairedWatersAdapter(IngestionAdapter):
    """EPA ATTAINS 303(d) impaired waters assessment."""
    source_type = "deq_303d"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        created = 0
        with httpx.Client(timeout=60) as client:
            console.print("    fetching EPA ATTAINS impaired waters...")

            # Query both lines (streams) and areas (lakes)
            for layer_id in [1, 2]:
                url = f"{ATTAINS_URL}/{layer_id}/query"
                features = _arcgis_query(client, url, site.bbox)
                if not features:
                    continue

                SQL_NO_GEOM = text("""
                    INSERT INTO impaired_waters (id, site_id, assessment_unit, water_name, parameter,
                        category, tmdl_status, listing_year, data_payload)
                    VALUES (gen_random_uuid(), :site_id, :au, :name, :param, :cat, :tmdl, :year,
                        CAST(:payload AS jsonb))
                """)
                SQL_WITH_GEOM = text("""
                    INSERT INTO impaired_waters (id, site_id, assessment_unit, water_name, parameter,
                        category, tmdl_status, listing_year, geometry, data_payload)
                    VALUES (gen_random_uuid(), :site_id, :au, :name, :param, :cat, :tmdl, :year,
                        ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326), CAST(:payload AS jsonb))
                """)

                with engine.connect() as conn:
                    for feat in features:
                        attrs = feat.get("attributes", {})
                        geojson_str = _esri_to_geojson(feat.get("geometry"))

                        params = {
                            "site_id": str(self.site_id),
                            "au": attrs.get("assessmentunitidentifier", ""),
                            "name": attrs.get("assessmentunitname", ""),
                            "param": attrs.get("parametername") or attrs.get("causename", ""),
                            "cat": attrs.get("ircategory", ""),
                            "tmdl": "Yes" if attrs.get("on303dlist") == "Y" else "No",
                            "year": attrs.get("reportingcycle"),
                            "payload": json.dumps({
                                k: v for k, v in attrs.items()
                                if isinstance(v, (str, int, float, bool, type(None)))
                            }),
                        }
                        try:
                            _insert_with_optional_geom(conn, SQL_NO_GEOM, SQL_WITH_GEOM, params, geojson_str)
                            created += 1
                        except Exception:
                            continue
                    conn.commit()

                console.print(f"    layer {layer_id}: {len(features)} assessment units")

        return created, 0


class WetlandsAdapter(IngestionAdapter):
    """USFWS National Wetlands Inventory."""
    source_type = "nwi"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        created = 0
        with httpx.Client(timeout=60) as client:
            console.print("    fetching NWI wetlands...")

            offset = 0
            while True:
                features = _arcgis_query(client, NWI_URL, site.bbox,
                    extra_params={"resultOffset": str(offset)})
                if not features:
                    break

                SQL_NWI_NO = text("""
                    INSERT INTO wetlands (id, site_id, wetland_type, attribute, acres, data_payload)
                    VALUES (gen_random_uuid(), :site_id, :wtype, :attr, :acres, CAST(:payload AS jsonb))
                """)
                SQL_NWI_GEOM = text("""
                    INSERT INTO wetlands (id, site_id, wetland_type, attribute, acres, geometry, data_payload)
                    VALUES (gen_random_uuid(), :site_id, :wtype, :attr, :acres,
                        ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326), CAST(:payload AS jsonb))
                """)

                with engine.connect() as conn:
                    for feat in features:
                        attrs = feat.get("attributes", {})
                        geojson_str = _esri_to_geojson(feat.get("geometry"))

                        wtype = attrs.get("Wetlands.WETLAND_TYPE") or attrs.get("WETLAND_TYPE", "")
                        attribute = attrs.get("Wetlands.ATTRIBUTE") or attrs.get("ATTRIBUTE", "")
                        acres = attrs.get("Wetlands.ACRES") or attrs.get("ACRES")

                        params = {
                            "site_id": str(self.site_id),
                            "wtype": wtype,
                            "attr": attribute,
                            "acres": float(acres) if acres else None,
                            "payload": json.dumps({
                                "system": attrs.get("NWI_Wetland_Codes.SYSTEM_NAME", ""),
                                "subsystem": attrs.get("NWI_Wetland_Codes.SUBSYSTEM_NAME", ""),
                                "class": attrs.get("NWI_Wetland_Codes.CLASS_NAME", ""),
                                "water_regime": attrs.get("NWI_Wetland_Codes.WATER_REGIME_NAME", ""),
                            }),
                        }
                        try:
                            _insert_with_optional_geom(conn, SQL_NWI_NO, SQL_NWI_GEOM, params, geojson_str)
                            created += 1
                        except Exception:
                            continue
                    conn.commit()

                console.print(f"    {offset + len(features)} wetland polygons...")
                if len(features) < 2000:
                    break
                offset += 2000

        return created, 0


class WatershedBoundaryAdapter(IngestionAdapter):
    """USGS Watershed Boundary Dataset (HUC12 polygons)."""
    source_type = "wbd"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        created = 0
        with httpx.Client(timeout=60) as client:
            console.print("    fetching HUC12 watershed boundaries...")

            features = _arcgis_query(client, WBD_URL, site.bbox)
            if not features:
                console.print("    no HUC12 boundaries found")
                return 0, 0

            SQL_WBD_NO = text("""
                INSERT INTO watershed_boundaries (id, site_id, huc12, name, area_sqkm, data_payload)
                VALUES (gen_random_uuid(), :site_id, :huc12, :name, :area, CAST(:payload AS jsonb))
            """)
            SQL_WBD_GEOM = text("""
                INSERT INTO watershed_boundaries (id, site_id, huc12, name, area_sqkm, geometry, data_payload)
                VALUES (gen_random_uuid(), :site_id, :huc12, :name, :area,
                    ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326), CAST(:payload AS jsonb))
            """)

            with engine.connect() as conn:
                for feat in features:
                    attrs = feat.get("attributes", {})
                    geojson_str = _esri_to_geojson(feat.get("geometry"))

                    params = {
                        "site_id": str(self.site_id),
                        "huc12": attrs.get("huc12", ""),
                        "name": attrs.get("name", ""),
                        "area": float(attrs.get("areasqkm")) if attrs.get("areasqkm") else None,
                        "payload": json.dumps({k: v for k, v in attrs.items()
                            if isinstance(v, (str, int, float, bool, type(None)))}),
                    }
                    try:
                        _insert_with_optional_geom(conn, SQL_WBD_NO, SQL_WBD_GEOM, params, geojson_str)
                        created += 1
                    except Exception:
                        continue
                conn.commit()

            console.print(f"    {created} HUC12 boundaries")

        return created, 0
