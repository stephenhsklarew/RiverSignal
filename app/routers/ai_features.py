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
            SELECT waterbody, stocking_date, total_fish FROM gold.stocking_schedule
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
              AND COALESCE(o.data_payload->>'visibility','public') != 'private'
        """), {"ws": watershed, "days": days_ago}).scalar() or 0

        # Invasive changes
        invasives = conn.execute(text("""
            SELECT taxon_name, recent_detections FROM gold.invasive_detections
            WHERE watershed = :ws AND recent_detections > 0
        """), {"ws": watershed}).fetchall()

        # Harvest
        harvest = conn.execute(text("""
            SELECT species, harvest_year, annual_harvest, harvest_pct_change
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
    """Catch probability for every game species on this watershed,
    sorted by score desc. Game-species filter uses
    pipeline.predictions.catch_forecast.SPECIES_MODELS as the canonical
    source — anything that doesn't match a specific (non-fallback) model
    is excluded (suckers, dace, chubs, etc.). UI shows top 3 and pages
    through the rest."""
    from pipeline.predictions.catch_forecast import _species_score, is_game_species

    now = datetime.now()
    month = now.month

    with engine.connect() as conn:
        # Current conditions — pick the most recent month with non-null
        # water temp / flow (the matview has empty rows for sparsely
        # populated months and a naive LIMIT 1 catches those).
        cond = conn.execute(text("""
            SELECT avg_water_temp_c, avg_discharge_cfs FROM gold.fishing_conditions
            WHERE watershed = :ws
              AND (avg_water_temp_c IS NOT NULL OR avg_discharge_cfs IS NOT NULL)
            ORDER BY obs_year DESC, obs_month DESC LIMIT 1
        """), {"ws": watershed}).fetchone()

        # Pull every distinct species — no LIMIT. The game-species filter
        # below will drop non-targets (suckers, dace, etc.). Ordering by
        # common_name keeps tie-broken score sort deterministic.
        species = conn.execute(text("""
            SELECT DISTINCT common_name, scientific_name, use_type FROM gold.species_by_reach
            WHERE watershed = :ws AND common_name IS NOT NULL
            ORDER BY common_name
        """), {"ws": watershed}).fetchall()

        hatch_count = conn.execute(text("""
            SELECT count(*) FROM gold.hatch_fly_recommendations
            WHERE watershed = :ws AND obs_month = :m
        """), {"ws": watershed, "m": month}).scalar() or 0

        refuge_count = conn.execute(text("""
            SELECT count(*) FROM gold.cold_water_refuges
            WHERE watershed = :ws AND thermal_classification = 'cold_water_refuge'
        """), {"ws": watershed}).scalar() or 0

    water_temp = float(cond[0]) if cond and cond[0] else None
    flow = float(cond[1]) if cond and cond[1] else None

    # Shape into the dict _species_score expects. We don't have
    # temp_trend or days_since_stocking on this endpoint; pass safe
    # defaults so those factors are neutral, not penalised.
    conditions = {
        "water_temp": water_temp,
        "flow_cfs": flow if flow is not None else 1000.0,
        "month": month,
        "day_of_year": now.timetuple().tm_yday,
        "hatch_activity": hatch_count,
        "days_since_stocking": 999,
        "cold_refuges": refuge_count,
        "temp_trend": 0.0,
    }

    scores = []
    # De-duplicate by scientific name when present, falling back to a
    # whitespace-normalised lowercased common name. Hybrid entries
    # (containing "×" or " x ") are dropped — they're not sport-targets
    # in user mental model and visually look like dupes of the parent.
    seen: set[str] = set()
    for sp in species:
        name = sp[0]
        sci = sp[1]
        if not name or not is_game_species(name):
            continue
        n_clean = " ".join(name.split())  # collapse internal whitespace
        if "×" in n_clean or " x " in f" {n_clean.lower()} ":
            continue  # skip hybrid species
        dedup_key = (sci or "").strip().lower() or n_clean.lower()
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        result = _species_score(name, conditions)
        # Title-case for display; "northern bluegill" → "Northern Bluegill".
        # Python's str.title() handles the unicode "×" / hyphens correctly.
        display = n_clean.title()
        scores.append({
            "species": display,
            "scientific_name": sci,
            "score": result["score"],
            "level": result["level"],
            "use_type": sp[2],
            "factors": result["factors"],
        })

    # Sort by score desc, stable on display name for tie-breaking.
    scores.sort(key=lambda x: (-x["score"], x["species"].lower()))

    # Overall score = average of top 3 (weighted by position).
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
        # Return all game species; the UI pages through them 3 at a time.
        "species": scores,
    }


