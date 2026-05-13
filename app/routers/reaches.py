"""Reach endpoints — the TQS modeling unit.

Per plan §6 (pull surface): GET /api/v1/reaches lists active reaches
optionally filtered by watershed. The output is consumed by the
ranking page, reach-selector chips, and the persona/UI gating logic.
"""

from fastapi import APIRouter, Query
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["reaches"])


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
