"""Geology ingestion adapters: USGS NGMDB geologic units, PBDB fossils, BLM land ownership.

Three geology-domain adapters that provide the foundational data for
DeepSignal and DeepTrail products.
"""

import json
import time

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# Macrostrat API — geologic units with full GeoJSON geometry
MACROSTRAT_URL = "https://macrostrat.org/api/v2/geologic_units/map"

# Paleobiology Database REST API
PBDB_URL = "https://paleobiodb.org/data1.2/occs/list.json"

# BLM Surface Management Agency - National dataset (with_PriUnk includes all ownership types)
BLM_SMA_URL = "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_Cached_with_PriUnk/MapServer/1/query"


# Geologic period lookup from age in Ma
PERIOD_RANGES = [
    (0, 0.0117, "Holocene"),
    (0.0117, 2.58, "Pleistocene"),
    (2.58, 5.33, "Pliocene"),
    (5.33, 23.03, "Miocene"),
    (23.03, 33.9, "Oligocene"),
    (33.9, 56.0, "Eocene"),
    (56.0, 66.0, "Paleocene"),
    (66.0, 145.0, "Cretaceous"),
    (145.0, 201.4, "Jurassic"),
    (201.4, 251.9, "Triassic"),
    (251.9, 298.9, "Permian"),
    (298.9, 358.9, "Carboniferous"),
    (358.9, 419.2, "Devonian"),
    (419.2, 443.8, "Silurian"),
    (443.8, 485.4, "Ordovician"),
    (485.4, 538.8, "Cambrian"),
]


def _age_to_period(age_ma: float | None) -> str | None:
    """Convert age in Ma to geologic period name."""
    if age_ma is None:
        return None
    for min_age, max_age, period in PERIOD_RANGES:
        if min_age <= age_ma < max_age:
            return period
    if age_ma >= 538.8:
        return "Precambrian"
    return None


def _esri_rings_to_geojson(geom: dict) -> str | None:
    """Convert ESRI JSON rings geometry to GeoJSON MultiPolygon."""
    if not geom or "rings" not in geom:
        return None
    return json.dumps({"type": "MultiPolygon", "coordinates": [geom["rings"]]})


