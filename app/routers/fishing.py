"""Fishing intelligence endpoints (FEAT-007 + RiverPath)."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from pipeline.db import engine
from pipeline.tools import get_fishing_brief, get_species_with_photos

router = APIRouter(tags=["fishing"])


@router.get("/sites/{watershed}/fishing/brief")
def fishing_brief(watershed: str, month: int = None):
    """Get fishing conditions summary for a watershed."""
    return get_fishing_brief(watershed, month)


@router.get("/sites/{watershed}/fishing/species")
def fishing_species(watershed: str):
    """Get fish species distribution by stream reach."""
    with engine.connect() as conn:
        site = conn.execute(text(
            "SELECT id FROM sites WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{watershed}' not found")

        rows = conn.execute(text("""
            SELECT stream_name, scientific_name, common_name, use_type, origin,
                   inat_observation_count, last_inat_observation
            FROM gold.species_by_reach WHERE watershed = :ws
            ORDER BY stream_name, scientific_name
        """), {"ws": watershed}).fetchall()

    return [
        {
            "stream": r[0],
            "scientific_name": r[1],
            "common_name": r[2],
            "use_type": r[3],
            "origin": r[4],
            "observation_count": r[5],
            "last_observed": str(r[6]) if r[6] else None,
        }
        for r in rows
    ]


@router.get("/sites/{watershed}/fishing/harvest")
def fishing_harvest(watershed: str):
    """Get sport catch harvest trends year-over-year."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT station_id, species, harvest_year, annual_harvest,
                   prev_year_harvest, harvest_delta, harvest_pct_change
            FROM gold.harvest_trends WHERE watershed = :ws
            ORDER BY harvest_year DESC, annual_harvest DESC
        """), {"ws": watershed}).fetchall()

    return [
        {
            "station": r[0],
            "species": r[1],
            "year": r[2],
            "harvest": r[3],
            "prev_year": r[4],
            "delta": r[5],
            "pct_change": float(r[6]) if r[6] else None,
        }
        for r in rows
    ]


@router.get("/sites/{watershed}/fishing/stocking")
def fishing_stocking(watershed: str):
    """Get trout stocking schedule."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT waterbody, stocking_date, total_fish
            FROM gold.stocking_schedule WHERE watershed = :ws
            ORDER BY stocking_date DESC LIMIT 20
        """), {"ws": watershed}).fetchall()

    return [
        {"waterbody": r[0], "date": str(r[1]), "fish": r[2]}
        for r in rows
    ]


@router.get("/sites/{watershed}/fishing/conditions")
def fishing_conditions(watershed: str):
    """Get monthly water conditions relevant to fishing."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT obs_year, obs_month, avg_water_temp_c, max_water_temp_c,
                   avg_discharge_cfs, avg_do_mg_l, steelhead_harvest, trout_stocked
            FROM gold.fishing_conditions WHERE watershed = :ws
              AND (avg_water_temp_c IS NOT NULL OR avg_discharge_cfs IS NOT NULL)
            ORDER BY obs_year DESC, obs_month DESC LIMIT 12
        """), {"ws": watershed}).fetchall()

    return [
        {
            "year": r[0], "month": r[1],
            "water_temp_c": float(r[2]) if r[2] else None,
            "max_temp_c": float(r[3]) if r[3] else None,
            "discharge_cfs": float(r[4]) if r[4] else None,
            "do_mg_l": float(r[5]) if r[5] else None,
            "steelhead_harvest": r[6],
            "trout_stocked": r[7],
        }
        for r in rows
    ]


@router.get("/sites/{watershed}/fishing/hatch")
def hatch_chart(watershed: str):
    """Get insect hatch chart for a watershed."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT taxon_name, common_name, obs_month, observation_count,
                   activity_level, photo_url
            FROM gold.hatch_chart WHERE watershed = :ws
            ORDER BY obs_month, observation_count DESC
        """), {"ws": watershed}).fetchall()

    return [
        {
            "taxon_name": r[0],
            "common_name": r[1],
            "month": r[2],
            "observations": r[3],
            "activity": r[4],
            "photo_url": r[5],
        }
        for r in rows
    ]


@router.get("/sites/{watershed}/fishing/barriers")
def fish_passage_barriers(watershed: str):
    """Get fish passage barriers in a watershed (FEAT-007 FR-5)."""
    with engine.connect() as conn:
        site = conn.execute(text("SELECT id FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(status_code=404, detail=f"Watershed '{watershed}' not found")

        rows = conn.execute(text("""
            SELECT taxon_name, latitude, longitude,
                   data_payload->>'barrier_type' as barrier_type,
                   data_payload->>'passage_status' as passage_status,
                   data_payload->>'stream_name' as stream_name,
                   data_payload->>'barrier_name' as barrier_name
            FROM observations
            WHERE site_id = :sid AND source_type = 'fish_barrier'
            ORDER BY taxon_name
        """), {"sid": site[0]}).fetchall()

    return [
        {
            "stream_name": r[5] or r[0],
            "barrier_name": r[6],
            "barrier_type": r[3],
            "passage_status": r[4],
            "latitude": r[1],
            "longitude": r[2],
        }
        for r in rows
    ]


@router.get("/sites/{watershed}/fishing/alerts")
def fishing_alerts(watershed: str):
    """Get current fishing-relevant alerts for a watershed (FEAT-007 FR-7).

    Checks for: temperature exceedances, low flow, recent stocking, anomalies.
    """
    with engine.connect() as conn:
        site = conn.execute(text("SELECT id FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(status_code=404, detail=f"Watershed '{watershed}' not found")

        alerts = []

        # Temperature anomalies
        temp_anomalies = conn.execute(text("""
            SELECT count(*) FROM gold.anomaly_flags
            WHERE watershed = :ws AND anomaly_type ILIKE '%temp%'
        """), {"ws": watershed}).scalar() or 0
        if temp_anomalies > 0:
            alerts.append({
                "type": "temperature",
                "severity": "warning",
                "message": f"{temp_anomalies} temperature anomalies detected",
            })

        # DO anomalies
        do_anomalies = conn.execute(text("""
            SELECT count(*) FROM gold.anomaly_flags
            WHERE watershed = :ws AND anomaly_type ILIKE '%oxygen%' OR anomaly_type ILIKE '%do%'
        """), {"ws": watershed}).scalar() or 0
        if do_anomalies > 0:
            alerts.append({
                "type": "dissolved_oxygen",
                "severity": "warning",
                "message": f"{do_anomalies} dissolved oxygen anomalies detected",
            })

        # Stocking — split past vs upcoming
        stocking = conn.execute(text("""
            SELECT
                count(*) FILTER (WHERE stocking_date <= CURRENT_DATE) as past,
                count(*) FILTER (WHERE stocking_date > CURRENT_DATE) as upcoming,
                min(stocking_date) FILTER (WHERE stocking_date > CURRENT_DATE)::date as next_date
            FROM gold.stocking_schedule WHERE watershed = :ws
        """), {"ws": watershed}).fetchone()
        if stocking and stocking[1] and stocking[1] > 0:
            alerts.append({
                "type": "stocking",
                "severity": "info",
                "message": f"{stocking[1]} upcoming stocking events, next: {stocking[2]}",
            })
        elif stocking and stocking[0] and stocking[0] > 0:
            alerts.append({
                "type": "stocking",
                "severity": "info",
                "message": f"{stocking[0]} past stocking events on record",
            })

    return {"watershed": watershed, "alerts": alerts}


@router.get("/sites/{watershed}/fishing/fly-recommendations")
def fly_recommendations(watershed: str, month: int = None):
    """Get fly pattern recommendations based on current insect activity."""
    from datetime import datetime
    if month is None:
        month = datetime.now().month

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT pattern_insect_name, insect_taxon, insect_common_name,
                   fly_pattern_name, fly_size, fly_type, fly_image_url,
                   life_stage, time_of_day, water_type, fly_notes,
                   observation_count, insect_photo_url
            FROM gold.hatch_fly_recommendations
            WHERE watershed = :ws AND obs_month = :month
            ORDER BY observation_count DESC
        """), {"ws": watershed, "month": month}).fetchall()

    return [
        {
            "insect": r[0] or r[2] or r[1],
            "insect_taxon": r[1],
            "fly_pattern": r[3],
            "fly_size": r[4],
            "fly_type": r[5],
            "fly_image_url": r[6],
            "life_stage": r[7],
            "time_of_day": r[8],
            "water_type": r[9],
            "notes": r[10],
            "observations": r[11],
            "insect_photo_url": r[12],
        }
        for r in rows
    ]


