"""Create or recreate all Silver and Gold materialized views.

This script extracts view definitions from the database if they exist,
or creates them from scratch using the canonical SQL definitions.

Usage:
    python -m pipeline.medallion_ddl          # Create all views
    python -m pipeline.medallion_ddl --dump    # Dump current definitions to SQL file

The canonical source of truth for view definitions is the database itself.
When views are modified via ad-hoc SQL, run --dump to capture the changes,
then commit the dumped SQL.
"""

import sys
from sqlalchemy import text
from pipeline.db import engine

# Dependency-ordered list of all views (dependents after their dependencies)
VIEW_ORDER = [
    # Silver — ecology (no dependencies on gold)
    "silver.species_observations",
    "silver.water_conditions",
    "silver.interventions_enriched",
    # Silver — geology (depend on bronze geology tables)
    "silver.geologic_context",
    "silver.fossil_records",
    "silver.land_access",
    # Gold: independent views (depend only on bronze or silver)
    "gold.anomaly_flags",
    "gold.cold_water_refuges",
    "gold.fishing_conditions",
    "gold.harvest_trends",
    "gold.invasive_detections",
    "gold.post_fire_recovery",
    "gold.restoration_outcomes",
    "gold.river_miles",
    "gold.seasonal_observation_patterns",
    "gold.site_ecological_summary",
    "gold.species_by_reach",
    "gold.species_trends",
    "gold.stocking_schedule",
    "gold.stewardship_opportunities",
    "gold.water_quality_monthly",
    "gold.watershed_scorecard",
    "gold.indicator_species_status",
    "gold.river_health_score",
    "gold.whats_alive_now",
    "gold.swim_safety",
    "gold.river_story_timeline",
    # Gold — ecology: views that depend on other gold views
    "gold.species_gallery",    # independent (reads bronze directly)
    "gold.hatch_chart",        # depends on species_gallery
    "gold.species_by_river_mile",  # depends on river_miles + species_gallery
    # Gold — geology (depend on silver geology views)
    "gold.geologic_age_at_location",  # depends on silver.geologic_context
    "gold.fossils_nearby",            # depends on silver.fossil_records
    "gold.legal_collecting_sites",    # depends on silver.land_access
    "gold.deep_time_story",           # depends on silver.geologic_context + silver.fossil_records
    "gold.formation_species_history", # depends on silver.geologic_context + silver.fossil_records
    "gold.geology_watershed_link",    # depends on silver.geologic_context + sites
]


def dump_definitions(output_file: str = "medallion_views.sql"):
    """Dump all current view definitions to a SQL file."""
    with engine.connect() as conn:
        with open(output_file, "w") as f:
            f.write("-- Medallion Architecture View Definitions\n")
            f.write(f"-- Exported from database, {len(VIEW_ORDER)} views\n")
            f.write("-- Re-run: python -m pipeline.medallion_ddl\n\n")
            f.write("CREATE SCHEMA IF NOT EXISTS silver;\n")
            f.write("CREATE SCHEMA IF NOT EXISTS gold;\n\n")

            for view_name in VIEW_ORDER:
                f.write(f"-- {view_name}\n")
                f.write(f"DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;\n")
                try:
                    defn = conn.execute(text(
                        f"SELECT pg_get_viewdef('{view_name}'::regclass, true)"
                    )).scalar()
                    f.write(f"CREATE MATERIALIZED VIEW {view_name} AS\n{defn};\n\n")
                except Exception:
                    f.write(f"-- VIEW NOT FOUND IN DATABASE\n\n")

    print(f"Dumped {len(VIEW_ORDER)} view definitions to {output_file}")


def create_all():
    """Recreate all views from the SQL dump file, or from database definitions."""
    import os

    sql_file = os.path.join(os.path.dirname(__file__), "..", "medallion_views.sql")
    if os.path.exists(sql_file):
        print(f"Creating views from {sql_file}...")
        with open(sql_file) as f:
            sql = f.read()
        with engine.connect() as conn:
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if stmt and not stmt.startswith("--"):
                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        if "already exists" not in str(e):
                            print(f"  Warning: {str(e)[:80]}")
        print("All materialized views created.")
    else:
        print(f"No {sql_file} found. Run: python -m pipeline.medallion_ddl --dump")
        print("Then: python -m pipeline.medallion_ddl")


if __name__ == "__main__":
    if "--dump" in sys.argv:
        output = sys.argv[sys.argv.index("--dump") + 1] if len(sys.argv) > sys.argv.index("--dump") + 1 else "medallion_views.sql"
        dump_definitions(output)
    else:
        create_all()