def _arcgis_query_paginated(client, url, bbox, extra_params=None, max_per_page=1000):
    """ArcGIS REST query with pagination via resultOffset."""
    all_features = []
    offset = 0
    while True:
        params = {
            "geometry": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326", "outSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
            "resultRecordCount": str(max_per_page),
            "resultOffset": str(offset),
        }
        if extra_params:
            params.update(extra_params)

        for attempt in range(3):
            try:
                resp = client.get(url, params=params, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    all_features.extend(features)
                    # Check if more pages
                    if len(features) < max_per_page or data.get("exceededTransferLimit") is False:
                        return all_features
                    offset += len(features)
                    break
                else:
                    time.sleep(5)
            except (httpx.ConnectError, httpx.ReadTimeout):
                time.sleep(10)
        else:
            # All retries failed
            return all_features

    return all_features


# Map of common BLM SMA agency codes to collecting rules
AGENCY_COLLECTING_RULES = {
    "BLM": ("permitted", "Casual collecting of common invertebrate and plant fossils permitted for personal use (reasonable amounts). Vertebrate fossils require a permit."),
    "USFS": ("restricted", "Limited collecting of common invertebrate and plant fossils permitted for personal use. Vertebrate fossils and petrified wood >25 lbs/day require permit."),
    "NPS": ("prohibited", "All fossil, mineral, and rock collecting is prohibited in National Park Service areas."),
    "FWS": ("prohibited", "Collecting generally prohibited in National Wildlife Refuges without special permit."),
    "DOD": ("prohibited", "Military lands — no public access without authorization."),
    "BOR": ("restricted", "Bureau of Reclamation lands — collecting rules vary by area, check locally."),
    "STATE": ("restricted", "Oregon state lands — rules vary by managing agency, check locally."),
    "PRIVATE": ("prohibited", "Private land — collecting requires landowner permission."),
}


class GeologicUnitsAdapter(IngestionAdapter):
    """Macrostrat — geologic unit polygons with formation, lithology, and age data.

    Queries Macrostrat's geologic_units/map endpoint on a grid across the
    watershed bbox.  Each grid point returns the geologic unit polygons at that
    location.  Deduplication is via map_id (Macrostrat's unique polygon ID).
    """
    source_type = "macrostrat"

    GRID_STEP_DEG = 0.15  # ~15 km grid spacing

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        bbox = site.bbox
        created = 0
        seen_map_ids: set[str] = set()

        # Build grid of sample points across the bbox
        import math
        lat_steps = max(2, int(math.ceil((bbox["north"] - bbox["south"]) / self.GRID_STEP_DEG)))
        lon_steps = max(2, int(math.ceil((bbox["east"] - bbox["west"]) / self.GRID_STEP_DEG)))
        total_points = lat_steps * lon_steps

        console.print(f"    querying Macrostrat at {total_points} grid points ({lat_steps}x{lon_steps})...")

        SQL = text("""
            INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                rock_type, lithology, age_min_ma, age_max_ma, period, description,
                geometry, data_payload)
            VALUES (gen_random_uuid(), 'macrostrat', :source_id, :unit_name, :formation,
                :rock_type, :lithology, :age_min, :age_max, :period, :description,
                ST_GeomFromGeoJSON(:geojson), CAST(:payload AS jsonb))
            ON CONFLICT DO NOTHING
        """)

        SQL_NO_GEOM = text("""
            INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                rock_type, lithology, age_min_ma, age_max_ma, period, description,
                data_payload)
            VALUES (gen_random_uuid(), 'macrostrat', :source_id, :unit_name, :formation,
                :rock_type, :lithology, :age_min, :age_max, :period, :description,
                CAST(:payload AS jsonb))
            ON CONFLICT DO NOTHING
        """)

        with httpx.Client(timeout=30) as client, engine.connect() as conn:
            for lat_i in range(lat_steps):
                lat = bbox["south"] + (lat_i + 0.5) * (bbox["north"] - bbox["south"]) / lat_steps
                for lon_i in range(lon_steps):
                    lon = bbox["west"] + (lon_i + 0.5) * (bbox["east"] - bbox["west"]) / lon_steps

                    for attempt in range(3):
                        try:
                            resp = client.get(MACROSTRAT_URL, params={
                                "lat": lat, "lng": lon, "format": "geojson"
                            })
                            if resp.status_code == 200:
                                break
                            time.sleep(2)
                        except (httpx.ConnectError, httpx.ReadTimeout):
                            time.sleep(3)
                    else:
                        continue

                    data = resp.json()
                    features = data.get("success", {}).get("data", {}).get("features", [])

                    for f in features:
                        props = f.get("properties", {})
                        map_id = str(props.get("map_id", ""))
                        if not map_id or map_id in seen_map_ids:
                            continue
                        seen_map_ids.add(map_id)

                        geom = f.get("geometry")
                        geojson = json.dumps(geom) if geom else None

                        # Extract rock type from lithology string
                        lith = props.get("lith", "") or ""
                        rock_type = _extract_rock_type(lith)

                        # Extract period from interval names
                        t_int = props.get("t_int_name", "")
                        b_int = props.get("b_int_name", "")
                        period = props.get("best_int_name") or t_int or b_int

                        try:
                            age_min = float(props["t_age"]) if props.get("t_age") is not None else None
                            age_max = float(props["b_age"]) if props.get("b_age") is not None else None
                        except (ValueError, TypeError):
                            age_min = None
                            age_max = None

                        params = {
                            "source_id": map_id,
                            "unit_name": str(props.get("name") or props.get("strat_name") or "")[:255],
                            "formation": str(props.get("strat_name") or "")[:255],
                            "rock_type": rock_type[:100] if rock_type else None,
                            "lithology": lith[:255] if lith else None,
                            "age_min": age_min,
                            "age_max": age_max,
                            "period": str(period or "")[:100] if period else None,
                            "description": str(props.get("descrip") or ""),
                            "payload": json.dumps(props),
                        }

                        if geojson:
                            params["geojson"] = geojson
                            conn.execute(SQL, params)
                        else:
                            conn.execute(SQL_NO_GEOM, params)
                        created += 1

                    # Rate limiting — be nice to Macrostrat
                    time.sleep(0.2)

            conn.commit()

        console.print(f"    loaded {created} unique geologic unit polygons")
        return created, 0


def _extract_rock_type(lith_string: str) -> str:
    """Extract broad rock type (igneous/sedimentary/metamorphic) from Macrostrat lith string."""
    lith_lower = lith_string.lower()
    igneous_terms = ["basalt", "rhyolite", "andesite", "dacite", "granite", "diorite", "gabbro",
                     "volcanic", "lava", "tuff", "ignimbrite", "obsidian", "pumice", "ash"]
    sedimentary_terms = ["sandstone", "shale", "limestone", "conglomerate", "mudstone", "siltstone",
                         "clay", "marl", "chalk", "dolostone", "chert", "coal", "evaporite"]
    metamorphic_terms = ["schist", "gneiss", "marble", "slate", "quartzite", "phyllite",
                         "amphibolite", "serpentinite", "greenstone", "metamorphic"]

    for term in igneous_terms:
        if term in lith_lower:
            return "igneous"
    for term in sedimentary_terms:
        if term in lith_lower:
            return "sedimentary"
    for term in metamorphic_terms:
        if term in lith_lower:
            return "metamorphic"
    return ""


class PBDBFossilAdapter(IngestionAdapter):
    """Paleobiology Database — fossil occurrences for Oregon."""
    source_type = "pbdb"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        bbox = site.bbox
        created = 0

        with httpx.Client(timeout=120) as client:
            console.print("    fetching PBDB fossil occurrences...")

            # PBDB default vocab uses abbreviated keys (oid, tna, eag, lag, etc.)
            params = {
                "lngmin": bbox["west"],
                "lngmax": bbox["east"],
                "latmin": bbox["south"],
                "latmax": bbox["north"],
                "show": "coords,class,loc,time,ref",
                "limit": "all",
            }

            resp = client.get(PBDB_URL, params=params)
            if resp.status_code != 200:
                raise ValueError(f"PBDB API returned {resp.status_code}")

            data = resp.json()
            records = data.get("records", [])
            console.print(f"    received {len(records)} fossil occurrences")

            if not records:
                return 0, 0

            SQL = text("""
                INSERT INTO fossil_occurrences (id, source, source_id, taxon_name, taxon_id,
                    common_name, phylum, class_name, order_name, family,
                    age_min_ma, age_max_ma, period, formation,
                    location, latitude, longitude,
                    collector, reference, museum, data_payload)
                VALUES (gen_random_uuid(), 'pbdb', :source_id, :taxon_name, :taxon_id,
                    :common_name, :phylum, :class_name, :order_name, :family,
                    :age_min, :age_max, :period, :formation,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :lat, :lon,
                    :collector, :reference, :museum, CAST(:payload AS jsonb))
                ON CONFLICT (source, source_id) DO UPDATE SET
                    taxon_name = EXCLUDED.taxon_name,
                    age_min_ma = EXCLUDED.age_min_ma,
                    age_max_ma = EXCLUDED.age_max_ma,
                    data_payload = EXCLUDED.data_payload
            """)

            with engine.connect() as conn:
                for rec in records:
                    # PBDB abbreviated keys: oid=occurrence_no, tna=taxon_name,
                    # eag=early_age (max_ma), lag=late_age (min_ma)
                    oid = str(rec.get("oid", ""))
                    if not oid:
                        continue
                    lat = rec.get("lat")
                    lon = rec.get("lng")
                    if lat is None or lon is None:
                        continue

                    try:
                        age_min = float(rec["lag"]) if rec.get("lag") else None  # late age = min_ma
                        age_max = float(rec["eag"]) if rec.get("eag") else None  # early age = max_ma
                    except (ValueError, TypeError):
                        age_min = None
                        age_max = None

                    # oei = early interval name (period)
                    period = rec.get("oei") or _age_to_period(age_max or age_min)

                    params = {
                        "source_id": oid,
                        "taxon_name": (rec.get("tna") or "")[:255],
                        "taxon_id": str(rec.get("tid", ""))[:100],
                        "common_name": None,
                        "phylum": (rec.get("phl") or "")[:100] or None,
                        "class_name": (rec.get("cll") or "")[:100] or None,
                        "order_name": (rec.get("odl") or "")[:100] or None,
                        "family": (rec.get("fml") or "")[:100] or None,
                        "age_min": age_min,
                        "age_max": age_max,
                        "period": str(period or "")[:100] if period else None,
                        "formation": None,  # Not in default show fields
                        "lat": float(lat),
                        "lon": float(lon),
                        "collector": None,
                        "reference": str(rec.get("ref") or ""),
                        "museum": None,
                        "payload": json.dumps(rec),
                    }
                    conn.execute(SQL, params)
                    created += 1

                conn.commit()

        return created, 0


class BLMLandOwnershipAdapter(IngestionAdapter):
    """BLM Surface Management Agency — land ownership for Oregon.

    The BLM SMA cached service does not return geometry in queries.
    We store the ownership records without geometry; real-time point-in-polygon
    lookups use the API's identify/query endpoint directly.
    """
    source_type = "blm_sma"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        created = 0
        with httpx.Client(timeout=120) as client:
            console.print("    fetching BLM SMA land ownership (attributes only)...")
            # Query without geometry since the cached service doesn't support it
            bbox = site.bbox
            all_features = []
            offset = 0
            while True:
                params = {
                    "geometry": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
                    "geometryType": "esriGeometryEnvelope",
                    "inSR": "4326", "outSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "where": "1=1",
                    "outFields": "*",
                    "returnGeometry": "false",
                    "f": "json",
                    "resultRecordCount": "1000",
                    "resultOffset": str(offset),
                }

                for attempt in range(3):
                    try:
                        resp = client.get(BLM_SMA_URL, params=params, timeout=60)
                        if resp.status_code == 200:
                            data = resp.json()
                            if "error" in data:
                                console.print(f"    [yellow]BLM SMA error: {data['error'].get('message', 'unknown')}[/yellow]")
                                break
                            features = data.get("features", [])
                            all_features.extend(features)
                            if len(features) < 1000:
                                break
                            offset += len(features)
                            break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        time.sleep(5)
                else:
                    break
                if not features or len(features) < 1000:
                    break

            console.print(f"    received {len(all_features)} land ownership records")

            if not all_features:
                return 0, 0

            SQL = text("""
                INSERT INTO land_ownership (id, source, source_id, agency, designation,
                    admin_unit, collecting_status, collecting_rules, data_payload)
                VALUES (gen_random_uuid(), 'blm_sma', :source_id, :agency, :designation,
                    :admin_unit, :collecting_status, :collecting_rules,
                    CAST(:payload AS jsonb))
                ON CONFLICT DO NOTHING
            """)

            with engine.connect() as conn:
                for f in all_features:
                    attrs = f.get("attributes", {})

                    source_id = str(attrs.get("OBJECTID", attrs.get("FID", "")))
                    agency = attrs.get("ADMIN_AGENCY_CODE", "")
                    designation = attrs.get("ADMIN_UNIT_TYPE", "")
                    admin_unit = attrs.get("ADMIN_UNIT_NAME", "")

                    # Derive collecting status from agency
                    agency_key = str(agency or "").upper().strip()
                    status_info = AGENCY_COLLECTING_RULES.get(agency_key, ("restricted", "Check local regulations."))
                    collecting_status = status_info[0]
                    collecting_rules = status_info[1]

                    params = {
                        "source_id": source_id,
                        "agency": str(agency or "")[:100],
                        "designation": str(designation or "")[:255],
                        "admin_unit": str(admin_unit or "")[:255],
                        "collecting_status": collecting_status,
                        "collecting_rules": collecting_rules,
                        "payload": json.dumps(attrs),
                    }
                    conn.execute(SQL, params)
                    created += 1

                conn.commit()

        return created, 0


def lookup_land_ownership_at_point(lat: float, lon: float) -> dict | None:
    """Real-time point query against BLM SMA service for land ownership at a lat/lon.

    Returns dict with agency, collecting_status, collecting_rules, or None if service unavailable.
    """
    url = BLM_SMA_URL
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "where": "1=1",
        "outFields": "ADMIN_AGENCY_CODE,ADMIN_UNIT_NAME,ADMIN_UNIT_TYPE",
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": "1",
    }
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
            features = data.get("features", [])
            if not features:
                return {"agency": "PRIVATE", "collecting_status": "prohibited",
                        "collecting_rules": "Private land — collecting requires landowner permission.",
                        "admin_unit": "Unknown"}
            attrs = features[0].get("attributes", {})
            agency = attrs.get("ADMIN_AGENCY_CODE", "")
            agency_key = str(agency or "").upper().strip()
            status_info = AGENCY_COLLECTING_RULES.get(agency_key, ("restricted", "Check local regulations."))
            return {
                "agency": agency,
                "admin_unit": attrs.get("ADMIN_UNIT_NAME", ""),
                "designation": attrs.get("ADMIN_UNIT_TYPE", ""),
                "collecting_status": status_info[0],
                "collecting_rules": status_info[1],
            }
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# Phase 2 adapters: DOGAMI, MRDS, iDigBio, NPS GRI
# ──────────────────────────────────────────────────────────────

