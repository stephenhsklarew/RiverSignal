"""Health check endpoint.

Two routes:

  /health      Cheap connectivity probe used by the Cloud Run startup +
               liveness probes. Returns 200 if the DB connection pool is
               reachable. Must stay sub-100ms or Cloud Run will reap the
               container — historically this endpoint also ran
               `SELECT count(*) FROM observations`, which is a sequential
               scan over 1.7M+ rows and was dominating prod cold-start.
               That count is now exposed via /health/details (separate
               endpoint, never hit by probes).

  /health/details   Diagnostic endpoint with observation + materialized
                    view counts. Use this manually; never wire it into
                    a probe.

Tracked in bead RiverSignal-7ea2ac57.
"""

from fastapi import APIRouter
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Cheap connectivity check for Cloud Run probes.

    Returns 200 if the DB pool can hand out a connection that responds
    to `SELECT 1`. No table scans, no metadata queries — must be
    sub-100ms so the liveness probe (default timeout 1s, bumped to 5s
    on 2026-05-16) doesn't reap the container under DB-connection load.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    return {"status": "healthy", "database": "connected"}


@router.get("/health/details")
def health_details():
    """Diagnostic counts. Slower — do NOT wire into Cloud Run probes."""
    try:
        with engine.connect() as conn:
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
