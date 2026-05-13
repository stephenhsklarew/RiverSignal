"""Weekly digest generator for the push-product opportunist persona.

Plan §3.6 + §6. Friday morning batch: for each user with at least one
watch, write one weekly_digest delivery row with a serialized payload
covering each watched reach + the next 14 days of TQS + band-crossings.

Idempotent for the same calendar week — UPDATE on existing delivery
row keyed (user_id, alert_type='weekly_digest', target_date=Friday-of-week).
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from pipeline.alerts.narratives import _short_label  # reuse helper
from pipeline.db import engine


def _friday_of_week(today: date | None = None) -> date:
    today = today or date.today()
    # Monday=0 ... Sunday=6; Friday=4
    offset = (4 - today.weekday()) % 7
    return today + timedelta(days=offset)


def _band(tqs: int) -> str:
    if tqs >= 90: return "Excellent"
    if tqs >= 70: return "Strong"
    if tqs >= 50: return "Mixed"
    if tqs >= 30: return "Marginal"
    return "Unfavorable"


def _users_with_watches(conn) -> list[str]:
    rows = conn.execute(text("""
        SELECT DISTINCT user_id::text
        FROM user_reach_watches
        WHERE muted_until IS NULL OR muted_until < now()
    """)).fetchall()
    return [r[0] for r in rows]


def _build_digest(conn, user_id: str, friday: date) -> dict:
    watches = conn.execute(text("""
        SELECT w.reach_id, r.name, r.short_label, r.watershed, w.alert_threshold
        FROM user_reach_watches w
        JOIN silver.river_reaches r ON r.id = w.reach_id
        WHERE w.user_id = :u
        ORDER BY r.watershed, w.created_at
    """), {"u": user_id}).fetchall()

    summaries = []
    for w in watches:
        reach_id, name, short_label, watershed, threshold = w
        # Next 14 days from Friday
        rows = conn.execute(text("""
            SELECT target_date, tqs, is_hard_closed
            FROM gold.trip_quality_daily
            WHERE reach_id = :r AND target_date BETWEEN :start AND :end
            ORDER BY target_date
        """), {"r": reach_id, "start": friday, "end": friday + timedelta(days=14)}).fetchall()
        daily = [
            {
                "date": rr[0].isoformat(),
                "tqs": int(rr[1]),
                "band": _band(int(rr[1])),
                "is_hard_closed": bool(rr[2]),
                "band_crossing": int(rr[1]) >= threshold,
            }
            for rr in rows
        ]
        peak = max((d for d in daily if not d["is_hard_closed"]), key=lambda d: d["tqs"], default=None)
        summaries.append({
            "reach_id": reach_id,
            "name": short_label or name,
            "watershed": watershed,
            "threshold": int(threshold),
            "peak": peak,
            "daily": daily,
        })
    return {
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "week_of": friday.isoformat(),
        "watershed_summaries": summaries,
    }


def generate_weekly_digests(today: date | None = None) -> int:
    """Returns the number of digests written/updated."""
    friday = _friday_of_week(today)
    n = 0
    with engine.connect() as conn:
        for user_id in _users_with_watches(conn):
            payload = _build_digest(conn, user_id, friday)
            # narrative_text holds the serialized JSON payload for v0.5
            existing = conn.execute(text("""
                SELECT id FROM user_alert_deliveries
                WHERE user_id = CAST(:u AS uuid)
                  AND alert_type = 'weekly_digest'
                  AND target_date = :d
            """), {"u": user_id, "d": friday}).fetchone()
            if existing:
                conn.execute(text("""
                    UPDATE user_alert_deliveries
                    SET narrative_text = :p, delivered_at = now()
                    WHERE id = :id
                """), {"p": json.dumps(payload), "id": existing[0]})
            else:
                conn.execute(text("""
                    INSERT INTO user_alert_deliveries
                        (user_id, reach_id, alert_type, target_date,
                         tqs_at_alert, channel, narrative_text)
                    VALUES (CAST(:u AS uuid), 'multi', 'weekly_digest', :d, 0,
                            'in_app', :p)
                """), {"u": user_id, "d": friday, "p": json.dumps(payload)})
            n += 1
        conn.commit()
    return n


if __name__ == "__main__":
    print(json.dumps({"digests_written": generate_weekly_digests()}, indent=2))
    sys.exit(0)
