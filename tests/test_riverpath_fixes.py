"""Integration tests for the RiverPath fixes #1–#6 (run against the local API + DB).

Requires the dev API on :8001 and local Postgres on :5433. Skips gracefully if
the API isn't reachable.

  DATABASE_URL=postgresql+psycopg://localhost:5433/riversignal \
    .venv/bin/python -m pytest tests/test_riverpath_fixes.py -q
"""
import os
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import create_engine, text

API = os.environ.get("RP_API_BASE", "http://localhost:8001/api/v1")
DB = os.environ.get("DATABASE_URL", "postgresql+psycopg://localhost:5433/riversignal")
WS = "clinch_river_va"


def _api_up() -> bool:
    try:
        return httpx.get(API.replace("/api/v1", "/health"), timeout=3).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _api_up(), reason="local API on :8001 not running")


# ── #6 Saved share-links ───────────────────────────────────────────────
def test_share_create_and_resolve():
    payload = {
        "watershed": WS,
        "sections": ["species", "fly"],
        "items": [
            {"type": "species", "id": "smallmouth_bass", "data": {"label": "Smallmouth Bass", "watershed": WS}},
            {"type": "fly", "id": "clouser-minnow", "data": {"label": "Clouser Minnow", "watershed": WS}},
        ],
    }
    r = httpx.post(f"{API}/saved/share", json=payload, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token"] and body["url"] == f"/path/shared/{body['token']}"
    assert body["item_count"] == 2
    # expires ~24h out
    exp = datetime.fromisoformat(body["expires_at"])
    assert timedelta(hours=23) < (exp - datetime.now(timezone.utc)) < timedelta(hours=25)

    # resolve
    g = httpx.get(f"{API}/saved/shared/{body['token']}", timeout=10)
    assert g.status_code == 200, g.text
    res = g.json()
    assert res["watershed"] == WS
    assert {i["id"] for i in res["items"]} == {"smallmouth_bass", "clouser-minnow"}
    assert res["items"][0]["data"]["label"]  # display fields survived


def test_share_empty_rejected():
    r = httpx.post(f"{API}/saved/share", json={"watershed": WS, "items": []}, timeout=10)
    assert r.status_code == 400


def test_share_bogus_token_404():
    assert httpx.get(f"{API}/saved/shared/does-not-exist-xyz", timeout=10).status_code == 404


def test_share_expired_token_404():
    # Insert a row that expired an hour ago; the resolver must 404 it.
    eng = create_engine(DB)
    tok = "pytest-expired-token"
    with eng.begin() as c:
        c.execute(text("DELETE FROM shared_collections WHERE share_token = :t"), {"t": tok})
        c.execute(text("""
            INSERT INTO shared_collections (share_token, watershed, payload, item_count, expires_at)
            VALUES (:t, :w, '{"items":[]}'::jsonb, 0, :exp)
        """), {"t": tok, "w": WS, "exp": datetime.now(timezone.utc) - timedelta(hours=1)})
    try:
        assert httpx.get(f"{API}/saved/shared/{tok}", timeout=10).status_code == 404
    finally:
        with eng.begin() as c:
            c.execute(text("DELETE FROM shared_collections WHERE share_token = :t"), {"t": tok})


# ── #2 River-story audio ───────────────────────────────────────────────
@pytest.mark.parametrize("level", ["adult", "kids", "expert"])
def test_river_story_has_audio_url(level):
    r = httpx.get(f"{API}/sites/{WS}/river-story?reading_level={level}", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("narrative"), "story narrative missing"
    assert body.get("audio_url"), f"no cached audio_url for {WS}/{level} (TTS not generated)"


def test_river_story_matches_watershed():
    # the story must reference its own river (no stale/cross content)
    r = httpx.get(f"{API}/sites/{WS}/river-story?reading_level=adult", timeout=10)
    assert "clinch" in r.json()["narrative"].lower()


# ── #1 Notifications vs SMS endpoints both respond ─────────────────────
def test_alerts_and_sms_endpoints_respond():
    # Anonymous: endpoints should respond (200 empty or 401), not 500.
    for path in ("/alerts", "/sms/subscriptions"):
        code = httpx.get(f"{API}{path}", timeout=10).status_code
        assert code in (200, 401, 403), f"{path} returned {code}"