# Oregon DOGAMI OGDC v6 — state geologic map, layer 3
DOGAMI_URL = "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/OGDC6/MapServer/3/query"

# USGS MRDS — mineral deposit locations (WFS)
MRDS_URL = "https://mrdata.usgs.gov/services/mrds"

# iDigBio — digitized museum fossil specimens
IDIGBIO_URL = "https://search.idigbio.org/v2/search/records"

# Commodity code lookup for MRDS
COMMODITY_NAMES = {
    "AU": "Gold", "AG": "Silver", "CU": "Copper", "HG": "Mercury",
    "CR": "Chromium", "NI": "Nickel", "ZN": "Zinc", "PB": "Lead",
    "FE": "Iron", "MN": "Manganese", "CO": "Cobalt", "MO": "Molybdenum",
    "W": "Tungsten", "U": "Uranium", "PUM": "Pumice", "ZEO": "Zeolites",
    "TLC": "Talc", "Cite": "Ite", "PER": "Perlite", "DIA": "Diatomite",
    "BNT": "Bentonite", "STN": "Stone", "SND": "Sand", "GVL": "Gravel",
    "Cite": "ite", "HES": "Geothermal",
}


class DOGAMIAdapter(IngestionAdapter):
    """Oregon DOGAMI OGDC v6 — high-resolution state geologic unit polygons."""
    source_type = "dogami"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        created = 0
        with httpx.Client(timeout=120) as client:
            console.print("    fetching DOGAMI OGDC6 geologic units...")
            features = _arcgis_query_paginated(client, DOGAMI_URL, site.bbox, max_per_page=1000)
            console.print(f"    received {len(features)} DOGAMI polygons")

            if not features:
                return 0, 0

            SQL = text("""
                INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                    rock_type, lithology, age_min_ma, age_max_ma, period, description,
                    geometry, data_payload)
                VALUES (gen_random_uuid(), 'dogami', :source_id, :unit_name, :formation,
                    :rock_type, :lithology, :age_min, :age_max, :period, :description,
                    ST_GeomFromGeoJSON(:geojson), CAST(:payload AS jsonb))
                ON CONFLICT DO NOTHING
            """)

            SQL_NO_GEOM = text("""
                INSERT INTO geologic_units (id, source, source_id, unit_name, formation,
                    rock_type, lithology, age_min_ma, age_max_ma, period, description,
                    data_payload)
                VALUES (gen_random_uuid(), 'dogami', :source_id, :unit_name, :formation,
                    :rock_type, :lithology, :age_min, :age_max, :period, :description,
                    CAST(:payload AS jsonb))
                ON CONFLICT DO NOTHING
            """)

            with engine.connect() as conn:
                for f in features:
                    attrs = f.get("attributes", {})
                    geojson = _esri_rings_to_geojson(f.get("geometry"))

                    source_id = str(attrs.get("OBJECTID", ""))
                    unit_name = attrs.get("MAP_UNIT_N", "") or attrs.get("MAP_UNIT_L", "")
                    formation = attrs.get("FORMATION", "") or ""
                    rock_type = attrs.get("GN_LITH_TY", "") or attrs.get("G_ROCK_TYP", "")
                    lithology = attrs.get("LTH_RK_TYP", "") or ""
                    age_name = attrs.get("AGE_NAME", "") or ""
                    description = attrs.get("des", "") or ""

                    # DOGAMI doesn't provide numeric ages, just period names
                    period = age_name.split("/")[0].strip() if age_name else None

                    params = {
                        "source_id": source_id,
                        "unit_name": str(unit_name)[:255],
                        "formation": str(formation)[:255],
                        "rock_type": str(rock_type)[:100],
                        "lithology": str(lithology)[:255],
                        "age_min": None,
                        "age_max": None,
                        "period": str(period or "")[:100] if period else None,
                        "description": str(description),
                        "payload": json.dumps(attrs),
                    }

                    if geojson:
                        params["geojson"] = geojson
                        conn.execute(SQL, params)
                    else:
                        conn.execute(SQL_NO_GEOM, params)
                    created += 1

                conn.commit()

        return created, 0


