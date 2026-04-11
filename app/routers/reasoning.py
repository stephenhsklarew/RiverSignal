"""Ecological reasoning endpoints: summaries, forecasts, recommendations."""

import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from pipeline.db import engine
from pipeline.tools import (
    get_indicator_status,
    get_post_fire_recovery,
    get_river_story,
    get_species_near_me,
)

router = APIRouter(tags=["reasoning"])


class ForecastRequest(BaseModel):
    horizon_months: int = 6


class SummaryRequest(BaseModel):
    date_start: str | None = None
    date_end: str | None = None


class ChatRequest(BaseModel):
    question: str


@router.post("/sites/{watershed}/summary")
def generate_ecological_summary(watershed: str, request: SummaryRequest = None):
    """Generate an AI-powered ecological summary for a watershed.

    Uses the hybrid pre-aggregation + LLM reasoning approach (AD-2):
    1. Pre-aggregate data from gold layer views
    2. Pass structured context to Claude with tool access
    3. Return structured summary with citations
    """
    with engine.connect() as conn:
        site = conn.execute(text(
            "SELECT id FROM sites WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{watershed}' not found")

        # Pre-aggregate from gold layer
        health = conn.execute(text("""
            SELECT health_score, avg_water_temp, avg_do, monthly_species, obs_year, obs_month
            FROM gold.river_health_score WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """), {"ws": watershed}).fetchone()

        species_trend = conn.execute(text("""
            SELECT obs_year, species_count, species_delta
            FROM gold.species_trends WHERE watershed = :ws
            ORDER BY obs_year DESC LIMIT 3
        """), {"ws": watershed}).fetchall()

        invasives = conn.execute(text("""
            SELECT taxon_name, detection_count, last_detected, recent_detections
            FROM gold.invasive_detections WHERE watershed = :ws
            ORDER BY recent_detections DESC
        """), {"ws": watershed}).fetchall()

        anomalies = conn.execute(text("""
            SELECT anomaly_type, count(*), max(detected_date)::date
            FROM gold.anomaly_flags WHERE watershed = :ws
            GROUP BY anomaly_type
        """), {"ws": watershed}).fetchall()

        indicators = get_indicator_status(watershed)
        fire_recovery = get_post_fire_recovery(watershed)

    # Build context for LLM
    context = {
        "watershed": watershed,
        "health_score": health[0] if health else None,
        "water_temp_c": float(health[1]) if health and health[1] else None,
        "dissolved_oxygen": float(health[2]) if health and health[2] else None,
        "species_this_month": health[3] if health else None,
        "species_trends": [{"year": r[0], "species": r[1], "delta": r[2]} for r in species_trend],
        "invasive_species": [{"name": r[0], "detections": r[1], "last_seen": str(r[2]), "recent": r[3]} for r in invasives],
        "anomalies": [{"type": r[0], "count": r[1], "last": str(r[2])} for r in anomalies],
        "indicators": indicators[:10],
        "fire_recovery": fire_recovery[:10] if fire_recovery else [],
    }

    # Try LLM reasoning if API key available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system="You are an ecological reasoning assistant for the RiverSignal watershed intelligence platform. Given pre-aggregated data about a watershed, produce a concise ecological summary. Include species richness trends, water quality status, invasive species alerts, indicator species presence, and any fire recovery context. Cite specific numbers. Be specific and actionable.",
                messages=[{"role": "user", "content": f"Generate an ecological summary for the {watershed} watershed based on this data:\n\n{json.dumps(context, indent=2, default=str)}"}],
            )
            narrative = message.content[0].text
        except Exception as e:
            narrative = f"LLM reasoning unavailable: {e}. Raw data summary below."
    else:
        narrative = None

    return {
        "watershed": watershed,
        "generated_at": datetime.now().isoformat(),
        "narrative": narrative,
        "data": context,
    }


