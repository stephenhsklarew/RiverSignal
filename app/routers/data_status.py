"""Data freshness endpoints: when pipelines last ran, layer status."""

from fastapi import APIRouter
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["data-status"])


@router.get("/data-status")
def get_data_status():
    """Get pipeline sync status and data freshness for all layers."""
    with engine.connect() as conn:
        # Bronze: last sync per pipeline
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

        # Overall freshness
        most_recent = conn.execute(text(
            "SELECT max(completed_at) FROM ingestion_jobs WHERE status = 'completed'"
        )).scalar()
        oldest = conn.execute(text(
            "SELECT min(max_sync) FROM (SELECT source_type, max(completed_at) as max_sync FROM ingestion_jobs WHERE status = 'completed' GROUP BY source_type) sub"
        )).scalar()

        # Record counts per layer
        bronze_obs = conn.execute(text("SELECT count(*) FROM observations")).scalar()
        bronze_ts = conn.execute(text("SELECT count(*) FROM time_series")).scalar()
        bronze_int = conn.execute(text("SELECT count(*) FROM interventions")).scalar()

        # Silver/Gold view counts
        views = conn.execute(text("""
            SELECT schemaname, count(*)
            FROM pg_matviews WHERE schemaname IN ('silver', 'gold')
            GROUP BY schemaname ORDER BY schemaname
        """)).fetchall()

    return {
        "bronze": {
            "observations": bronze_obs,
            "time_series": bronze_ts,
            "interventions": bronze_int,
            "most_recent_sync": most_recent.isoformat() if most_recent else None,
            "oldest_pipeline_sync": oldest.isoformat() if oldest else None,
        },
        "silver": {
            "views": next((r[1] for r in views if r[0] == 'silver'), 0),
        },
        "gold": {
            "views": next((r[1] for r in views if r[0] == 'gold'), 0),
        },
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
