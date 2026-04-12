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

        # Sample recent observations for citations
        recent_obs = conn.execute(text("""
            SELECT source_type, source_id, taxon_name, observed_at::date,
                   data_payload->>'common_name' as common_name
            FROM observations
            WHERE site_id = :sid
            ORDER BY observed_at DESC LIMIT 10
        """), {"sid": site[0]}).fetchall()

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
        "recent_observations": [
            {"source": r[0], "id": r[1], "taxon": r[2], "date": str(r[3]), "common_name": r[4]}
            for r in recent_obs
        ],
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
                system="""You are an ecological reasoning assistant for the RiverSignal watershed intelligence platform. Given pre-aggregated data about a watershed, produce a concise ecological summary.

Include:
1. Species richness trends with specific year-over-year numbers
2. Water quality status (temperature, dissolved oxygen) with values
3. Invasive species alerts with detection counts and dates
4. Indicator species presence/absence with detection numbers
5. Fire recovery context if applicable

IMPORTANT: Cite specific data values (e.g., "Species richness increased from 2,100 to 2,400 species (2024→2025)"). Reference observation counts, detection dates, and measurement values. End with a confidence assessment: HIGH (strong data support), MEDIUM (some gaps), or LOW (limited data).""",
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
                system="""You are an ecological forecasting assistant for restoration professionals. Given restoration history, species trends, fire recovery data, and thermal conditions, predict what ecological changes to expect in the next 3-12 months.

For each prediction, include:
1. **Specific expected change** (name species, habitat metrics, water quality shifts)
2. **Confidence level** (HIGH/MEDIUM/LOW) with brief justification
3. **Evidence basis** — cite the specific data points that support this prediction
4. **Risk factors** that could prevent the predicted outcome

Format as a structured list of 3-5 predictions, each with the fields above. End with an overall forecast confidence assessment.""",
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


@router.post("/sites/{watershed}/recommendations")
def generate_recommendations(watershed: str):
    """Generate prioritized field action recommendations for a watershed (FEAT-003).

    Produces a ranked list of 3-5 recommended actions based on current anomalies,
    seasonal windows, restoration milestones, and invasive follow-up needs.
    """
    with engine.connect() as conn:
        site = conn.execute(text("SELECT id, name FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{watershed}' not found")

        # Anomalies (urgent signals)
        anomalies = conn.execute(text("""
            SELECT anomaly_type, count(*) as cnt, max(detected_date)::date as last
            FROM gold.anomaly_flags WHERE watershed = :ws
            GROUP BY anomaly_type ORDER BY cnt DESC
        """), {"ws": watershed}).fetchall()

        # Invasive detections (treatment urgency)
        invasives = conn.execute(text("""
            SELECT taxon_name, detection_count, last_detected, recent_detections
            FROM gold.invasive_detections WHERE watershed = :ws
            ORDER BY recent_detections DESC LIMIT 5
        """), {"ws": watershed}).fetchall()

        # Restoration outcomes (active projects to monitor)
        outcomes = conn.execute(text("""
            SELECT intervention_category, intervention_year, intervention_count,
                   species_before, species_after
            FROM gold.restoration_outcomes WHERE watershed = :ws
            ORDER BY intervention_year DESC LIMIT 10
        """), {"ws": watershed}).fetchall()

        # Seasonal patterns (what to survey now)
        current_month = datetime.now().month
        seasonal = conn.execute(text("""
            SELECT taxon_group, peak_month, avg_observations
            FROM gold.seasonal_observation_patterns WHERE watershed = :ws
            ORDER BY avg_observations DESC
        """), {"ws": watershed}).fetchall()

        # Indicator species (monitoring gaps)
        indicators = conn.execute(text("""
            SELECT taxon_name, common_name, indicator_direction, status, last_detected
            FROM gold.indicator_species_status WHERE watershed = :ws
        """), {"ws": watershed}).fetchall()

        # Data freshness (stale data warning)
        freshness = conn.execute(text("""
            SELECT source_type, max(last_sync_at)::date as last_sync
            FROM data_sources WHERE site_id = :sid
            GROUP BY source_type ORDER BY last_sync ASC
        """), {"sid": site[0]}).fetchall()

    context = {
        "watershed": watershed,
        "site_name": site[1],
        "current_month": current_month,
        "anomalies": [{"type": r[0], "count": r[1], "last": str(r[2])} for r in anomalies],
        "invasive_species": [
            {"name": r[0], "total_detections": r[1], "last_seen": str(r[2]), "recent": r[3]}
            for r in invasives
        ],
        "restoration_outcomes": [
            {"category": r[0], "year": r[1], "count": r[2], "species_before": r[3], "species_after": r[4]}
            for r in outcomes
        ],
        "seasonal_patterns": [
            {"taxon_group": r[0], "peak_month": r[1], "avg_obs": r[2]}
            for r in seasonal
        ],
        "indicators": [
            {"taxon": r[0], "common_name": r[1], "direction": r[2], "status": r[3],
             "last_detected": str(r[4]) if r[4] else None}
            for r in indicators
        ],
        "data_freshness": [{"source": r[0], "last_sync": str(r[1])} for r in freshness],
    }

    # LLM-powered recommendations
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    recommendations = []
    narrative = None

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system="""You are a watershed management advisor for the RiverSignal platform. Given pre-aggregated ecological data, produce a JSON array of 3-5 prioritized field action recommendations.

Each recommendation must have:
- "rank": integer (1 = highest priority)
- "action": brief action description (e.g., "Invasive reed canarygrass sweep along riparian corridor")
- "site": target location within the watershed
- "time_sensitivity": deadline (e.g., "Within 10 days", "This month", "Next survey window")
- "reasoning": 2-3 sentences connecting this recommendation to specific data (anomalies, seasonal timing, restoration goals, invasive detections)
- "grounded_in": what data type drove this (e.g., "invasive_detection", "seasonal_window", "anomaly", "restoration_milestone")

If no actionable signals exist, return an empty array with a "status" field explaining overall site health.

Return ONLY valid JSON — no markdown fences, no explanation outside the JSON.""",
                messages=[{"role": "user", "content": f"Generate field recommendations for {watershed} watershed:\n\n{json.dumps(context, indent=2, default=str)}"}],
            )
            raw = message.content[0].text.strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    recommendations = parsed
                elif isinstance(parsed, dict) and "recommendations" in parsed:
                    recommendations = parsed["recommendations"]
                else:
                    recommendations = [parsed]
            except json.JSONDecodeError:
                narrative = raw  # LLM returned prose instead of JSON
        except Exception as e:
            narrative = f"LLM reasoning unavailable: {e}"

    return {
        "watershed": watershed,
        "generated_at": datetime.now().isoformat(),
        "recommendations": recommendations,
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
