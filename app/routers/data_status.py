"""Data freshness endpoints: when pipelines last ran, layer status."""

from fastapi import APIRouter
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["data-status"])


@router.get("/data-status")
def get_data_status():
    """Get pipeline sync status, record counts, and layer inventory."""
    with engine.connect() as conn:
        # Pipeline sync status
        pipelines = conn.execute(text("""
            SELECT source_type,
                   max(completed_at) as last_sync,
                   count(*) as total_jobs,
                   count(CASE WHEN status = 'completed' THEN 1 END) as completed,
                   count(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM ingestion_jobs
            GROUP BY source_type
            ORDER BY max(completed_at) DESC NULLS LAST
        """)).fetchall()

        most_recent = conn.execute(text(
            "SELECT max(completed_at) FROM ingestion_jobs WHERE status = 'completed'"
        )).scalar()
        oldest = conn.execute(text(
            "SELECT min(max_sync) FROM (SELECT source_type, max(completed_at) as max_sync FROM ingestion_jobs WHERE status = 'completed' GROUP BY source_type) sub"
        )).scalar()

        # Bronze record counts
        bronze_obs = conn.execute(text("SELECT count(*) FROM observations")).scalar()
        bronze_ts = conn.execute(text("SELECT count(*) FROM time_series")).scalar()
        bronze_int = conn.execute(text("SELECT count(*) FROM interventions")).scalar()

        # View count summary
        view_counts = conn.execute(text("""
            SELECT schemaname, count(*)
            FROM pg_matviews WHERE schemaname IN ('silver', 'gold')
            GROUP BY schemaname ORDER BY schemaname
        """)).fetchall()

        # Bronze table inventory
        bronze_tables = {}
        for tbl in ['observations', 'time_series', 'interventions', 'fire_perimeters',
                    'stream_flowlines', 'impaired_waters', 'wetlands', 'watershed_boundaries',
                    'geologic_units', 'fossil_occurrences', 'mineral_deposits', 'land_ownership',
                    'recreation_sites', 'curated_hatch_chart', 'deep_time_stories']:
            try:
                bronze_tables[tbl] = conn.execute(text(f"SELECT count(*) FROM {tbl}")).scalar()
            except Exception:
                conn.rollback()
                bronze_tables[tbl] = 0

        # Silver/Gold view inventory with counts
        silver_views = {}
        gold_views = {}
        mv_rows = conn.execute(text(
            "SELECT schemaname, matviewname FROM pg_matviews WHERE schemaname IN ('silver','gold') ORDER BY schemaname, matviewname"
        )).fetchall()
        for r in mv_rows:
            try:
                cnt = conn.execute(text(f"SELECT count(*) FROM {r[0]}.{r[1]}")).scalar()
            except Exception:
                conn.rollback()
                cnt = 0
            if r[0] == 'silver':
                silver_views[r[1]] = cnt
            else:
                gold_views[r[1]] = cnt

        # Curated data sources (manually created, not from public APIs)
        curated = []
        try:
            fly_count = conn.execute(text("SELECT count(*) FROM silver.insect_fly_patterns")).scalar()
            curated.append({
                "name": "Insect-to-Fly Pattern Mapping",
                "table": "silver.insect_fly_patterns",
                "records": fly_count,
                "description": "Aquatic insects mapped to fly fishing patterns with hook sizes, fly types, photos, seasons, and fishing tips",
                "source": "Hand-curated from fly fishing literature",
            })
        except Exception:
            conn.rollback()

        try:
            shop_count = conn.execute(text("SELECT count(*) FROM fly_shops_guides")).scalar()
            curated.append({
                "name": "Fly Shops & Guide Services",
                "table": "fly_shops_guides",
                "records": shop_count,
                "description": "Oregon fly shops and guide services with contact info, websites, and coordinates per watershed",
                "source": "Hand-curated from web research (verified businesses)",
            })
        except Exception:
            conn.rollback()

        try:
            mineral_shop_count = conn.execute(text("SELECT count(*) FROM mineral_shops")).scalar()
            curated.append({
                "name": "Mineral & Rock Shops",
                "table": "mineral_shops",
                "records": mineral_shop_count,
                "description": "Oregon mineral shops, rock ranches, and paleontology museums with contact info and coordinates",
                "source": "Hand-curated from web research (verified businesses)",
            })
        except Exception:
            conn.rollback()

        # Fossil common names
        fossil_common = conn.execute(text(
            "SELECT count(*) FROM fossil_occurrences WHERE common_name IS NOT NULL AND common_name != ''"
        )).scalar()
        curated.append({
            "name": "Fossil Common Names",
            "table": "fossil_occurrences.common_name",
            "records": fossil_common,
            "description": "Latin genus/species names mapped to English common names (e.g., Mesohippus → Three-toed Horse)",
            "source": "Hand-curated lookup table (~60 genera)",
        })

        # Mineral commodity code expansion
        mineral_expanded = conn.execute(text(
            "SELECT count(*) FROM mineral_deposits WHERE commodity NOT SIMILAR TO '%[A-Z]{2,}%'"
        )).scalar()
        curated.append({
            "name": "Mineral Commodity Names",
            "table": "mineral_deposits.commodity",
            "records": mineral_expanded,
            "description": "MRDS abbreviations expanded to human-readable names (SDG → Sand & Gravel, PGE_PT → Platinum)",
            "source": "Hand-curated code-to-name mapping (~16 codes)",
        })

        # Fly tying videos
        try:
            video_count = conn.execute(text("SELECT count(*) FROM fly_tying_videos")).scalar()
            curated.append({
                "name": "Fly Tying Videos",
                "table": "fly_tying_videos",
                "records": video_count,
                "description": "YouTube fly tying tutorial links for each fly pattern — opens in new tab from Hatch Intelligence",
                "source": "Curated from Tightline Productions, InTheRiffle, Tim Flagler, Davie McPhail",
            })
        except Exception:
            conn.rollback()

        # Curated hatch chart
        try:
            hatch_count = conn.execute(text("SELECT count(*) FROM curated_hatch_chart")).scalar()
            curated.append({
                "name": "Expert Hatch Chart",
                "table": "curated_hatch_chart",
                "records": hatch_count,
                "description": "Month-by-month aquatic insect emergence timing with fly pattern recommendations for 5 Oregon watersheds",
                "source": "Compiled from Western Hatches, The Caddis Fly Shop, Westfly.com, The Fly Fisher's Place",
            })
        except Exception:
            conn.rollback()

    return {
        "bronze": {
            "observations": bronze_obs,
            "time_series": bronze_ts,
            "interventions": bronze_int,
            "most_recent_sync": most_recent.isoformat() if most_recent else None,
            "oldest_pipeline_sync": oldest.isoformat() if oldest else None,
            "tables": bronze_tables,
        },
        "silver": {
            "views": next((r[1] for r in view_counts if r[0] == 'silver'), 0),
            "tables": silver_views,
        },
        "gold": {
            "views": next((r[1] for r in view_counts if r[0] == 'gold'), 0),
            "tables": gold_views,
        },
        "curated": curated,
        "pipelines": [
            {
                "source": r[0],
                "last_sync": r[1].isoformat() if r[1] else None,
                "total_jobs": r[2],
                "completed": r[3],
                "failed": r[4],
            }
            for r in pipelines
        ],
    }
