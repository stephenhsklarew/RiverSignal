"""SMS dispatcher — daily 9 AM PT batch.

Walks sms_alert_subscriptions × gold.trip_quality_watershed_daily, applies
anti-spam rules (cooldown / weekly cap / digest), and sends through Telnyx.
Layers two budget caps: app-level daily/monthly + carrier prepay (outer).

Run via:
    python -m pipeline.sms.dispatcher

Idempotent — re-running for the same day is a no-op because the
sms_alert_history unique constraint on (user_id, watershed, target_date)
rejects duplicates, and the cooldown query filters them out anyway.
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import httpx
from sqlalchemy import text

from app.lib.phone_crypto import decrypt_phone
from app.lib.telnyx import send_sms
from pipeline.db import engine


log = logging.getLogger(__name__)

# Plan defaults — overridable via env for ops tuning.
WEEKLY_CAP        = int(os.environ.get("SMS_WEEKLY_CAP_PER_USER", "3"))
COOLDOWN_HOURS    = int(os.environ.get("SMS_COOLDOWN_HOURS", "48"))
FORECAST_HORIZON  = int(os.environ.get("SMS_FORECAST_HORIZON_DAYS", "3"))
DAILY_BUDGET      = int(os.environ.get("MAX_SMS_PER_DAY", "500"))
MONTHLY_BUDGET    = int(os.environ.get("MAX_SMS_PER_MONTH", "5000"))
EST_COST_CENTS    = float(os.environ.get("SMS_EST_COST_CENTS", "0.4"))  # Telnyx ~$0.004
SHORT_LINK_BASE   = os.environ.get("SMS_SHORT_LINK", "https://riversignal.app/path/now")


@dataclass
class Match:
    user_id: str
    watershed: str
    target_date: date
    tqs: int
    confidence: str
    primary_factor: str | None


@dataclass
class UserSend:
    user_id: str
    phone_e164: str
    matches: list[Match]


WATERSHED_DISPLAY = {
    "mckenzie":    "McKenzie",
    "deschutes":   "Deschutes",
    "metolius":    "Metolius",
    "klamath":     "Klamath",
    "johnday":     "John Day",
    "skagit":      "Skagit",
    "green_river": "Green River",
}


def compose_body(matches: list[Match]) -> str:
    """Single SMS body for one user — handles digest mode for multi-watershed.

    Single match: "Deschutes is forecast Excellent for Saturday (TQS 85). Open: <link>"
    Multi-match:  "Excellent conditions: Deschutes Sat (85), Metolius Sun (82). Open: <link>"
    """
    weekday = lambda d: d.strftime("%a")
    if len(matches) == 1:
        m = matches[0]
        name = WATERSHED_DISPLAY.get(m.watershed, m.watershed)
        return (
            f"{name} is forecast Excellent for {weekday(m.target_date)} (TQS {m.tqs}). "
            f"Open RiverPath: {SHORT_LINK_BASE}/{m.watershed}"
        )
    parts = [
        f"{WATERSHED_DISPLAY.get(m.watershed, m.watershed)} {weekday(m.target_date)} ({m.tqs})"
        for m in matches
    ]
    return (
        f"Excellent conditions: {', '.join(parts)}. "
        f"Open RiverPath: {SHORT_LINK_BASE}"
    )


def _budget_remaining(conn) -> tuple[int, int]:
    """Return (daily_remaining, monthly_remaining) using sms_send_log."""
    today_count = conn.execute(
        text("SELECT count(*) FROM sms_send_log WHERE sent_at::date = current_date AND success")
    ).scalar() or 0
    # Month-to-date using DATE_TRUNC for the local server month boundary.
    month_count = conn.execute(
        text("""
            SELECT count(*) FROM sms_send_log
            WHERE sent_at >= date_trunc('month', current_date) AND success
        """)
    ).scalar() or 0
    return DAILY_BUDGET - today_count, MONTHLY_BUDGET - month_count


def _find_matches(conn) -> list[Match]:
    """Pull candidate matches for today's batch.

    Filters:
      - Forecast target_date in [today, today + FORECAST_HORIZON]
      - Watershed TQS >= subscription threshold
      - Confidence is not 'low' (we skip climatological-only days)
      - Subscription is not muted (muted_until is null or in the past)
      - User has not opted out (users.sms_paused is false)
      - User has a verified phone number
      - No prior history row for (user, watershed, target_date) within cooldown
    """
    rows = conn.execute(
        text(f"""
            WITH eligible AS (
                SELECT sub.user_id,
                       sub.watershed,
                       d.target_date,
                       d.watershed_tqs        AS tqs,
                       d.confidence,
                       d.primary_factor
                FROM sms_alert_subscriptions sub
                JOIN users u ON u.id = sub.user_id
                JOIN gold.trip_quality_watershed_daily d
                  ON d.watershed = sub.watershed
                WHERE u.phone_verified_at IS NOT NULL
                  AND u.sms_paused IS NOT TRUE
                  AND u.phone_number_e164_encrypted IS NOT NULL
                  AND (sub.muted_until IS NULL OR sub.muted_until < now())
                  AND d.target_date BETWEEN current_date AND current_date + INTERVAL '{FORECAST_HORIZON} days'
                  AND d.watershed_tqs >= sub.threshold
                  AND d.confidence >= 40  -- "low" bucket cutoff (see _confidence_bucket in reaches.py)
            )
            SELECT e.user_id, e.watershed, e.target_date, e.tqs, e.confidence, e.primary_factor
            FROM eligible e
            WHERE NOT EXISTS (
                SELECT 1 FROM sms_alert_history h
                WHERE h.user_id = e.user_id
                  AND h.watershed = e.watershed
                  AND h.target_date = e.target_date
                  AND h.sent_at >= now() - make_interval(hours => :cooldown)
            )
            ORDER BY e.user_id, e.target_date, e.watershed
        """),
        {"cooldown": COOLDOWN_HOURS},
    ).fetchall()

    return [
        Match(
            user_id=str(r[0]),
            watershed=r[1],
            target_date=r[2],
            tqs=int(r[3]),
            confidence=str(r[4]),
            primary_factor=r[5],
        )
        for r in rows
    ]


def _weekly_send_count(conn, user_id: str) -> int:
    return conn.execute(
        text("""
            SELECT count(*) FROM sms_alert_history
            WHERE user_id = :uid
              AND sent_at >= now() - INTERVAL '7 days'
        """),
        {"uid": user_id},
    ).scalar() or 0


def _load_phone(conn, user_id: str) -> str | None:
    row = conn.execute(
        text("SELECT phone_number_e164_encrypted FROM users WHERE id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or not row[0]:
        return None
    try:
        return decrypt_phone(bytes(row[0]))
    except Exception as exc:
        log.error("Failed to decrypt phone for user %s: %s", user_id, exc)
        return None


def _record_send(conn, send: UserSend, message_id: str | None, status: str) -> None:
    for m in send.matches:
        conn.execute(
            text("""
                INSERT INTO sms_alert_history
                    (user_id, watershed, target_date, tqs_at_send, forecast_source,
                     telnyx_message_id, delivery_status)
                VALUES
                    (:uid, :ws, :td, :tqs, :src, :mid, :status)
                ON CONFLICT (user_id, watershed, target_date) DO NOTHING
            """),
            {
                "uid": send.user_id,
                "ws": m.watershed,
                "td": m.target_date,
                "tqs": m.tqs,
                "src": m.primary_factor,
                "mid": message_id,
                "status": status,
            },
        )
    conn.execute(
        text("""
            INSERT INTO sms_send_log (cost_cents, success)
            VALUES (:cost, :ok)
        """),
        {"cost": EST_COST_CENTS, "ok": status == "queued"},
    )


def run() -> dict[str, Any]:
    """Execute the dispatcher run. Returns a summary dict."""
    started_at = log.info("SMS dispatcher starting")
    sent = 0
    skipped_cap = 0
    skipped_budget = 0
    failed = 0

    with engine.connect() as conn:
        daily_left, monthly_left = _budget_remaining(conn)
        if daily_left <= 0 or monthly_left <= 0:
            log.warning(
                "SMS budget cap hit before run: daily_left=%s monthly_left=%s",
                daily_left, monthly_left,
            )
            return {"status": "budget_capped", "sent": 0, "daily_left": daily_left}

        matches = _find_matches(conn)
        log.info("Found %d candidate matches", len(matches))

        # Group by user → digest.
        by_user: dict[str, list[Match]] = defaultdict(list)
        for m in matches:
            by_user[m.user_id].append(m)

        for user_id, user_matches in by_user.items():
            # Weekly cap check.
            wc = _weekly_send_count(conn, user_id)
            if wc >= WEEKLY_CAP:
                skipped_cap += 1
                continue

            # Budget check (re-read; another caller may have spent it).
            daily_left, monthly_left = _budget_remaining(conn)
            if daily_left <= 0 or monthly_left <= 0:
                skipped_budget += 1
                continue

            phone = _load_phone(conn, user_id)
            if not phone:
                log.error("user %s has subscriptions but no decryptable phone", user_id)
                continue

            # Cap matches per send at the same target_date+watershed combination —
            # already enforced by the schema's unique constraint, but defensive here.
            user_matches = sorted(user_matches, key=lambda m: (m.target_date, m.watershed))

            body = compose_body(user_matches)
            try:
                resp = send_sms(phone, body)
                message_id = resp.get("id")
                with conn.begin():
                    _record_send(UserSend(user_id, phone, user_matches), message_id, "queued")
                sent += 1
            except httpx.HTTPStatusError as e:
                log.error("Telnyx %s for user %s: %s", e.response.status_code, user_id, e)
                with conn.begin():
                    _record_send(UserSend(user_id, phone, user_matches),
                                 None, f"failed_{e.response.status_code}")
                failed += 1
            except Exception as exc:
                log.exception("SMS send failed for user %s: %s", user_id, exc)
                failed += 1

    log.info(
        "SMS dispatcher complete: sent=%d skipped_cap=%d skipped_budget=%d failed=%d",
        sent, skipped_cap, skipped_budget, failed,
    )
    return {
        "status": "ok",
        "sent": sent,
        "skipped_weekly_cap": skipped_cap,
        "skipped_budget": skipped_budget,
        "failed": failed,
    }


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(run(), indent=2))
