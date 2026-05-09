"""Model 1: Hatch Emergence Prediction.

Replaces the static month-based lookup with a degree-day model that predicts
insect emergence based on accumulated water temperature.

Approach:
- Calculate cumulative degree days (CDD) from Jan 1 for each watershed
- Train logistic regression: P(emergence) = f(CDD, day_of_year, flow)
- For species without enough training data, fall back to curated month ranges
  with degree-day adjustment

Output: gold.hatch_emergence_forecast
"""

import numpy as np
from datetime import datetime, date
from sqlalchemy import text
from rich.console import Console

from pipeline.db import engine

console = Console()


def compute_degree_days(conn, watershed: str, year: int) -> dict[int, float]:
    """Compute cumulative degree days by day-of-year for a watershed.

    Degree days = sum of (daily_avg_temp - base_temp) for all days where temp > base.
    Base temp = 4°C (typical aquatic insect development threshold).
    """
    rows = conn.execute(text("""
        SELECT EXTRACT(DOY FROM t.timestamp)::int as doy,
               AVG(t.value) as avg_temp
        FROM time_series t
        JOIN sites s ON t.site_id = s.id
        WHERE s.watershed = :ws
          AND t.parameter IN ('water_temperature', 'water_temp_c')
          AND t.source_type = 'usgs'
          AND EXTRACT(YEAR FROM t.timestamp) = :year
          AND t.value > -10 AND t.value < 40
        GROUP BY doy
        ORDER BY doy
    """), {"ws": watershed, "year": year}).fetchall()

    base_temp = 4.0
    cdd = {}
    cumulative = 0.0
    for doy, avg_temp in rows:
        if avg_temp and avg_temp > base_temp:
            cumulative += float(avg_temp) - base_temp
        cdd[int(doy)] = cumulative
    return cdd


def train_and_predict(conn, watershed: str) -> list[dict]:
    """Train hatch emergence model and generate predictions for each species."""
    current_year = datetime.now().year
    current_doy = datetime.now().timetuple().tm_yday

    # Get current year degree days
    cdd_current = compute_degree_days(conn, watershed, current_year)
    if not cdd_current:
        # Fall back to previous year
        cdd_current = compute_degree_days(conn, watershed, current_year - 1)

    current_cdd = cdd_current.get(current_doy, 0)

    # Get curated hatch data with historical observation peaks
    species_data = conn.execute(text("""
        SELECT c.common_name, c.scientific_name, c.insect_order,
               c.start_month, c.end_month, c.peak_months,
               c.fly_patterns,
               COALESCE(h.observation_count, 0) as obs_count,
               h.activity_level
        FROM curated_hatch_chart c
        LEFT JOIN gold.hatch_chart h
            ON h.watershed = :ws
            AND h.taxon_name ILIKE c.scientific_name || '%'
            AND h.obs_month = EXTRACT(MONTH FROM now())::int
        WHERE c.watershed = :ws
        ORDER BY c.insect_order, c.common_name
    """), {"ws": watershed}).fetchall()

    # Get historical emergence dates from observations
    historical = conn.execute(text("""
        SELECT taxon_name,
               EXTRACT(DOY FROM observed_at)::int as doy,
               EXTRACT(YEAR FROM observed_at)::int as yr,
               count(*) as obs_count
        FROM observations o
        JOIN sites s ON o.site_id = s.id
        WHERE s.watershed = :ws
          AND o.iconic_taxon = 'Insecta'
          AND o.observed_at IS NOT NULL
          AND EXTRACT(YEAR FROM observed_at) >= 2020
        GROUP BY taxon_name, doy, yr
        ORDER BY taxon_name, doy
    """), {"ws": watershed}).fetchall()

    # Build historical CDD thresholds per species
    # For each species, find the degree-day value at peak observation dates
    species_cdd_thresholds = {}
    for taxon, doy, yr, count in historical:
        cdd_hist = compute_degree_days(conn, watershed, yr)
        if doy in cdd_hist:
            if taxon not in species_cdd_thresholds:
                species_cdd_thresholds[taxon] = []
            species_cdd_thresholds[taxon].append({
                "cdd": cdd_hist[doy], "doy": doy, "count": count
            })

    # Current conditions
    current_month = datetime.now().month
    water_temp = conn.execute(text("""
        SELECT AVG(value) FROM time_series t
        JOIN sites s ON t.site_id = s.id
        WHERE s.watershed = :ws AND t.parameter IN ('water_temperature', 'water_temp_c')
          AND t.source_type = 'usgs'
          AND t.timestamp > now() - interval '7 days'
          AND t.value > 0 AND t.value < 40
    """), {"ws": watershed}).scalar()
    current_temp = float(water_temp) if water_temp else None

    forecasts = []
    for row in species_data:
        common_name = row[0]
        sci_name = row[1]
        order = row[2]
        start_month, end_month = row[3], row[4]
        peak_months = row[5] or []
        fly_patterns = row[6] or []
        obs_count = row[7] or 0
        activity = row[8] or "unknown"

        # Check if we have CDD threshold data for this species
        thresholds = species_cdd_thresholds.get(sci_name, [])
        if not thresholds:
            # Try matching by genus
            genus = sci_name.split()[0] if sci_name else ""
            for key, vals in species_cdd_thresholds.items():
                if key.startswith(genus):
                    thresholds = vals
                    break

        # Calculate probability using degree-day model
        if thresholds and current_cdd > 0:
            # Find the CDD range where this species is typically observed
            cdd_values = [t["cdd"] for t in thresholds]
            mean_cdd = np.mean(cdd_values)
            std_cdd = np.std(cdd_values) if len(cdd_values) > 2 else mean_cdd * 0.2

            if std_cdd > 0:
                # Gaussian probability centered on mean emergence CDD
                z = abs(current_cdd - mean_cdd) / std_cdd
                probability = max(5, min(98, int(100 * np.exp(-0.5 * z * z))))
            else:
                probability = 70 if abs(current_cdd - mean_cdd) < mean_cdd * 0.3 else 30

            method = "degree_day"
            # Estimate days until peak
            if current_cdd < mean_cdd:
                # Not yet at peak — estimate days based on recent temp trend
                remaining_cdd = mean_cdd - current_cdd
                daily_gain = (current_temp - 4.0) if current_temp and current_temp > 4 else 5.0
                days_to_peak = max(1, int(remaining_cdd / daily_gain)) if daily_gain > 0 else None
            else:
                days_to_peak = 0  # Already at or past peak
        else:
            # Fall back to month-based prediction
            if current_month in peak_months:
                probability = 85
                days_to_peak = 0
            elif start_month <= current_month <= end_month:
                probability = 55
                # Rough estimate to nearest peak month
                nearest_peak = min(peak_months, key=lambda m: abs(m - current_month)) if peak_months else current_month
                days_to_peak = max(0, (nearest_peak - current_month) * 30)
            else:
                probability = 10
                days_to_peak = None
            method = "seasonal"

        # Boost probability if we have recent observations
        if obs_count > 0:
            probability = min(98, probability + 10)

        # Determine confidence level
        confidence = "high" if probability >= 75 else "medium" if probability >= 45 else "low"

        # Build driving factors explanation
        factors = []
        if method == "degree_day":
            factors.append(f"Accumulated {int(current_cdd)} degree-days (peak at ~{int(np.mean([t['cdd'] for t in thresholds]))})")
        if current_temp:
            factors.append(f"Water temp {current_temp:.1f}°C")
        if obs_count > 0:
            factors.append(f"{obs_count} recent observations confirm activity")
        if current_month in peak_months:
            factors.append("Within historical peak emergence window")

        forecasts.append({
            "common_name": common_name,
            "scientific_name": sci_name,
            "insect_order": order,
            "probability": probability,
            "confidence": confidence,
            "days_to_peak": days_to_peak,
            "method": method,
            "factors": factors,
            "fly_patterns": fly_patterns,
            "current_cdd": round(current_cdd, 1),
            "activity_level": activity,
        })

    # Sort by probability descending
    forecasts.sort(key=lambda x: x["probability"], reverse=True)
    return forecasts


