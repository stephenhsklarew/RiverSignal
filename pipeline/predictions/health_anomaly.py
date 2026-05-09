"""Model 3: River Health Anomaly Detection.

Replaces the 3-line if/else health score with statistical anomaly detection
that identifies unusual patterns and predicts emerging problems.

Approach:
- Compute z-scores against historical monthly baselines
- Detect trend shifts (consecutive months of decline)
- Flag compound anomalies (multiple parameters deviating simultaneously)

Output: gold_health_anomaly
"""

import json
import numpy as np
from datetime import datetime
from sqlalchemy import text
from rich.console import Console

from pipeline.db import engine

console = Console()


def _compute_baselines(conn, watershed: str) -> dict:
    """Compute historical monthly baselines (mean + std) for key parameters."""
    rows = conn.execute(text("""
        SELECT parameter,
               EXTRACT(MONTH FROM timestamp)::int as month,
               AVG(value) as mean_val,
               STDDEV(value) as std_val,
               COUNT(*) as n
        FROM time_series t
        JOIN sites s ON t.site_id = s.id
        WHERE s.watershed = :ws
          AND parameter IN ('water_temperature', 'water_temp_c', 'dissolved_oxygen',
                           'discharge', 'discharge_cfs')
          AND source_type = 'usgs'
          AND value IS NOT NULL
          AND EXTRACT(YEAR FROM timestamp) >= 2020
        GROUP BY parameter, month
        HAVING COUNT(*) >= 10
        ORDER BY parameter, month
    """), {"ws": watershed}).fetchall()

    baselines = {}
    for param, month, mean, std, n in rows:
        # Normalize parameter names
        norm_param = param
        if param in ('water_temp_c', 'water_temperature'):
            norm_param = 'temperature'
        elif param in ('discharge', 'discharge_cfs'):
            norm_param = 'flow'
        elif param == 'dissolved_oxygen':
            norm_param = 'do'

        if norm_param not in baselines:
            baselines[norm_param] = {}
        baselines[norm_param][int(month)] = {
            "mean": float(mean), "std": float(std) if std else 1.0, "n": int(n)
        }
    return baselines


def _get_recent_values(conn, watershed: str) -> dict:
    """Get recent 30-day values for anomaly detection."""
    rows = conn.execute(text("""
        SELECT parameter, AVG(value) as avg_val, MIN(value) as min_val, MAX(value) as max_val
        FROM time_series t
        JOIN sites s ON t.site_id = s.id
        WHERE s.watershed = :ws
          AND parameter IN ('water_temperature', 'water_temp_c', 'dissolved_oxygen',
                           'discharge', 'discharge_cfs')
          AND source_type = 'usgs'
          AND timestamp > now() - interval '30 days'
          AND value IS NOT NULL
        GROUP BY parameter
    """), {"ws": watershed}).fetchall()

    recent = {}
    for param, avg, mn, mx in rows:
        norm = param
        if param in ('water_temp_c', 'water_temperature'):
            norm = 'temperature'
        elif param in ('discharge', 'discharge_cfs'):
            norm = 'flow'
        elif param == 'dissolved_oxygen':
            norm = 'do'
        recent[norm] = {"avg": float(avg), "min": float(mn), "max": float(mx)}
    return recent


def _detect_species_trend(conn, watershed: str) -> dict | None:
    """Detect species richness trend over recent months."""
    rows = conn.execute(text("""
        SELECT obs_year, obs_month, count(DISTINCT taxon_name) as species
        FROM silver.species_observations
        WHERE watershed = :ws AND taxon_name IS NOT NULL
          AND obs_year >= EXTRACT(YEAR FROM now())::int - 1
        GROUP BY obs_year, obs_month
        ORDER BY obs_year, obs_month
    """), {"ws": watershed}).fetchall()

    if len(rows) < 3:
        return None

    counts = [r[2] for r in rows]
    # Check for consecutive decline
    declining = 0
    for i in range(1, len(counts)):
        if counts[i] < counts[i - 1]:
            declining += 1
        else:
            declining = 0

    if declining >= 3:
        return {
            "trend": "declining",
            "months": declining,
            "current": counts[-1],
            "previous": counts[-declining - 1],
            "change_pct": round(100 * (counts[-1] - counts[-declining - 1]) / counts[-declining - 1], 1) if counts[-declining - 1] > 0 else 0,
        }
    return None


