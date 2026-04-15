"""DeepTrail AI features: Time Narrator, Cross-Domain Connector, Formation Explorer,
Fossil Rarity, Kid Quiz, Compare Eras, Mineral Match."""

import json
import os
import pathlib
import hashlib

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["deeptrail-ai"])

CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / ".deeptrail_cache"


# ═══════════════════════════════════════════════
# 4. GEOLOGIC TIME NARRATOR — tap timeline entry → narrated audio
# ═══════════════════════════════════════════════
@router.post("/deep-time/narrate")
def narrate_timeline_entry(body: dict):
    """Generate a 30-second narrated description of a geologic event + audio."""
    period = body.get("period", "")
    age_ma = body.get("age_ma")
    name = body.get("name", "")
    rock_type = body.get("rock_type", "")
    description = body.get("description", "")
    reading_level = body.get("reading_level", "adult")
    lat = body.get("lat")
    lon = body.get("lon")

    if not name and not period:
        raise HTTPException(400, "period or name required")

    # Cache key
    CACHE_DIR.mkdir(exist_ok=True)
    cache_key = hashlib.sha256(f"{name}:{period}:{age_ma}:{reading_level}".encode()).hexdigest()[:20]
    text_file = CACHE_DIR / f"narrate_{cache_key}.txt"
    audio_file = CACHE_DIR / f"narrate_{cache_key}.mp3"

    # Check cache
    if text_file.exists():
        return {
            "narration": text_file.read_text(),
            "audio_url": f"/api/v1/deep-time/narrate-audio/{cache_key}" if audio_file.exists() else None,
            "cached": True,
        }

    # Get nearby fossils for context
    fossil_context = ""
    if lat and lon:
        with engine.connect() as conn:
            fossils = conn.execute(text("""
                SELECT taxon_name, common_name, phylum, period FROM fossil_occurrences
                WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 50000)
                  AND age_max_ma IS NOT NULL AND age_max_ma BETWEEN :age_lo AND :age_hi
                LIMIT 5
            """), {"lat": lat, "lon": lon, "age_lo": (age_ma or 0) - 10, "age_hi": (age_ma or 0) + 10}).fetchall()
            if fossils:
                fossil_context = "Fossils from this era: " + ", ".join(
                    f"{r[1] or r[0]} ({r[2]})" for r in fossils
                )

    level_style = {
        "kids": "Speak like a friendly teacher to a 7-year-old. Use 'imagine' and comparisons to things kids know.",
        "adult": "Speak like a nature documentary narrator. Vivid and engaging.",
        "expert": "Use precise geological terminology. Include formation names and radiometric context.",
    }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY not configured")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=f"""Generate a 30-second narration (about 60-80 words) describing what was happening at this location during this geologic event. {level_style.get(reading_level, level_style['adult'])} No markdown. This will be spoken aloud.""",
        messages=[{"role": "user", "content": f"Event: {name}\nPeriod: {period}\nAge: {age_ma} million years ago\nRock type: {rock_type}\nDescription: {description}\n{fossil_context}"}],
    )

    narration = message.content[0].text
    text_file.write_text(narration)

    # Generate audio via OpenAI TTS
    audio_url = None
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import httpx
            resp = httpx.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={"model": "tts-1", "voice": "nova", "input": narration},
                timeout=30,
            )
            if resp.status_code == 200:
                audio_file.write_bytes(resp.content)
                audio_url = f"/api/v1/deep-time/narrate-audio/{cache_key}"
        except Exception:
            pass

    return {"narration": narration, "audio_url": audio_url, "cached": False}


@router.get("/deep-time/narrate-audio/{cache_key}")
def narrate_audio(cache_key: str):
    """Serve cached narration audio."""
    audio_file = CACHE_DIR / f"narrate_{cache_key}.mp3"
    if not audio_file.exists():
        raise HTTPException(404)
    return Response(content=audio_file.read_bytes(), media_type="audio/mpeg")


# ═══════════════════════════════════════════════
# 5. CROSS-DOMAIN CONNECTOR — geology explains ecology
# ═══════════════════════════════════════════════
@router.get("/deep-time/geology-ecology/{lat}/{lon}")
def geology_ecology_connector(lat: float, lon: float):
    """Explain how geology at this location drives the local ecology."""
    with engine.connect() as conn:
        # Geology at point
        geo = conn.execute(text("""
            SELECT unit_name, formation, rock_type, lithology, period, age_max_ma
            FROM geologic_units
            WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            ORDER BY age_max_ma ASC NULLS LAST LIMIT 3
        """), {"lat": lat, "lon": lon}).fetchall()

        # Nearest watershed
        nearest = conn.execute(text("""
            SELECT s.watershed, s.name FROM sites s
            ORDER BY ST_Distance(
                ST_MakeEnvelope((s.bbox->>'west')::float, (s.bbox->>'south')::float,
                    (s.bbox->>'east')::float, (s.bbox->>'north')::float, 4326),
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
            ) LIMIT 1
        """), {"lat": lat, "lon": lon}).fetchone()

        # Ecology data if we have a watershed
        ecology = {}
        if nearest:
            ws = nearest[0]
            health = conn.execute(text("""
                SELECT health_score, avg_water_temp, avg_do FROM gold.river_health_score
                WHERE watershed = :ws ORDER BY obs_year DESC, obs_month DESC LIMIT 1
            """), {"ws": ws}).fetchone()
            refuges = conn.execute(text("""
                SELECT count(*) FILTER (WHERE thermal_classification = 'cold_water_refuge') as cold,
                       count(*) FILTER (WHERE thermal_classification = 'thermal_stress') as warm
                FROM gold.cold_water_refuges WHERE watershed = :ws
            """), {"ws": ws}).fetchone()
            ecology = {
                "watershed": ws, "river_name": nearest[1],
                "health_score": health[0] if health else None,
                "water_temp_c": float(health[1]) if health and health[1] else None,
                "cold_refuges": refuges[0] if refuges else 0,
                "thermal_stress": refuges[1] if refuges else 0,
            }

    # Known geology-ecology connections
    connections = []
    for g in geo:
        rt = (g[2] or "").lower()
        lith = (g[3] or "").lower()
        if "basalt" in lith or "volcanic" in rt:
            connections.append({
                "geology": f"{g[1] or g[0]} ({g[4]})",
                "connection": "Volcanic basalt creates fractured aquifers that feed cold-water springs — the foundation of spring-fed rivers like the Metolius.",
                "icon": "🌋→💧",
            })
        if "sediment" in rt or "sandstone" in lith or "clay" in lith:
            connections.append({
                "geology": f"{g[1] or g[0]} ({g[4]})",
                "connection": "Sedimentary layers filter and store water, releasing it slowly to maintain baseflows during dry months.",
                "icon": "🪨→🌊",
            })
        if "ash" in lith or "tuff" in lith:
            connections.append({
                "geology": f"{g[1] or g[0]} ({g[4]})",
                "connection": "Volcanic ash soils are nutrient-poor, driving unique plant communities adapted to thin soils — which in turn support specialized insect and bird species.",
                "icon": "🌋→🌿",
            })

    return {
        "lat": lat, "lon": lon,
        "geologic_units": [{"name": g[0], "formation": g[1], "rock_type": g[2], "period": g[4]} for g in geo],
        "ecology": ecology,
        "connections": connections,
    }


# ═══════════════════════════════════════════════
# 6. FORMATION EXPLORER — all fossils in a formation
# ═══════════════════════════════════════════════
@router.get("/deep-time/formation/{formation}")
def formation_explorer(formation: str):
    """Explore a geologic formation: fossils, age range, rock types, narrative."""
    with engine.connect() as conn:
        # Formation info
        geo = conn.execute(text("""
            SELECT DISTINCT unit_name, rock_type, lithology, period, age_min_ma, age_max_ma, description
            FROM geologic_units WHERE formation ILIKE :f OR unit_name ILIKE :f
            LIMIT 5
        """), {"f": f"%{formation}%"}).fetchall()

        # Fossils in this formation
        fossils = conn.execute(text("""
            SELECT taxon_name, common_name, phylum, class_name, period, age_min_ma, age_max_ma,
                   count(*) as occurrences
            FROM fossil_occurrences WHERE formation ILIKE :f
            GROUP BY taxon_name, common_name, phylum, class_name, period, age_min_ma, age_max_ma
            ORDER BY occurrences DESC LIMIT 30
        """), {"f": f"%{formation}%"}).fetchall()

        # Also match by period overlap
        if geo and not fossils:
            age_min = min(g[4] or 0 for g in geo)
            age_max = max(g[5] or 999 for g in geo)
            fossils = conn.execute(text("""
                SELECT taxon_name, common_name, phylum, class_name, period, age_min_ma, age_max_ma,
                       count(*) as occurrences
                FROM fossil_occurrences
                WHERE age_max_ma BETWEEN :lo AND :hi
                GROUP BY taxon_name, common_name, phylum, class_name, period, age_min_ma, age_max_ma
                ORDER BY occurrences DESC LIMIT 20
            """), {"lo": age_min, "hi": age_max}).fetchall()

    return {
        "formation": formation,
        "units": [{"name": g[0], "rock_type": g[1], "lithology": g[2], "period": g[3],
                   "age_min_ma": g[4], "age_max_ma": g[5], "description": g[6]} for g in geo],
        "fossils": [{"taxon": r[0], "common_name": r[1], "phylum": r[2], "class": r[3],
                     "period": r[4], "age_min_ma": r[5], "age_max_ma": r[6], "occurrences": r[7]} for r in fossils],
        "fossil_count": len(fossils),
    }


# ═══════════════════════════════════════════════
# 7. FOSSIL RARITY SCORE
# ═══════════════════════════════════════════════
@router.get("/deep-time/rarity")
def fossil_rarity_scores():
    """Get rarity scores for all fossil taxa based on occurrence count."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT taxon_name, count(*) as occurrences
            FROM fossil_occurrences
            WHERE taxon_name IS NOT NULL AND taxon_name != ''
            GROUP BY taxon_name ORDER BY occurrences DESC
        """)).fetchall()

    # Rarity thresholds
    scores = {}
    for r in rows:
        occ = r[1]
        if occ >= 20:
            rarity = "common"
        elif occ >= 5:
            rarity = "uncommon"
        elif occ >= 2:
            rarity = "rare"
        else:
            rarity = "very_rare"
        scores[r[0]] = {"occurrences": occ, "rarity": rarity}

    return {"taxa_count": len(scores), "scores": scores}


# ═══════════════════════════════════════════════
# 8. KID QUIZ MODE
# ═══════════════════════════════════════════════
@router.get("/deep-time/quiz")
def kid_quiz(lat: float = Query(...), lon: float = Query(...)):
    """Generate quiz questions from fossil and geology data at a location."""
    with engine.connect() as conn:
        fossils = conn.execute(text("""
            SELECT taxon_name, common_name, phylum, class_name, period, age_max_ma
            FROM fossil_occurrences
            WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 50000)
              AND common_name IS NOT NULL AND common_name != ''
            ORDER BY random() LIMIT 10
        """), {"lat": lat, "lon": lon}).fetchall()

        geo = conn.execute(text("""
            SELECT unit_name, rock_type, period, age_max_ma
            FROM geologic_units
            WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            LIMIT 3
        """), {"lat": lat, "lon": lon}).fetchall()

    questions = []

    # Fossil-based questions
    for f in fossils[:4]:
        common = f[1]
        taxon = f[0]
        period = f[4]
        age = f[5]

        # Question type 1: "What is [taxon] commonly known as?"
        wrong_answers = ["Ancient Shark", "Giant Beetle", "Sea Scorpion", "Woolly Mammoth",
                        "Saber-toothed Cat", "Giant Sloth", "Cave Bear", "Terror Bird"]
        import random
        wrong = random.sample([w for w in wrong_answers if w != common], 3)
        choices = wrong + [common]
        random.shuffle(choices)

        questions.append({
            "question": f"What is '{taxon}' commonly known as?",
            "choices": choices,
            "correct": common,
            "hint": f"It lived during the {period} period, about {int(age) if age else '?'} million years ago.",
            "type": "fossil_id",
        })

    # Geology-based questions
    for g in geo[:2]:
        period = g[2]
        age = g[3]
        if age:
            questions.append({
                "question": f"How old is the {g[0] or 'rock'} at this location?",
                "choices": [
                    f"About {int(age)} million years",
                    f"About {int(age * 2)} million years",
                    f"About {int(age / 2)} million years",
                    f"About {int(age * 0.1)} million years",
                ],
                "correct": f"About {int(age)} million years",
                "hint": f"This is a {g[1] or 'geologic'} formation from the {period} period.",
                "type": "age_guess",
            })

    return {"lat": lat, "lon": lon, "questions": questions[:5]}


# ═══════════════════════════════════════════════
# 9. COMPARE ERAS
# ═══════════════════════════════════════════════
@router.get("/deep-time/compare-eras")
def compare_eras(
    lat: float = Query(...), lon: float = Query(...),
    era1: str = Query(...), era2: str = Query(...)
):
    """Side-by-side comparison of two geologic periods at a location."""
    def get_era_data(conn, lat, lon, era):
        geo = conn.execute(text("""
            SELECT unit_name, formation, rock_type, lithology, age_min_ma, age_max_ma, description
            FROM geologic_units
            WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
              AND period ILIKE :era
            LIMIT 3
        """), {"lat": lat, "lon": lon, "era": f"%{era}%"}).fetchall()

        fossils = conn.execute(text("""
            SELECT taxon_name, common_name, phylum, count(*) as occ
            FROM fossil_occurrences
            WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 50000)
              AND period ILIKE :era
            GROUP BY taxon_name, common_name, phylum ORDER BY occ DESC LIMIT 8
        """), {"lat": lat, "lon": lon, "era": f"%{era}%"}).fetchall()

        return {
            "era": era,
            "geologic_units": [{"name": g[0], "formation": g[1], "rock_type": g[2],
                               "lithology": g[3], "age_range": f"{g[4] or '?'}–{g[5] or '?'} Ma"} for g in geo],
            "fossils": [{"name": f[1] or f[0], "phylum": f[2], "occurrences": f[3]} for f in fossils],
            "fossil_count": len(fossils),
        }

    with engine.connect() as conn:
        data1 = get_era_data(conn, lat, lon, era1)
        data2 = get_era_data(conn, lat, lon, era2)

    return {"era1": data1, "era2": data2}


# ═══════════════════════════════════════════════
# 10. MINERAL MATCH — mineral shops + legality per site
# ═══════════════════════════════════════════════
@router.get("/deep-time/mineral-shops")
def mineral_shops():
    """Get curated list of mineral/rock shops in Oregon."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT name, city, address, latitude, longitude, phone, website, description, watersheds
            FROM mineral_shops ORDER BY name
        """)).fetchall()

    return [{
        "name": r[0], "city": r[1], "address": r[2],
        "latitude": r[3], "longitude": r[4],
        "phone": r[5], "website": r[6], "description": r[7],
        "watersheds": r[8],
    } for r in rows]


@router.get("/deep-time/mineral-match/{lat}/{lon}")
def mineral_match(lat: float, lon: float, radius_km: float = Query(50, le=200)):
    """Minerals at this location with legality and nearby shops."""
    with engine.connect() as conn:
        minerals = conn.execute(text("""
            SELECT site_name, commodity, dev_status, latitude, longitude,
                   ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000 as dist_km
            FROM mineral_deposits
            WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :r)
            ORDER BY dist_km LIMIT 20
        """), {"lat": lat, "lon": lon, "r": radius_km * 1000}).fetchall()

        # Land ownership for legality
        land = conn.execute(text("""
            SELECT agency, collecting_status, collecting_rules FROM land_ownership
            WHERE collecting_status = 'permitted'
            LIMIT 5
        """)).fetchall()

        # Nearby shops
        shops = conn.execute(text("""
            SELECT name, city, phone, website,
                   ST_Distance(
                       ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                       ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                   ) / 1000 as dist_km
            FROM mineral_shops
            ORDER BY dist_km LIMIT 3
        """), {"lat": lat, "lon": lon}).fetchall()

    return {
        "minerals": [{"name": r[0], "commodity": r[1], "status": r[2],
                      "latitude": r[3], "longitude": r[4], "distance_km": round(r[5], 1)} for r in minerals],
        "legal_collecting": [{"agency": r[0], "status": r[1], "rules": r[2]} for r in land],
        "nearby_shops": [{"name": r[0], "city": r[1], "phone": r[2], "website": r[3],
                         "distance_km": round(r[4], 1) if r[4] else None} for r in shops],
    }
