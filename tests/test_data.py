"""Data layer tests: verify gold layer views return expected data."""

from pipeline.db import engine
from sqlalchemy import text


def _query(sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).fetchall()


def test_bronze_has_data():
    for table in ["observations", "time_series", "interventions", "sites"]:
        rows = _query(f"SELECT count(*) FROM {table}")
        assert rows[0][0] > 0, f"{table} is empty"


def test_silver_species_observations():
    rows = _query("SELECT count(*) FROM silver.species_observations")
    assert rows[0][0] > 400000


def test_silver_water_conditions():
    rows = _query("SELECT count(*) FROM silver.water_conditions")
    assert rows[0][0] > 1000000


def test_silver_has_common_names():
    rows = _query("SELECT count(*) FROM silver.species_observations WHERE common_name IS NOT NULL")
    assert rows[0][0] > 100000, "iNaturalist enrichment not applied"


def test_gold_watershed_scorecard():
    rows = _query("SELECT watershed, total_species FROM gold.watershed_scorecard ORDER BY total_species DESC")
    assert len(rows) == 5
    assert rows[0][1] > 5000  # McKenzie or Deschutes should have 5000+ species


def test_gold_species_gallery_has_photos():
    rows = _query("SELECT count(*) FROM gold.species_gallery WHERE photo_url IS NOT NULL")
    assert rows[0][0] > 10000, "Photo backfill not complete"


def test_gold_species_by_river_mile():
    rows = _query("""
        SELECT count(*) FROM gold.species_by_river_mile
        WHERE river_name = 'Deschutes River' AND mile_section_start = 40
    """)
    assert rows[0][0] > 10


def test_gold_indicator_species():
    rows = _query("SELECT count(*) FROM gold.indicator_species_status WHERE status = 'detected'")
    assert rows[0][0] > 20


def test_gold_invasive_detections():
    rows = _query("SELECT count(*) FROM gold.invasive_detections")
    assert rows[0][0] > 10


def test_gold_post_fire_recovery():
    rows = _query("""
        SELECT fire_name, species_total_watershed
        FROM gold.post_fire_recovery
        WHERE fire_name = 'HOLIDAY FARM' AND years_since_fire = 5
    """)
    assert len(rows) > 0
    assert rows[0][1] > 3000, "McKenzie should have 3000+ species 5 years after Holiday Farm Fire"


def test_gold_hatch_chart():
    rows = _query("SELECT count(*) FROM gold.hatch_chart WHERE watershed = 'mckenzie'")
    assert rows[0][0] > 100


def test_gold_stocking_schedule():
    rows = _query("SELECT count(*) FROM gold.stocking_schedule")
    assert rows[0][0] > 100


def test_gold_harvest_trends():
    rows = _query("SELECT count(*) FROM gold.harvest_trends WHERE species = 'steelhead'")
    assert rows[0][0] > 0


def test_spatial_stream_flowlines():
    rows = _query("SELECT count(*) FROM stream_flowlines WHERE gnis_name = 'Deschutes River'")
    assert rows[0][0] > 100


def test_spatial_fire_perimeters():
    rows = _query("SELECT count(*) FROM fire_perimeters WHERE fire_name = 'HOLIDAY FARM'")
    assert rows[0][0] > 0


def test_river_miles_exist():
    rows = _query("SELECT max(segment_end_mile) FROM gold.river_miles WHERE river_name = 'Deschutes River'")
    assert rows[0][0] > 100, "Deschutes should be 100+ river miles"


# ── Geology data tests ──

def test_geologic_units_loaded():
    rows = _query("SELECT count(*) FROM geologic_units")
    assert rows[0][0] >= 300, "Should have 300+ geologic unit polygons"


def test_geologic_units_have_geometry():
    rows = _query("SELECT count(*) FROM geologic_units WHERE geometry IS NOT NULL")
    total = _query("SELECT count(*) FROM geologic_units")[0][0]
    assert rows[0][0] == total, "All geologic units should have geometry"


def test_fossil_occurrences_loaded():
    rows = _query("SELECT count(*) FROM fossil_occurrences")
    assert rows[0][0] >= 600, "Should have 600+ fossil occurrences (John Day + others)"


def test_fossil_john_day_coverage():
    rows = _query("""
        SELECT count(*) FROM fossil_occurrences
        WHERE latitude BETWEEN 44.15 AND 45.05
          AND longitude BETWEEN -119.9 AND -118.4
    """)
    assert rows[0][0] >= 500, "John Day basin should have 500+ fossils"


def test_land_ownership_loaded():
    rows = _query("SELECT count(*) FROM land_ownership")
    assert rows[0][0] >= 30, "Should have 30+ land ownership records"


def test_land_ownership_agencies():
    rows = _query("SELECT DISTINCT agency FROM land_ownership ORDER BY agency")
    agencies = {r[0] for r in rows}
    assert "BLM" in agencies, "Should have BLM lands"
    assert "USFS" in agencies, "Should have USFS lands"
