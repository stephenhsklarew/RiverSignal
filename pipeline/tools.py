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
            SELECT taxon_name, common_name, indicator_direction, status, trend,
                   total_detections, recent_detections, last_detected
            FROM gold.indicator_species_status
            WHERE watershed = :ws
            ORDER BY indicator_direction, status, total_detections DESC
        """), {"ws": watershed}).fetchall()

    return [
        {
            "taxon_name": r[0],
            "common_name": r[1],
            "direction": r[2],  # positive = good sign, negative = bad sign
            "status": r[3],
            "trend": r[4],
            "total_detections": r[5],
            "recent_detections": r[6],
            "last_detected": str(r[7]) if r[7] else None,
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
    with engine.connect() as conn:
        events = conn.execute(text("""
            SELECT event_year, event_type, event_name, description, magnitude
            FROM gold.river_story_timeline WHERE watershed = :ws
            ORDER BY event_year DESC LIMIT 30
        """), {"ws": watershed}).fetchall()

        health = conn.execute(text("""
            SELECT health_score, avg_water_temp, avg_do, monthly_species
            FROM gold.river_health_score WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """), {"ws": watershed}).fetchone()

        recovery = conn.execute(text("""
            SELECT fire_name, fire_year, acres, observation_year, years_since_fire, species_total_watershed
            FROM gold.post_fire_recovery WHERE watershed = :ws AND acres > 1000
            ORDER BY fire_year DESC, observation_year
        """), {"ws": watershed}).fetchall()

        swim = conn.execute(text("""
            SELECT station_id, avg_temp_c, avg_flow_cfs, temp_comfort, safety_rating
            FROM gold.swim_safety WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 5
        """), {"ws": watershed}).fetchall()

    return {
        "timeline": [{"year": r[0], "type": r[1], "name": r[2], "description": r[3]} for r in events],
        "health": {"score": health[0], "water_temp_c": float(health[1]) if health[1] else None,
                   "do_mg_l": float(health[2]) if health[2] else None, "species": health[3]} if health else None,
        "fire_recovery": [{"fire": r[0], "year": r[1], "acres": r[2], "obs_year": r[3], "years_since": r[4], "species": r[5]} for r in recovery],
        "swim_safety": [{"station": r[0], "temp_c": float(r[1]) if r[1] else None, "flow_cfs": float(r[2]) if r[2] else None, "comfort": r[3], "safety": r[4]} for r in swim],
    }
