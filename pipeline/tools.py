"""LLM tool functions for the ecological reasoning agent.

These functions are designed to be called by a tool-using LLM agent.
Each returns structured data that the LLM can reason over and format
for the user.
"""

import json
from pipeline.db import engine
from sqlalchemy import text


def get_species_with_photos(river_name: str, mile_start: float, mile_end: float) -> list[dict]:
    """Returns species list with photo URLs for a river section.

    Args:
        river_name: e.g., "Deschutes River", "McKenzie River"
        mile_start: start river mile from source
        mile_end: end river mile from source

    Returns:
        List of species dicts with taxon_name, common_name, photo_url,
        observation_count, taxonomic_group
    """
    section_start = int(mile_start // 5) * 5
    section_end = int(mile_end // 5) * 5 + 5

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT taxon_name, common_name, taxonomic_group,
                   sum(observation_count) as total_obs,
                   max(last_seen) as last_seen,
                   max(photo_url) as photo_url
            FROM gold.species_by_river_mile
            WHERE river_name = :river
              AND mile_section_start >= :start AND mile_section_end <= :end
            GROUP BY taxon_name, common_name, taxonomic_group
            ORDER BY total_obs DESC
        """), {"river": river_name, "start": section_start, "end": section_end}).fetchall()

    return [
        {
            "taxon_name": r[0],
            "common_name": r[1] or r[0],
            "taxonomic_group": r[2],
            "observation_count": r[3],
            "last_seen": str(r[4]) if r[4] else None,
            "photo_url": r[5],
        }
        for r in rows
    ]


def get_river_conditions(river_name: str, watershed: str) -> dict:
    """Returns current water conditions for a river.

    Args:
        river_name: e.g., "Deschutes River"
        watershed: e.g., "deschutes"

    Returns:
        Dict with water_temp, discharge, dissolved_oxygen, and thermal stations
    """
    with engine.connect() as conn:
        # Latest water conditions
        conditions = conn.execute(text("""
            SELECT parameter, avg_value, unit, station_id
            FROM (
                SELECT w.parameter,
                       round(avg(w.value)::numeric, 1) as avg_value,
                       w.unit, w.station_id,
                       row_number() OVER (PARTITION BY w.parameter ORDER BY w.obs_date DESC) as rn
                FROM silver.water_conditions w
                WHERE w.watershed = :ws AND w.source_type = 'usgs'
                  AND w.parameter IN ('water_temperature', 'discharge', 'dissolved_oxygen')
                GROUP BY w.parameter, w.unit, w.station_id, w.obs_date
            ) sub WHERE rn = 1
        """), {"ws": watershed}).fetchall()

        # Cold water refuges
        refuges = conn.execute(text("""
            SELECT station_id, thermal_classification, summer_avg_temp, multi_year_summer_avg
            FROM gold.cold_water_refuges
            WHERE watershed = :ws AND obs_year = (SELECT max(obs_year) FROM gold.cold_water_refuges WHERE watershed = :ws)
            ORDER BY summer_avg_temp
        """), {"ws": watershed}).fetchall()

    return {
        "conditions": [
            {"parameter": r[0], "value": float(r[1]), "unit": r[2], "station": r[3]}
            for r in conditions
        ],
        "cold_water_refuges": [
            {"station": r[0], "classification": r[1],
             "summer_avg_temp": float(r[2]) if r[2] else None,
             "multi_year_avg": float(r[3]) if r[3] else None}
            for r in refuges
        ],
    }


def get_fishing_brief(watershed: str, month: int = None) -> dict:
    """Returns a fishing conditions summary for a watershed.

    Args:
        watershed: e.g., "deschutes"
        month: optional month (1-12), defaults to most recent

    Returns:
        Dict with water conditions, harvest trends, stocking, species by reach
    """
    with engine.connect() as conn:
        # Fishing conditions for the month
        if month:
            fc = conn.execute(text("""
                SELECT avg_water_temp_c, max_water_temp_c, avg_discharge_cfs, avg_do_mg_l,
                       steelhead_harvest, chinook_harvest, coho_harvest, trout_stocked
                FROM gold.fishing_conditions
                WHERE watershed = :ws AND obs_month = :m
                ORDER BY obs_year DESC LIMIT 1
            """), {"ws": watershed, "m": month}).fetchone()
        else:
            fc = conn.execute(text("""
                SELECT avg_water_temp_c, max_water_temp_c, avg_discharge_cfs, avg_do_mg_l,
                       steelhead_harvest, chinook_harvest, coho_harvest, trout_stocked
                FROM gold.fishing_conditions
                WHERE watershed = :ws
                ORDER BY obs_year DESC, obs_month DESC LIMIT 1
            """), {"ws": watershed}).fetchone()

        # Harvest trends
        trends = conn.execute(text("""
            SELECT species, harvest_year, annual_harvest, harvest_delta, harvest_pct_change
            FROM gold.harvest_trends WHERE watershed = :ws
            ORDER BY harvest_year DESC, annual_harvest DESC LIMIT 10
        """), {"ws": watershed}).fetchall()

        # Upcoming stocking
        stocking = conn.execute(text("""
            SELECT waterbody, stocking_date, total_fish
            FROM gold.stocking_schedule WHERE watershed = :ws
            ORDER BY stocking_date DESC LIMIT 5
        """), {"ws": watershed}).fetchall()

        # Species by reach (top fish)
        species = conn.execute(text("""
            SELECT stream_name, scientific_name, common_name, use_type, origin
            FROM gold.species_by_reach WHERE watershed = :ws
            ORDER BY stream_name, scientific_name LIMIT 20
        """), {"ws": watershed}).fetchall()

    return {
        "conditions": {
            "water_temp_c": float(fc[0]) if fc and fc[0] else None,
            "max_water_temp_c": float(fc[1]) if fc and fc[1] else None,
            "discharge_cfs": float(fc[2]) if fc and fc[2] else None,
            "do_mg_l": float(fc[3]) if fc and fc[3] else None,
            "steelhead_harvest": fc[4] if fc else None,
            "chinook_harvest": fc[5] if fc else None,
            "trout_stocked": fc[7] if fc else None,
        } if fc else None,
        "harvest_trends": [
            {"species": r[0], "year": r[1], "harvest": r[2], "delta": r[3], "pct_change": float(r[4]) if r[4] else None}
            for r in trends
        ],
        "stocking": [
            {"waterbody": r[0], "date": str(r[1]), "fish": r[2]}
            for r in stocking
        ],
        "species_by_reach": [
            {"stream": r[0], "species": r[1], "common_name": r[2], "use_type": r[3], "origin": r[4]}
            for r in species
        ],
    }


def get_indicator_status(watershed: str) -> list[dict]:
    """Returns indicator species presence/absence for a watershed.

    Args:
        watershed: e.g., "mckenzie"

    Returns:
        List of indicator species with detection status and trend
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT taxon_name, common_name, indicator_direction, status,
                   total_detections, last_detected
            FROM gold.indicator_species_status
            WHERE watershed = :ws
            ORDER BY indicator_direction, status, total_detections DESC
        """), {"ws": watershed}).fetchall()

    return [
        {
            "taxon_name": r[0],
            "common_name": r[1],
            "direction": r[2],
            "status": r[3],
            "total_detections": r[4],
            "last_detected": str(r[5]) if r[5] else None,
        }
        for r in rows
    ]


def get_post_fire_recovery(watershed: str, fire_name: str = None) -> list[dict]:
    """Returns species recovery trajectory for fires in a watershed.

    Args:
        watershed: e.g., "mckenzie"
        fire_name: optional specific fire (e.g., "HOLIDAY FARM")

    Returns:
        List of year-by-year species counts relative to fire event
    """
    with engine.connect() as conn:
        params = {"ws": watershed}
        where = "WHERE watershed = :ws"
        if fire_name:
            where += " AND fire_name = :fn"
            params["fn"] = fire_name

        rows = conn.execute(text(f"""
            SELECT fire_name, fire_year, acres, observation_year, years_since_fire,
                   species_total_watershed, total_obs_that_year
            FROM gold.post_fire_recovery
            {where}
            ORDER BY fire_name, observation_year
        """), params).fetchall()

    return [
        {
            "fire_name": r[0],
            "fire_year": r[1],
            "acres": r[2],
            "observation_year": r[3],
            "years_since_fire": r[4],
            "species_count": r[5],
            "observation_count": r[6],
        }
        for r in rows
    ]


def get_species_near_me(lat: float, lon: float, radius_km: float = 2.0) -> list[dict]:
    """Returns species with photos observed near a GPS point.

    Args:
        lat: latitude (e.g., 44.125)
        lon: longitude (e.g., -122.471)
        radius_km: search radius in km (default 2.0)

    Returns:
        List of species with common_name, photo_url, observation_count
    """
    radius_deg = radius_km / 111.0

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT o.taxon_name, o.data_payload->>'common_name' as common_name,
                o.iconic_taxon as taxonomic_group, count(*) as observation_count,
                max(o.observed_at)::date as last_seen,
                (SELECT g.photo_url FROM gold.species_gallery g WHERE g.taxon_name = o.taxon_name LIMIT 1) as photo_url,
                (SELECT g.photo_license FROM gold.species_gallery g WHERE g.taxon_name = o.taxon_name LIMIT 1) as photo_license,
                (SELECT g.observer FROM gold.species_gallery g WHERE g.taxon_name = o.taxon_name LIMIT 1) as attribution
            FROM observations o
            WHERE o.taxon_name IS NOT NULL AND o.location IS NOT NULL
              AND ST_DWithin(o.location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :radius)
            GROUP BY o.taxon_name, o.data_payload->>'common_name', o.iconic_taxon
            ORDER BY count(*) DESC LIMIT 50
        """), {"lat": lat, "lon": lon, "radius": radius_deg}).fetchall()

    return [
        {"taxon_name": r[0], "common_name": r[1] or r[0], "taxonomic_group": r[2],
         "observation_count": r[3], "last_seen": str(r[4]) if r[4] else None,
         "photo_url": r[5], "photo_license": r[6], "attribution": r[7]}
        for r in rows
    ]


