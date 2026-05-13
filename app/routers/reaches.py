"""Reach + Trip Quality Score endpoints.

Per plan §6 pull surface:
- GET /api/v1/reaches?watershed=…       — list active reaches
- GET /api/v1/trip-quality?date=&reach_id=  — single-reach TQS
- GET /api/v1/trip-quality?date=&watershed=  — watershed rollup + reaches
- GET /api/v1/trip-quality/ranking?…    — geo-filtered ranked watersheds
"""

from datetime import date as date_t
from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["reaches"])


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles."""
    r_earth_mi = 3958.7613
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * r_earth_mi * asin(sqrt(a))


@router.get("/reaches")
def list_reaches(watershed: str | None = Query(None)):
    sql = """
        SELECT id, watershed, name, short_label, description,
               river_mile_start, river_mile_end,
               centroid_lat, centroid_lon,
               primary_usgs_site_id, general_flow_bearing,
               typical_species, is_warm_water
        FROM silver.river_reaches
        WHERE is_active = true
    """
    params: dict[str, object] = {}
    if watershed:
        sql += " AND watershed = :ws"
        params["ws"] = watershed
    sql += " ORDER BY watershed, COALESCE(river_mile_start, 0), name"

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    return {
        "reaches": [
            {
                "id": r[0],
                "watershed": r[1],
                "name": r[2],
                "short_label": r[3],
                "description": r[4],
                "river_mile_start": r[5],
                "river_mile_end": r[6],
                "centroid_lat": r[7],
                "centroid_lon": r[8],
                "primary_usgs_site_id": r[9],
                "general_flow_bearing": r[10],
                "typical_species": list(r[11] or []),
                "is_warm_water": bool(r[12]),
            }
            for r in rows
        ]
    }


def _tqs_row_to_dict(r) -> dict:
    return {
        "reach_id": r[0],
        "watershed": r[1],
        "target_date": r[2].isoformat() if r[2] else None,
        "tqs": int(r[3]),
        "confidence": int(r[4]),
        "is_hard_closed": bool(r[5]),
        "catch_score": int(r[6]),
        "water_temp_score": int(r[7]),
        "flow_score": int(r[8]),
        "weather_score": int(r[9]),
        "hatch_score": int(r[10]),
        "access_score": int(r[11]),
        "primary_factor": r[12],
        "partial_access_flag": bool(r[13]),
        "horizon_days": int(r[14]),
        "forecast_source": r[15],
    }


_TQS_COLS = """
    reach_id, watershed, target_date, tqs, confidence, is_hard_closed,
    catch_score, water_temp_score, flow_score, weather_score, hatch_score,
    access_score, primary_factor, partial_access_flag, horizon_days,
    forecast_source
"""


@router.get("/trip-quality")
def get_trip_quality(
    date: date_t = Query(...),
    reach_id: str | None = Query(None),
    watershed: str | None = Query(None),
):
    """Per plan §6. Either reach_id or watershed must be supplied."""
    if not reach_id and not watershed:
        raise HTTPException(400, "Provide either reach_id or watershed")

    with engine.connect() as conn:
        if reach_id:
            row = conn.execute(
                text(f"SELECT {_TQS_COLS} FROM gold.trip_quality_daily "
                     f"WHERE reach_id = :rid AND target_date = :d"),
                {"rid": reach_id, "d": date},
            ).fetchone()
            if not row:
                raise HTTPException(404, "No TQS row for that reach + date")
            return _tqs_row_to_dict(row)

        # watershed rollup + nested reaches
        rollup = conn.execute(
            text("""
                SELECT watershed, target_date, watershed_tqs, best_reach_id,
                       confidence, primary_factor, best_reach_is_hard_closed,
                       unfavorable_count, total_reaches, reach_spread,
                       horizon_days, forecast_source
                FROM gold.trip_quality_watershed_daily
                WHERE watershed = :ws AND target_date = :d
            """),
            {"ws": watershed, "d": date},
        ).fetchone()
        if not rollup:
            raise HTTPException(404, "No TQS rollup for that watershed + date")
        reaches = conn.execute(
            text(f"SELECT {_TQS_COLS} FROM gold.trip_quality_daily "
                 f"WHERE watershed = :ws AND target_date = :d "
                 f"ORDER BY tqs DESC, reach_id"),
            {"ws": watershed, "d": date},
        ).fetchall()
        return {
            "watershed": rollup[0],
            "target_date": rollup[1].isoformat(),
            "watershed_tqs": int(rollup[2]),
            "best_reach_id": rollup[3],
            "confidence": int(rollup[4]),
            "primary_factor": rollup[5],
            "is_hard_closed": bool(rollup[6]),
            "unfavorable_count": int(rollup[7]),
            "total_reaches": int(rollup[8]),
            "reach_spread": float(rollup[9]),
            "horizon_days": int(rollup[10]),
            "forecast_source": rollup[11],
            "reaches": [_tqs_row_to_dict(r) for r in reaches],
        }


@router.get("/guide-availability/{reach_id}")
def guide_availability_for_reach(reach_id: str, date: date_t = Query(...)):
    """Median guide availability for a (reach, date), for the why-panel
    divergence callout. Returns null when we have no recent data."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY availability_pct) AS median_pct,
                   COUNT(*) AS guide_count
            FROM bronze.guide_availability
            WHERE reach_id = :rid AND target_date = :d
              AND fetched_date >= (CURRENT_DATE - INTERVAL '14 days')
              AND availability_pct IS NOT NULL
        """), {"rid": reach_id, "d": date}).fetchone()
    if not row or not row[1]:
        return {"median_availability_pct": None, "guide_count": 0}
    return {"median_availability_pct": float(row[0]), "guide_count": int(row[1])}


@router.get("/trip-quality/ranking")
def trip_quality_ranking(
    date: date_t = Query(...),
    user_lat: float = Query(...),
    user_lon: float = Query(...),
    max_miles: float = Query(150),
):
    """Geo-filtered watershed ranking. Returns watersheds sorted by best
    reach's TQS, with distance from the user to that reach's centroid."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT w.watershed, w.target_date, w.watershed_tqs,
                       w.best_reach_id, w.confidence, w.primary_factor,
                       w.unfavorable_count, w.total_reaches, w.reach_spread,
                       w.horizon_days, w.forecast_source,
                       r.name AS best_reach_name,
                       r.centroid_lat, r.centroid_lon
                FROM gold.trip_quality_watershed_daily w
                JOIN silver.river_reaches r ON r.id = w.best_reach_id
                WHERE w.target_date = :d
            """),
            {"d": date},
        ).fetchall()

    results = []
    for r in rows:
        miles = _haversine_miles(user_lat, user_lon, float(r[12]), float(r[13]))
        if miles > max_miles:
            continue
        results.append({
            "watershed": r[0],
            "target_date": r[1].isoformat(),
            "watershed_tqs": int(r[2]),
            "best_reach_id": r[3],
            "best_reach_name": r[11],
            "confidence": int(r[4]),
            "primary_factor": r[5],
            "unfavorable_count": int(r[6]),
            "total_reaches": int(r[7]),
            "reach_spread": float(r[8]),
            "horizon_days": int(r[9]),
            "forecast_source": r[10],
            "miles_from_user": round(miles, 1),
        })
    results.sort(key=lambda x: (-x["watershed_tqs"], x["miles_from_user"]))
    return {"date": date.isoformat(), "results": results}
