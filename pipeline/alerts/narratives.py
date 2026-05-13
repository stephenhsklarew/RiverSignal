"""Alert narrative generator.

Plan §3.7 specs ADR-007 LLM narratives grounded in warehouse data.
v0.5 uses a deterministic template that pulls real numbers (current
sub-scores, prior-week TQS for context, primary_factor) from the
warehouse — meets the acceptance criteria (2-4 sentences referencing
concrete numbers; never regenerated thanks to the cache) without burning
LLM cost during alert volume ramp-up.

When the LLM upgrade lands, generate_narrative() is the swap point:
replace its body, keep the per-(alert_id) caching contract.
"""

from __future__ import annotations

import json
import sys
from datetime import date

from sqlalchemy import text

from pipeline.db import engine


FACTOR_PHRASES: dict[str, str] = {
    "catch": "the catch outlook (predicted catch model)",
    "water_temp": "water temperature",
    "flow": "flow",
    "weather": "weather",
    "hatch": "hatch alignment with the seasonal insect calendar",
    "access": "access (closures or fire perimeter)",
}


def _band(tqs: int) -> str:
    if tqs >= 90: return "Excellent"
    if tqs >= 70: return "Strong"
    if tqs >= 50: return "Mixed"
    if tqs >= 30: return "Marginal"
    return "Unfavorable"


def _short_label(conn, reach_id: str) -> str:
    row = conn.execute(text(
        "SELECT name, short_label FROM silver.river_reaches WHERE id = :r"
    ), {"r": reach_id}).fetchone()
    if not row:
        return reach_id
    return row[1] or row[0]


def _current_row(conn, reach_id: str, target_date: date):
    return conn.execute(text("""
        SELECT tqs, confidence, primary_factor,
               catch_score, water_temp_score, flow_score, weather_score,
               hatch_score, access_score, horizon_days, forecast_source
        FROM gold.trip_quality_daily
        WHERE reach_id = :r AND target_date = :d
    """), {"r": reach_id, "d": target_date}).fetchone()


def _prior_tqs(conn, reach_id: str, target_date: date, days_back: int = 3) -> int | None:
    row = conn.execute(text("""
        SELECT tqs FROM gold.trip_quality_history
        WHERE reach_id = :r AND target_date = :d
        ORDER BY snapshot_date ASC
        OFFSET GREATEST(0, (SELECT COUNT(*) FROM gold.trip_quality_history
                            WHERE reach_id = :r AND target_date = :d) - :n)
        LIMIT 1
    """), {"r": reach_id, "d": target_date, "n": days_back}).fetchone()
    return int(row[0]) if row else None


def generate_narrative(reach_id: str, target_date: date, alert_type: str) -> str:
    """Produce a 2-4 sentence narrative grounded in warehouse data."""
    with engine.connect() as conn:
        cur = _current_row(conn, reach_id, target_date)
        if not cur:
            return ""
        tqs, conf, pf, ct, wt, fl, wr, ht, acc, horizon, src = (
            int(cur[0]), int(cur[1]), cur[2],
            int(cur[3]), int(cur[4]), int(cur[5]), int(cur[6]),
            int(cur[7]), int(cur[8]), int(cur[9]), cur[10],
        )
        prior = _prior_tqs(conn, reach_id, target_date, days_back=3)
        label = _short_label(conn, reach_id)

    band = _band(tqs)
    when = "today" if horizon == 0 else (
        "tomorrow" if horizon == 1 else f"in {horizon} days"
    )

    parts: list[str] = []
    if alert_type == "band_cross_up":
        if prior is not None:
            parts.append(
                f"{label}'s trip-quality for {when} crossed into the {band} band "
                f"(was {prior}, now {tqs})."
            )
        else:
            parts.append(f"{label}'s trip-quality for {when} reached {tqs} ({band}).")
    elif alert_type == "trend_rising":
        if prior is not None:
            parts.append(
                f"{label}'s trip-quality for {when} has been rising "
                f"({prior} → {tqs} over the last few days)."
            )
        else:
            parts.append(f"{label}'s trip-quality for {when} is trending up to {tqs}.")
    else:
        parts.append(f"{label}'s trip-quality for {when} is {tqs} ({band}).")

    parts.append(
        f"The biggest factor is {FACTOR_PHRASES.get(pf, pf)} — current sub-score levels: "
        f"catch {ct}, water temp {wt}, flow {fl}, weather {wr}, hatch {ht}, access {acc}."
    )
    parts.append(f"Confidence ±{100 - conf} · source: {src}.")
    return " ".join(parts)


def attach_narratives(limit: int = 200) -> int:
    """Find pending alert deliveries without a narrative and populate them.

    Idempotent: only touches rows where narrative_text IS NULL.
    Returns the number of narratives written.
    """
    written = 0
    with engine.connect() as conn:
        pending = conn.execute(text("""
            SELECT id::text, reach_id, target_date, alert_type
            FROM user_alert_deliveries
            WHERE narrative_text IS NULL
            ORDER BY delivered_at DESC
            LIMIT :n
        """), {"n": limit}).fetchall()
        for row in pending:
            text_out = generate_narrative(row[1], row[2], row[3])
            if not text_out:
                continue
            conn.execute(text("""
                UPDATE user_alert_deliveries
                   SET narrative_text = :t
                 WHERE id = CAST(:i AS uuid)
            """), {"t": text_out, "i": row[0]})
            written += 1
        conn.commit()
    return written


if __name__ == "__main__":
    print(json.dumps({"narratives_written": attach_narratives()}, indent=2))
    sys.exit(0)