@router.get("/sites/{watershed}/fishing/hatch-confidence")
def hatch_confidence(watershed: str, month: int = None):
    """Get hatch confidence scoring — top aquatic insects ranked by likelihood.

    Uses curated hatch chart data (expert-sourced emergence timing) enriched
    with observation counts from gold.aquatic_hatch_chart. Falls back to
    observation-only data if no curated entries exist.
    """
    from datetime import datetime
    if month is None:
        month = datetime.now().month

    with engine.connect() as conn:
        # Get current water temp
        temp_row = conn.execute(text("""
            SELECT avg_water_temp_c FROM gold.fishing_conditions
            WHERE watershed = :ws AND avg_water_temp_c IS NOT NULL
            ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """), {"ws": watershed}).fetchone()
        current_temp = float(temp_row[0]) if temp_row and temp_row[0] else None

        insects = []

        # 1. Curated hatch chart entries active this month and next
        try:
            curated = conn.execute(text("""
                SELECT c.common_name, c.scientific_name, c.insect_order,
                       c.start_month, c.end_month, c.peak_months, c.fly_patterns,
                       (SELECT g.photo_url FROM gold.species_gallery g
                        WHERE g.taxon_name ILIKE '%' || split_part(c.scientific_name, ' ', 1) || '%'
                          AND g.watershed = c.watershed LIMIT 1) as photo_url
                FROM curated_hatch_chart c
                WHERE c.watershed = :ws
                  AND (c.start_month <= :m1 AND c.end_month >= :m1
                       OR c.start_month <= :m2 AND c.end_month >= :m2)
                ORDER BY
                    CASE WHEN :m1 = ANY(c.peak_months) THEN 0
                         WHEN :m2 = ANY(c.peak_months) THEN 1
                         ELSE 2 END,
                    c.common_name
            """), {"ws": watershed, "m1": month, "m2": (month % 12) + 1}).fetchall()
        except Exception:
            conn.rollback()
            curated = []

        for r in curated:
            is_peak = month in (r[5] or [])
            active_month = month if (r[3] <= month <= r[4]) else (month % 12) + 1
            confidence = 'high' if is_peak else 'medium'
            insects.append({
                "taxon_name": r[1],
                "common_name": r[0],
                "month": active_month,
                "observations": None,
                "activity": "peak" if is_peak else "present",
                "confidence": confidence,
                "photo_url": r[7],
                "years_observed": None,
                "insect_order": r[2],
                "fly_patterns": r[6] or [],
                "source": "curated",
            })

        # 2. Supplement with observation-based data from aquatic hatch chart
        try:
            obs_rows = conn.execute(text("""
                SELECT taxon_name, common_name, obs_month, observation_count,
                       activity_level, photo_url, years_observed
                FROM gold.aquatic_hatch_chart
                WHERE watershed = :ws AND obs_month IN (:m1, :m2)
                ORDER BY obs_month, observation_count DESC
            """), {"ws": watershed, "m1": month, "m2": (month % 12) + 1}).fetchall()
        except Exception:
            conn.rollback()
            obs_rows = []

        # Add observation entries not already covered by curated data
        curated_names = {i["taxon_name"].lower() for i in insects}
        for r in obs_rows:
            if r[0].lower() in curated_names:
                continue
            obs = r[3] or 0
            activity = r[4] or 'present'
            years = r[6] or 1
            if activity == 'peak' and obs >= 10:
                confidence = 'high'
            elif obs >= 3 or years >= 2:
                confidence = 'medium'
            else:
                confidence = 'low'
            insects.append({
                "taxon_name": r[0],
                "common_name": r[1],
                "month": r[2],
                "observations": obs,
                "activity": activity,
                "confidence": confidence,
                "photo_url": r[5],
                "years_observed": years,
                "insect_order": None,
                "fly_patterns": [],
                "source": "observed",
            })

    return {
        "watershed": watershed,
        "current_month": month,
        "water_temp_c": current_temp,
        "insects": insects[:15],
    }


