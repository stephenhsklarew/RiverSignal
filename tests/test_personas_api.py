"""Contract tests for the persona-self-selection API endpoints.

Covers:
  - GET  /api/v1/personas/catalog (public read)
  - GET  /api/v1/auth/me          (extended with persona fields)
  - POST /api/v1/auth/personas    (write — auth required, catalog-validated)

Tests that exercise the database use a DATABASE_URL-backed fixture. When
DATABASE_URL is unset, those tests skip. The catalog endpoint can also be
verified via TestClient without a DB if the seed migration has been applied.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.routers.auth import create_token, set_auth_cookie

NEEDS_DB = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set; skipping live DB checks",
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authed_user_id():
    """Return a test user id that exists in the DB. Skips if DATABASE_URL unset."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")
    from pipeline.db import engine

    with engine.connect() as conn:
        # Find any existing user — tests don't create users, they reuse one
        row = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        if not row:
            pytest.skip("No users in DB; cannot exercise authed endpoints")
        return str(row[0])


def _authed_client(client, user_id: str) -> TestClient:
    """Return a client with a valid auth cookie for the given user."""
    token = create_token(user_id, "test@example.com", "Test User")
    client.cookies.set("rs_token", token)
    return client


# ─── /personas/catalog ──────────────────────────────────────────────────────

@NEEDS_DB
def test_catalog_returns_six_personas(client):
    """The catalog endpoint returns the v1 six personas in sort order."""
    resp = client.get("/api/v1/personas/catalog")
    assert resp.status_code == 200
    body = resp.json()
    assert "personas" in body
    keys = [p["key"] for p in body["personas"]]
    expected = [
        "angler_self_guided",
        "guide_professional",
        "family_outdoor",
        "rockhound",
        "outdoor_general",
        "watershed_pro",
    ]
    # Order matches sort_order from the seed migration
    for k in expected:
        assert k in keys, f"persona '{k}' missing from catalog response"
    # First entry is angler_self_guided (sort_order 10)
    assert body["personas"][0]["key"] == "angler_self_guided"


@NEEDS_DB
def test_catalog_response_shape(client):
    """Every persona has the documented fields."""
    resp = client.get("/api/v1/personas/catalog")
    assert resp.status_code == 200
    for p in resp.json()["personas"]:
        assert set(p.keys()) >= {"key", "display_label", "description", "icon", "sort_order"}
        assert isinstance(p["sort_order"], int)
        assert p["display_label"]  # non-empty


def test_catalog_is_public_no_auth_required():
    """No auth cookie should not gate the catalog endpoint."""
    # raise_server_exceptions=False so a missing DB surfaces as 500, not a raise
    c = TestClient(app, raise_server_exceptions=False)
    c.cookies.clear()
    resp = c.get("/api/v1/personas/catalog")
    # Either 200 (DB applied) or 500 (no DB) — but never 401
    assert resp.status_code != 401


# ─── /auth/me extension ─────────────────────────────────────────────────────

@NEEDS_DB
def test_auth_me_includes_persona_fields(client, authed_user_id):
    """Authed /auth/me response contains personas, personas_set_at, personas_version."""
    _authed_client(client, authed_user_id)
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["anonymous"] is False
    user = body["user"]
    assert "personas" in user
    assert isinstance(user["personas"], list)
    assert "personas_set_at" in user
    assert "personas_version" in user
    assert isinstance(user["personas_version"], int)


def test_auth_me_anonymous_unchanged(client):
    """Anonymous /auth/me does not leak persona fields."""
    client.cookies.clear()
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["anonymous"] is True
    assert body["user"] is None


# ─── POST /auth/personas ────────────────────────────────────────────────────

def test_post_personas_requires_auth(client):
    """Unauthenticated POST is rejected."""
    client.cookies.clear()
    resp = client.post("/api/v1/auth/personas", json={"personas": ["angler_self_guided"]})
    assert resp.status_code == 401


@NEEDS_DB
def test_post_personas_writes_valid_keys(client, authed_user_id):
    """Posting valid catalog keys updates the user row and returns the new state."""
    _authed_client(client, authed_user_id)
    resp = client.post(
        "/api/v1/auth/personas",
        json={"personas": ["angler_self_guided", "family_outdoor"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body["personas"]) == {"angler_self_guided", "family_outdoor"}
    assert body["personas_set_at"] is not None


@NEEDS_DB
def test_post_personas_empty_is_valid_skip(client, authed_user_id):
    """Empty array is the 'skip' case — recorded with personas_set_at."""
    _authed_client(client, authed_user_id)
    resp = client.post("/api/v1/auth/personas", json={"personas": []})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["personas"] == []
    assert body["personas_set_at"] is not None


@NEEDS_DB
def test_post_personas_rejects_unknown_key(client, authed_user_id):
    """An unknown persona key rejects the whole request with 400."""
    _authed_client(client, authed_user_id)
    resp = client.post(
        "/api/v1/auth/personas",
        json={"personas": ["angler_self_guided", "not_a_real_persona"]},
    )
    assert resp.status_code == 400
    assert "not_a_real_persona" in resp.text


@NEEDS_DB
def test_post_personas_dedupes(client, authed_user_id):
    """Duplicate keys in the request are deduped server-side."""
    _authed_client(client, authed_user_id)
    resp = client.post(
        "/api/v1/auth/personas",
        json={"personas": ["angler_self_guided", "angler_self_guided", "family_outdoor"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert sorted(body["personas"]) == ["angler_self_guided", "family_outdoor"]


# Suppress the unused import warning while keeping the helper available.
_ = set_auth_cookie