@router.post("/sites/{watershed}/forecast")
def generate_restoration_forecast(watershed: str, request: ForecastRequest = None):
    """Generate a restoration forecast for a watershed (FEAT-002).

    Predicts expected species returns and habitat changes based on
    intervention history, current conditions, and ecological succession models.
    """
    horizon = request.horizon_months if request else 6

    with engine.connect() as conn:
        site = conn.execute(text("SELECT id FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{watershed}' not found")

        # Restoration outcomes (before/after species at intervention sites)
        outcomes = conn.execute(text("""
            SELECT intervention_category, intervention_year, intervention_count,
                   species_before, species_after
            FROM gold.restoration_outcomes WHERE watershed = :ws
            ORDER BY intervention_year DESC
        """), {"ws": watershed}).fetchall()

        # Current species trend
        trends = conn.execute(text("""
            SELECT obs_year, species_count, species_delta
            FROM gold.species_trends WHERE watershed = :ws
            ORDER BY obs_year DESC LIMIT 5
        """), {"ws": watershed}).fetchall()

        # Fire recovery (if applicable)
        fire = conn.execute(text("""
            SELECT fire_name, fire_year, acres, observation_year, years_since_fire, species_total_watershed
            FROM gold.post_fire_recovery WHERE watershed = :ws AND acres > 1000
            ORDER BY fire_year DESC, observation_year DESC LIMIT 10
        """), {"ws": watershed}).fetchall()

        # Cold water refuges
        refuges = conn.execute(text("""
            SELECT station_id, thermal_classification, summer_avg_temp
            FROM gold.cold_water_refuges WHERE watershed = :ws
            ORDER BY obs_year DESC LIMIT 10
        """), {"ws": watershed}).fetchall()

    context = {
        "watershed": watershed,
        "horizon_months": horizon,
        "restoration_outcomes": [
            {"category": r[0], "year": r[1], "count": r[2], "species_before": r[3], "species_after": r[4]}
            for r in outcomes
        ],
        "species_trends": [{"year": r[0], "count": r[1], "delta": r[2]} for r in trends],
        "fire_recovery": [
            {"fire": r[0], "fire_year": r[1], "acres": r[2], "obs_year": r[3], "years_since": r[4], "species": r[5]}
            for r in fire
        ],
        "cold_water_refuges": [
            {"station": r[0], "classification": r[1], "temp": float(r[2]) if r[2] else None}
            for r in refuges
        ],
    }

    # LLM forecast if available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    narrative = None
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system="You are an ecological forecasting assistant. Given restoration history, species trends, fire recovery data, and thermal conditions, predict what ecological changes to expect in the next 3-12 months. Be specific: name expected species returns, habitat improvements, and risk factors. Assign confidence (high/medium/low) to each prediction.",
                messages=[{"role": "user", "content": f"Generate a restoration forecast for the {watershed} watershed:\n\n{json.dumps(context, indent=2, default=str)}"}],
            )
            narrative = message.content[0].text
        except Exception as e:
            narrative = f"LLM forecasting unavailable: {e}"

    return {
        "watershed": watershed,
        "horizon_months": horizon,
        "generated_at": datetime.now().isoformat(),
        "narrative": narrative,
        "data": context,
    }


@router.post("/sites/{watershed}/chat")
def chat_with_site(watershed: str, request: ChatRequest):
    """Natural-language query about a watershed."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY not configured")

    # Get site context
    with engine.connect() as conn:
        site = conn.execute(text(
            "SELECT id, name FROM sites WHERE watershed = :ws"
        ), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{watershed}' not found")

    # Build tool-call context from gold layer
    story = get_river_story("", watershed)
    indicators = get_indicator_status(watershed)

    context = json.dumps({
        "watershed": watershed,
        "name": site[1],
        "story": story,
        "indicators": indicators,
    }, default=str)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=f"You are a river ecology assistant. Answer questions about the {site[1]} watershed using this context:\n\n{context}\n\nBe specific, cite data, and suggest actions when appropriate. If the question is not about this watershed's ecology, politely redirect.",
        messages=[{"role": "user", "content": request.question}],
    )

    return {
        "watershed": watershed,
        "question": request.question,
        "answer": message.content[0].text,
    }


@router.get("/species/near")
def species_near_location(lat: float, lon: float, radius_km: float = 2.0):
    """Get species with photos near a GPS location (RiverPath)."""
    return get_species_near_me(lat, lon, radius_km)