@router.get("/sites/{watershed}/stewardship")
def stewardship(watershed: str):
    """Get stewardship opportunities and restoration outcomes."""
    with engine.connect() as conn:
        # Stewardship opportunities
        opps = conn.execute(text("""
            SELECT intervention_category, raw_type, project_count,
                   most_recent_year, project_summaries
            FROM gold.stewardship_opportunities WHERE watershed = :ws
            ORDER BY project_count DESC
        """), {"ws": watershed}).fetchall()

        # Restoration outcomes (before/after)
        outcomes = conn.execute(text("""
            SELECT intervention_category, intervention_year,
                   intervention_count, species_before, species_after
            FROM gold.restoration_outcomes WHERE watershed = :ws
            ORDER BY intervention_year DESC
        """), {"ws": watershed}).fetchall()

    return {
        "watershed": watershed,
        "opportunities": [
            {
                "category": r[0],
                "type": r[1],
                "project_count": r[2],
                "most_recent_year": r[3],
                "examples": r[4],
            }
            for r in opps
        ],
        "outcomes": [
            {
                "name": f"{r[0]} ({r[1]})",
                "category": r[0],
                "year": r[1],
                "projects": r[2],
                "species_before": r[3],
                "species_after": r[4],
            }
            for r in outcomes
        ],
    }


@router.get("/river/{river_name}/species")
def river_species_by_mile(river_name: str, mile_start: float = 0, mile_end: float = 999, taxonomic_group: str = None):
    """Get species with photos for a river section by mile range."""
    results = get_species_with_photos(river_name, mile_start, mile_end)
    if taxonomic_group:
        results = [r for r in results if r.get("taxonomic_group") == taxonomic_group]
    return results


@router.get("/sites/{watershed}/swim-safety")
def swim_safety(watershed: str):
    """Get swimming/wading safety ratings per station."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT station_id, obs_year, obs_month, avg_temp_c, avg_flow_cfs,
                   temp_comfort, safety_rating
            FROM gold.swim_safety WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 20
        """), {"ws": watershed}).fetchall()

    return [
        {
            "station": r[0], "year": r[1], "month": r[2],
            "temp_c": float(r[3]) if r[3] else None,
            "flow_cfs": float(r[4]) if r[4] else None,
            "comfort": r[5], "safety": r[6],
        }
        for r in rows
    ]
