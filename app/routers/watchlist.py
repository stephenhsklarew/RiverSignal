"""Watchlist CRUD for the TQS push (opportunist) persona.

Plan §6 push section. Auth-required for all verbs. The list response
enriches each watch with current_tqs and a 7-day trend so the
Watchlist tab in /path/alerts can render without follow-up requests.
"""
from datetime import date as date_t, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.routers.auth import get_current_user
from pipeline.db import engine

router = APIRouter(tags=["watchlist"])


def _require_user(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Must be logged in")
    return user


class WatchCreate(BaseModel):
    reach_id: str = Field(..., min_length=1, max_length=80)
    alert_threshold: Optional[int] = Field(70, ge=0, le=100)
    alert_trend: Optional[bool] = True


class WatchPatch(BaseModel):
    alert_threshold: Optional[int] = Field(None, ge=0, le=100)
    alert_trend: Optional[bool] = None
    muted_until: Optional[datetime] = None


def _enriched_rows(conn, user_id: str) -> list[dict]:
    rows = conn.execute(text("""
        WITH today_tqs AS (
            SELECT reach_id, tqs FROM gold.trip_quality_daily WHERE target_date = :today
        ),
        week_ago AS (
            SELECT reach_id, tqs
            FROM gold.trip_quality_history
            WHERE target_date = :today
              AND snapshot_date <= :today - INTERVAL '7 days'
            ORDER BY snapshot_date DESC
            LIMIT 1
        )
        SELECT w.reach_id, r.name, r.short_label, r.watershed,
               w.alert_threshold, w.alert_trend, w.muted_until, w.created_at,
               t.tqs AS current_tqs,
               COALESCE(t.tqs - wa.tqs, 0) AS trend_7d
        FROM user_reach_watches w
        JOIN silver.river_reaches r ON r.id = w.reach_id
        LEFT JOIN today_tqs t ON t.reach_id = w.reach_id
        LEFT JOIN week_ago  wa ON wa.reach_id = w.reach_id
        WHERE w.user_id = :uid
        ORDER BY w.created_at DESC
    """), {"uid": user_id, "today": date_t.today()}).fetchall()
    return [
        {
            "reach_id": r[0], "name": r[1], "short_label": r[2], "watershed": r[3],
            "alert_threshold": int(r[4]), "alert_trend": bool(r[5]),
            "muted_until": r[6].isoformat() if r[6] else None,
            "created_at": r[7].isoformat() if r[7] else None,
            "current_tqs": int(r[8]) if r[8] is not None else None,
            "trend_7d": int(r[9]) if r[9] is not None else 0,
        }
        for r in rows
    ]


@router.get("/watchlist")
def list_watchlist(request: Request):
    user = _require_user(request)
    with engine.connect() as conn:
        return {"watches": _enriched_rows(conn, user["id"])}


@router.post("/watchlist", status_code=201)
def add_watch(body: WatchCreate, request: Request):
    user = _require_user(request)
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM silver.river_reaches WHERE id = :rid AND is_active = true"),
            {"rid": body.reach_id},
        ).fetchone()
        if not exists:
            raise HTTPException(404, f"Unknown reach: {body.reach_id}")
        dup = conn.execute(
            text("SELECT 1 FROM user_reach_watches WHERE user_id = :uid AND reach_id = :rid"),
            {"uid": user["id"], "rid": body.reach_id},
        ).fetchone()
        if dup:
            raise HTTPException(409, "Already watching that reach")
        conn.execute(text("""
            INSERT INTO user_reach_watches (user_id, reach_id, alert_threshold, alert_trend)
            VALUES (:uid, :rid, :th, :trend)
        """), {
            "uid": user["id"], "rid": body.reach_id,
            "th": body.alert_threshold or 70,
            "trend": body.alert_trend if body.alert_trend is not None else True,
        })
        conn.commit()
        rows = _enriched_rows(conn, user["id"])
    new = next((r for r in rows if r["reach_id"] == body.reach_id), None)
    return new or {"reach_id": body.reach_id}


@router.patch("/watchlist/{reach_id}")
def update_watch(reach_id: str, body: WatchPatch, request: Request):
    user = _require_user(request)
    sets, params = [], {"uid": user["id"], "rid": reach_id}
    if body.alert_threshold is not None:
        sets.append("alert_threshold = :th"); params["th"] = body.alert_threshold
    if body.alert_trend is not None:
        sets.append("alert_trend = :trend"); params["trend"] = body.alert_trend
    if body.muted_until is not None:
        sets.append("muted_until = :mu"); params["mu"] = body.muted_until
    if not sets:
        raise HTTPException(400, "No fields to update")
    with engine.connect() as conn:
        result = conn.execute(
            text(f"UPDATE user_reach_watches SET {', '.join(sets)} "
                 f"WHERE user_id = :uid AND reach_id = :rid"),
            params,
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Not watching that reach")
        conn.commit()
        rows = _enriched_rows(conn, user["id"])
    return next((r for r in rows if r["reach_id"] == reach_id), {"reach_id": reach_id})


@router.delete("/watchlist/{reach_id}", status_code=204)
def remove_watch(reach_id: str, request: Request):
    user = _require_user(request)
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM user_reach_watches WHERE user_id = :uid AND reach_id = :rid"),
            {"uid": user["id"], "rid": reach_id},
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Not watching that reach")
    return None


# ─── Alert deliveries (plan §6) ────────────────────────────────────────────

@router.get("/alerts")
def list_alerts(request: Request, seen: Optional[bool] = None):
    user = _require_user(request)
    sql = """
        SELECT d.id::text, d.reach_id, r.name, r.watershed,
               d.alert_type, d.target_date, d.tqs_at_alert,
               d.narrative_text, d.delivered_at, d.seen_at
        FROM user_alert_deliveries d
        JOIN silver.river_reaches r ON r.id = d.reach_id
        WHERE d.user_id = :uid
    """
    params: dict[str, object] = {"uid": user["id"]}
    if seen is False:
        sql += " AND d.seen_at IS NULL"
    elif seen is True:
        sql += " AND d.seen_at IS NOT NULL"
    sql += " ORDER BY d.delivered_at DESC LIMIT 100"
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()
    return {
        "alerts": [
            {
                "id": r[0], "reach_id": r[1], "reach_name": r[2],
                "watershed": r[3], "alert_type": r[4],
                "target_date": r[5].isoformat() if r[5] else None,
                "tqs_at_alert": int(r[6]),
                "narrative": r[7],
                "delivered_at": r[8].isoformat() if r[8] else None,
                "seen_at": r[9].isoformat() if r[9] else None,
            }
            for r in rows
        ]
    }


@router.post("/alerts/{alert_id}/seen")
def mark_alert_seen(alert_id: str, request: Request):
    user = _require_user(request)
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                UPDATE user_alert_deliveries
                   SET seen_at = COALESCE(seen_at, now())
                 WHERE id = CAST(:id AS uuid) AND user_id = :uid
            """),
            {"id": alert_id, "uid": user["id"]},
        )
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Alert not found")
    return {"ok": True}
