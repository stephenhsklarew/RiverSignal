"""Hourly TQS alert engine.

Per plan §3.6. For each (user, watched reach):
  1. band_cross_up — today's tqs >= threshold AND most recent prior
     snapshot's tqs (for the same target_date) was < threshold.
  2. trend_rising — slope over last 5 daily snapshots >= +4 tqs/day for
     a future target_date. Rate-limited to one fire per (user, reach)
     every 5 days.
  3. weekly_digest — produced by a separate Friday batch job (B5_5);
     not handled here.
  4. Honor muted_until.

Writes user_alert_deliveries rows; safe to re-run within the same hour
because the band-cross detection inherently requires a state transition
and the trend rate-limit checks last delivery time.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from pipeline.alerts.narratives import attach_narratives
from pipeline.db import engine


# Future target dates we evaluate band-crossings against (relative to today).
HORIZONS_DAYS = [0, 1, 3, 7, 14, 21]


def _users_with_watches(conn) -> list[tuple[str, str, int, bool, datetime | None]]:
    """Returns [(user_id, reach_id, threshold, alert_trend, muted_until)]."""
    rows = conn.execute(text("""
        SELECT user_id::text, reach_id, alert_threshold, alert_trend, muted_until
        FROM user_reach_watches
        WHERE muted_until IS NULL OR muted_until < now()
    """)).fetchall()
    return [(r[0], r[1], int(r[2]), bool(r[3]), r[4]) for r in rows]


def _current_tqs(conn, reach_id: str, target_date: date) -> int | None:
    row = conn.execute(text(
        "SELECT tqs FROM gold.trip_quality_daily WHERE reach_id = :r AND target_date = :d"
    ), {"r": reach_id, "d": target_date}).fetchone()
    return int(row[0]) if row else None


def _prior_snapshot_tqs(conn, reach_id: str, target_date: date, today: date) -> int | None:
    """Most recent snapshot strictly before today, for the same target_date."""
    row = conn.execute(text("""
        SELECT tqs FROM gold.trip_quality_history
        WHERE reach_id = :r AND target_date = :d AND snapshot_date < :today
        ORDER BY snapshot_date DESC
        LIMIT 1
    """), {"r": reach_id, "d": target_date, "today": today}).fetchone()
    return int(row[0]) if row else None


def _last_n_snapshots(conn, reach_id: str, target_date: date, n: int = 5) -> list[int]:
    rows = conn.execute(text("""
        SELECT tqs FROM gold.trip_quality_history
        WHERE reach_id = :r AND target_date = :d
        ORDER BY snapshot_date DESC
        LIMIT :n
    """), {"r": reach_id, "d": target_date, "n": n}).fetchall()
    return [int(r[0]) for r in rows]


def _recent_delivery_exists(conn, user_id: str, reach_id: str,
                             alert_type: str, target_date: date, since_days: int) -> bool:
    row = conn.execute(text("""
        SELECT 1 FROM user_alert_deliveries
        WHERE user_id = :u AND reach_id = :r AND alert_type = :t AND target_date = :d
          AND delivered_at >= now() - (CAST(:days AS text) || ' days')::interval
        LIMIT 1
    """), {"u": user_id, "r": reach_id, "t": alert_type, "d": target_date, "days": since_days}).fetchone()
    return bool(row)


def _trend_slope(snapshots: list[int]) -> float:
    """Average per-day slope across the snapshot list (most-recent first)."""
    if len(snapshots) < 2:
        return 0.0
    diffs = [snapshots[i - 1] - snapshots[i] for i in range(1, len(snapshots))]
    return sum(diffs) / len(diffs)


def compute_alerts(now: datetime | None = None) -> dict[str, int]:
    """Returns a summary dict like {band_cross_up: N, trend_rising: M, skipped: K}."""
    if now is None:
        now = datetime.now(timezone.utc)
    today = now.date()
    band_fires = 0
    trend_fires = 0
    skipped = 0

    with engine.connect() as conn:
        watches = _users_with_watches(conn)

        for (user_id, reach_id, threshold, alert_trend, _muted) in watches:
            for h in HORIZONS_DAYS:
                target = today + timedelta(days=h)
                cur = _current_tqs(conn, reach_id, target)
                if cur is None:
                    continue
                prior = _prior_snapshot_tqs(conn, reach_id, target, today)
                # Band-cross-up
                if cur >= threshold and prior is not None and prior < threshold:
                    # Dedupe: same alert for same (user, reach, target) within 24h
                    if not _recent_delivery_exists(conn, user_id, reach_id,
                                                    "band_cross_up", target, since_days=1):
                        conn.execute(text("""
                            INSERT INTO user_alert_deliveries
                                (user_id, reach_id, alert_type, target_date, tqs_at_alert, channel)
                            VALUES (:u, :r, 'band_cross_up', :d, :t, 'in_app')
                        """), {"u": user_id, "r": reach_id, "d": target, "t": cur})
                        band_fires += 1

                # Rising-trend (future targets only)
                if alert_trend and h >= 1:
                    snaps = _last_n_snapshots(conn, reach_id, target, n=5)
                    slope = _trend_slope(snaps)
                    if slope >= 4.0:
                        if not _recent_delivery_exists(conn, user_id, reach_id,
                                                        "trend_rising", target, since_days=5):
                            conn.execute(text("""
                                INSERT INTO user_alert_deliveries
                                    (user_id, reach_id, alert_type, target_date, tqs_at_alert, channel)
                                VALUES (:u, :r, 'trend_rising', :d, :t, 'in_app')
                            """), {"u": user_id, "r": reach_id, "d": target, "t": cur})
                            trend_fires += 1
                        else:
                            skipped += 1
        conn.commit()
    # Attach narratives to any new deliveries (also picks up backlog)
    narr_written = attach_narratives()
    return {
        "band_cross_up": band_fires,
        "trend_rising": trend_fires,
        "rate_limited_skips": skipped,
        "narratives_written": narr_written,
    }


if __name__ == "__main__":
    summary = compute_alerts()
    print(json.dumps(summary, indent=2))
    sys.exit(0)