def get_river_story(river_name: str, watershed: str) -> dict:
    """Returns narrative timeline for a river: fires, restoration, species, regulatory events.

    Args:
        river_name: e.g., "McKenzie River"
        watershed: e.g., "mckenzie"

    Returns:
        Dict with timeline, health score, fire recovery, swim safety
    """
    def _safe_query(conn, sql, params):
        try:
            return conn.execute(text(sql), params).fetchall()
        except Exception:
            conn.rollback()
            return []

    def _safe_query_one(conn, sql, params):
        try:
            return conn.execute(text(sql), params).fetchone()
        except Exception:
            conn.rollback()
            return None

    with engine.connect() as conn:
        events = _safe_query(conn, """
            SELECT event_year, event_type, event_name, description, magnitude
            FROM gold.river_story_timeline WHERE watershed = :ws
            ORDER BY event_year DESC LIMIT 30
        """, {"ws": watershed})

        health = _safe_query_one(conn, """
            SELECT health_score, avg_water_temp, avg_do, monthly_species
            FROM gold.river_health_score WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """, {"ws": watershed})

        recovery = _safe_query(conn, """
            SELECT fire_name, fire_year, acres, observation_year, years_since_fire, species_total_watershed
            FROM gold.post_fire_recovery WHERE watershed = :ws AND acres > 1000
            ORDER BY fire_year DESC, observation_year
        """, {"ws": watershed})

        swim = _safe_query(conn, """
            SELECT station_id, avg_temp_c, avg_flow_cfs, temp_comfort, safety_rating
            FROM gold.swim_safety WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 5
        """, {"ws": watershed})

    return {
        "timeline": [{"year": r[0], "type": r[1], "name": r[2], "description": r[3]} for r in events],
        "health": {"score": health[0], "water_temp_c": float(health[1]) if health[1] else None,
                   "do_mg_l": float(health[2]) if health[2] else None, "species": health[3]} if health else None,
        "fire_recovery": [{"fire": r[0], "year": r[1], "acres": r[2], "obs_year": r[3], "years_since": r[4], "species": r[5]} for r in recovery],
        "swim_safety": [{"station": r[0], "temp_c": float(r[1]) if r[1] else None, "flow_cfs": float(r[2]) if r[2] else None, "comfort": r[3], "safety": r[4]} for r in swim],
    }