def analyze_watershed(conn, watershed: str) -> dict:
    """Run full anomaly analysis for a watershed."""
    baselines = _compute_baselines(conn, watershed)
    recent = _get_recent_values(conn, watershed)
    current_month = datetime.now().month

    anomalies = []
    health_score = 70  # start at baseline
    param_scores = {}

    for param in ['temperature', 'do', 'flow']:
        if param not in recent or param not in baselines:
            continue
        if current_month not in baselines[param]:
            continue

        baseline = baselines[param][current_month]
        current_val = recent[param]["avg"]
        z_score = (current_val - baseline["mean"]) / baseline["std"] if baseline["std"] > 0 else 0

        # Classify anomaly
        severity = None
        if abs(z_score) > 3:
            severity = "critical"
        elif abs(z_score) > 2:
            severity = "warning"
        elif abs(z_score) > 1.5:
            severity = "watch"

        direction = "above" if z_score > 0 else "below"

        # Impact on health score
        if param == "temperature":
            if current_val < 16:
                param_scores["temp"] = 20
            elif current_val < 20:
                param_scores["temp"] = 10
            else:
                param_scores["temp"] = 0
                if severity is None:
                    severity = "warning"

        elif param == "do":
            if current_val > 8:
                param_scores["do"] = 20
            elif current_val > 6:
                param_scores["do"] = 10
            else:
                param_scores["do"] = 0
                if severity is None:
                    severity = "warning"

        elif param == "flow":
            param_scores["flow"] = 10  # neutral

        if severity:
            anomalies.append({
                "parameter": param,
                "current_value": round(current_val, 2),
                "baseline_mean": round(baseline["mean"], 2),
                "baseline_std": round(baseline["std"], 2),
                "z_score": round(z_score, 2),
                "severity": severity,
                "direction": direction,
                "description": f"{param.title()} is {abs(z_score):.1f} standard deviations {direction} the historical mean for {datetime.now().strftime('%B')}",
            })

    # Compute health score
    health_score = 30 + param_scores.get("temp", 10) + param_scores.get("do", 10) + param_scores.get("flow", 10)

    # Species trend analysis
    species_trend = _detect_species_trend(conn, watershed)
    if species_trend and species_trend["trend"] == "declining":
        anomalies.append({
            "parameter": "species_richness",
            "current_value": species_trend["current"],
            "baseline_mean": species_trend["previous"],
            "z_score": None,
            "severity": "warning" if species_trend["months"] >= 4 else "watch",
            "direction": "declining",
            "description": f"Species richness has declined {species_trend['months']} consecutive months ({species_trend['change_pct']}%)",
        })
        health_score -= 5

    # Compound anomaly detection
    critical_count = sum(1 for a in anomalies if a["severity"] == "critical")
    warning_count = sum(1 for a in anomalies if a["severity"] == "warning")
    if critical_count >= 2:
        health_score -= 15
    elif warning_count >= 2:
        health_score -= 5

    health_score = max(10, min(100, health_score))
    health_level = "good" if health_score >= 70 else "moderate" if health_score >= 50 else "poor"

    return {
        "health_score": health_score,
        "health_level": health_level,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "species_trend": species_trend,
        "recent_conditions": {k: round(v["avg"], 2) for k, v in recent.items()},
    }


def refresh_health_anomaly():
    """Compute health anomaly analysis for all watersheds."""
    console.print("  Computing river health anomaly detection...")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_health_anomaly (
                id SERIAL PRIMARY KEY,
                watershed VARCHAR NOT NULL UNIQUE,
                health_score INTEGER,
                health_level VARCHAR,
                anomaly_count INTEGER,
                anomalies JSONB,
                species_trend JSONB,
                recent_conditions JSONB,
                computed_at TIMESTAMPTZ DEFAULT now()
            )
        """))

        watersheds = conn.execute(text("SELECT watershed FROM sites")).fetchall()
        total = 0

        for (ws,) in watersheds:
            result = analyze_watershed(conn, ws)
            conn.execute(text("""
                INSERT INTO gold_health_anomaly
                    (watershed, health_score, health_level, anomaly_count,
                     anomalies, species_trend, recent_conditions, computed_at)
                VALUES (:ws, :score, :level, :count, :anomalies, :trend, :conditions, now())
                ON CONFLICT (watershed) DO UPDATE SET
                    health_score = EXCLUDED.health_score,
                    health_level = EXCLUDED.health_level,
                    anomaly_count = EXCLUDED.anomaly_count,
                    anomalies = EXCLUDED.anomalies,
                    species_trend = EXCLUDED.species_trend,
                    recent_conditions = EXCLUDED.recent_conditions,
                    computed_at = now()
            """), {
                "ws": ws, "score": result["health_score"],
                "level": result["health_level"],
                "count": result["anomaly_count"],
                "anomalies": json.dumps(result["anomalies"]),
                "trend": json.dumps(result["species_trend"]),
                "conditions": json.dumps(result["recent_conditions"]),
            })
            total += 1

        console.print(f"  gold_health_anomaly: {total} watersheds analyzed")
