"""Thin Telnyx HTTP client for Verify (OTP) and Messaging.

Keeps the surface small and easy to mock. All calls return parsed JSON
or raise httpx errors that the caller layer translates into HTTPException.

Env config:
  TELNYX_API_KEY                  — bearer token for the v2 API
  TELNYX_VERIFY_PROFILE_ID        — Verify profile id (created in Telnyx console)
  TELNYX_MESSAGING_PROFILE_ID     — Messaging profile id for outbound SMS
  TELNYX_FROM_NUMBER              — Long code or short code we send from (E.164)
  TELNYX_PUBLIC_KEY               — ed25519 public key for inbound webhook verification

Telnyx Verify auto-generates and delivers the OTP. We never see the code,
just an opaque verification_id we hand back to the user. On confirm, we
submit (verification_id, code) and Telnyx tells us whether the code matched.
"""
from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx


API_BASE = "https://api.telnyx.com/v2"


def _api_key() -> str:
    k = os.environ.get("TELNYX_API_KEY")
    if not k:
        raise RuntimeError("TELNYX_API_KEY env var is not set")
    return k


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}


@dataclass
class VerificationStart:
    verification_id: str
    expires_at: float  # unix ts


def start_verification(phone_e164: str) -> VerificationStart:
    """Trigger Telnyx Verify to send an OTP SMS to the given E.164 number.

    Returns the verification id we'll hand back to the client. The OTP itself
    is delivered by Telnyx; we never see it.
    """
    profile_id = os.environ.get("TELNYX_VERIFY_PROFILE_ID")
    if not profile_id:
        raise RuntimeError("TELNYX_VERIFY_PROFILE_ID env var is not set")

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            f"{API_BASE}/verifications/sms",
            headers=_headers(),
            json={
                "phone_number": phone_e164,
                "verify_profile_id": profile_id,
                "timeout_secs": 600,  # 10-minute OTP validity
            },
        )
        resp.raise_for_status()
        data = resp.json()["data"]
    return VerificationStart(
        verification_id=data["id"],
        expires_at=time.time() + 600,
    )


def confirm_verification(verification_id: str, code: str) -> bool:
    """Check a user-submitted code against a Telnyx verification record.

    Returns True if accepted; False if rejected. Raises for transport errors.
    """
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            f"{API_BASE}/verifications/by_verification_id/{verification_id}/actions/verify",
            headers=_headers(),
            json={"code": code},
        )
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        return resp.json()["data"]["response_code"] == "accepted"


def send_sms(to_e164: str, body: str) -> dict[str, Any]:
    """Send a single SMS via Telnyx Messaging API.

    Returns the parsed response dict; caller persists message id + status.
    """
    messaging_profile_id = os.environ.get("TELNYX_MESSAGING_PROFILE_ID")
    from_number = os.environ.get("TELNYX_FROM_NUMBER")
    if not (messaging_profile_id and from_number):
        raise RuntimeError(
            "TELNYX_MESSAGING_PROFILE_ID and TELNYX_FROM_NUMBER must be set"
        )

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            f"{API_BASE}/messages",
            headers=_headers(),
            json={
                "messaging_profile_id": messaging_profile_id,
                "from": from_number,
                "to": to_e164,
                "text": body,
            },
        )
        resp.raise_for_status()
        return resp.json()["data"]


def verify_webhook_signature(payload_raw: bytes, signature_b64: str, ts_str: str) -> bool:
    """Verify an inbound Telnyx webhook using the ed25519 public key.

    Telnyx signs `f"{timestamp}|{raw_body}"` with ed25519. We hold the
    public key as TELNYX_PUBLIC_KEY (base64). Returns True if valid.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature

    pub_b64 = os.environ.get("TELNYX_PUBLIC_KEY")
    if not pub_b64:
        # In dev / staging where webhook signing isn't configured, fail closed.
        return False
    try:
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))
        sig = base64.b64decode(signature_b64)
        message = f"{ts_str}|".encode() + payload_raw
        pub.verify(sig, message)
        return True
    except (InvalidSignature, ValueError):
        return False
