"""Unit tests for SMS alerts (network- and DB-free).

Covers the two bug fixes:
  - subscription watershed allowlist is driven by the canonical registry
    (shenandoah / mad_river_oh / ipswich_river_ma must be accepted)
  - dispatcher SMS copy never falls back to a raw watershed key
Plus the supporting primitives: phone normalization, AES-GCM round-trip,
and the deterministic key-bound lookup hash used by the inbound STOP handler.
"""
import base64

import pytest
from pydantic import ValidationError

from pipeline.config.watersheds import VALID_WATERSHEDS, watershed_name


# A fixed 32-byte AES-256 key for crypto tests. _key() is lru_cached, so set
# the env and clear the cache before exercising phone_crypto.
_TEST_KEY_B64 = base64.b64encode(b"0123456789abcdef0123456789abcdef").decode()


@pytest.fixture
def phone_crypto(monkeypatch):
    monkeypatch.setenv("SMS_ENCRYPTION_KEY", _TEST_KEY_B64)
    from app.lib import phone_crypto as pc
    pc._key.cache_clear()
    yield pc
    pc._key.cache_clear()


# ── Phone normalization ──────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("5035551234", "+15035551234"),
    ("(503) 555-1234", "+15035551234"),
    ("1-503-555-1234", "+15035551234"),
    ("+15035551234", "+15035551234"),
])
def test_normalize_phone_valid(raw, expected):
    from app.routers.sms import _normalize_phone
    assert _normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "12345", "555123456789", "+445035551234"])
def test_normalize_phone_invalid(raw):
    from app.routers.sms import _normalize_phone
    with pytest.raises(ValueError):
        _normalize_phone(raw)


# ── Subscription watershed allowlist (bug 2) ─────────────────────────────────

def test_subscription_accepts_all_onboarded_watersheds():
    """Every watershed in the canonical registry must be subscribable —
    previously shenandoah / mad_river_oh / ipswich_river_ma were rejected."""
    from app.routers.sms import SubscriptionPayload
    payload = SubscriptionPayload(watersheds=sorted(VALID_WATERSHEDS), threshold=80)
    assert set(payload.watersheds) == set(VALID_WATERSHEDS)


def test_subscription_accepts_recently_added_watersheds():
    from app.routers.sms import SubscriptionPayload
    for ws in ("shenandoah", "mad_river_oh", "ipswich_river_ma"):
        assert ws in VALID_WATERSHEDS
        SubscriptionPayload(watersheds=[ws], threshold=80)  # must not raise


def test_subscription_rejects_unknown_watershed():
    from app.routers.sms import SubscriptionPayload
    with pytest.raises(ValidationError):
        SubscriptionPayload(watersheds=["atlantis"], threshold=80)


def test_subscription_rejects_empty_and_bad_threshold():
    from app.routers.sms import SubscriptionPayload
    with pytest.raises(ValidationError):
        SubscriptionPayload(watersheds=[], threshold=80)
    with pytest.raises(ValidationError):
        SubscriptionPayload(watersheds=["mckenzie"], threshold=55)


# ── Dispatcher copy never leaks a raw key (bug 2) ────────────────────────────

def test_watershed_name_covers_registry():
    for ws in VALID_WATERSHEDS:
        name = watershed_name(ws)
        assert name and name != ws  # always a human label, never the raw id


def test_compose_body_single_uses_display_name():
    from datetime import date
    from pipeline.sms.dispatcher import compose_body, Match
    m = Match(user_id="u1", watershed="mad_river_oh", target_date=date(2026, 6, 6),
              tqs=85, confidence="high", primary_factor="flow")
    body = compose_body([m])
    assert "Mad River" in body
    assert "mad_river_oh" not in body.split("path/now/")[0]  # key only in the link
    assert "TQS 85" in body


def test_compose_body_multi_digest():
    from datetime import date
    from pipeline.sms.dispatcher import compose_body, Match
    matches = [
        Match("u1", "shenandoah", date(2026, 6, 6), 88, "high", None),
        Match("u1", "ipswich_river_ma", date(2026, 6, 7), 82, "high", None),
    ]
    body = compose_body(matches)
    assert "Shenandoah River" in body
    assert "Ipswich River (MA)" in body
    assert "(88)" in body and "(82)" in body


# ── Phone crypto + lookup hash (bug 1 support) ───────────────────────────────

def test_encrypt_decrypt_round_trip(phone_crypto):
    blob = phone_crypto.encrypt_phone("+15035551234")
    assert isinstance(blob, bytes) and len(blob) > 12
    assert phone_crypto.decrypt_phone(blob) == "+15035551234"


def test_encrypt_is_non_deterministic(phone_crypto):
    """Distinct nonces → distinct ciphertext, which is exactly why the
    STOP handler needs a separate deterministic hash to look up by."""
    a = phone_crypto.encrypt_phone("+15035551234")
    b = phone_crypto.encrypt_phone("+15035551234")
    assert a != b


def test_lookup_hash_is_deterministic_and_phone_specific(phone_crypto):
    h1 = phone_crypto.hash_phone_for_lookup("+15035551234")
    h2 = phone_crypto.hash_phone_for_lookup("+15035551234")
    other = phone_crypto.hash_phone_for_lookup("+15035559999")
    assert h1 == h2          # deterministic → usable in a WHERE clause
    assert h1 != other       # different numbers don't collide
    assert isinstance(h1, bytes) and len(h1) == 32
