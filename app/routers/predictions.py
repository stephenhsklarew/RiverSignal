"""Predictive analytics endpoints: generate, list, track, score predictions."""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["predictions"])


class PredictionRequest(BaseModel):
    prediction_type: str  # species_return, fire_recovery, thermal_forecast, invasive_spread
    intervention_type: str | None = None
    intervention_scale: str | None = None
    horizon_months: int = 12
    scenario: str = "with_intervention"


# ── List predictions ──
@router.get("/sites/{watershed}/predictions")
def list_predictions(watershed: str):
    """List all predictions for a watershed."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, prediction_type, intervention_type, horizon_months, scenario,
                   overall_confidence, confidence_level, status,
                   generated_at, check_date, accuracy_score
            FROM predictions
            WHERE watershed = :ws
            ORDER BY generated_at DESC
            LIMIT 50
        """), {"ws": watershed}).fetchall()

    # Overall accuracy
    with engine.connect() as conn:
        acc = conn.execute(text("""
            SELECT count(*) FILTER (WHERE status = 'resolved') as resolved,
                   avg(accuracy_score) FILTER (WHERE accuracy_score IS NOT NULL) as avg_accuracy,
                   count(*) FILTER (WHERE status = 'resolved' AND accuracy_score >= 70) as confirmed
            FROM predictions WHERE watershed = :ws
        """), {"ws": watershed}).fetchone()

    return {
        "watershed": watershed,
        "total": len(rows),
        "accuracy_summary": {
            "resolved": acc[0] if acc else 0,
            "avg_accuracy": round(acc[1], 1) if acc and acc[1] else None,
            "confirmed": acc[2] if acc else 0,
        },
        "predictions": [{
            "id": str(r[0]),
            "type": r[1],
            "intervention": r[2],
            "horizon_months": r[3],
            "scenario": r[4],
            "confidence": r[5],
            "confidence_level": r[6],
            "status": r[7],
            "generated_at": str(r[8]),
            "check_date": str(r[9]) if r[9] else None,
            "accuracy": r[10],
        } for r in rows],
    }


# ── Get single prediction ──
@router.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: str):
    """Get full prediction details."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT id, watershed, prediction_type, intervention_type, intervention_scale,
                   horizon_months, scenario, parameters,
                   overall_confidence, confidence_level,
                   predictions_json, risk_factors_json, scenario_comparison,
                   narrative, status, check_date, generated_at,
                   accuracy_score, actuals_json
            FROM predictions WHERE id = :id
        """), {"id": prediction_id}).fetchone()

    if not r:
        raise HTTPException(404, "Prediction not found")

    return {
        "id": str(r[0]), "watershed": r[1], "type": r[2],
        "intervention": r[3], "scale": r[4],
        "horizon_months": r[5], "scenario": r[6], "parameters": r[7],
        "confidence": r[8], "confidence_level": r[9],
        "predictions": r[10], "risk_factors": r[11],
        "scenario_comparison": r[12], "narrative": r[13],
        "status": r[14], "check_date": str(r[15]) if r[15] else None,
        "generated_at": str(r[16]),
        "accuracy": r[17], "actuals": r[18],
    }


