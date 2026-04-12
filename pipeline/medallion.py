"""Medallion architecture: Silver and Gold layer management.

Silver Layer (cleaned, standardized):
- silver.species_observations -- unified species data across all sources
- silver.water_conditions -- standardized water/climate time series
- silver.interventions_enriched -- clean intervention records

Gold Layer (business aggregates):
- gold.site_ecological_summary -- species richness per watershed per year
- gold.species_trends -- year-over-year biodiversity changes
- gold.water_quality_monthly -- monthly water quality by station
- gold.invasive_detections -- invasive species tracker with trends
- gold.fishing_conditions -- angler-relevant conditions per month
- gold.restoration_outcomes -- before/after species at intervention sites
- gold.watershed_scorecard -- cross-watershed comparison metrics
- gold.anomaly_flags -- temperature/DO exceedance alerts
- gold.seasonal_observation_patterns -- survey timing windows by taxonomic group
- gold.indicator_species_status -- checklist-based presence/absence tracker
- gold.species_by_reach -- ODFW fish distribution by stream name
- gold.stocking_schedule -- upcoming/recent stocking events
- gold.harvest_trends -- year-over-year sport catch with delta
- gold.post_fire_recovery -- species trajectory pre/post fire events
- gold.cold_water_refuges -- thermal classification of stream stations
"""

from sqlalchemy import text

from pipeline.db import engine

VIEWS = [
    # Silver — ecology
    "silver.species_observations",
    "silver.water_conditions",
    "silver.interventions_enriched",
    # Silver — geology
    "silver.geologic_context",
    "silver.fossil_records",
    "silver.land_access",
    "silver.mineral_sites",
    # Gold — ecology
    "gold.site_ecological_summary",
    "gold.species_trends",
    "gold.water_quality_monthly",
    "gold.invasive_detections",
    "gold.fishing_conditions",
    "gold.restoration_outcomes",
    "gold.watershed_scorecard",
    "gold.anomaly_flags",
    "gold.seasonal_observation_patterns",
    "gold.indicator_species_status",
    "gold.species_by_reach",
    "gold.stocking_schedule",
    "gold.harvest_trends",
    "gold.post_fire_recovery",
    "gold.cold_water_refuges",
    "gold.river_miles",
    "gold.species_gallery",
    "gold.species_by_river_mile",
    "gold.river_health_score",
    "gold.whats_alive_now",
    "gold.hatch_chart",
    "gold.river_story_timeline",
    "gold.swim_safety",
    "gold.stewardship_opportunities",
    # Gold — geology
    "gold.geologic_age_at_location",
    "gold.fossils_nearby",
    "gold.legal_collecting_sites",
    "gold.deep_time_story",
    "gold.formation_species_history",
    "gold.geology_watershed_link",
    "gold.mineral_sites_nearby",
]


def refresh_all():
    """Refresh all materialized views. Recreates any that don't exist."""
    with engine.connect() as conn:
        missing = False
        for view in VIEWS:
            try:
                conn.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
                count = conn.execute(text(f"SELECT count(*) FROM {view}")).scalar()
                print(f"  {view:45s}: {count:>10,} rows")
            except Exception:
                conn.rollback()
                missing = True
                print(f"  {view:45s}:    MISSING -- run: python -m pipeline.medallion_ddl")
        conn.commit()
        if missing:
            print("\n  Some views are missing. Recreating all...")
            conn.close()
            from pipeline.medallion_ddl import create_all
            create_all()
            # Now refresh
            with engine.connect() as conn2:
                for view in VIEWS:
                    try:
                        count = conn2.execute(text(f"SELECT count(*) FROM {view}")).scalar()
                        print(f"  {view:45s}: {count:>10,} rows")
                    except Exception:
                        print(f"  {view:45s}:    ERROR")
                        conn2.rollback()