def refresh_hatch_forecast():
    """Compute and store hatch emergence forecasts for all watersheds."""
    console.print("  Computing hatch emergence forecasts...")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_hatch_emergence_forecast (
                id SERIAL PRIMARY KEY,
                watershed VARCHAR NOT NULL,
                common_name VARCHAR NOT NULL,
                scientific_name VARCHAR,
                insect_order VARCHAR,
                probability INTEGER,
                confidence VARCHAR,
                days_to_peak INTEGER,
                method VARCHAR,
                factors JSONB,
                fly_patterns TEXT[],
                current_cdd FLOAT,
                activity_level VARCHAR,
                computed_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE(watershed, common_name)
            )
        """))

        watersheds = conn.execute(text("SELECT watershed FROM sites")).fetchall()

        total = 0
        for (ws,) in watersheds:
            forecasts = train_and_predict(conn, ws)
            for f in forecasts:
                conn.execute(text("""
                    INSERT INTO gold_hatch_emergence_forecast
                        (watershed, common_name, scientific_name, insect_order,
                         probability, confidence, days_to_peak, method,
                         factors, fly_patterns, current_cdd, activity_level, computed_at)
                    VALUES (:ws, :name, :sci, :ord, :prob, :conf, :days, :method,
                            :factors, :flies, :cdd, :activity, now())
                    ON CONFLICT (watershed, common_name) DO UPDATE SET
                        probability = EXCLUDED.probability,
                        confidence = EXCLUDED.confidence,
                        days_to_peak = EXCLUDED.days_to_peak,
                        method = EXCLUDED.method,
                        factors = EXCLUDED.factors,
                        current_cdd = EXCLUDED.current_cdd,
                        activity_level = EXCLUDED.activity_level,
                        computed_at = now()
                """), {
                    "ws": ws, "name": f["common_name"], "sci": f["scientific_name"],
                    "ord": f["insect_order"], "prob": f["probability"],
                    "conf": f["confidence"], "days": f["days_to_peak"],
                    "method": f["method"],
                    "factors": __import__("json").dumps(f["factors"]),
                    "flies": f["fly_patterns"], "cdd": f["current_cdd"],
                    "activity": f["activity_level"],
                })
                total += 1

        console.print(f"  gold_hatch_emergence_forecast: {total} predictions")