# ── Generate prediction ──
@router.post("/sites/{watershed}/predictions")
def generate_prediction(watershed: str, req: PredictionRequest):
    """Generate a new prediction using statistical models + LLM narrative."""

    with engine.connect() as conn:
        site = conn.execute(text("SELECT id, name FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{watershed}' not found")

        # ── Gather context data ──
        # Restoration outcomes (for species_return)
        outcomes = conn.execute(text("""
            SELECT intervention_category, intervention_year, intervention_count,
                   species_before, species_after
            FROM gold.restoration_outcomes WHERE watershed = :ws
            ORDER BY intervention_year DESC LIMIT 20
        """), {"ws": watershed}).fetchall()

        # Species trends
        trends = conn.execute(text("""
            SELECT obs_year, species_count, species_delta
            FROM gold.species_trends WHERE watershed = :ws
            ORDER BY obs_year DESC LIMIT 5
        """), {"ws": watershed}).fetchall()

        # Fire recovery (for fire_recovery type)
        fire = conn.execute(text("""
            SELECT fire_name, fire_year, acres, observation_year, years_since_fire, species_total_watershed
            FROM gold.post_fire_recovery WHERE watershed = :ws AND acres > 500
            ORDER BY fire_year DESC, observation_year DESC LIMIT 20
        """), {"ws": watershed}).fetchall()

        # Thermal data (for thermal_forecast)
        thermal = conn.execute(text("""
            SELECT station_id, thermal_classification, summer_avg_temp
            FROM gold.cold_water_refuges WHERE watershed = :ws
            ORDER BY obs_year DESC LIMIT 20
        """), {"ws": watershed}).fetchall()

        # Invasive detections (for invasive_spread)
        invasives = conn.execute(text("""
            SELECT taxon_name, detection_count, last_detected, recent_detections
            FROM gold.invasive_detections WHERE watershed = :ws
            ORDER BY recent_detections DESC LIMIT 10
        """), {"ws": watershed}).fetchall()

        # Current conditions
        health = conn.execute(text("""
            SELECT health_score, avg_water_temp, avg_do, monthly_species
            FROM gold.river_health_score WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """), {"ws": watershed}).fetchone()

    # ── Build statistical context ──
    context = {
        "watershed": watershed,
        "site_name": site[1],
        "prediction_type": req.prediction_type,
        "intervention_type": req.intervention_type,
        "intervention_scale": req.intervention_scale,
        "horizon_months": req.horizon_months,
        "scenario": req.scenario,
        "restoration_outcomes": [
            {"category": r[0], "year": r[1], "count": r[2], "species_before": r[3], "species_after": r[4]}
            for r in outcomes
        ],
        "species_trends": [{"year": r[0], "count": r[1], "delta": r[2]} for r in trends],
        "fire_recovery": [
            {"fire": r[0], "fire_year": r[1], "acres": r[2], "obs_year": r[3], "years_since": r[4], "species": r[5]}
            for r in fire
        ],
        "thermal_stations": [
            {"station": r[0], "classification": r[1], "temp": float(r[2]) if r[2] else None}
            for r in thermal
        ],
        "invasive_species": [
            {"name": r[0], "detections": r[1], "last_seen": str(r[2]), "recent": r[3]}
            for r in invasives
        ],
        "current_health": {
            "score": health[0] if health else None,
            "water_temp_c": float(health[1]) if health and health[1] else None,
            "do_mg_l": float(health[2]) if health and health[2] else None,
            "species": health[3] if health else None,
        } if health else None,
    }

    # ── Simple statistical estimates ──
    stats = _compute_statistical_predictions(context)

    # ── LLM prediction narrative ──
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    narrative = None
    predictions_json = stats.get("predictions", [])
    risk_factors = stats.get("risk_factors", [])
    scenario_comparison = stats.get("scenario_comparison")
    overall_confidence = stats.get("overall_confidence", 50)
    confidence_level = "HIGH" if overall_confidence >= 75 else "MEDIUM" if overall_confidence >= 50 else "LOW"

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            type_prompts = {
                "species_return": "Predict which species will return and when, based on prior restoration outcomes at similar sites.",
                "fire_recovery": "Predict the recovery trajectory based on post-fire species data and years-since-fire patterns.",
                "thermal_forecast": "Predict summer thermal conditions and cold-water refuge viability based on temperature trends.",
                "invasive_spread": "Predict invasive species spread risk based on detection patterns and river network connectivity.",
            }

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=f"""You are a restoration ecologist generating a data-driven prediction.

{type_prompts.get(req.prediction_type, 'Generate an ecological prediction.')}

Return a JSON object with:
- "predictions": array of {{"species": "name", "prediction": "description", "confidence": 0-100, "evidence": "citation"}}
- "risk_factors": array of {{"risk": "description", "severity": "high/medium/low", "mitigation": "action"}}
- "scenario_comparison": {{"with_intervention": {{"species_delta": N, "key_metric": "..."}}, "baseline": {{"species_delta": N, "key_metric": "..."}}}}
- "narrative": 2-3 paragraph summary for the watershed manager
- "overall_confidence": number 0-100

Return ONLY valid JSON.""",
                messages=[{"role": "user", "content": f"Generate a {req.prediction_type} prediction for {watershed}:\n\n{json.dumps(context, indent=2, default=str)}"}],
            )

            raw = message.content[0].text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3].strip()
                elif "```" in raw:
                    raw = raw[:raw.rfind("```")].strip()
            try:
                parsed = json.loads(raw)
                predictions_json = parsed.get("predictions", predictions_json)
                risk_factors = parsed.get("risk_factors", risk_factors)
                scenario_comparison = parsed.get("scenario_comparison", scenario_comparison)
                narrative = parsed.get("narrative", raw)
                overall_confidence = parsed.get("overall_confidence", overall_confidence)
                confidence_level = "HIGH" if overall_confidence >= 75 else "MEDIUM" if overall_confidence >= 50 else "LOW"
            except json.JSONDecodeError:
                narrative = raw
        except Exception as e:
            narrative = f"Statistical prediction only (LLM unavailable): {e}"

    # ── Store prediction ──
    pred_id = uuid.uuid4()
    check_date = datetime.now(timezone.utc) + timedelta(days=req.horizon_months * 30)

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO predictions (id, watershed, prediction_type, intervention_type, intervention_scale,
                horizon_months, scenario, parameters, overall_confidence, confidence_level,
                predictions_json, risk_factors_json, scenario_comparison, narrative, model_version,
                status, check_date)
            VALUES (:id, :ws, :type, :intervention, :scale, :horizon, :scenario,
                CAST(:params AS jsonb), :conf, :conf_level,
                CAST(:preds AS jsonb), CAST(:risks AS jsonb), CAST(:comparison AS jsonb),
                :narrative, :model, 'active', :check_date)
        """), {
            "id": pred_id, "ws": watershed, "type": req.prediction_type,
            "intervention": req.intervention_type, "scale": req.intervention_scale,
            "horizon": req.horizon_months, "scenario": req.scenario,
            "params": json.dumps(context, default=str),
            "conf": overall_confidence, "conf_level": confidence_level,
            "preds": json.dumps(predictions_json), "risks": json.dumps(risk_factors),
            "comparison": json.dumps(scenario_comparison) if scenario_comparison else None,
            "narrative": narrative, "model": "claude-sonnet-4+stats",
            "check_date": check_date,
        })
        conn.commit()

    return {
        "id": str(pred_id),
        "watershed": watershed,
        "type": req.prediction_type,
        "confidence": overall_confidence,
        "confidence_level": confidence_level,
        "predictions": predictions_json,
        "risk_factors": risk_factors,
        "scenario_comparison": scenario_comparison,
        "narrative": narrative,
        "check_date": str(check_date.date()),
        "status": "active",
    }


def _compute_statistical_predictions(ctx: dict) -> dict:
    """Simple statistical estimates based on available data."""
    ptype = ctx.get("prediction_type", "")
    preds = []
    risks = []
    comparison = None
    confidence = 50

    if ptype == "species_return":
        outcomes = ctx.get("restoration_outcomes", [])
        if outcomes:
            # Average species gain from prior restorations
            gains = [o["species_after"] - o["species_before"] for o in outcomes
                     if o.get("species_after") and o.get("species_before")]
            if gains:
                avg_gain = sum(gains) / len(gains)
                confidence = min(85, 50 + len(gains) * 3)
                preds.append({
                    "species": "Overall species richness",
                    "prediction": f"+{avg_gain:.0f} species based on {len(gains)} prior restorations",
                    "confidence": confidence,
                    "evidence": f"Average gain of {avg_gain:.0f} species across {len(gains)} interventions",
                })
                comparison = {
                    "with_intervention": {"species_delta": round(avg_gain), "key_metric": f"+{avg_gain:.0f} species"},
                    "baseline": {"species_delta": round(avg_gain * 0.2), "key_metric": f"+{avg_gain * 0.2:.0f} species (natural recovery)"},
                }

    elif ptype == "fire_recovery":
        fire = ctx.get("fire_recovery", [])
        if fire:
            # Fit recovery curve: species count vs years since fire
            latest_fire = fire[0]
            recovery_pts = [(r["years_since"], r["species"]) for r in fire if r.get("years_since") and r.get("species")]
            if len(recovery_pts) >= 3:
                max_species = max(s for _, s in recovery_pts)
                latest_species = recovery_pts[0][1] if recovery_pts else 0
                pct_recovered = (latest_species / max_species * 100) if max_species > 0 else 0
                confidence = min(80, 40 + len(recovery_pts) * 5)
                preds.append({
                    "species": "Fire recovery trajectory",
                    "prediction": f"Currently at {pct_recovered:.0f}% of peak species richness",
                    "confidence": confidence,
                    "evidence": f"Based on {len(recovery_pts)} observation years post-fire",
                })

    elif ptype == "thermal_forecast":
        thermal = ctx.get("thermal_stations", [])
        if thermal:
            cold = sum(1 for t in thermal if t.get("classification") == "cold_water_refuge")
            warm = sum(1 for t in thermal if t.get("classification") == "thermal_stress")
            confidence = min(75, 50 + len(thermal) * 2)
            preds.append({
                "species": "Thermal classification",
                "prediction": f"{cold} cold-water refuges, {warm} thermal stress zones",
                "confidence": confidence,
                "evidence": f"Based on {len(thermal)} monitoring stations",
            })
            if warm > 0:
                risks.append({
                    "risk": f"{warm} stations in thermal stress zone",
                    "severity": "high" if warm > cold else "medium",
                    "mitigation": "Monitor daily temps during July-August; identify shade restoration opportunities",
                })

    elif ptype == "invasive_spread":
        invasives = ctx.get("invasive_species", [])
        if invasives:
            top = invasives[0]
            confidence = min(70, 40 + top.get("detections", 0))
            preds.append({
                "species": top["name"],
                "prediction": f"{top['detections']} detections, last seen {top['last_seen']}",
                "confidence": confidence,
                "evidence": f"{top.get('recent', 0)} recent detections suggest active spread",
            })
            risks.append({
                "risk": f"{top['name']} spreading along riparian corridor",
                "severity": "high" if top.get("recent", 0) > 5 else "medium",
                "mitigation": "Schedule treatment sweep within 10 days of detection",
            })

    return {
        "predictions": preds,
        "risk_factors": risks,
        "scenario_comparison": comparison,
        "overall_confidence": confidence,
    }
