"""API endpoint tests."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["observations"] > 0
    assert data["materialized_views"] >= 20


def test_list_sites(client):
    resp = client.get("/api/v1/sites")
    assert resp.status_code == 200
    sites = resp.json()
    assert len(sites) == 4
    names = {s["watershed"] for s in sites}
    assert names == {"klamath", "mckenzie", "deschutes", "metolius"}
    for site in sites:
        assert site["observations"] > 0
        assert "bbox" in site


def test_get_site_detail(client):
    resp = client.get("/api/v1/sites/mckenzie")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "McKenzie River"
    assert data["scorecard"]["total_species"] > 5000
    assert data["scorecard"]["fish_species"] > 30
    assert len(data["indicators"]) > 0


def test_get_site_not_found(client):
    resp = client.get("/api/v1/sites/nonexistent")
    assert resp.status_code == 404


def test_site_species(client):
    resp = client.get("/api/v1/sites/deschutes/species?limit=10")
    assert resp.status_code == 200
    species = resp.json()
    assert len(species) <= 10
    assert all("taxon_name" in s for s in species)


def test_site_story(client):
    resp = client.get("/api/v1/sites/mckenzie/story")
    assert resp.status_code == 200
    data = resp.json()
    assert "timeline" in data
    assert len(data["timeline"]) > 0


def test_fishing_brief(client):
    resp = client.get("/api/v1/sites/deschutes/fishing/brief")
    assert resp.status_code == 200
    data = resp.json()
    assert "conditions" in data
    assert "stocking" in data
    assert "species_by_reach" in data


def test_fishing_harvest(client):
    resp = client.get("/api/v1/sites/deschutes/fishing/harvest")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "species" in data[0]
    assert "harvest" in data[0]


def test_fishing_stocking(client):
    resp = client.get("/api/v1/sites/mckenzie/fishing/stocking")
    assert resp.status_code == 200


def test_fishing_hatch(client):
    resp = client.get("/api/v1/sites/mckenzie/fishing/hatch")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "taxon_name" in data[0]
    assert "month" in data[0]


def test_fishing_conditions(client):
    resp = client.get("/api/v1/sites/deschutes/fishing/conditions")
    assert resp.status_code == 200


def test_river_species_by_mile(client):
    resp = client.get("/api/v1/river/Deschutes%20River/species?mile_start=40&mile_end=50")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "taxon_name" in data[0]
    assert "observation_count" in data[0]


def test_species_near_location(client):
    resp = client.get("/api/v1/species/near?lat=44.125&lon=-122.471&radius_km=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "common_name" in data[0]


def test_swim_safety(client):
    resp = client.get("/api/v1/sites/deschutes/swim-safety")
    assert resp.status_code == 200


def test_ecological_summary(client):
    resp = client.post("/api/v1/sites/mckenzie/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["watershed"] == "mckenzie"
    assert "data" in data
    assert "species_trends" in data["data"]


def test_forecast(client):
    resp = client.post("/api/v1/sites/mckenzie/forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert data["watershed"] == "mckenzie"
    assert "data" in data
    assert "restoration_outcomes" in data["data"]


def test_report_json(client):
    resp = client.post("/api/v1/sites/mckenzie/report",
                       json={"date_start": "2023-01-01", "date_end": "2025-12-31", "format": "json"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["watershed"] == "mckenzie"
    assert len(data["species_summary"]) > 0
    assert len(data["indicator_species"]) > 0


def test_report_markdown(client):
    resp = client.post("/api/v1/sites/mckenzie/report",
                       json={"date_start": "2023-01-01", "date_end": "2025-12-31", "format": "markdown"})
    assert resp.status_code == 200
    assert "# McKenzie River" in resp.text
    assert "Species Richness" in resp.text
    assert "Indicator Species" in resp.text