# ──────────────────────────────────────────────────────────────
# Geology / Deep Time tools (FEAT-008, FEAT-009, FEAT-010)
# ──────────────────────────────────────────────────────────────

def get_geologic_context(lat: float, lon: float) -> dict:
    """Returns geologic unit, rock type, age, formation, and description for a point.

    Args:
        lat: latitude
        lon: longitude

    Returns:
        Dict with unit_name, formation, rock_type, lithology, age range, period, description.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT unit_name, formation, rock_type, lithology,
                   age_min_ma, age_max_ma, period, description
            FROM geologic_units
            WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            ORDER BY age_max_ma ASC NULLS LAST
        """), {"lat": lat, "lon": lon}).fetchall()

    if not rows:
        return {"message": f"No geologic data at ({lat}, {lon}). This area may not have detailed mapping."}

    units = []
    for r in rows:
        units.append({
            "unit_name": r[0], "formation": r[1], "rock_type": r[2], "lithology": r[3],
            "age_min_ma": r[4], "age_max_ma": r[5], "period": r[6], "description": r[7],
        })
    return {"location": {"lat": lat, "lon": lon}, "geologic_units": units}


def get_fossils_near_me(lat: float, lon: float, radius_km: float = 25) -> dict:
    """Returns fossil occurrences within radius with taxa, ages, and legal status.

    Args:
        lat: latitude
        lon: longitude
        radius_km: search radius in km (default 25)

    Returns:
        Dict with fossils list including taxon, age, period, distance.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT taxon_name, phylum, class_name, order_name, family,
                   age_min_ma, age_max_ma, period,
                   latitude, longitude,
                   ST_Distance(location::geography,
                       ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000 as dist_km
            FROM fossil_occurrences
            WHERE ST_DWithin(location::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m)
            ORDER BY dist_km
            LIMIT 50
        """), {"lat": lat, "lon": lon, "radius_m": radius_km * 1000}).fetchall()

    fossils = [{
        "taxon_name": r[0], "phylum": r[1], "class_name": r[2],
        "order_name": r[3], "family": r[4],
        "age_min_ma": r[5], "age_max_ma": r[6], "period": r[7],
        "latitude": r[8], "longitude": r[9],
        "distance_km": round(r[10], 1) if r[10] else None,
    } for r in rows]

    if not fossils:
        return {
            "message": f"No documented fossil occurrences within {radius_km}km of ({lat}, {lon}).",
            "suggestion": "Try expanding the search radius or visiting nearby known fossil sites."
        }

    return {"location": {"lat": lat, "lon": lon}, "radius_km": radius_km, "fossils": fossils, "count": len(fossils)}