class MRDSAdapter(IngestionAdapter):
    """USGS Mineral Resources Data System — mineral deposit locations via WFS."""
    source_type = "mrds"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        bbox = site.bbox
        created = 0

        with httpx.Client(timeout=120) as client:
            console.print("    fetching USGS MRDS mineral deposits (WFS)...")

            # WFS requires BBOX in lat,lon order for EPSG:4326
            wfs_bbox = f"{bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']},urn:ogc:def:crs:EPSG::4326"

            offset = 0
            while True:
                params = {
                    "service": "WFS",
                    "version": "1.1.0",
                    "request": "GetFeature",
                    "typeName": "mrds-high",
                    "maxFeatures": "500",
                    "startIndex": str(offset),
                    "BBOX": wfs_bbox,
                }

                for attempt in range(3):
                    try:
                        resp = client.get(MRDS_URL, params=params, timeout=60)
                        if resp.status_code == 200:
                            break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        time.sleep(5)
                else:
                    break

                # Parse GML XML response
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(resp.text)
                except ET.ParseError:
                    console.print("    [yellow]MRDS: failed to parse WFS response[/yellow]")
                    break

                ns = {
                    "gml": "http://www.opengis.net/gml",
                    "ms": "http://mapserver.gis.umn.edu/mapserver",
                    "wfs": "http://www.opengis.net/wfs",
                }

                members = root.findall(".//gml:featureMember", ns)
                if not members:
                    break

                SQL = text("""
                    INSERT INTO mineral_deposits (id, source, source_id, site_name, commodity,
                        dev_status, location, latitude, longitude, data_payload)
                    VALUES (gen_random_uuid(), 'mrds', :source_id, :site_name, :commodity,
                        :dev_status, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                        :lat, :lon, CAST(:payload AS jsonb))
                    ON CONFLICT (source, source_id) DO UPDATE SET
                        commodity = EXCLUDED.commodity,
                        dev_status = EXCLUDED.dev_status,
                        data_payload = EXCLUDED.data_payload
                """)

                with engine.connect() as conn:
                    batch_count = 0
                    for member in members:
                        feat = member.find("ms:mrds-high", ns)
                        if feat is None:
                            continue

                        dep_id = feat.findtext("ms:dep_id", "", ns)
                        site_name = feat.findtext("ms:site_name", "", ns)
                        dev_stat = feat.findtext("ms:dev_stat", "", ns)
                        code_list = feat.findtext("ms:code_list", "", ns).strip()

                        # Expand commodity codes to names
                        codes = [c.strip() for c in code_list.split() if c.strip()]
                        commodity_names = [COMMODITY_NAMES.get(c, c) for c in codes]
                        commodity = ", ".join(commodity_names) if commodity_names else code_list

                        # Extract coordinates from GML pos
                        pos_el = feat.find(".//gml:pos", ns)
                        if pos_el is None or not pos_el.text:
                            continue
                        parts = pos_el.text.strip().split()
                        if len(parts) < 2:
                            continue
                        lat = float(parts[0])
                        lon = float(parts[1])

                        payload = {
                            "dep_id": dep_id, "site_name": site_name,
                            "dev_stat": dev_stat, "code_list": code_list,
                            "fips_code": feat.findtext("ms:fips_code", "", ns),
                            "url": feat.findtext("ms:url", "", ns),
                        }

                        conn.execute(SQL, {
                            "source_id": dep_id,
                            "site_name": str(site_name)[:255],
                            "commodity": str(commodity)[:255],
                            "dev_status": str(dev_stat)[:100],
                            "lat": lat, "lon": lon,
                            "payload": json.dumps(payload),
                        })
                        created += 1
                        batch_count += 1

                    conn.commit()

                if batch_count < 500:
                    break
                offset += batch_count

        console.print(f"    loaded {created} mineral deposits")
        return created, 0


