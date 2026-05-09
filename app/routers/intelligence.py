"""Predictive intelligence API endpoints.

Serves predictions from the 5 ML models:
1. Hatch emergence forecast
2. Catch probability
3. River health anomaly detection
4. Species distribution shifts
5. Restoration impact predictions
"""

from fastapi import APIRouter, Query
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["intelligence"])


@router.get("/sites/{watershed}/hatch-forecast")
def hatch_forecast(watershed: str):
    """Get hatch emergence predictions with degree-day analysis."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT common_name, scientific_name, insect_order,
                   probability, confidence, days_to_peak, method,
                   factors, fly_patterns, current_cdd, activity_level, computed_at
            FROM gold_hatch_emergence_forecast
            WHERE watershed = :ws
            ORDER BY probability DESC
        """), {"ws": watershed}).fetchall()

    return {
        "watershed": watershed,
        "forecasts": [{
            "common_name": r[0], "scientific_name": r[1], "insect_order": r[2],
            "probability": r[3], "confidence": r[4], "days_to_peak": r[5],
            "method": r[6], "factors": r[7], "fly_patterns": r[8],
            "current_cdd": r[9], "activity_level": r[10],
            "computed_at": str(r[11]) if r[11] else None,
        } for r in rows],
        "count": len(rows),
    }


@router.get("/sites/{watershed}/catch-forecast")
def catch_forecast(watershed: str):
    """Get catch probability predictions per species."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT species, score, level, factors,
                   water_temp, flow_cfs, hatch_activity, computed_at
            FROM gold_catch_forecast
            WHERE watershed = :ws
            ORDER BY score DESC
        """), {"ws": watershed}).fetchall()

    species = [{
        "species": r[0], "score": r[1], "level": r[2], "factors": r[3],
        "computed_at": str(r[7]) if r[7] else None,
    } for r in rows]

    top3 = species[:3]
    overall = round(sum(s["score"] for s in top3) / len(top3)) if top3 else 50

    return {
        "watershed": watershed,
        "overall_score": overall,
        "overall_level": "excellent" if overall >= 80 else "good" if overall >= 60 else "fair" if overall >= 40 else "poor",
        "water_temp_c": rows[0][4] if rows else None,
        "flow_cfs": rows[0][5] if rows else None,
        "hatch_activity": rows[0][6] if rows else 0,
        "species": species,
        "count": len(species),
    }


@router.get("/sites/{watershed}/health-anomaly")
def health_anomaly(watershed: str):
    """Get river health anomaly analysis with z-scores and trend detection."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT health_score, health_level, anomaly_count,
                   anomalies, species_trend, recent_conditions, computed_at
            FROM gold_health_anomaly
            WHERE watershed = :ws
        """), {"ws": watershed}).fetchone()

    if not row:
        return {"watershed": watershed, "health_score": None, "message": "No anomaly data available"}

    return {
        "watershed": watershed,
        "health_score": row[0],
        "health_level": row[1],
        "anomaly_count": row[2],
        "anomalies": row[3],
        "species_trend": row[4],
        "recent_conditions": row[5],
        "computed_at": str(row[6]) if row[6] else None,
    }


@router.get("/sites/{watershed}/species-shifts")
def species_shifts(watershed: str, min_confidence: str = Query("low")):
    """Get species distribution shift analysis."""
    confidence_order = {"low": 0, "medium": 1, "high": 2}
    min_conf = confidence_order.get(min_confidence, 0)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT taxon_name, common_name, taxonomic_group,
                   shift_type, direction, total_shift_km,
                   years_tracked, early_range_km, recent_range_km,
                   population_trend, confidence, observation_count, computed_at
            FROM gold_species_distribution_shifts
            WHERE watershed = :ws
            ORDER BY ABS(total_shift_km) DESC
        """), {"ws": watershed}).fetchall()

    shifts = [{
        "taxon_name": r[0], "common_name": r[1], "taxonomic_group": r[2],
        "shift_type": r[3], "direction": r[4], "total_shift_km": r[5],
        "years_tracked": r[6], "early_range_km": r[7], "recent_range_km": r[8],
        "population_trend": r[9], "confidence": r[10], "observation_count": r[11],
    } for r in rows if confidence_order.get(r[10], 0) >= min_conf]

    return {
        "watershed": watershed,
        "shifts": shifts,
        "count": len(shifts),
        "summary": {
            "northward": sum(1 for s in shifts if s["direction"] == "northward"),
            "southward": sum(1 for s in shifts if s["direction"] == "southward"),
            "contracting": sum(1 for s in shifts if s["shift_type"] == "range_contraction"),
            "expanding": sum(1 for s in shifts if s["shift_type"] == "range_expansion"),
            "new_arrivals": sum(1 for s in shifts if s["shift_type"] == "new_arrival"),
        },
    }


@router.get("/sites/{watershed}/restoration-forecast")
def restoration_forecast(watershed: str):
    """Get restoration impact predictions and recovery timeline."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT intervention_type, predicted_species_gain, recovery_ratio,
                   success_rate, confidence, sample_size,
                   fire_recovery, cost_effectiveness_rank, computed_at
            FROM gold_restoration_forecast
            WHERE watershed = :ws
            ORDER BY cost_effectiveness_rank
        """), {"ws": watershed}).fetchall()

    return {
        "watershed": watershed,
        "interventions": [{
            "type": r[0], "predicted_species_gain": r[1], "recovery_ratio": r[2],
            "success_rate": r[3], "confidence": r[4], "sample_size": r[5],
            "fire_recovery": r[6], "rank": r[7],
        } for r in rows],
        "count": len(rows),
    }
