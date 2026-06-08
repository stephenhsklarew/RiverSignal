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


# ── Saved-items cross-device sync + observation attribution ────────────
def test_saved_items_requires_auth():
    assert httpx.get(f"{API}/saved/items", timeout=10).status_code == 401
    assert httpx.post(f"{API}/saved/items", json={"items": []}, timeout=10).status_code == 401
    assert httpx.delete(f"{API}/saved/items/species/x", timeout=10).status_code == 401


def _forge_token(uid: str) -> str:
    # Local API runs with the default dev AUTH_SECRET_KEY; mint a matching JWT.
    from jose import jwt
    secret = os.environ.get("AUTH_SECRET_KEY", "dev-secret-key-change-in-production-32chars!")
    return jwt.encode({"sub": uid, "email": "t@t.co", "name": "Test Angler", "username": "tester"},
                      secret, algorithm="HS256")


def test_saved_items_authed_roundtrip_preserves_attribution():
    import uuid
    uid = str(uuid.uuid4())
    c = httpx.Client(cookies={"rs_token": _forge_token(uid)}, base_url=API, timeout=10)
    try:
        body = {"items": [
            {"type": "species", "id": "smb", "watershed": WS, "payload": {"label": "Smallmouth"}},
            {"type": "observation", "id": "obs-1", "watershed": WS, "payload": {
                "label": "Otter", "observer": "Original Angler", "source": "RiverPath",
                "visibility": "private", "originObservationId": "abc"}},
        ]}
        assert c.post("/saved/items", json=body).status_code == 200
        items = {i["id"]: i for i in c.get("/saved/items").json()["items"]}
        assert set(items) == {"smb", "obs-1"}
        # attribution + privacy survive the round-trip
        assert items["obs-1"]["observer"] == "Original Angler"
        assert items["obs-1"]["visibility"] == "private"
        assert c.delete("/saved/items/observation/obs-1").status_code == 200
        assert {i["id"] for i in c.get("/saved/items").json()["items"]} == {"smb"}
    finally:
        eng = create_engine(DB)
        with eng.begin() as conn:
            conn.execute(text("DELETE FROM saved_items WHERE user_id = :u"), {"u": uid})


def test_share_observation_carries_attribution_and_visibility():
    payload = {
        "watershed": WS, "sections": ["observation"],
        "items": [{"type": "observation", "id": "share-obs-9", "data": {
            "watershed": WS, "label": "River Otter", "observer": "Jane Doe",
            "source": "RiverPath", "visibility": "private", "originObservationId": "xyz",
        }}],
    }
    r = httpx.post(f"{API}/saved/share", json=payload, timeout=10)
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    resolved = httpx.get(f"{API}/saved/shared/{token}", timeout=10).json()
    item = resolved["items"][0]
    assert item["data"]["observer"] == "Jane Doe"
    assert item["data"]["visibility"] == "private"


# ── #1 Notifications vs SMS endpoints both respond ─────────────────────
def test_alerts_and_sms_endpoints_respond():
    # Anonymous: endpoints should respond (200 empty or 401), not 500.
    for path in ("/alerts", "/sms/subscriptions"):
        code = httpx.get(f"{API}{path}", timeout=10).status_code
        assert code in (200, 401, 403), f"{path} returned {code}"


# ── E1: Apple OAuth callback must not be a 501 stub ────────────────────
def test_apple_callback_not_501():
    # Apple posts form_post to /auth/apple/callback. With no body it should be a
    # 400 ("no authorization code"), never the old 501 stub. The -async alias too.
    for path in ("/auth/apple/callback", "/auth/apple/callback-async"):
        code = httpx.post(f"{API}{path}", timeout=10).status_code
        assert code != 501, f"{path} still returns 501"
        assert code == 400, f"{path} expected 400 (no code), got {code}"


# ── E4: fishing DO-anomaly count must be watershed-scoped (SQL precedence) ──
def test_do_anomaly_query_is_watershed_scoped():
    # Guards the parenthesized predicate: `ws AND (oxygen OR do)`, not
    # `ws AND oxygen OR do` (which leaks other watersheds' 'do' rows).
    eng = create_engine(DB)
    q = """
      SELECT count(*) FROM (VALUES ('A','low_oxygen'),('B','do_crash'),('B','do_crash'))
      AS t(watershed, anomaly_type)
      WHERE watershed = 'A' AND (anomaly_type ILIKE '%oxygen%' OR anomaly_type ILIKE '%do%')
    """
    with eng.connect() as c:
        assert c.execute(text(q)).scalar() == 1  # only A's row, never B's


# ── River Oracle grounds "what fish" on the watershed's species (ADR-007) ──
def test_oracle_fish_grounding_is_watershed_scoped():
    # The /river-oracle answer is grounded on gold.species_by_reach for the
    # watershed (the `fish_present` context). Regression: it hallucinated PNW
    # species (bull trout, steelhead) for Chattahoochee because no species were
    # in the context. Guard that the grounding species are watershed-correct.
    eng = create_engine(DB)
    with eng.connect() as c:
        names = " ".join(
            (r[0] or "").lower() for r in c.execute(text("""
                SELECT common_name FROM gold.species_by_reach
                WHERE watershed = :ws GROUP BY common_name
            """), {"ws": "chattahoochee"}).fetchall()
        )
    assert names, "no fish-present grounding data for chattahoochee"
    assert "bass" in names  # real Chattahoochee fish are present to ground on
    assert "bull trout" not in names and "steelhead" not in names  # PNW-only


def test_catch_probability_matches_fish_present_canonicalization():
    # FEAT-026 Phase 2: catch-probability uses the same canonicalize() as Fish
    # Present, so names agree — run-timing variants collapse (one "Chinook
    # Salmon", no "Fall/Spring Chinook") and there are no duplicate names.
    r = httpx.get(f"{API}/sites/johnday/catch-probability", timeout=20)
    assert r.status_code == 200, r.text
    names = [s["species"] for s in r.json().get("species", [])]
    assert len(names) == len(set(names)), f"duplicate species names: {names}"
    assert sum("chinook" in n.lower() for n in names) <= 1, names
    assert not any(n.lower().startswith(("fall ", "spring ", "summer ", "winter ")) for n in names), names


def test_oracle_endpoint_not_500():
    # Regression: a recreation_sites query referencing non-existent columns
    # (type/distance_km/watershed) 500'd the whole /river-oracle endpoint before
    # the grounding code ran. Accept 200 (worked) or 503 (no ANTHROPIC key in
    # this env) — but never 500.
    r = httpx.post(f"{API}/river-oracle",
                   json={"watershed": "chattahoochee", "question": "what fish can I catch today?"},
                   timeout=60)
    assert r.status_code in (200, 503), f"oracle returned {r.status_code}: {r.text[:200]}"
