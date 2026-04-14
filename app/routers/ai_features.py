"""RiverPath AI features: River Oracle, Catch Probability, Species Spotter,
River Replay, Restoration Impact, Compare Rivers, Campfire Story, Time Machine."""

import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["ai-features"])

API_BASE = "http://localhost:8001/api/v1"


# ═══════════════════════════════════════════════
# 1. RIVER ORACLE — Personalized trip planner
# ═══════════════════════════════════════════════
class OracleRequest(BaseModel):
    question: str
    watershed: str | None = None


@router.post("/river-oracle")
def river_oracle(req: OracleRequest):
    """AI trip planner that generates personalized itineraries from real data."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY not configured")

    ws = req.watershed or "deschutes"

    with engine.connect() as conn:
        site = conn.execute(text("SELECT name FROM sites WHERE watershed = :ws"), {"ws": ws}).fetchone()
        if not site:
            raise HTTPException(404, f"Watershed '{ws}' not found")

        # Gather comprehensive context
        conditions = conn.execute(text("""
            SELECT avg_water_temp_c, avg_discharge_cfs FROM gold.fishing_conditions
            WHERE watershed = :ws ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """), {"ws": ws}).fetchone()

        hatch = conn.execute(text("""
            SELECT fly_pattern_name, pattern_insect_name, fly_size, fly_type, time_of_day, water_type
            FROM gold.hatch_fly_recommendations WHERE watershed = :ws
            ORDER BY observation_count DESC LIMIT 5
        """), {"ws": ws}).fetchall()

        stocking = conn.execute(text("""
            SELECT waterbody_name, stocking_date, total_fish FROM gold.stocking_schedule
            WHERE watershed = :ws ORDER BY stocking_date DESC LIMIT 5
        """), {"ws": ws}).fetchall()

        recreation = conn.execute(text("""
            SELECT name, type, distance_km FROM recreation_sites
            WHERE watershed = :ws ORDER BY distance_km LIMIT 10
        """), {"ws": ws}).fetchall() if _table_exists(conn, 'recreation_sites') else []

        swim = conn.execute(text("""
            SELECT station_id, avg_temp_c, safety_rating FROM gold.swim_safety
            WHERE watershed = :ws ORDER BY obs_year DESC, obs_month DESC LIMIT 5
        """), {"ws": ws}).fetchall()

    context = {
        "watershed": ws, "river_name": site[0],
        "water_temp_c": float(conditions[0]) if conditions and conditions[0] else None,
        "flow_cfs": float(conditions[1]) if conditions and conditions[1] else None,
        "current_flies": [{"pattern": r[0], "insect": r[1], "size": r[2], "type": r[3], "time": r[4], "water": r[5]} for r in hatch],
        "recent_stocking": [{"waterbody": r[0], "date": str(r[1]), "fish": r[2]} for r in stocking],
        "recreation": [{"name": r[0], "type": r[1], "dist_km": r[2]} for r in recreation],
        "swim_safety": [{"station": r[0], "temp": float(r[1]) if r[1] else None, "rating": r[2]} for r in swim],
        "month": datetime.now().month,
    }

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system="""You are the River Oracle — a knowledgeable, friendly river guide AI for Oregon's rivers. Given real-time data about a watershed, answer the user's question with specific, actionable advice.

If they ask about fishing: recommend specific flies (from the data), reaches, times of day.
If they ask about family activities: suggest swimming spots (with safety ratings), trails, campgrounds.
If they ask for a trip plan: create a day-by-day itinerary with morning/afternoon/evening activities.

Always cite specific data: water temperature, fly patterns, stocking events. Be warm and enthusiastic. Use the river's name.""",
        messages=[{"role": "user", "content": f"Question: {req.question}\n\nCurrent data for {site[0]}:\n{json.dumps(context, default=str)}"}],
    )

    return {"answer": message.content[0].text, "watershed": ws, "context_used": list(context.keys())}


