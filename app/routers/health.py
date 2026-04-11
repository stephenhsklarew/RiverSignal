"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Check API and database connectivity."""
    try:
        with engine.connect() as conn:
            db_ok = conn.execute(text("SELECT 1")).scalar() == 1
            obs_count = conn.execute(text("SELECT count(*) FROM observations")).scalar()
            view_count = conn.execute(text(
                "SELECT count(*) FROM pg_matviews WHERE schemaname IN ('silver','gold')"
            )).scalar()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

    return {
        "status": "healthy",
        "database": "connected",
        "observations": obs_count,
        "materialized_views": view_count,
    }
