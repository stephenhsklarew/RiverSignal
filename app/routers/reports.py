"""Report generation endpoints (FEAT-004)."""

import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["reports"])


class ReportRequest(BaseModel):
    date_start: str = "2024-01-01"
    date_end: str = "2024-12-31"
    format: str = "markdown"  # markdown or json


@router.post("/sites/{watershed}/report")
def generate_funder_report(watershed: str, request: ReportRequest = None):
    """Generate an OWEB-format quarterly restoration progress report (FEAT-004).

    Assembles data from all gold layer views into a structured report
    with executive summary, intervention timeline, species indicators,
    water quality trends, and outcome KPIs.
    """
    req = request or ReportRequest()
    start_year = int(req.date_start[:4])
    end_year = int(req.date_end[:4])

    with engine.connect() as conn:
        site = conn.execute(text("SELECT id, name FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{watershed}' not found")

        site_name = site[1]

        # 1. Species summary
        species_current = conn.execute(text("""
            SELECT obs_year, species_richness, plant_species, bird_species, insect_species,
                   fish_species, amphibian_species, total_observations
            FROM gold.site_ecological_summary WHERE watershed = :ws AND obs_year BETWEEN :y1 AND :y2
            ORDER BY obs_year
        """), {"ws": watershed, "y1": start_year, "y2": end_year}).fetchall()

        # 2. Species trend
        trend = conn.execute(text("""
            SELECT obs_year, species_count, species_delta FROM gold.species_trends
            WHERE watershed = :ws ORDER BY obs_year DESC LIMIT 3
        """), {"ws": watershed}).fetchall()

        # 3. Interventions in period
        interventions = conn.execute(text("""
            SELECT intervention_category, count(*), min(intervention_year), max(intervention_year)
            FROM silver.interventions_enriched
            WHERE watershed = :ws AND intervention_year BETWEEN :y1 AND :y2
            GROUP BY intervention_category ORDER BY count(*) DESC
        """), {"ws": watershed, "y1": start_year, "y2": end_year}).fetchall()

        # 4. Water quality summary
        wq = conn.execute(text("""
            SELECT parameter, round(avg(avg_value)::numeric, 2) as mean_val,
                   round(min(min_value)::numeric, 2) as min_val,
                   round(max(max_value)::numeric, 2) as max_val, unit
            FROM gold.water_quality_monthly
            WHERE watershed = :ws AND obs_year BETWEEN :y1 AND :y2
              AND parameter IN ('water_temperature', 'dissolved_oxygen', 'discharge', 'ph', 'turbidity')
            GROUP BY parameter, unit ORDER BY parameter
        """), {"ws": watershed, "y1": start_year, "y2": end_year}).fetchall()

        # 5. Indicator species
        indicators = conn.execute(text("""
            SELECT common_name, taxon_name, indicator_direction, status, total_detections
            FROM gold.indicator_species_status WHERE watershed = :ws
            ORDER BY indicator_direction DESC, total_detections DESC
        """), {"ws": watershed}).fetchall()

        # 6. Anomalies
        anomalies = conn.execute(text("""
            SELECT anomaly_type, count(*), min(detected_date)::date, max(detected_date)::date
            FROM gold.anomaly_flags WHERE watershed = :ws
            GROUP BY anomaly_type
        """), {"ws": watershed}).fetchall()

        # 7. Invasive species
        invasives = conn.execute(text("""
            SELECT taxon_name, detection_count, first_detected, last_detected, recent_detections
            FROM gold.invasive_detections WHERE watershed = :ws
            ORDER BY detection_count DESC
        """), {"ws": watershed}).fetchall()

        # 8. Restoration outcomes
        outcomes = conn.execute(text("""
            SELECT intervention_category, intervention_year, species_before, species_after
            FROM gold.restoration_outcomes WHERE watershed = :ws
            ORDER BY intervention_year DESC LIMIT 10
        """), {"ws": watershed}).fetchall()

    # Assemble report
    report_data = {
        "title": f"{site_name} Watershed Restoration Progress Report",
        "period": f"{req.date_start} to {req.date_end}",
        "generated_at": datetime.now().isoformat(),
        "watershed": watershed,
        "species_summary": [
            {"year": r[0], "total_species": r[1], "plants": r[2], "birds": r[3],
             "insects": r[4], "fish": r[5], "amphibians": r[6], "observations": r[7]}
            for r in species_current
        ],
        "species_trend": [{"year": r[0], "species": r[1], "delta": r[2]} for r in trend],
        "interventions": [
            {"category": r[0], "count": r[1], "year_range": f"{r[2]}-{r[3]}"}
            for r in interventions
        ],
        "water_quality": [
            {"parameter": r[0], "mean": float(r[1]), "min": float(r[2]), "max": float(r[3]), "unit": r[4]}
            for r in wq
        ],
        "indicator_species": [
            {"name": r[0], "scientific": r[1], "direction": r[2], "status": r[3], "detections": r[4]}
            for r in indicators
        ],
        "anomalies": [
            {"type": r[0], "count": r[1], "first": str(r[2]), "last": str(r[3])}
            for r in anomalies
        ],
        "invasive_species": [
            {"species": r[0], "detections": r[1], "first": str(r[2]), "last": str(r[3]), "recent": r[4]}
            for r in invasives
        ],
        "restoration_outcomes": [
            {"category": r[0], "year": r[1], "species_before": r[2], "species_after": r[3]}
            for r in outcomes
        ],
    }

    if req.format == "json":
        return report_data

    # Generate markdown report
    md = _generate_markdown_report(report_data)

    # Try LLM for executive summary
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system="Write a 2-3 paragraph executive summary for this watershed restoration progress report. Be specific, cite numbers, and highlight key outcomes.",
                messages=[{"role": "user", "content": f"Data:\n{json.dumps(report_data, indent=2, default=str)[:3000]}"}],
            )
            executive_summary = msg.content[0].text
            md = md.replace("[Executive summary will be generated]", executive_summary)
        except Exception:
            pass

    return PlainTextResponse(content=md, media_type="text/markdown")


