"""Site endpoints: list sites, get site details, ecological summary."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["sites"])


@router.get("/sites/nearest")
def nearest_site(lat: float = Query(...), lon: float = Query(...)):
    """Find the nearest watershed and river reach to GPS coordinates."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT s.watershed, s.name, rm.river_name,
                   rm.river_mile_from_source,
                   ST_Distance(
                     rm.flowline::geography,
                     ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                   ) as distance_m
            FROM gold.river_miles rm
            JOIN sites s ON rm.watershed = s.watershed
            ORDER BY rm.flowline <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
            LIMIT 1
        """), {"lat": lat, "lon": lon}).fetchone()

    if not row or row[4] > 100000:  # > 100km away
        raise HTTPException(status_code=404, detail="No tracked river within range")

    return {
        "watershed": row[0],
        "watershed_name": row[1],
        "river_name": row[2],
        "river_mile": float(row[3]) if row[3] else None,
        "distance_m": round(row[4], 1),
    }


@router.get("/sites/{watershed}/recreation")
def recreation_sites(watershed: str, rec_type: str = None):
    """Get recreation sites for a watershed from the recreation_sites table."""
    with engine.connect() as conn:
        site = conn.execute(text(
            "SELECT id FROM sites WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(status_code=404, detail=f"Watershed '{watershed}' not found")

        params: dict = {"sid": site[0]}
        where = "WHERE rs.site_id = :sid"
        if rec_type:
            where += " AND rs.rec_type = :rt"
            params["rt"] = rec_type

        try:
            rows = conn.execute(text(f"""
                SELECT rs.id, rs.name, rs.rec_type, rs.latitude, rs.longitude,
                       rs.amenities, rs.source_type
                FROM recreation_sites rs
                {where}
                ORDER BY rs.name
            """), params).fetchall()
        except Exception:
            conn.rollback()
            return []

    return [
        {
            "id": r[0],
            "name": r[1],
            "rec_type": r[2],
            "latitude": r[3],
            "longitude": r[4],
            "amenities": r[5] or {},
            "source": r[6],
            "watershed": watershed,
        }
        for r in rows
    ]


@router.get("/sites/{watershed}/cold-water-refuges")
def cold_water_refuges(watershed: str):
    """Get cold-water refuge thermal classifications for map overlay."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT station_id, thermal_classification, multi_year_summer_avg,
                   yoy_temp_change
            FROM gold.cold_water_refuges WHERE watershed = :ws
            ORDER BY multi_year_summer_avg
        """), {"ws": watershed}).fetchall()

    return [
        {
            "station": r[0],
            "thermal_class": r[1],
            "avg_summer_temp_c": float(r[2]) if r[2] else None,
            "temp_trend_per_year": float(r[3]) if r[3] else None,
        }
        for r in rows
    ]


@router.get("/sites")
def list_sites():
    """List all configured watersheds/sites."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT s.id, s.name, s.watershed, s.bbox,
                   (SELECT count(*) FROM observations o WHERE o.site_id = s.id) as observations,
                   (SELECT count(*) FROM time_series t WHERE t.site_id = s.id) as time_series,
                   (SELECT count(*) FROM interventions i WHERE i.site_id = s.id) as interventions
            FROM sites s ORDER BY s.name
        """)).fetchall()

    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "watershed": r[2],
            "bbox": r[3],
            "observations": r[4],
            "time_series": r[5],
            "interventions": r[6],
        }
        for r in rows
    ]


@router.get("/sites/{watershed}")
def get_site(watershed: str):
    """Get site details with health score and current conditions."""
    with engine.connect() as conn:
        site = conn.execute(text(
            "SELECT id, name, watershed, bbox FROM sites WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()

        if not site:
            raise HTTPException(status_code=404, detail=f"Watershed '{watershed}' not found")

        # Health score (may not exist if view hasn't been created)
        try:
            health = conn.execute(text("""
                SELECT health_score, avg_water_temp, avg_do, monthly_species, obs_year, obs_month
                FROM gold.river_health_score WHERE watershed = :ws
                ORDER BY obs_year DESC, obs_month DESC LIMIT 1
            """), {"ws": watershed}).fetchone()
        except Exception:
            conn.rollback()
            health = None

        # Scorecard
        scorecard = conn.execute(text(
            "SELECT * FROM gold.watershed_scorecard WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()

        # Indicator species
        indicators = conn.execute(text("""
            SELECT taxon_name, common_name, indicator_direction, status, total_detections, last_detected
            FROM gold.indicator_species_status WHERE watershed = :ws
            ORDER BY indicator_direction, status
        """), {"ws": watershed}).fetchall()

    return {
        "id": str(site[0]),
        "name": site[1],
        "watershed": site[2],
        "bbox": site[3],
        "health": {
            "score": health[0] if health else None,
            "water_temp_c": float(health[1]) if health and health[1] else None,
            "dissolved_oxygen_mg_l": float(health[2]) if health and health[2] else None,
            "species_this_month": health[3] if health else None,
            "as_of": f"{health[4]}-{health[5]:02d}" if health else None,
        },
        "scorecard": {
            "total_observations": scorecard[2] if scorecard else 0,
            "total_time_series": scorecard[3] if scorecard else 0,
            "total_interventions": scorecard[4] if scorecard else 0,
            "total_species": scorecard[5] if scorecard else 0,
            "fish_species": scorecard[6] if scorecard else 0,
            "amphibian_species": scorecard[7] if scorecard else 0,
            "usgs_stations": scorecard[8] if scorecard else 0,
            "stream_reaches": scorecard[10] if scorecard else 0,
            "fire_events": scorecard[12] if scorecard else 0,
        } if scorecard else None,
        "indicators": [
            {
                "taxon_name": r[0],
                "common_name": r[1],
                "direction": r[2],
                "status": r[3],
                "detections": r[4],
                "last_detected": str(r[5]) if r[5] else None,
            }
            for r in indicators
        ],
    }


@router.get("/sites/{watershed}/observations/search")
def search_observations(
    watershed: str,
    q: str = Query(..., description="Search term (taxon name or common name)"),
    limit: int = Query(500, le=2000),
):
    """Search observations by species name, returning GeoJSON for map display.

    Searches taxon_name, common_name, and iconic_taxon. Handles plurals
    by also trying a truncated stem (e.g. "mayfly" → "mayfl").
    """
    with engine.connect() as conn:
        site = conn.execute(text(
            "SELECT id FROM sites WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(status_code=404, detail=f"Watershed '{watershed}' not found")

        # Truncate search term to handle plurals: "mayfly" → "mayfl", "eagles" → "eagle"
        term = q.strip()
        if len(term) > 4:
            search_term = term[:-2]  # drop last 2 chars to match plural/conjugation variants
        else:
            search_term = term
        pattern = f"%{search_term}%"

        rows = conn.execute(text("""
            SELECT o.taxon_name,
                   o.data_payload->>'common_name' as common_name,
                   o.latitude, o.longitude,
                   o.observed_at::date as obs_date,
                   o.data_payload->>'photo_url' as photo_url,
                   o.quality_grade,
                   o.source_type
            FROM observations o
            WHERE o.site_id = :site_id
              AND o.latitude IS NOT NULL
              AND (o.taxon_name ILIKE :q
                   OR o.data_payload->>'common_name' ILIKE :q
                   OR o.iconic_taxon ILIKE :q)
            ORDER BY o.observed_at DESC
            LIMIT :limit
        """), {"site_id": site[0], "q": pattern, "limit": limit}).fetchall()

    features = []
    for r in rows:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r[3], r[2]]},
            "properties": {
                "taxon_name": r[0],
                "common_name": r[1],
                "observed_at": str(r[4]) if r[4] else None,
                "photo_url": r[5],
                "quality_grade": r[6],
                "source": r[7],
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "query": q,
        "watershed": watershed,
        "count": len(features),
    }


@router.get("/sites/{watershed}/seasonal")
def get_seasonal_planner(watershed: str):
    """Seasonal trip planner: peak activity windows by species group and month."""
    with engine.connect() as conn:
        site = conn.execute(text(
            "SELECT id FROM sites WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(status_code=404, detail=f"Watershed '{watershed}' not found")

        # Seasonal observation patterns
        patterns = conn.execute(text("""
            SELECT taxon_group, peak_month, avg_observations
            FROM gold.seasonal_observation_patterns
            WHERE watershed = :ws
            ORDER BY peak_month, avg_observations DESC
        """), {"ws": watershed}).fetchall()

        # Hatch chart for insects
        hatches = conn.execute(text("""
            SELECT taxon_name, common_name, month, observation_count
            FROM gold.hatch_chart
            WHERE watershed = :ws
            ORDER BY month, observation_count DESC
        """), {"ws": watershed}).fetchall()

    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    return {
        "watershed": watershed,
        "seasonal_patterns": [
            {"taxon_group": r[0], "peak_month": r[1],
             "peak_month_name": month_names[r[1]] if r[1] and 1 <= r[1] <= 12 else '?',
             "avg_observations": r[2]}
            for r in patterns
        ],
        "hatch_chart": [
            {"taxon_name": r[0], "common_name": r[1], "month": r[2],
             "month_name": month_names[r[2]] if r[2] and 1 <= r[2] <= 12 else '?',
             "count": r[3]}
            for r in hatches[:30]
        ],
    }


@router.get("/sites/{watershed}/story")
def get_site_story(watershed: str, reading_level: str = Query("adult", pattern="^(kids|adult|science)$")):
    """Get the river story timeline for a watershed.

    reading_level controls narrative tone: kids (5th-grade), adult (default), science (technical).
    """
    from pipeline.tools import get_river_story
    data = get_river_story(river_name="", watershed=watershed)
    data["reading_level"] = reading_level
    return data


@router.get("/sites/{watershed}/species")
def get_site_species(watershed: str, taxonomic_group: str = None, limit: int = 5000):
    """Get species observed at a watershed with photos."""
    with engine.connect() as conn:
        params = {"ws": watershed, "limit": limit}
        where = "WHERE g.watershed = :ws"
        if taxonomic_group:
            where += " AND g.taxonomic_group = :tg"
            params["tg"] = taxonomic_group

        rows = conn.execute(text(f"""
            SELECT g.taxon_name, g.common_name, g.taxonomic_group,
                   g.photo_url, g.photo_license, g.observer, g.conservation_status
            FROM gold.species_gallery g
            {where}
            ORDER BY g.taxonomic_group, g.common_name
            LIMIT :limit
        """), params).fetchall()

    from app.image_cache import get_cached_url
    return [
        {
            "taxon_name": r[0],
            "common_name": r[1],
            "taxonomic_group": r[2],
            "photo_url": get_cached_url(r[3], 'species'),
            "photo_license": r[4],
            "observer": r[5],
            "conservation_status": r[6],
        }
        for r in rows
    ]
