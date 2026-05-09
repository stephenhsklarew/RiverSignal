"""Model 5: Restoration Impact Prediction.

Predicts expected species recovery for different intervention types
and estimates recovery timelines based on historical outcomes.

Approach:
- Train regression model on historical restoration outcomes
- Features: intervention type, pre-intervention species count,
  watershed, years since fire, distance to refuge
- Predict species gain and recovery timeline for each intervention type

Output: gold_restoration_forecast
"""

import json
import numpy as np
from sqlalchemy import text
from rich.console import Console

from pipeline.db import engine

console = Console()


def _train_intervention_model(conn) -> dict:
    """Build intervention effectiveness model from historical data."""
    rows = conn.execute(text("""
        SELECT watershed, intervention_category,
               species_before, species_after,
               intervention_count, intervention_year
        FROM gold.restoration_outcomes
        WHERE species_before IS NOT NULL AND species_after IS NOT NULL
          AND species_before > 0 AND species_after > 0
    """)).fetchall()

    if not rows:
        return {}

    # Group by intervention type and compute average effectiveness
    type_stats = {}
    for ws, category, before, after, count, year in rows:
        if category not in type_stats:
            type_stats[category] = {
                "gains": [], "ratios": [], "before_counts": [],
                "watersheds": set(), "years": [],
            }
        gain = after - before
        ratio = after / before if before > 0 else 1.0
        type_stats[category]["gains"].append(gain)
        type_stats[category]["ratios"].append(ratio)
        type_stats[category]["before_counts"].append(before)
        type_stats[category]["watersheds"].add(ws)
        type_stats[category]["years"].append(year)

    # Compute model parameters per intervention type
    models = {}
    for category, stats in type_stats.items():
        gains = np.array(stats["gains"])
        ratios = np.array(stats["ratios"])
        n = len(gains)

        models[category] = {
            "avg_species_gain": round(float(np.mean(gains)), 1),
            "median_species_gain": round(float(np.median(gains)), 1),
            "avg_recovery_ratio": round(float(np.mean(ratios)), 2),
            "std_gain": round(float(np.std(gains)), 1) if n > 2 else 0,
            "success_rate": round(float(np.mean(gains > 0)) * 100, 1),
            "sample_size": n,
            "watersheds": len(stats["watersheds"]),
            "avg_before": round(float(np.mean(stats["before_counts"])), 0),
        }

    return models


def _estimate_recovery_timeline(conn, watershed: str) -> dict | None:
    """Estimate recovery trajectory from fire recovery data."""
    rows = conn.execute(text("""
        SELECT fire_name, fire_year, observation_year, species_total_watershed
        FROM gold.post_fire_recovery
        WHERE watershed = :ws
        ORDER BY fire_year DESC, observation_year
    """), {"ws": watershed}).fetchall()

    if len(rows) < 3:
        return None

    # Group by fire
    fires = {}
    for fire_name, fire_year, obs_year, species in rows:
        if fire_name not in fires:
            fires[fire_name] = {"year": fire_year, "trajectory": []}
        fires[fire_name]["trajectory"].append({
            "year": obs_year,
            "years_since": obs_year - fire_year,
            "species": species,
        })

    # Analyze the most recent fire with enough data
    for fire_name, data in fires.items():
        trajectory = data["trajectory"]
        if len(trajectory) < 3:
            continue

        trajectory.sort(key=lambda x: x["years_since"])

        # Find species count at fire time and latest
        at_fire = [t for t in trajectory if t["years_since"] == 0]
        pre_fire = [t for t in trajectory if t["years_since"] < 0]
        post_fire = [t for t in trajectory if t["years_since"] > 0]

        if not post_fire:
            continue

        baseline = pre_fire[-1]["species"] if pre_fire else (at_fire[0]["species"] if at_fire else post_fire[0]["species"])
        current = post_fire[-1]["species"]
        recovery_pct = (current / baseline * 100) if baseline > 0 else 0

        # Linear regression on post-fire recovery
        if len(post_fire) >= 2:
            x = np.array([t["years_since"] for t in post_fire])
            y = np.array([t["species"] for t in post_fire])
            slope, _ = np.polyfit(x, y, 1)
            species_per_year = round(float(slope), 1)

            # Estimate years to full recovery
            if slope > 0 and current < baseline:
                years_to_full = round((baseline - current) / slope, 1)
            else:
                years_to_full = 0
        else:
            species_per_year = 0
            years_to_full = None

        return {
            "fire_name": fire_name,
            "fire_year": data["year"],
            "baseline_species": baseline,
            "current_species": current,
            "recovery_pct": round(recovery_pct, 1),
            "species_per_year": species_per_year,
            "years_to_full_recovery": years_to_full,
            "years_tracked": int(post_fire[-1]["years_since"]),
        }

    return None


def refresh_restoration_forecast():
    """Compute restoration impact predictions for all watersheds."""
    console.print("  Computing restoration impact predictions...")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_restoration_forecast (
                id SERIAL PRIMARY KEY,
                watershed VARCHAR NOT NULL,
                intervention_type VARCHAR NOT NULL,
                predicted_species_gain FLOAT,
                recovery_ratio FLOAT,
                success_rate FLOAT,
                confidence VARCHAR,
                sample_size INTEGER,
                fire_recovery JSONB,
                cost_effectiveness_rank INTEGER,
                computed_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE(watershed, intervention_type)
            )
        """))

        # Train model on all data
        models = _train_intervention_model(conn)

        watersheds = conn.execute(text("SELECT watershed FROM sites")).fetchall()
        total = 0

        for (ws,) in watersheds:
            fire_recovery = _estimate_recovery_timeline(conn, ws)

            # Rank intervention types by effectiveness
            ranked = sorted(models.items(), key=lambda x: x[1]["avg_species_gain"], reverse=True)

            for rank, (intervention_type, model) in enumerate(ranked, 1):
                confidence = "high" if model["sample_size"] >= 10 else "medium" if model["sample_size"] >= 5 else "low"

                conn.execute(text("""
                    INSERT INTO gold_restoration_forecast
                        (watershed, intervention_type, predicted_species_gain,
                         recovery_ratio, success_rate, confidence, sample_size,
                         fire_recovery, cost_effectiveness_rank, computed_at)
                    VALUES (:ws, :type, :gain, :ratio, :success, :conf, :n,
                            :fire, :rank, now())
                    ON CONFLICT (watershed, intervention_type) DO UPDATE SET
                        predicted_species_gain = EXCLUDED.predicted_species_gain,
                        recovery_ratio = EXCLUDED.recovery_ratio,
                        success_rate = EXCLUDED.success_rate,
                        confidence = EXCLUDED.confidence,
                        fire_recovery = EXCLUDED.fire_recovery,
                        cost_effectiveness_rank = EXCLUDED.cost_effectiveness_rank,
                        computed_at = now()
                """), {
                    "ws": ws, "type": intervention_type,
                    "gain": model["avg_species_gain"],
                    "ratio": model["avg_recovery_ratio"],
                    "success": model["success_rate"],
                    "conf": confidence, "n": model["sample_size"],
                    "fire": json.dumps(fire_recovery) if fire_recovery else None,
                    "rank": rank,
                })
                total += 1

        console.print(f"  gold_restoration_forecast: {total} predictions")
