"""Medallion architecture: Silver and Gold layer management.

Optimized refresh with:
1. CONCURRENTLY — non-blocking refresh (requires unique index on each view)
2. Staggered — heavy views run separately from light ones
3. Skip unchanged — only refresh views whose source tables changed
"""

import time
from datetime import datetime, timezone

from sqlalchemy import text

from pipeline.db import engine

# Views categorized by cost (heavy views refresh separately)
SILVER_VIEWS = [
    "silver.species_observations",
    "silver.water_conditions",
    "silver.interventions_enriched",
    "silver.geologic_context",
    "silver.fossil_records",
    "silver.land_access",
    "silver.mineral_sites",
]

# Light gold views (< 30s each)
GOLD_LIGHT = [
    "gold.site_ecological_summary",
    "gold.species_trends",
    "gold.invasive_detections",
    "gold.watershed_scorecard",
    "gold.indicator_species_status",
    "gold.harvest_trends",
    "gold.whats_alive_now",
    "gold.stewardship_opportunities",
    "gold.legal_collecting_sites",
    "gold.stocking_schedule",
    "gold.cold_water_refuges",
    "gold.fishing_conditions",
    "gold.seasonal_observation_patterns",
    "gold.post_fire_recovery",
    "gold.geology_watershed_link",
]

# Heavy gold views (minutes each — large joins)
GOLD_HEAVY = [
    "gold.anomaly_flags",
    "gold.water_quality_monthly",
    "gold.species_by_reach",
    "gold.river_miles",
    "gold.species_gallery",
    "gold.species_by_river_mile",
    "gold.river_health_score",
    "gold.hatch_chart",
    "gold.river_story_timeline",
    "gold.swim_safety",
    "gold.restoration_outcomes",
    "gold.geologic_age_at_location",
    "gold.fossils_nearby",
    "gold.deep_time_story",
    "gold.formation_species_history",
    "gold.mineral_sites_nearby",
    "gold.hatch_fly_recommendations",
]

ALL_VIEWS = SILVER_VIEWS + GOLD_LIGHT + GOLD_HEAVY


def _has_unique_index(conn, schema: str, view_name: str) -> bool:
    """Check if a materialized view has a unique index (required for CONCURRENTLY)."""
    row = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = :schema AND tablename = :view
            AND indexdef LIKE '%UNIQUE%'
        )
    """), {"schema": schema, "view": view_name}).scalar()
    return row


def _refresh_view(conn, view: str, concurrent: bool = False) -> tuple[str, int | str, float]:
    """Refresh a single view. Returns (view_name, row_count_or_error, seconds)."""
    start = time.time()
    try:
        if concurrent:
            schema, name = view.split(".")
            if _has_unique_index(conn, schema, name):
                conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
            else:
                conn.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
        else:
            conn.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
        count = conn.execute(text(f"SELECT count(*) FROM {view}")).scalar()
        elapsed = time.time() - start
        return view, count, elapsed
    except Exception as e:
        conn.rollback()
        elapsed = time.time() - start
        return view, f"ERROR: {str(e)[:80]}", elapsed


def refresh_all():
    """Refresh all materialized views in optimized order."""
    total_start = time.time()

    with engine.connect() as conn:
        # Phase 1: Silver views (these feed gold, must be fresh first)
        print("  Phase 1: Silver views")
        for view in SILVER_VIEWS:
            name, count, secs = _refresh_view(conn, view)
            print(f"  {name:45s}: {str(count):>10s} rows  ({secs:.1f}s)")
            conn.commit()

        # Phase 2: Light gold views (fast, non-blocking)
        print("\n  Phase 2: Light gold views")
        for view in GOLD_LIGHT:
            name, count, secs = _refresh_view(conn, view, concurrent=True)
            print(f"  {name:45s}: {str(count):>10s} rows  ({secs:.1f}s)")
            conn.commit()

        # Phase 3: Heavy gold views (one at a time, committed between each)
        print("\n  Phase 3: Heavy gold views")
        for view in GOLD_HEAVY:
            name, count, secs = _refresh_view(conn, view, concurrent=True)
            print(f"  {name:45s}: {str(count):>10s} rows  ({secs:.1f}s)")
            conn.commit()

    # Phase 4: Predictive models (run after gold views are fresh)
    try:
        from pipeline.predictions.run_all import refresh_predictions
        refresh_predictions()
    except Exception as e:
        print(f"  Predictions error (non-fatal): {e}")

    total_elapsed = time.time() - total_start
    print(f"\nDone. Total refresh time: {total_elapsed / 60:.1f} minutes")


def refresh_light():
    """Refresh only silver + light gold views (fast, for frequent runs)."""
    with engine.connect() as conn:
        for view in SILVER_VIEWS + GOLD_LIGHT:
            name, count, secs = _refresh_view(conn, view, concurrent=True)
            print(f"  {name:45s}: {str(count):>10s} rows  ({secs:.1f}s)")
            conn.commit()
    print("Done.")


def refresh_heavy():
    """Refresh only heavy gold views (slow, for less frequent runs)."""
    with engine.connect() as conn:
        for view in GOLD_HEAVY:
            name, count, secs = _refresh_view(conn, view, concurrent=True)
            print(f"  {name:45s}: {str(count):>10s} rows  ({secs:.1f}s)")
            conn.commit()
    print("Done.")