# ═══════════════════════════════════════════════
# 4. SPECIES SPOTTER — What you'll likely see today
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/species-spotter")
def species_spotter(watershed: str):
    """Predict fish food organisms likely active today — aquatic insects, scuds, terrestrials near water."""
    month = datetime.now().month

    with engine.connect() as conn:
        # 1. Aquatic insects from curated hatch chart (highest confidence)
        curated = conn.execute(text("""
            SELECT common_name, scientific_name, insect_order, start_month, end_month, peak_months
            FROM curated_hatch_chart
            WHERE watershed = :ws AND start_month <= :m AND end_month >= :m
            ORDER BY CASE WHEN :m = ANY(peak_months) THEN 0 ELSE 1 END
        """), {"ws": watershed, "m": month}).fetchall()

        # 2. Aquatic insects from observation data
        observed = conn.execute(text("""
            SELECT taxon_name, common_name, observation_count, activity_level, photo_url
            FROM gold.aquatic_hatch_chart
            WHERE watershed = :ws AND obs_month = :m
            ORDER BY observation_count DESC LIMIT 10
        """), {"ws": watershed, "m": month}).fetchall()

        # 3. Other aquatic invertebrates (scuds, worms, leeches) from species gallery
        inverts = conn.execute(text("""
            SELECT g.common_name, g.taxon_name, g.taxonomic_group, g.photo_url, g.observer
            FROM gold.species_gallery g
            WHERE g.watershed = :ws AND g.photo_url IS NOT NULL
              AND (g.taxonomic_group IN ('Insecta', 'Arachnida', 'Mollusca')
                   OR g.taxon_name ILIKE ANY(ARRAY[
                       '%amphipoda%', '%gammarus%', '%hyalella%',
                       '%oligochaeta%', '%lumbriculid%',
                       '%hirudinea%',
                       '%isopod%', '%asellus%',
                       '%collembola%', '%springtail%'
                   ]))
            ORDER BY random() LIMIT 15
        """), {"ws": watershed}).fetchall()

        # 4. Photos for curated insects (lookup from species gallery)
        photo_lookup = {}
        if curated:
            sci_names = [r[1] for r in curated]
            for name in sci_names:
                genus = name.split()[0] if ' ' in name else name
                photo = conn.execute(text("""
                    SELECT photo_url, observer FROM gold.species_gallery
                    WHERE watershed = :ws AND taxon_name ILIKE :pattern AND photo_url IS NOT NULL
                    LIMIT 1
                """), {"ws": watershed, "pattern": f"%{genus}%"}).fetchone()
                if photo:
                    photo_lookup[name] = {"photo_url": photo[0], "observer": photo[1]}

        # Current hatch for context
        hatch = conn.execute(text("""
            SELECT pattern_insect_name, observation_count
            FROM gold.hatch_fly_recommendations
            WHERE watershed = :ws AND obs_month = :m
            ORDER BY observation_count DESC LIMIT 3
        """), {"ws": watershed, "m": month}).fetchall()

    # Build scored results — fish food first
    scored = []
    seen = set()

    # Curated aquatic insects (highest value — these are what fish eat)
    for r in curated:
        name = r[0]
        if name in seen:
            continue
        seen.add(name)
        is_peak = month in (r[5] or [])
        photo_info = photo_lookup.get(r[1], {})
        scored.append({
            "common_name": name,
            "taxon_name": r[1],
            "group": r[2] or "Aquatic Insect",
            "photo_url": photo_info.get("photo_url"),
            "observer": photo_info.get("observer"),
            "probability": 90 if is_peak else 70,
            "fish_food": True,
            "note": f"{'Peak' if is_peak else 'Active'} — fish are keying on these",
        })

    # Observed aquatic insects
    for r in observed:
        name = r[1] or r[0]
        if name in seen:
            continue
        seen.add(name)
        scored.append({
            "common_name": name,
            "taxon_name": r[0],
            "group": "Aquatic Insect",
            "photo_url": r[4],
            "observer": None,
            "probability": min(85, 50 + (r[2] or 0) // 3),
            "fish_food": True,
            "note": f"{r[2]} observations · {r[3]}",
        })

    # Other aquatic invertebrates
    for sp in inverts:
        name = sp[0] or sp[1]
        if name in seen:
            continue
        seen.add(name)
        scored.append({
            "common_name": name,
            "taxon_name": sp[1],
            "group": sp[2] or "Invertebrate",
            "photo_url": sp[3],
            "observer": sp[4],
            "probability": 60,
            "fish_food": True,
            "note": "Aquatic food source",
        })

    scored.sort(key=lambda x: x["probability"], reverse=True)

    return {
        "watershed": watershed,
        "month": month,
        "species": scored[:8],
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
                SELECT species, annual_harvest, harvest_pct_change FROM gold.harvest_trends
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
            "harvest": {"species": harvest[0], "count": harvest[1], "delta_pct": float(harvest[2]) if harvest[2] else None} if harvest else None,
        }

    return {"river1": get_stats(ws1), "river2": get_stats(ws2)}


# ═══════════════════════════════════════════════
# 8. CAMPFIRE STORY — Spoken ecological narrative
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/campfire-story")
def campfire_story(watershed: str, reading_level: str = "adult"):
    """Generate a campfire story. Cached on disk per reading level (text + audio)."""
    import pathlib
    import httpx
    from fastapi import Query as Q

    if reading_level not in ("kids", "adult", "expert"):
        reading_level = "adult"

    cache_dir = pathlib.Path(__file__).resolve().parent.parent.parent / ".campfire_cache"
    cache_dir.mkdir(exist_ok=True)
    text_file = cache_dir / f"{watershed}_{reading_level}.txt"
    audio_file = cache_dir / f"{watershed}_{reading_level}.mp3"

    # ── Check cache ──
    if text_file.exists():
        story_text = text_file.read_text()
        return {
            "watershed": watershed,
            "reading_level": reading_level,
            "story": story_text,
            "audio_url": f"/api/v1/sites/{watershed}/campfire-audio?reading_level={reading_level}" if audio_file.exists() else None,
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

    level_prompts = {
        "kids": """You are a campfire storyteller for kids ages 6-10. Generate a 2-minute story (300-400 words).

Use simple vocabulary (5th grade level). Start with "Imagine you're sitting by the river..."
Use comparisons kids understand ("as big as a school bus", "as cold as a freezer").
Make animals feel like characters with personalities. End with "And that's why we take care of our rivers."
No markdown formatting — this will be spoken aloud.""",

        "adult": """You are a campfire storyteller. Generate a 3-minute spoken story (400-500 words) for a family.

Start with "Let me tell you the story of the [river name]..."
Weave together the river's ecological history: fires, restoration, species recovery, dam removals.
Include moments of drama and wonder. End with hope and a call to stewardship.
Use vivid sensory language (sounds of the river, the smell of pine, the flash of a salmon).
No markdown formatting — this will be spoken aloud.""",

        "expert": """You are a restoration ecologist telling the scientific story of a watershed. Generate a 3-minute narrative (400-500 words).

Use proper ecological terminology: species richness, trophic cascades, riparian buffer zones.
Include specific data: species counts, restoration outcomes, temperature measurements.
Reference monitoring methodologies and cite intervention types by name.
End with assessment of current trajectory and research questions.
No markdown formatting — this will be spoken aloud.""",
    }

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=level_prompts.get(reading_level, level_prompts["adult"]),
        messages=[{"role": "user", "content": json.dumps(context, default=str)}],
    )

    story_text = message.content[0].text

    # ── Cache story text ──
    text_file.write_text(story_text)

    # ── Generate and cache audio via OpenAI audio model ──
    import base64
    openai_key = os.environ.get("OPENAI_API_KEY")
    has_audio = False
    if openai_key:
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-audio-preview",
                    "modalities": ["text", "audio"],
                    "audio": {"voice": "echo", "format": "mp3"},
                    "messages": [
                        {"role": "system", "content": "You are a narrator. Begin with a brief calm pause before you start reading. Then read the following text aloud exactly as written. Do not add commentary. Just read naturally and expressively."},
                        {"role": "user", "content": story_text[:4000]},
                    ],
                },
                timeout=180,
            )
            if resp.status_code == 200:
                audio_data = resp.json().get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data")
                if audio_data:
                    audio_file.write_bytes(base64.b64decode(audio_data))
                    has_audio = True
        except Exception:
            pass

    return {
        "watershed": watershed,
        "river": site[0],
        "reading_level": reading_level,
        "story": story_text,
        "audio_url": f"/api/v1/sites/{watershed}/campfire-audio?reading_level={reading_level}" if has_audio else None,
        "cached": False,
    }


