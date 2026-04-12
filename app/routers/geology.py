"""Geology API endpoints: geologic context, fossils, land ownership, deep time."""

import json

from fastapi import APIRouter, Query
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["geology"])


@router.get("/geology/at/{lat}/{lon}")
def get_geology_at_point(lat: float, lon: float):
    """Return geologic unit at a geographic point."""
    sql = text("""
        SELECT id, source, source_id, unit_name, formation, rock_type, lithology,
               age_min_ma, age_max_ma, period, description
        FROM geologic_units
        WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        ORDER BY age_max_ma ASC NULLS LAST
        LIMIT 5
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"lat": lat, "lon": lon}).fetchall()

    if not rows:
        return {"units": [], "message": "No geologic data at this location"}

    units = []
    for r in rows:
        units.append({
            "id": str(r[0]),
            "source": r[1],
            "unit_name": r[3],
            "formation": r[4],
            "rock_type": r[5],
            "lithology": r[6],
            "age_min_ma": r[7],
            "age_max_ma": r[8],
            "period": r[9],
            "description": r[10],
        })
    return {"units": units}


@router.get("/geology/units")
def get_geology_units_in_bbox(
    west: float = Query(...), south: float = Query(...),
    east: float = Query(...), north: float = Query(...),
    limit: int = Query(500, le=1000),
):
    """Return geologic unit polygons within a bounding box as GeoJSON."""
    sql = text("""
        SELECT source_id, unit_name, formation, rock_type, lithology,
               age_min_ma, age_max_ma, period,
               ST_AsGeoJSON(geometry) as geojson
        FROM geologic_units
        WHERE geometry && ST_MakeEnvelope(:west, :south, :east, :north, 4326)
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {
            "west": west, "south": south, "east": east, "north": north, "limit": limit
        }).fetchall()

    features = []
    for r in rows:
        features.append({
            "type": "Feature",
            "properties": {
                "source_id": r[0], "unit_name": r[1], "formation": r[2],
                "rock_type": r[3], "lithology": r[4],
                "age_min_ma": r[5], "age_max_ma": r[6], "period": r[7],
            },
            "geometry": json.loads(r[8]) if r[8] else None,
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/geology/watershed-link/{watershed}")
def get_geology_watershed_link(watershed: str):
    """Return geology-ecology correlations for a watershed."""
    # Get geologic units in the watershed bbox
    from pipeline.config.watersheds import WATERSHEDS
    ws = WATERSHEDS.get(watershed)
    if not ws:
        return {"error": f"Unknown watershed: {watershed}"}

    bbox = ws["bbox"]
    sql = text("""
        SELECT DISTINCT unit_name, formation, rock_type, lithology, period,
               age_min_ma, age_max_ma
        FROM geologic_units
        WHERE geometry && ST_MakeEnvelope(:west, :south, :east, :north, 4326)
        ORDER BY age_max_ma DESC NULLS LAST
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, bbox).fetchall()

    units = [{
        "unit_name": r[0], "formation": r[1], "rock_type": r[2],
        "lithology": r[3], "period": r[4],
        "age_min_ma": r[5], "age_max_ma": r[6],
    } for r in rows]

    return {"watershed": watershed, "geologic_units": units, "count": len(units)}


@router.get("/fossils/near/{lat}/{lon}")
def get_fossils_near(lat: float, lon: float, radius_km: float = Query(25, le=100)):
    """Return fossil occurrences within radius of a point."""
    sql = text("""
        SELECT source_id, taxon_name, phylum, class_name, order_name, family,
               age_min_ma, age_max_ma, period, formation,
               latitude, longitude, collector, reference, museum,
               ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000 as distance_km
        FROM fossil_occurrences
        WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m)
        ORDER BY distance_km
        LIMIT 100
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {
            "lat": lat, "lon": lon, "radius_m": radius_km * 1000
        }).fetchall()

    fossils = []
    for r in rows:
        fossils.append({
            "source_id": r[0], "taxon_name": r[1],
            "phylum": r[2], "class_name": r[3],
            "order_name": r[4], "family": r[5],
            "age_min_ma": r[6], "age_max_ma": r[7],
            "period": r[8], "formation": r[9],
            "latitude": r[10], "longitude": r[11],
            "collector": r[12], "reference": r[13], "museum": r[14],
            "distance_km": round(r[15], 1) if r[15] else None,
            "image_url": r[13] if r[13] and (r[13].startswith('https://images.') or r[13].startswith('https://www.') or r[13].startswith('https://collections.') or '.jpg' in r[13] or '.jpeg' in r[13]) else None,
        })

    return {"fossils": fossils, "count": len(fossils), "radius_km": radius_km}


@router.get("/fossils/by-formation/{formation}")
def get_fossils_by_formation(formation: str):
    """Return fossils found in a specific geologic formation."""
    sql = text("""
        SELECT taxon_name, phylum, class_name, period, age_min_ma, age_max_ma,
               latitude, longitude, count(*) as occurrences
        FROM fossil_occurrences
        WHERE formation ILIKE :formation
        GROUP BY taxon_name, phylum, class_name, period, age_min_ma, age_max_ma,
                 latitude, longitude
        ORDER BY occurrences DESC
        LIMIT 100
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"formation": f"%{formation}%"}).fetchall()

    return {
        "formation": formation,
        "taxa": [{
            "taxon_name": r[0], "phylum": r[1], "class_name": r[2],
            "period": r[3], "age_min_ma": r[4], "age_max_ma": r[5],
            "latitude": r[6], "longitude": r[7], "occurrences": r[8],
        } for r in rows],
        "count": len(rows),
    }


@router.get("/land/at/{lat}/{lon}")
def get_land_ownership_at_point(lat: float, lon: float):
    """Return land ownership and legal collecting status at a point.

    Uses real-time BLM SMA API query. Always shows disclaimer.
    """
    from pipeline.ingest.geology import lookup_land_ownership_at_point

    result = lookup_land_ownership_at_point(lat, lon)
    if result is None:
        return {
            "agency": "unknown",
            "collecting_status": "unknown",
            "collecting_rules": "Unable to determine land ownership. Check with local land manager.",
            "disclaimer": "Always verify on-site with posted signs and local regulations.",
        }

    result["disclaimer"] = "Always verify on-site with posted signs and local regulations."
    return result


@router.get("/land/collecting-sites")
def get_legal_collecting_sites(
    west: float = Query(...), south: float = Query(...),
    east: float = Query(...), north: float = Query(...),
):
    """Return land ownership records where collecting is permitted within bbox."""
    sql = text("""
        SELECT agency, designation, admin_unit, collecting_status, collecting_rules
        FROM land_ownership
        WHERE collecting_status IN ('permitted', 'restricted')
        ORDER BY collecting_status, agency
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()

    sites = [{
        "agency": r[0], "designation": r[1], "admin_unit": r[2],
        "collecting_status": r[3], "collecting_rules": r[4],
    } for r in rows]

    return {
        "sites": sites,
        "count": len(sites),
        "disclaimer": "Always verify on-site with posted signs and local regulations.",
    }


@router.get("/minerals/near/{lat}/{lon}")
def get_minerals_near(lat: float, lon: float, radius_km: float = Query(50, le=200)):
    """Return mineral deposit locations within radius of a point."""
    sql = text("""
        SELECT source_id, site_name, commodity, dev_status,
               latitude, longitude,
               ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000 as distance_km
        FROM mineral_deposits
        WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m)
        ORDER BY distance_km
        LIMIT 100
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {
            "lat": lat, "lon": lon, "radius_m": radius_km * 1000
        }).fetchall()

    minerals = [{
        "source_id": r[0], "site_name": r[1], "commodity": r[2],
        "dev_status": r[3], "latitude": r[4], "longitude": r[5],
        "distance_km": round(r[6], 1) if r[6] else None,
    } for r in rows]

    return {"minerals": minerals, "count": len(minerals), "radius_km": radius_km}


@router.post("/deep-time/story")
def generate_deep_time_story(body: dict):
    """Generate a deep time narrative for a location.

    Request body: {"lat": float, "lon": float, "reading_level": "adult"|"kid_friendly"|"expert"}
    """
    lat = body.get("lat")
    lon = body.get("lon")
    reading_level = body.get("reading_level", "adult")

    if lat is None or lon is None:
        return {"error": "lat and lon are required"}

    # Check cache first
    cache_sql = text("""
        SELECT narrative, evidence_cited, generated_at
        FROM deep_time_stories
        WHERE geologic_unit_id = (
            SELECT id FROM geologic_units
            WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            ORDER BY age_max_ma ASC NULLS LAST
            LIMIT 1
        ) AND reading_level = :level
    """)
    with engine.connect() as conn:
        cached = conn.execute(cache_sql, {"lat": lat, "lon": lon, "level": reading_level}).fetchone()

    if cached and cached[0]:
        return {
            "narrative": cached[0],
            "evidence_cited": cached[1],
            "generated_at": str(cached[2]),
            "cached": True,
        }

    # Build context from geology + fossils for LLM
    from pipeline.tools import get_deep_time_story
    result = get_deep_time_story(lat, lon)

    return {**result, "cached": False}


@router.get("/deep-time/timeline/{lat}/{lon}")
def get_deep_time_timeline(lat: float, lon: float):
    """Return chronological geologic event timeline at a location."""
    # Get geologic units at this point
    geo_sql = text("""
        SELECT unit_name, formation, rock_type, lithology, age_min_ma, age_max_ma, period, description
        FROM geologic_units
        WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        ORDER BY age_max_ma DESC NULLS LAST
    """)

    # Get nearby fossils
    fossil_sql = text("""
        SELECT taxon_name, phylum, class_name, period, age_min_ma, age_max_ma
        FROM fossil_occurrences
        WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 25000)
        ORDER BY age_max_ma DESC NULLS LAST
    """)

    with engine.connect() as conn:
        geo_rows = conn.execute(geo_sql, {"lat": lat, "lon": lon}).fetchall()
        fossil_rows = conn.execute(fossil_sql, {"lat": lat, "lon": lon}).fetchall()

    timeline = []
    for r in geo_rows:
        timeline.append({
            "type": "geologic_unit",
            "name": r[0] or r[1],
            "rock_type": r[2], "lithology": r[3],
            "age_min_ma": r[4], "age_max_ma": r[5],
            "period": r[6], "description": r[7],
        })

    for r in fossil_rows:
        timeline.append({
            "type": "fossil",
            "taxon_name": r[0], "phylum": r[1], "class_name": r[2],
            "period": r[3], "age_min_ma": r[4], "age_max_ma": r[5],
        })

    # Sort by age (oldest first)
    timeline.sort(key=lambda x: x.get("age_max_ma") or 0, reverse=True)

    return {"lat": lat, "lon": lon, "timeline": timeline}
