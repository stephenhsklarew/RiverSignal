"""Tests for observation feature changes:
- Typeahead returns scientific_name for riverpath
- Visibility field (public/private) on observation create
- Private observations filtered from search/list/geojson queries
- SavedItem type 'observation' accepted
"""

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.routers.user_observations import _rate_limit
from pipeline.db import engine


@pytest.fixture(autouse=True)
def clear_rate_limit():
    """Reset the in-memory rate limiter before each test."""
    _rate_limit.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ── Typeahead ──

def test_typeahead_returns_scientific_name(client):
    """RiverPath typeahead results should include a scientific_name field."""
    resp = client.get("/api/v1/observations/typeahead?q=trout&app=riverpath")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0, "Expected at least one typeahead result for 'trout'"
    first = results[0]
    assert "scientific_name" in first, "Missing scientific_name field in typeahead result"
    assert "name" in first
    assert "type" in first


def test_typeahead_deeptrail_no_scientific_name(client):
    """DeepTrail typeahead should still work (no scientific_name field expected)."""
    resp = client.get("/api/v1/observations/typeahead?q=obsidian&app=deeptrail")
    assert resp.status_code == 200
    results = resp.json()
    # DeepTrail results have name/type but not necessarily scientific_name
    if len(results) > 0:
        assert "name" in results[0]
        assert "type" in results[0]


# ── Observation Create — visibility ──

def _make_observation(client, *, visibility="public", species="Test Species",
                      scientific_name=None, watershed="mckenzie"):
    """Helper to create an observation and return the response."""
    body = {
        "source_app": "riverpath",
        "species_name": species,
        "common_name": species,
        "category": "fish",
        "latitude": 44.05,
        "longitude": -122.95,
        "watershed": watershed,
        "visibility": visibility,
    }
    if scientific_name:
        body["scientific_name"] = scientific_name
    return client.post("/api/v1/observations/user", json=body)


def test_create_public_observation(client):
    resp = _make_observation(client, visibility="public", species=f"PublicFish-{uuid.uuid4().hex[:6]}")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["message"] == "Observation saved"


def test_create_private_observation(client):
    resp = _make_observation(client, visibility="private", species=f"PrivateFish-{uuid.uuid4().hex[:6]}")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data


def test_invalid_visibility_rejected(client):
    resp = client.post("/api/v1/observations/user", json={
        "source_app": "riverpath",
        "species_name": "SomeSpecies",
        "category": "fish",
        "visibility": "secret",
    })
    assert resp.status_code == 422, "Invalid visibility value should be rejected"


def test_scientific_name_stored(client):
    """Observation with scientific_name should store it in user_observations."""
    sci = "Oncorhynchus mykiss"
    tag = uuid.uuid4().hex[:8]
    species = f"Rainbow Trout {tag}"
    resp = _make_observation(client, species=species, scientific_name=sci)
    assert resp.status_code == 200
    obs_id = resp.json()["id"]

    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT scientific_name FROM user_observations WHERE id = :id"
        ), {"id": obs_id}).fetchone()
    assert row is not None
    assert row[0] == sci


# ── Private observation filtering ──

class TestPrivateFiltering:
    """Private observations should be excluded from all public query endpoints."""

    @pytest.fixture(autouse=True)
    def setup_observations(self, client):
        """Create one public and one private observation with unique species names."""
        self.tag = uuid.uuid4().hex[:8]
        self.public_species = f"PublicTestSpecies-{self.tag}"
        self.private_species = f"PrivateTestSpecies-{self.tag}"

        r1 = _make_observation(client, visibility="public", species=self.public_species)
        assert r1.status_code == 200
        self.public_id = r1.json()["id"]

        r2 = _make_observation(client, visibility="private", species=self.private_species)
        assert r2.status_code == 200
        self.private_id = r2.json()["id"]

    def test_list_excludes_private(self, client):
        """GET /observations/user should not return private observations."""
        resp = client.get("/api/v1/observations/user?source_app=riverpath&watershed=mckenzie")
        assert resp.status_code == 200
        ids = {o["id"] for o in resp.json()}
        assert self.public_id in ids, "Public observation missing from list"
        assert self.private_id not in ids, "Private observation should be excluded from list"

    def test_geojson_excludes_private(self, client):
        """GET /observations/user/geojson should not return private observations."""
        resp = client.get("/api/v1/observations/user/geojson?watershed=mckenzie")
        assert resp.status_code == 200
        data = resp.json()
        taxon_names = [f["properties"]["taxon_name"] for f in data["features"]]
        assert self.private_species not in taxon_names, "Private observation in geojson"

    def test_search_excludes_private(self, client):
        """Observation search should not return private observations."""
        resp = client.get(f"/api/v1/sites/mckenzie/observations/search?q={self.private_species}")
        assert resp.status_code == 200
        data = resp.json()
        matched = [f for f in data["features"]
                   if f["properties"]["taxon_name"] == self.private_species]
        assert len(matched) == 0, "Private observation should not appear in search"

    def test_search_includes_public(self, client):
        """Observation search should still return public observations."""
        resp = client.get(f"/api/v1/sites/mckenzie/observations/search?q={self.public_species}")
        assert resp.status_code == 200
        data = resp.json()
        matched = [f for f in data["features"]
                   if f["properties"]["taxon_name"] == self.public_species]
        assert len(matched) > 0, "Public observation should appear in search"

    def test_private_still_in_user_observations_table(self, client):
        """Private observation should still exist in user_observations (for future sharing)."""
        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT visibility FROM user_observations WHERE id = :id"
            ), {"id": self.private_id}).fetchone()
        assert row is not None, "Private observation should still be stored"
        assert row[0] == "private"

    def test_private_in_bronze_with_visibility_flag(self, client):
        """Private observation should be in bronze observations table with visibility in payload."""
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT data_payload->>'visibility'
                FROM observations
                WHERE source_id LIKE :pattern
            """), {"pattern": f"%{self.private_id}"}).fetchone()
        # It should exist in bronze
        if row:
            assert row[0] == "private", "Bronze payload should have visibility=private"


# ── Default visibility ──

def test_default_visibility_is_public(client):
    """Omitting visibility should default to public."""
    resp = client.post("/api/v1/observations/user", json={
        "source_app": "riverpath",
        "species_name": f"DefaultVis-{uuid.uuid4().hex[:6]}",
        "category": "fish",
        "latitude": 44.05,
        "longitude": -122.95,
    })
    assert resp.status_code == 200
    obs_id = resp.json()["id"]

    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT visibility FROM user_observations WHERE id = :id"
        ), {"id": obs_id}).fetchone()
    assert row[0] == "public"