@router.get("/sites/{watershed}/campfire-audio")
def campfire_audio(watershed: str, reading_level: str = "adult"):
    """Serve cached campfire story audio (MP3)."""
    import pathlib
    from fastapi.responses import Response

    if reading_level not in ("kids", "adult", "expert"):
        reading_level = "adult"

    audio_file = pathlib.Path(__file__).resolve().parent.parent.parent / ".campfire_cache" / f"{watershed}_{reading_level}.mp3"
    # Fallback to old format
    if not audio_file.exists():
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
              AND COALESCE(o.data_payload->>'visibility','public') != 'private'
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
                  AND COALESCE(o.data_payload->>'visibility','public') != 'private'
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


# ═══════════════════════════════════════════════
# 10. RIVER STORY — Pre-cached ecological narratives
# ═══════════════════════════════════════════════
@router.get("/sites/{watershed}/river-story")
def river_story(watershed: str, reading_level: str = Query("adult")):
    """Serve pre-generated river story from cache. Falls back to campfire-story if not cached."""
    if reading_level not in ("kids", "adult", "expert"):
        reading_level = "adult"

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT narrative, generated_at FROM river_stories
            WHERE watershed = :ws AND reading_level = :lvl
        """), {"ws": watershed, "lvl": reading_level}).fetchone()

    if row:
        from app.audio_cache import get_audio_url
        filename = f"{watershed}_{reading_level}.mp3"
        audio = get_audio_url("river_stories", filename)
        # In GCS mode, return direct GCS URL; in local mode, return API path
        if audio and audio.startswith("http"):
            audio_url = audio
        elif audio:
            audio_url = f"/api/v1/sites/{watershed}/river-story-audio?reading_level={reading_level}"
        else:
            audio_url = None
        return {
            "watershed": watershed,
            "reading_level": reading_level,
            "narrative": row[0],
            "generated_at": str(row[1]) if row[1] else None,
            "audio_url": audio_url,
            "cached": True,
        }

    raise HTTPException(404, f"No cached story for {watershed}/{reading_level}. Run: python -m pipeline.generate_river_stories")


@router.get("/sites/{watershed}/river-story-audio")
def river_story_audio(watershed: str, reading_level: str = Query("adult")):
    """Serve cached River Path story audio (MP3)."""
    from fastapi.responses import Response
    from app.audio_cache import get_audio_bytes

    if reading_level not in ("kids", "adult", "expert"):
        reading_level = "adult"

    audio = get_audio_bytes("river_stories", f"{watershed}_{reading_level}.mp3")
    if not audio:
        raise HTTPException(404, "No cached audio for this story.")

    return Response(content=audio, media_type="audio/mpeg")


def _table_exists(conn, table_name: str) -> bool:
    r = conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"), {"t": table_name}).scalar()
    return r