class IDigBioFossilAdapter(IngestionAdapter):
    """iDigBio — digitized museum fossil specimens with photos."""
    source_type = "idigbio"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        bbox = site.bbox
        created = 0
        page_size = 100

        with httpx.Client(timeout=60) as client:
            console.print("    fetching iDigBio fossil specimens...")

            offset = 0
            while True:
                body = {
                    "rq": {
                        "basisofrecord": "fossilspecimen",
                        "geopoint": {
                            "type": "geo_bounding_box",
                            "top_left": {"lat": bbox["north"], "lon": bbox["west"]},
                            "bottom_right": {"lat": bbox["south"], "lon": bbox["east"]},
                        },
                    },
                    "limit": page_size,
                    "offset": offset,
                }

                for attempt in range(3):
                    try:
                        resp = client.post(IDIGBIO_URL, json=body)
                        if resp.status_code == 200:
                            break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        time.sleep(5)
                else:
                    break

                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                SQL = text("""
                    INSERT INTO fossil_occurrences (id, source, source_id, taxon_name, taxon_id,
                        common_name, phylum, class_name, order_name, family,
                        age_min_ma, age_max_ma, period, formation,
                        location, latitude, longitude,
                        collector, reference, museum, data_payload)
                    VALUES (gen_random_uuid(), 'idigbio', :source_id, :taxon_name, :taxon_id,
                        :common_name, :phylum, :class_name, :order_name, :family,
                        :age_min, :age_max, :period, :formation,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :lat, :lon,
                        :collector, :reference, :museum, CAST(:payload AS jsonb))
                    ON CONFLICT (source, source_id) DO UPDATE SET
                        taxon_name = EXCLUDED.taxon_name,
                        data_payload = EXCLUDED.data_payload
                """)

                with engine.connect() as conn:
                    for item in items:
                        idx = item.get("indexTerms", {})
                        dat = item.get("data", {})
                        uuid_val = item.get("uuid", "")

                        geopoint = idx.get("geopoint", {})
                        lat = geopoint.get("lat")
                        lon = geopoint.get("lon")
                        if lat is None or lon is None:
                            continue

                        taxon = idx.get("scientificname", dat.get("dwc:scientificName", ""))
                        if not taxon:
                            continue

                        # Check for photo
                        has_image = idx.get("hasImage", False)
                        media = idx.get("mediarecords", [])
                        photo_url = f"https://search.idigbio.org/v2/view/mediarecords/{media[0]}" if media else None

                        conn.execute(SQL, {
                            "source_id": uuid_val,
                            "taxon_name": str(taxon)[:255],
                            "taxon_id": str(idx.get("uuid", ""))[:100],
                            "common_name": None,
                            "phylum": (idx.get("phylum") or "")[:100] or None,
                            "class_name": (idx.get("class") or "")[:100] or None,
                            "order_name": (idx.get("order") or "")[:100] or None,
                            "family": (idx.get("family") or "")[:100] or None,
                            "age_min": None,
                            "age_max": None,
                            "period": (dat.get("dwc:earliestPeriodOrLowestSystem") or "")[:100] or None,
                            "formation": (dat.get("dwc:formation") or "")[:255] or None,
                            "lat": float(lat),
                            "lon": float(lon),
                            "collector": (dat.get("dwc:recordedBy") or "")[:255] or None,
                            "reference": photo_url or "",
                            "museum": (idx.get("institutioncode") or "")[:255] or None,
                            "payload": json.dumps({"uuid": uuid_val, "hasImage": has_image,
                                                   "catalog": dat.get("dwc:catalogNumber", "")}),
                        })
                        created += 1

                    conn.commit()

                if len(items) < page_size:
                    break
                offset += len(items)
                time.sleep(0.5)  # Rate limiting

        console.print(f"    loaded {created} iDigBio fossil specimens")
        return created, 0