def _generate_markdown_report(data: dict) -> str:
    lines = [
        f"# {data['title']}",
        f"**Period:** {data['period']}",
        f"**Generated:** {data['generated_at'][:10]}",
        "",
        "## Executive Summary",
        "",
        "[Executive summary will be generated]",
        "",
        "## Species Richness",
        "",
        "| Year | Total Species | Plants | Birds | Insects | Fish | Amphibians | Observations |",
        "|------|--------------|--------|-------|---------|------|-----------|-------------|",
    ]
    for s in data["species_summary"]:
        lines.append(f"| {s['year']} | {s['total_species']:,} | {s['plants']:,} | {s['birds']:,} | {s['insects']:,} | {s['fish']} | {s['amphibians']} | {s['observations']:,} |")

    if data["species_trend"]:
        lines += ["", "**Trend:**"]
        for t in data["species_trend"]:
            delta = f"+{t['delta']}" if t['delta'] and t['delta'] > 0 else str(t['delta'] or '—')
            lines.append(f"- {t['year']}: {t['species']:,} species ({delta})")

    lines += ["", "## Restoration Interventions", ""]
    if data["interventions"]:
        lines.append("| Category | Projects | Years |")
        lines.append("|----------|----------|-------|")
        for i in data["interventions"]:
            lines.append(f"| {i['category']} | {i['count']} | {i['year_range']} |")

    lines += ["", "## Water Quality", ""]
    if data["water_quality"]:
        lines.append("| Parameter | Mean | Min | Max | Unit |")
        lines.append("|-----------|------|-----|-----|------|")
        for w in data["water_quality"]:
            lines.append(f"| {w['parameter']} | {w['mean']} | {w['min']} | {w['max']} | {w['unit']} |")

    lines += ["", "## Indicator Species", ""]
    positive = [i for i in data["indicator_species"] if i["direction"] == "positive"]
    negative = [i for i in data["indicator_species"] if i["direction"] == "negative"]
    lines.append("**Positive indicators (native/sensitive):**")
    for i in positive:
        icon = "✅" if i["status"] == "detected" else "❌"
        lines.append(f"- {icon} {i['name']} (*{i['scientific']}*) — {i['detections']} detections")
    lines.append("")
    lines.append("**Negative indicators (invasive):**")
    for i in negative:
        icon = "⚠️" if i["status"] == "detected" else "✅"
        lines.append(f"- {icon} {i['name']} (*{i['scientific']}*) — {i['detections']} detections")

    if data["anomalies"]:
        lines += ["", "## Anomalies Detected", ""]
        for a in data["anomalies"]:
            lines.append(f"- **{a['type']}**: {a['count']} events ({a['first']} to {a['last']})")

    if data["restoration_outcomes"]:
        lines += ["", "## Restoration Outcomes (Before/After Species)", ""]
        lines.append("| Category | Year | Species Before | Species After | Change |")
        lines.append("|----------|------|---------------|--------------|--------|")
        for o in data["restoration_outcomes"]:
            delta = o["species_after"] - o["species_before"] if o["species_before"] and o["species_after"] else 0
            sign = "+" if delta > 0 else ""
            lines.append(f"| {o['category']} | {o['year']} | {o['species_before']:,} | {o['species_after']:,} | {sign}{delta:,} |")

    lines += ["", "---", f"*Report generated by RiverSignal Watershed Intelligence Platform*"]
    return "\n".join(lines)
