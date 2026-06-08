"""SMS alerts: phone verification, per-watershed subscriptions, inbound webhook.

Routes mounted under /api/v1. See plan-2026-05-15-sms-alerts.md.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from app.lib.phone_crypto import encrypt_phone, hash_phone_for_lookup
from app.lib.telnyx import (
    confirm_verification,
    start_verification,
    verify_webhook_signature,
)
from app.routers.auth import get_current_user
from pipeline.config.watersheds import VALID_WATERSHEDS
from pipeline.db import engine


router = APIRouter(tags=["sms"])


# ── Validators ──────────────────────────────────────────────────────────────

# US + Canada both use country code +1. Accept any number with that prefix.
# Strip formatting; the canonical stored form is E.164.
_E164_RE = re.compile(r"^\+1\d{10}$")


def _normalize_phone(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw or "")
    if cleaned.startswith("+"):
        normalized = cleaned
    elif cleaned.startswith("1") and len(cleaned) == 11:
        normalized = "+" + cleaned
    elif len(cleaned) == 10:
        normalized = "+1" + cleaned
    else:
        raise ValueError("phone number must be a US or Canadian +1 number")
    if not _E164_RE.match(normalized):
        raise ValueError("phone number must be in E.164 +1NXXNXXXXXX format")
    return normalized


# ── In-memory rate limit (per-process; OK for single-instance Cloud Run) ────

_RATE_BUCKET: dict[str, list[float]] = {}
_VERIFY_RATE_LIMIT = 3       # per minute per IP
_VERIFY_RATE_WINDOW = 60


def _check_rate_limit(key: str) -> None:
    now = time.time()
    bucket = _RATE_BUCKET.setdefault(key, [])
    cutoff = now - _VERIFY_RATE_WINDOW
    bucket[:] = [t for t in bucket if t > cutoff]
    if len(bucket) >= _VERIFY_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many verification attempts. Try again in a minute.",
        )
    bucket.append(now)


# ── Phone verification ──────────────────────────────────────────────────────

class StartVerificationBody(BaseModel):
    phone: str = Field(..., max_length=20)

    @field_validator("phone")
    @classmethod
    def _v(cls, v: str) -> str:
        return _normalize_phone(v)


class StartVerificationResponse(BaseModel):
    verification_id: str
    expires_at: float


@router.post("/sms/phone/start-verification", response_model=StartVerificationResponse)
def post_start_verification(
    body: StartVerificationBody,
    request: Request,
    user: dict = Depends(get_current_user),
):
    if not user:
        raise HTTPException(401, "Authentication required to register a phone number")
    client_ip = (request.client.host if request.client else "unknown")
    _check_rate_limit(f"verify:{client_ip}")
    _check_rate_limit(f"verify:user:{user['id']}")
    try:
        res = start_verification(body.phone)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Verification provider error: {e}") from e
    return StartVerificationResponse(
        verification_id=res.verification_id,
        expires_at=res.expires_at,
    )


class ConfirmVerificationBody(BaseModel):
    verification_id: str
    code: str = Field(..., min_length=4, max_length=10)
    phone: str = Field(..., max_length=20)

    @field_validator("phone")
    @classmethod
    def _v(cls, v: str) -> str:
        return _normalize_phone(v)


@router.post("/sms/phone/confirm-verification")
def post_confirm_verification(
    body: ConfirmVerificationBody,
    user: dict = Depends(get_current_user),
):
    if not user:
        raise HTTPException(401, "Authentication required")
    try:
        ok = confirm_verification(body.verification_id, body.code)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Verification provider error: {e}") from e
    if not ok:
        raise HTTPException(400, "Verification code is incorrect or expired")

    # Persist encrypted phone + a deterministic, key-bound hash for inbound
    # STOP lookups (AES-GCM ciphertext is non-deterministic, so it can't be
    # queried by; the hash can) + verification timestamp.
    encrypted = encrypt_phone(body.phone)
    phone_hash = hash_phone_for_lookup(body.phone)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(
                text("""
                    UPDATE users
                    SET phone_number_e164_encrypted = :enc,
                        phone_hash = :phash,
                        phone_verified_at = now(),
                        sms_paused = false
                    WHERE id = :uid
                """),
                {"enc": encrypted, "phash": phone_hash, "uid": user["id"]},
            )
    return {"verified": True}


# ── Subscriptions ───────────────────────────────────────────────────────────

class SubscriptionPayload(BaseModel):
    watersheds: list[str]
    threshold: int = 80

    @field_validator("threshold")
    @classmethod
    def _t(cls, v: int) -> int:
        if v not in (70, 80):
            raise ValueError("threshold must be 70 or 80")
        return v

    @field_validator("watersheds")
    @classmethod
    def _w(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("at least one watershed is required")
        bad = [w for w in v if w not in VALID_WATERSHEDS]
        if bad:
            raise ValueError(f"unknown watershed(s): {bad}")
        return v


def _require_verified(user: dict) -> None:
    if not user:
        raise HTTPException(401, "Authentication required")
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT phone_verified_at FROM users WHERE id = :uid"),
            {"uid": user["id"]},
        ).fetchone()
    if not row or not row[0]:
        raise HTTPException(403, "Phone number must be verified before managing alerts")


@router.get("/sms/subscriptions")
def list_subscriptions(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Authentication required")
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT watershed, threshold, muted_until, created_at
                FROM sms_alert_subscriptions
                WHERE user_id = :uid
                ORDER BY created_at DESC
            """),
            {"uid": user["id"]},
        ).fetchall()
        verified_row = conn.execute(
            text("SELECT phone_verified_at, sms_paused FROM users WHERE id = :uid"),
            {"uid": user["id"]},
        ).fetchone()
    return {
        "phone_verified": bool(verified_row and verified_row[0]),
        "sms_paused": bool(verified_row and verified_row[1]),
        "subscriptions": [
            {
                "watershed": r[0],
                "threshold": r[1],
                "muted_until": r[2].isoformat() if r[2] else None,
                "created_at": r[3].isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/sms/health")
def sms_health():
    """Aggregate SMS alert delivery health for the public status page.

    Returns only counts (no phone numbers / user data). Surfaces the
    "accepted by Telnyx (200) but not delivered" failure mode by breaking
    down sms_alert_history.delivery_status — if sends exist but none reach
    'delivered', the carrier is dropping them (e.g. unregistered A2P 10DLC).
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT COALESCE(delivery_status, 'unknown') AS status, count(*)
            FROM sms_alert_history
            WHERE sent_at >= now() - INTERVAL '30 days'
            GROUP BY 1
            ORDER BY 2 DESC
        """)).fetchall()
        last_send = conn.execute(
            text("SELECT max(sent_at) FROM sms_alert_history")
        ).scalar()
        sent_7d = conn.execute(text("""
            SELECT count(*) FROM sms_send_log
            WHERE sent_at >= now() - INTERVAL '7 days' AND success
        """)).scalar() or 0
        verified = conn.execute(text("""
            SELECT count(*) FROM users
            WHERE phone_verified_at IS NOT NULL AND sms_paused IS NOT TRUE
        """)).scalar() or 0

    by_status = {r[0]: r[1] for r in rows}
    total_30d = sum(by_status.values())
    delivered = by_status.get("delivered", 0)

    # Health bucket. Delivery receipts (message.finalized) set 'delivered' on
    # success; everything stuck at 'queued' / *_failed with zero delivered is
    # the carrier-drop signature.
    if total_30d == 0:
        status = "unknown"
    elif delivered == 0:
        status = "error"
    elif delivered < total_30d:
        status = "warning"
    else:
        status = "healthy"

    return {
        "status": status,
        "verified_active_recipients": verified,
        "sent_last_7d": sent_7d,
        "last_send": last_send.isoformat() if last_send else None,
        "by_delivery_status_30d": by_status,
        "total_30d": total_30d,
        "delivered_30d": delivered,
    }


@router.post("/sms/subscriptions")
def upsert_subscriptions(
    body: SubscriptionPayload,
    user: dict = Depends(get_current_user),
):
    _require_verified(user)
    with engine.connect() as conn:
        with conn.begin():
            for ws in body.watersheds:
                conn.execute(
                    text("""
                        INSERT INTO sms_alert_subscriptions (user_id, watershed, threshold)
                        VALUES (:uid, :ws, :th)
                        ON CONFLICT (user_id, watershed) DO UPDATE
                          SET threshold = EXCLUDED.threshold,
                              muted_until = NULL
                    """),
                    {"uid": user["id"], "ws": ws, "th": body.threshold},
                )
    return {"count": len(body.watersheds)}


@router.delete("/sms/subscriptions/{watershed}")
def delete_subscription(watershed: str, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Authentication required")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(
                text("""
                    DELETE FROM sms_alert_subscriptions
                    WHERE user_id = :uid AND watershed = :ws
                """),
                {"uid": user["id"], "ws": watershed},
            )
    return {"deleted": True}


@router.post("/sms/pause")
def pause_all(user: dict = Depends(get_current_user)):
    """Global mute — keep subscriptions but stop sending."""
    if not user:
        raise HTTPException(401, "Authentication required")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(
                text("UPDATE users SET sms_paused = true WHERE id = :uid"),
                {"uid": user["id"]},
            )
    return {"paused": True}


@router.post("/sms/resume")
def resume_all(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Authentication required")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(
                text("UPDATE users SET sms_paused = false WHERE id = :uid"),
                {"uid": user["id"]},
            )
    return {"paused": False}


# ── Inbound webhook (STOP / HELP / replies) ─────────────────────────────────

@router.post("/sms/inbound")
async def inbound_webhook(request: Request):
    """Telnyx posts inbound SMS here. We handle STOP / STOPALL / HELP.

    Carrier compliance requires that STOP be respected within seconds.
    """
    raw = await request.body()
    signature = request.headers.get("Telnyx-Signature-ED25519") or ""
    ts = request.headers.get("Telnyx-Timestamp") or ""
    if not verify_webhook_signature(raw, signature, ts):
        raise HTTPException(401, "Invalid webhook signature")

    payload = (await request.json()) if raw else {}
    event = (payload.get("data") or {}).get("event_type")

    # Outbound delivery receipts (DLRs). Telnyx posts message.sent when the
    # carrier accepts and message.finalized with the terminal state. Persist
    # the per-recipient status onto sms_alert_history so a 200-but-undelivered
    # (e.g. unregistered A2P 10DLC traffic dropped by US carriers) is visible
    # instead of frozen at "queued".
    if event in {"message.sent", "message.finalized"}:
        msg = (payload.get("data") or {}).get("payload") or {}
        message_id = msg.get("id")
        to = msg.get("to") or []
        status = (to[0].get("status") if to else None) or "unknown"
        if message_id:
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(
                        text("""
                            UPDATE sms_alert_history
                               SET delivery_status = :st
                             WHERE telnyx_message_id = :mid
                        """),
                        {"st": status, "mid": message_id},
                    )
        return {"ok": True}

    if event != "message.received":
        return {"ok": True}

    msg = payload["data"]["payload"]
    from_e164 = (msg.get("from") or {}).get("phone_number")
    body_text = (msg.get("text") or "").strip().upper()

    if not from_e164:
        return {"ok": True}

    cmd = body_text.split()[0] if body_text else ""
    if cmd in {"STOP", "STOPALL", "UNSUBSCRIBE", "QUIT", "CANCEL", "END"}:
        # Pause only the sender: match the deterministic, key-bound phone hash
        # stored at confirm-verification. (Telnyx also enforces STOP at the
        # messaging-profile level; this keeps our own state consistent.)
        phone_hash = hash_phone_for_lookup(from_e164)
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text("UPDATE users SET sms_paused = true WHERE phone_hash = :h"),
                    {"h": phone_hash},
                )
        return {"ok": True}

    if cmd in {"HELP", "INFO"}:
        # Send a help response inline (Telnyx auto-handles HELP at profile level
        # too; this is belt-and-braces).
        return {"ok": True}

    # Anything else: silently log + 200. Don't auto-respond.
    return {"ok": True}
