"""Model 4: Species Distribution Shift Tracking.

Detects species range shifts by comparing recent observation locations
against historical baselines. Identifies species moving upstream,
new arrivals, and range contractions.

Approach:
- For each species, compute centroid of observations by year
- Detect northward/upstream movement via latitude trend
- Flag new arrivals (first observation in a watershed)
- Estimate range contraction for cold-water specialists based on warming trends

Output: gold_species_distribution_shifts
"""

import json
import numpy as np
from datetime import datetime
from sqlalchemy import text
from rich.console import Console

from pipeline.db import engine

console = Console()


def analyze_species_shifts(conn, watershed: str) -> list[dict]:
    """Analyze species distribution changes in a watershed."""
    # Get species with multi-year observation data
    species_data = conn.execute(text("""
        SELECT taxon_name,
               COALESCE(data_payload->>'common_name', taxon_name) as common_name,
               iconic_taxon,
               EXTRACT(YEAR FROM observed_at)::int as yr,
               AVG(latitude) as avg_lat,
               AVG(longitude) as avg_lon,
               MIN(latitude) as min_lat,
               MAX(latitude) as max_lat,
               COUNT(*) as obs_count
        FROM observations o
        JOIN sites s ON o.site_id = s.id
        WHERE s.watershed = :ws
          AND o.latitude IS NOT NULL
          AND o.observed_at IS NOT NULL
          AND EXTRACT(YEAR FROM observed_at) >= 2018
          AND o.taxon_name IS NOT NULL
        GROUP BY taxon_name, common_name, iconic_taxon, yr
        HAVING COUNT(*) >= 3
        ORDER BY taxon_name, yr
    """), {"ws": watershed}).fetchall()

    # Group by species
    species_years = {}
    for taxon, common, iconic, yr, avg_lat, avg_lon, min_lat, max_lat, count in species_data:
        if taxon not in species_years:
            species_years[taxon] = {"common": common, "iconic": iconic, "years": []}
        species_years[taxon]["years"].append({
            "year": yr, "avg_lat": float(avg_lat), "avg_lon": float(avg_lon),
            "min_lat": float(min_lat), "max_lat": float(max_lat), "count": count,
        })

    shifts = []
    for taxon, data in species_years.items():
        years = data["years"]
        if len(years) < 2:
            continue

        # Sort by year
        years.sort(key=lambda x: x["year"])

        # Compute latitude trend (linear regression)
        x = np.array([y["year"] for y in years])
        y_lat = np.array([y["avg_lat"] for y in years])

        if len(x) >= 3:
            # Linear fit
            slope, intercept = np.polyfit(x, y_lat, 1)
            lat_shift_per_year = slope

            # Significance: is the shift meaningful?
            lat_range = y_lat.max() - y_lat.min()
            total_shift = slope * (x[-1] - x[0])

            # Range change
            early_range = years[0]["max_lat"] - years[0]["min_lat"]
            recent_range = years[-1]["max_lat"] - years[-1]["min_lat"]

            # Observation count trend
            early_count = sum(y["count"] for y in years[:len(years) // 2])
            recent_count = sum(y["count"] for y in years[len(years) // 2:])

            # Classify the shift
            direction = None
            shift_type = None
            confidence = "low"

            if abs(total_shift) > 0.01:  # ~1.1 km
                direction = "northward" if total_shift > 0 else "southward"
                shift_type = "range_shift"
                if abs(total_shift) > 0.05:  # ~5.5 km
                    confidence = "high"
                elif abs(total_shift) > 0.02:
                    confidence = "medium"

            elif recent_range < early_range * 0.7 and early_range > 0.01:
                shift_type = "range_contraction"
                direction = "contracting"
                confidence = "medium" if recent_range < early_range * 0.5 else "low"

            elif recent_range > early_range * 1.3 and early_range > 0:
                shift_type = "range_expansion"
                direction = "expanding"
                confidence = "medium"

            # Detect new arrivals (only observed in recent years)
            if years[0]["year"] >= datetime.now().year - 2 and len(years) <= 2:
                shift_type = "new_arrival"
                direction = "detected"
                confidence = "medium"

            # Population trend
            pop_trend = None
            if recent_count > early_count * 1.5:
                pop_trend = "increasing"
            elif recent_count < early_count * 0.5:
                pop_trend = "declining"

            if shift_type:
                shifts.append({
                    "taxon_name": taxon,
                    "common_name": data["common"],
                    "taxonomic_group": data["iconic"],
                    "shift_type": shift_type,
                    "direction": direction,
                    "lat_shift_per_year": round(lat_shift_per_year, 6),
                    "total_shift_km": round(total_shift * 111, 1),  # degrees to km
                    "years_tracked": int(x[-1] - x[0]),
                    "early_range_km": round(early_range * 111, 1),
                    "recent_range_km": round(recent_range * 111, 1),
                    "population_trend": pop_trend,
                    "confidence": confidence,
                    "observation_count": sum(y["count"] for y in years),
                })

    # Sort by significance
    shifts.sort(key=lambda x: abs(x["total_shift_km"]), reverse=True)
    return shifts


def refresh_species_distribution():
    """Compute species distribution shift analysis for all watersheds."""
    console.print("  Computing species distribution shifts...")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_species_distribution_shifts (
                id SERIAL PRIMARY KEY,
                watershed VARCHAR NOT NULL,
                taxon_name VARCHAR NOT NULL,
                common_name VARCHAR,
                taxonomic_group VARCHAR,
                shift_type VARCHAR,
                direction VARCHAR,
                lat_shift_per_year FLOAT,
                total_shift_km FLOAT,
                years_tracked INTEGER,
                early_range_km FLOAT,
                recent_range_km FLOAT,
                population_trend VARCHAR,
                confidence VARCHAR,
                observation_count INTEGER,
                computed_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE(watershed, taxon_name)
            )
        """))

        watersheds = conn.execute(text("SELECT watershed FROM sites")).fetchall()
        total = 0

        for (ws,) in watersheds:
            shifts = analyze_species_shifts(conn, ws)
            for s in shifts:
                conn.execute(text("""
                    INSERT INTO gold_species_distribution_shifts
                        (watershed, taxon_name, common_name, taxonomic_group,
                         shift_type, direction, lat_shift_per_year, total_shift_km,
                         years_tracked, early_range_km, recent_range_km,
                         population_trend, confidence, observation_count, computed_at)
                    VALUES (:ws, :taxon, :common, :group, :type, :dir, :lat_shift,
                            :total_km, :years, :early, :recent, :pop, :conf, :obs, now())
                    ON CONFLICT (watershed, taxon_name) DO UPDATE SET
                        shift_type = EXCLUDED.shift_type,
                        direction = EXCLUDED.direction,
                        total_shift_km = EXCLUDED.total_shift_km,
                        population_trend = EXCLUDED.population_trend,
                        confidence = EXCLUDED.confidence,
                        computed_at = now()
                """), {
                    "ws": ws, "taxon": s["taxon_name"], "common": s["common_name"],
                    "group": s["taxonomic_group"], "type": s["shift_type"],
                    "dir": s["direction"], "lat_shift": s["lat_shift_per_year"],
                    "total_km": s["total_shift_km"], "years": s["years_tracked"],
                    "early": s["early_range_km"], "recent": s["recent_range_km"],
                    "pop": s["population_trend"], "conf": s["confidence"],
                    "obs": s["observation_count"],
                })
                total += 1

        console.print(f"  gold_species_distribution_shifts: {total} species analyzed")
