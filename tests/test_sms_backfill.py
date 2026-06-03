"""DB-backed test for the phone_hash backfill (pipeline.sms.backfill_phone_hash).

Seeds throwaway users (provider='test-backfill'), runs the backfill, and
asserts it populates only the verified-but-unhashed row, leaves an
already-hashed row and a no-phone row alone, and is idempotent. Cleans up in
a finally block. Requires the local DB (same as the existing API tests).
"""
import base64
import uuid

import pytest
from sqlalchemy import text

from pipeline.db import engine

_TEST_KEY_B64 = base64.b64encode(b"0123456789abcdef0123456789abcdef").decode()
_PROVIDER = "test-backfill"


@pytest.fixture
def crypto(monkeypatch):
    monkeypatch.setenv("SMS_ENCRYPTION_KEY", _TEST_KEY_B64)
    from app.lib import phone_crypto as pc
    pc._key.cache_clear()
    yield pc
    pc._key.cache_clear()


def _insert(conn, **cols):
    uid = uuid.uuid4()
    cols.setdefault("sms_paused", False)
    keys = ["id", "provider", "provider_id"] + list(cols)
    conn.execute(
        text(f"INSERT INTO users ({', '.join(keys)}) "
             f"VALUES (:id, :provider, :provider_id, {', '.join(f':{k}' for k in cols)})"),
        {"id": uid, "provider": _PROVIDER, "provider_id": f"{_PROVIDER}-{uid}", **cols},
    )
    return uid


def test_backfill_populates_only_missing_hash(crypto):
    from pipeline.sms.backfill_phone_hash import run

    phone = "+15035557777"
    enc = crypto.encrypt_phone(phone)
    expected_hash = crypto.hash_phone_for_lookup(phone)
    preexisting_hash = crypto.hash_phone_for_lookup("+15035550000")

    with engine.begin() as conn:
        # needs backfill: has encrypted phone, NULL hash
        u_missing = _insert(conn, phone_number_e164_encrypted=enc, phone_hash=None)
        # already hashed: must stay untouched
        u_hashed = _insert(conn, phone_number_e164_encrypted=crypto.encrypt_phone("+15035550000"),
                           phone_hash=preexisting_hash)
        # no phone at all: must stay NULL
        u_nophone = _insert(conn)

    try:
        result = run()
        assert result["candidates"] == 1 and result["updated"] == 1 and result["failed"] == 0

        with engine.connect() as conn:
            got = {r[0]: r[1] for r in conn.execute(
                text("SELECT id, phone_hash FROM users WHERE provider = :p"),
                {"p": _PROVIDER},
            )}
        assert bytes(got[u_missing]) == expected_hash       # backfilled correctly
        assert bytes(got[u_hashed]) == preexisting_hash      # untouched
        assert got[u_nophone] is None                        # no phone → no hash

        # Idempotent: a second run finds nothing to do.
        assert run()["candidates"] == 0
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM users WHERE provider = :p"), {"p": _PROVIDER})