# ═══════════════════════════════════════════════
# 2. RIVER REPLAY — What changed since last visit
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/replay")
def river_replay(watershed: str, days_ago: int = Query(30, ge=7, le=365)):
    """Show what changed at a watershed in the last N days."""
    with engine.connect() as conn:
        site = conn.execute(text("SELECT name FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404)

        # Species trend
        trends = conn.execute(text("""
            SELECT obs_year, species_count, species_delta
            FROM gold.species_trends WHERE watershed = :ws ORDER BY obs_year DESC LIMIT 2
        """), {"ws": watershed}).fetchall()

        # Health score change
        health = conn.execute(text("""
            SELECT health_score, avg_water_temp, avg_do, obs_year, obs_month
            FROM gold.river_health_score WHERE watershed = :ws
            ORDER BY obs_year DESC, obs_month DESC LIMIT 2
        """), {"ws": watershed}).fetchall()

        # Recent observations count
        recent_obs = conn.execute(text("""
            SELECT count(*) FROM observations o
            JOIN sites s ON o.site_id = s.id
            WHERE s.watershed = :ws AND o.observed_at > now() - make_interval(days => :days)
        """), {"ws": watershed, "days": days_ago}).scalar() or 0

        # Invasive changes
        invasives = conn.execute(text("""
            SELECT taxon_name, recent_detections FROM gold.invasive_detections
            WHERE watershed = :ws AND recent_detections > 0
        """), {"ws": watershed}).fetchall()

        # Harvest
        harvest = conn.execute(text("""
            SELECT species, harvest_year, harvest, harvest_delta_pct
            FROM gold.harvest_trends WHERE watershed = :ws
            ORDER BY harvest_year DESC LIMIT 2
        """), {"ws": watershed}).fetchall()

        # Fire recovery
        recovery = conn.execute(text("""
            SELECT fire_name, observation_year, species_total_watershed
            FROM gold.post_fire_recovery WHERE watershed = :ws
            ORDER BY observation_year DESC LIMIT 2
        """), {"ws": watershed}).fetchall()

    changes = []
    if len(trends) >= 2:
        delta = (trends[0][1] or 0) - (trends[1][1] or 0)
        if delta != 0:
            changes.append({"type": "species", "label": f"Species richness {'↑' if delta > 0 else '↓'} {abs(delta)}", "delta": delta})

    if len(health) >= 2 and health[0][1] and health[1][1]:
        temp_delta = round(float(health[0][1]) - float(health[1][1]), 1)
        if temp_delta != 0:
            changes.append({"type": "temperature", "label": f"Water temp {'↑' if temp_delta > 0 else '↓'} {abs(temp_delta)}°C", "delta": temp_delta})

    if recent_obs > 0:
        changes.append({"type": "observations", "label": f"{recent_obs} new observations in last {days_ago} days", "delta": recent_obs})

    for inv in invasives:
        changes.append({"type": "invasive", "label": f"Invasive alert: {inv[0]} ({inv[1]} recent detections)", "delta": inv[1]})

    if harvest:
        h = harvest[0]
        if h[3]:
            changes.append({"type": "harvest", "label": f"{h[0]} harvest {h[2]:,} in {h[1]} ({'+' if h[3] > 0 else ''}{h[3]}%)", "delta": h[3]})

    if len(recovery) >= 2:
        rec_delta = (recovery[0][2] or 0) - (recovery[1][2] or 0)
        if rec_delta != 0:
            changes.append({"type": "recovery", "label": f"{recovery[0][0]} recovery: {'↑' if rec_delta > 0 else '↓'} {abs(rec_delta)} species", "delta": rec_delta})

    return {"watershed": watershed, "river_name": site[0], "days_ago": days_ago, "changes": changes}


# ═══════════════════════════════════════════════
# 3. CATCH PROBABILITY — Real-time fishing score
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/catch-probability")
def catch_probability(watershed: str):
    """Calculate catch probability per species based on conditions, season, and hatch."""
    month = datetime.now().month

    with engine.connect() as conn:
        # Current conditions
        cond = conn.execute(text("""
            SELECT avg_water_temp_c, avg_discharge_cfs FROM gold.fishing_conditions
            WHERE watershed = :ws ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """), {"ws": watershed}).fetchone()

        # Species by reach
        species = conn.execute(text("""
            SELECT DISTINCT common_name, species, use_type FROM gold.species_by_reach
            WHERE watershed = :ws AND common_name IS NOT NULL
            LIMIT 10
        """), {"ws": watershed}).fetchall()

        # Hatch activity
        hatch_count = conn.execute(text("""
            SELECT count(*) FROM gold.hatch_fly_recommendations
            WHERE watershed = :ws AND obs_month = :m
        """), {"ws": watershed, "m": month}).scalar() or 0

        # Thermal refuges
        refuge_count = conn.execute(text("""
            SELECT count(*) FROM gold.cold_water_refuges
            WHERE watershed = :ws AND thermal_classification = 'cold_water_refuge'
        """), {"ws": watershed}).scalar() or 0

    water_temp = float(cond[0]) if cond and cond[0] else None
    flow = float(cond[1]) if cond and cond[1] else None

    # Preferred temp ranges by species type
    PREF_TEMPS = {
        'chinook': (7, 14), 'steelhead': (8, 15), 'rainbow': (10, 18),
        'bull trout': (4, 12), 'kokanee': (8, 15), 'brown trout': (10, 18),
        'brook trout': (7, 16), 'cutthroat': (8, 16), 'bass': (18, 27),
    }

    scores = []
    for sp in species:
        name = (sp[0] or '').lower()
        score = 50  # base

        # Temperature match
        if water_temp:
            for key, (lo, hi) in PREF_TEMPS.items():
                if key in name:
                    if lo <= water_temp <= hi:
                        score += 25
                    elif abs(water_temp - (lo + hi) / 2) < 5:
                        score += 10
                    else:
                        score -= 15
                    break

        # Seasonal boost (spawning = more catchable for some, less for others)
        use = (sp[2] or '').lower()
        if 'spawning' in use:
            score += 15
        elif 'rearing' in use:
            score += 5

        # Hatch activity boost
        if hatch_count > 3:
            score += 10
        elif hatch_count > 0:
            score += 5

        # Refuge availability
        if refuge_count > 0 and water_temp and water_temp > 16:
            score += 5  # fish congregate at refuges

        score = max(5, min(98, score))
        level = "excellent" if score >= 80 else "good" if score >= 60 else "fair" if score >= 40 else "poor"

        scores.append({
            "species": sp[0] or sp[1],
            "score": score,
            "level": level,
            "use_type": sp[2],
            "factors": [],
        })

    # Sort by score
    scores.sort(key=lambda x: x["score"], reverse=True)

    # Overall score = weighted average of top 3
    top3 = scores[:3]
    overall = round(sum(s["score"] for s in top3) / len(top3)) if top3 else 50

    return {
        "watershed": watershed,
        "overall_score": overall,
        "overall_level": "excellent" if overall >= 80 else "good" if overall >= 60 else "fair" if overall >= 40 else "poor",
        "water_temp_c": water_temp,
        "flow_cfs": flow,
        "hatch_activity": hatch_count,
        "cold_refuges": refuge_count,
        "species": scores[:8],
    }


# ═══════════════════════════════════════════════
# 4. SPECIES SPOTTER — What you'll likely see today
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/species-spotter")
def species_spotter(watershed: str):
    """Predict which species are likely to be seen today based on season and patterns."""
    month = datetime.now().month

    with engine.connect() as conn:
        # Seasonal patterns — what's typically observed this month
        patterns = conn.execute(text("""
            SELECT taxon_group, peak_month, avg_observations
            FROM gold.seasonal_observation_patterns
            WHERE watershed = :ws ORDER BY avg_observations DESC
        """), {"ws": watershed}).fetchall()

        # Species with photos observed recently
        species = conn.execute(text("""
            SELECT g.common_name, g.taxon_name, g.taxonomic_group, g.photo_url
            FROM gold.species_gallery g
            WHERE g.watershed = :ws AND g.photo_url IS NOT NULL
            ORDER BY random() LIMIT 30
        """), {"ws": watershed}).fetchall()

        # Current month hatch
        hatch = conn.execute(text("""
            SELECT pattern_insect_name, observation_count
            FROM gold.hatch_fly_recommendations
            WHERE watershed = :ws AND obs_month = :m
            ORDER BY observation_count DESC LIMIT 3
        """), {"ws": watershed, "m": month}).fetchall()

    # Score species by likelihood this month
    peak_groups = {r[0]: r[1] for r in patterns}
    group_obs = {r[0]: r[2] for r in patterns}

    scored = []
    for sp in species:
        group = sp[2] or 'Unknown'
        peak = peak_groups.get(group, 6)
        obs_avg = group_obs.get(group, 0)

        # Probability based on distance from peak month
        month_dist = min(abs(month - peak), 12 - abs(month - peak))
        if month_dist == 0:
            prob = min(95, 70 + obs_avg // 5)
        elif month_dist <= 2:
            prob = min(85, 50 + obs_avg // 8)
        elif month_dist <= 4:
            prob = min(65, 30 + obs_avg // 10)
        else:
            prob = max(10, 15 + obs_avg // 20)

        scored.append({
            "common_name": sp[0] or sp[1],
            "taxon_name": sp[1],
            "group": group,
            "photo_url": sp[3],
            "probability": prob,
        })

    # Deduplicate and sort
    seen = set()
    unique = []
    for s in sorted(scored, key=lambda x: x["probability"], reverse=True):
        if s["common_name"] not in seen:
            seen.add(s["common_name"])
            unique.append(s)

    return {
        "watershed": watershed,
        "month": month,
        "species": unique[:8],
        "hatch_active": [{"insect": r[0], "observations": r[1]} for r in hatch],
    }


# ═══════════════════════════════════════════════
# 5. RESTORATION IMPACT — Quantified impact story
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/restoration-impact")
def restoration_impact(watershed: str):
    """Quantified restoration impact storytelling."""
    with engine.connect() as conn:
        # Scorecard
        sc = conn.execute(text("""
            SELECT total_species, total_interventions, total_observations
            FROM gold.watershed_scorecard WHERE watershed = :ws
        """), {"ws": watershed}).fetchone()

        # Recovery trajectory
        recovery = conn.execute(text("""
            SELECT fire_name, fire_year, min(species_total_watershed) as min_species,
                   max(species_total_watershed) as max_species,
                   count(DISTINCT observation_year) as years_tracked
            FROM gold.post_fire_recovery WHERE watershed = :ws
            GROUP BY fire_name, fire_year ORDER BY fire_year DESC
        """), {"ws": watershed}).fetchall()

        # Restoration outcomes
        outcomes = conn.execute(text("""
            SELECT intervention_category, count(*) as projects,
                   avg(species_after - species_before) as avg_species_gain
            FROM gold.restoration_outcomes WHERE watershed = :ws
              AND species_before IS NOT NULL AND species_after IS NOT NULL
            GROUP BY intervention_category ORDER BY avg_species_gain DESC
        """), {"ws": watershed}).fetchall()

        # Stewardship
        opps = conn.execute(text("""
            SELECT count(*), sum(project_count) FROM gold.stewardship_opportunities WHERE watershed = :ws
        """), {"ws": watershed}).fetchone()

    return {
        "watershed": watershed,
        "total_species": sc[0] if sc else 0,
        "total_projects": sc[1] if sc else 0,
        "total_observations": sc[2] if sc else 0,
        "fire_recovery": [{
            "fire": r[0], "year": r[1], "min_species": r[2], "max_species": r[3],
            "species_gained": (r[3] or 0) - (r[2] or 0), "years_tracked": r[4],
        } for r in recovery],
        "top_interventions": [{
            "category": r[0], "projects": r[1], "avg_species_gain": round(r[2], 1) if r[2] else 0,
        } for r in outcomes],
        "stewardship_categories": opps[0] if opps else 0,
        "stewardship_projects": opps[1] if opps else 0,
    }


# ═══════════════════════════════════════════════
# 7. COMPARE RIVERS — Side-by-side
# ═══════════════════════════════════════════════
@router.get("/compare")
def compare_rivers(ws1: str = Query(...), ws2: str = Query(...)):
    """Side-by-side comparison of two watersheds."""
    def get_stats(ws: str) -> dict:
        with engine.connect() as conn:
            site = conn.execute(text("SELECT name FROM sites WHERE watershed = :ws"), {"ws": ws}).fetchone()
            sc = conn.execute(text("SELECT * FROM gold.watershed_scorecard WHERE watershed = :ws"), {"ws": ws}).fetchone()
            health = conn.execute(text("""
                SELECT health_score, avg_water_temp, avg_do FROM gold.river_health_score
                WHERE watershed = :ws ORDER BY obs_year DESC, obs_month DESC LIMIT 1
            """), {"ws": ws}).fetchone()
            hatch = conn.execute(text("""
                SELECT count(*) FROM gold.hatch_fly_recommendations
                WHERE watershed = :ws AND obs_month = :m
            """), {"ws": ws, "m": datetime.now().month}).scalar() or 0
            harvest = conn.execute(text("""
                SELECT species, harvest, harvest_delta_pct FROM gold.harvest_trends
                WHERE watershed = :ws ORDER BY harvest_year DESC LIMIT 1
            """), {"ws": ws}).fetchone()

        return {
            "watershed": ws,
            "name": site[0] if site else ws,
            "species": sc[5] if sc else 0,
            "observations": sc[2] if sc else 0,
            "projects": sc[4] if sc else 0,
            "health_score": health[0] if health else None,
            "water_temp_c": float(health[1]) if health and health[1] else None,
            "do_mg_l": float(health[2]) if health and health[2] else None,
            "hatch_activity": hatch,
            "harvest": {"species": harvest[0], "count": harvest[1], "delta_pct": harvest[2]} if harvest else None,
        }

    return {"river1": get_stats(ws1), "river2": get_stats(ws2)}


# ═══════════════════════════════════════════════
# 8. CAMPFIRE STORY — Spoken ecological narrative
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/campfire-story")
def campfire_story(watershed: str):
    """Generate a 3-minute campfire story. Cached on disk (text + audio)."""
    import pathlib
    import httpx

    cache_dir = pathlib.Path(__file__).resolve().parent.parent.parent / ".campfire_cache"
    cache_dir.mkdir(exist_ok=True)
    text_file = cache_dir / f"{watershed}.txt"
    audio_file = cache_dir / f"{watershed}.mp3"

    # ── Check cache ──
    if text_file.exists():
        story_text = text_file.read_text()
        return {
            "watershed": watershed,
            "story": story_text,
            "audio_url": f"/api/v1/sites/{watershed}/campfire-audio" if audio_file.exists() else None,
            "cached": True,
        }

    # ── Generate story via Claude ──
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY not configured")

    with engine.connect() as conn:
        site = conn.execute(text("SELECT name FROM sites WHERE watershed = :ws"), {"ws": watershed}).fetchone()
        if not site:
            raise HTTPException(404)

        timeline = conn.execute(text("""
            SELECT event_year, event_type, event_name, description
            FROM gold.river_story_timeline WHERE watershed = :ws
            ORDER BY event_year DESC LIMIT 15
        """), {"ws": watershed}).fetchall()

        recovery = conn.execute(text("""
            SELECT fire_name, fire_year, acres, max(species_total_watershed) as peak_species
            FROM gold.post_fire_recovery WHERE watershed = :ws
            GROUP BY fire_name, fire_year, acres ORDER BY fire_year DESC LIMIT 3
        """), {"ws": watershed}).fetchall()

        sc = conn.execute(text("SELECT * FROM gold.watershed_scorecard WHERE watershed = :ws"), {"ws": watershed}).fetchone()

    context = {
        "river": site[0],
        "timeline": [{"year": r[0], "type": r[1], "name": r[2], "desc": r[3]} for r in timeline],
        "fire_recovery": [{"fire": r[0], "year": r[1], "acres": r[2], "species": r[3]} for r in recovery],
        "species_count": sc[5] if sc else 0,
        "projects": sc[4] if sc else 0,
    }

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system="""You are a campfire storyteller. Generate a 3-minute spoken story (about 400-500 words) about this Oregon river for a family sitting around a campfire.

The story should:
- Start with "Let me tell you the story of the [river name]..."
- Weave together the river's ecological history: fires, restoration, species recovery, dam removals
- Include moments of drama and wonder
- End with hope and a call to stewardship
- Use vivid sensory language (sounds of the river, the smell of pine, the flash of a salmon)
- Be appropriate for kids ages 6+

Do NOT use markdown formatting — this will be spoken aloud.""",
        messages=[{"role": "user", "content": json.dumps(context, default=str)}],
    )

    story_text = message.content[0].text

    # ── Cache story text ──
    text_file.write_text(story_text)

    # ── Generate and cache audio via OpenAI TTS ──
    openai_key = os.environ.get("OPENAI_API_KEY")
    has_audio = False
    if openai_key:
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={"model": "tts-1", "voice": "nova", "input": story_text[:4096]},
                timeout=60,
            )
            if resp.status_code == 200:
                audio_file.write_bytes(resp.content)
                has_audio = True
        except Exception:
            pass

    return {
        "watershed": watershed,
        "river": site[0],
        "story": story_text,
        "audio_url": f"/api/v1/sites/{watershed}/campfire-audio" if has_audio else None,
        "cached": False,
    }


@router.get("/sites/{watershed}/campfire-audio")
def campfire_audio(watershed: str):
    """Serve cached campfire story audio (MP3)."""
    import pathlib
    from fastapi.responses import Response

    audio_file = pathlib.Path(__file__).resolve().parent.parent.parent / ".campfire_cache" / f"{watershed}.mp3"
    if not audio_file.exists():
        raise HTTPException(404, "No cached audio. Generate the campfire story first.")

    return Response(content=audio_file.read_bytes(), media_type="audio/mpeg")


# ═══════════════════════════════════════════════
# 9. TIME MACHINE — Species through the decades
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/time-machine")
def time_machine(watershed: str):
    """Species observations grouped by year — shows ecological change over time."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT EXTRACT(YEAR FROM o.observed_at)::int as obs_year,
                   count(DISTINCT o.taxon_name) as species_count,
                   count(*) as observation_count,
                   array_agg(DISTINCT o.iconic_taxon) FILTER (WHERE o.iconic_taxon IS NOT NULL) as taxon_groups
            FROM observations o
            JOIN sites s ON o.site_id = s.id
            WHERE s.watershed = :ws AND o.observed_at IS NOT NULL
            GROUP BY obs_year
            ORDER BY obs_year
        """), {"ws": watershed}).fetchall()

        # Sample species per year (top 5 by observation count)
        year_species = {}
        for r in rows:
            yr = r[0]
            sp = conn.execute(text("""
                SELECT o.taxon_name, o.data_payload->>'common_name' as common,
                       o.data_payload->>'photo_url' as photo, count(*) as cnt
                FROM observations o JOIN sites s ON o.site_id = s.id
                WHERE s.watershed = :ws AND EXTRACT(YEAR FROM o.observed_at) = :yr
                  AND o.taxon_name IS NOT NULL
                GROUP BY o.taxon_name, o.data_payload->>'common_name', o.data_payload->>'photo_url'
                ORDER BY cnt DESC LIMIT 5
            """), {"ws": watershed, "yr": yr}).fetchall()
            year_species[yr] = [{"taxon": s[0], "common": s[1], "photo": s[2], "count": s[3]} for s in sp]

    return {
        "watershed": watershed,
        "years": [{
            "year": r[0],
            "species_count": r[1],
            "observations": r[2],
            "taxon_groups": r[3] or [],
            "top_species": year_species.get(r[0], []),
        } for r in rows],
    }


def _table_exists(conn, table_name: str) -> bool:
    r = conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"), {"t": table_name}).scalar()
    return r