def get_deep_time_story(lat: float, lon: float) -> dict:
    """Returns a deep time narrative describing what this location looked like in past geologic periods.

    Assembles context from geologic units and fossils, then generates a narrative.

    Args:
        lat: latitude
        lon: longitude

    Returns:
        Dict with narrative text, evidence cited, and geologic context.
    """
    geology = get_geologic_context(lat, lon)
    fossils = get_fossils_near_me(lat, lon, radius_km=50)

    context_parts = []
    if geology.get("geologic_units"):
        for u in geology["geologic_units"]:
            age_str = ""
            if u.get("age_max_ma"):
                age_str = f" ({u['age_max_ma']}-{u.get('age_min_ma', '?')} Ma)"
            context_parts.append(
                f"Geologic unit: {u.get('formation') or u.get('unit_name', 'Unknown')}{age_str}, "
                f"{u.get('rock_type', '')}, {u.get('lithology', '')}. "
                f"{u.get('description', '')}"
            )

    if fossils.get("fossils"):
        fossil_list = []
        for f in fossils["fossils"][:20]:
            fossil_list.append(f"{f['taxon_name']} ({f.get('phylum', '?')}, {f.get('period', '?')})")
        context_parts.append(f"Nearby fossils: {'; '.join(fossil_list)}")

    return {
        "location": {"lat": lat, "lon": lon},
        "geologic_context": geology.get("geologic_units", []),
        "nearby_fossils": fossils.get("fossils", []),
        "context_summary": "\n".join(context_parts) if context_parts else "No geologic data available for this location.",
    }


def is_collecting_legal(lat: float, lon: float) -> dict:
    """Returns definitive land ownership and collecting rules for a point.

    Args:
        lat: latitude
        lon: longitude

    Returns:
        Dict with agency, collecting_status (permitted/restricted/prohibited),
        collecting_rules text, and disclaimer.
    """
    from pipeline.ingest.geology import lookup_land_ownership_at_point

    result = lookup_land_ownership_at_point(lat, lon)
    if result is None:
        return {
            "agency": "unknown",
            "collecting_status": "unknown",
            "collecting_rules": "Unable to determine land ownership at this time.",
            "disclaimer": "Always verify on-site with posted signs and local regulations.",
        }

    result["disclaimer"] = "Always verify on-site with posted signs and local regulations."
    return result


def get_geology_ecology_link(watershed: str) -> dict:
    """Explains how geology drives water chemistry, springs, and fish habitat.

    Args:
        watershed: watershed key (e.g., "mckenzie", "deschutes")

    Returns:
        Dict with geologic units and their ecological implications.
    """
    from pipeline.config.watersheds import WATERSHEDS
    ws = WATERSHEDS.get(watershed)
    if not ws:
        return {"error": f"Unknown watershed: {watershed}"}

    bbox = ws["bbox"]

    with engine.connect() as conn:
        # Geologic units in the watershed
        geo_rows = conn.execute(text("""
            SELECT DISTINCT unit_name, formation, rock_type, lithology, period,
                   age_min_ma, age_max_ma, description
            FROM geologic_units
            WHERE geometry && ST_MakeEnvelope(:west, :south, :east, :north, 4326)
            ORDER BY age_max_ma DESC NULLS LAST
        """), bbox).fetchall()

        # Fossil count
        fossil_count = conn.execute(text("""
            SELECT count(*)
            FROM fossil_occurrences
            WHERE ST_Within(location, ST_MakeEnvelope(:west, :south, :east, :north, 4326))
        """), bbox).scalar() or 0

    units = [{
        "unit_name": r[0], "formation": r[1], "rock_type": r[2], "lithology": r[3],
        "period": r[4], "age_min_ma": r[5], "age_max_ma": r[6], "description": r[7],
    } for r in geo_rows]

    return {
        "watershed": watershed,
        "geologic_units": units,
        "unit_count": len(units),
        "fossil_occurrences_in_area": fossil_count,
    }
