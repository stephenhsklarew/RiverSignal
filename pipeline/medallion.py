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
"""

from sqlalchemy import text

from pipeline.db import engine

VIEWS = [
    "silver.species_observations",
    "silver.water_conditions",
    "silver.interventions_enriched",
    "gold.site_ecological_summary",
    "gold.species_trends",
    "gold.water_quality_monthly",
    "gold.invasive_detections",
    "gold.fishing_conditions",
    "gold.restoration_outcomes",
    "gold.watershed_scorecard",
    "gold.anomaly_flags",
]


def refresh_all():
    """Refresh all materialized views in dependency order."""
    with engine.connect() as conn:
        for view in VIEWS:
            conn.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
            count = conn.execute(text(f"SELECT count(*) FROM {view}")).scalar()
            print(f"  {view:45s}: {count:>10,} rows")
        conn.commit()
