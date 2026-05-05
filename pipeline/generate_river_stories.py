"""Pre-generate and cache River Stories for each watershed at all reading levels.

Creates narrative ecological stories for each watershed using the LLM,
cached in the river_stories table for instant serving.

Usage:
    python -m pipeline.generate_river_stories              # All watersheds, all levels
    python -m pipeline.generate_river_stories --watershed deschutes
    python -m pipeline.generate_river_stories --level kids
"""

import os
import click
from rich.console import Console
from sqlalchemy import text
from pipeline.db import engine

console = Console()

WATERSHEDS = {
    'mckenzie': 'McKenzie River',
    'deschutes': 'Deschutes River',
    'metolius': 'Metolius River',
    'klamath': 'Upper Klamath Basin',
    'johnday': 'John Day River',
    'skagit': 'Skagit River',
    'green_river': 'Green River',
}

READING_LEVELS = ['adult', 'kids', 'expert']


def get_watershed_context(conn, ws: str) -> str:
    """Gather data context for story generation."""
    parts = []

    # Health score
    health = conn.execute(text("""
        SELECT health_score, avg_water_temp, avg_do FROM gold.river_health_score
        WHERE watershed = :ws ORDER BY obs_year DESC, obs_month DESC LIMIT 1
    """), {"ws": ws}).fetchone()
    if health:
        parts.append(f"Health score: {health[0]}/100, water temp: {health[1]}°C, DO: {health[2]} mg/L")

    # Species count
    sc = conn.execute(text("SELECT total_species FROM gold.watershed_scorecard WHERE watershed = :ws"), {"ws": ws}).fetchone()
    if sc:
        parts.append(f"Total species documented: {sc[0]}")

    # Fire recovery
    fires = conn.execute(text("""
        SELECT fire_name, fire_year, acres, species_total_watershed, observation_year
        FROM gold.post_fire_recovery WHERE watershed = :ws
        ORDER BY fire_year DESC, observation_year DESC LIMIT 4
    """), {"ws": ws}).fetchall()
    for f in fires:
        parts.append(f"Fire: {f[0]} ({f[1]}, {f[2]} acres), {f[3]} species observed in {f[4]}")

    # Restoration
    rest = conn.execute(text("""
        SELECT intervention_category, species_before, species_after
        FROM gold.restoration_outcomes WHERE watershed = :ws
        ORDER BY intervention_year DESC LIMIT 3
    """), {"ws": ws}).fetchall()
    for r in rest:
        parts.append(f"Restoration ({r[0]}): {r[1]} species before → {r[2]} after")

    # Indicator species
    indicators = conn.execute(text("""
        SELECT taxon_name, common_name, status FROM gold.indicator_species_status
        WHERE watershed = :ws AND status = 'detected' LIMIT 5
    """), {"ws": ws}).fetchall()
    if indicators:
        names = [f"{r[1] or r[0]} ({r[2]})" for r in indicators]
        parts.append(f"Indicator species: {', '.join(names)}")

    # Invasive
    invasives = conn.execute(text("""
        SELECT taxon_name, detection_count FROM gold.invasive_detections
        WHERE watershed = :ws ORDER BY detection_count DESC LIMIT 3
    """), {"ws": ws}).fetchall()
    if invasives:
        names = [f"{r[0]} ({r[1]} detections)" for r in invasives]
        parts.append(f"Invasive threats: {', '.join(names)}")

    return '\n'.join(parts)


def generate_story(watershed: str, ws_name: str, level: str, context: str) -> str:
    """Generate a river story using the LLM."""
    try:
        import anthropic
    except ImportError:
        console.print("[yellow]anthropic package not installed — using template stories[/yellow]")
        return _template_story(watershed, ws_name, level, context)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[yellow]ANTHROPIC_API_KEY not set — using template stories[/yellow]")
        return _template_story(watershed, ws_name, level, context)

    level_instructions = {
        'adult': "Write for a general adult audience. Use clear, engaging language. Include specific data points and species names. 3-4 paragraphs.",
        'kids': "Write for a 5th-grader (age 10-11). Use 'imagine you're standing here...' framing. Simple vocabulary, short sentences. Make it exciting and wonder-filled. 3-4 paragraphs.",
        'expert': "Write for a professional ecologist. Include technical terminology, cite specific data points, mention restoration methodologies and monitoring metrics. 3-4 paragraphs.",
    }

    prompt = f"""Write a compelling ecological story about the {ws_name}.

{level_instructions[level]}

Use this real data to ground the story:
{context}

The story should cover:
1. What makes this river special — its character, its ecological significance
2. What's happening right now — current health, active species, seasonal highlights
3. Challenges it faces — fire recovery, invasive species, water quality
4. How it's recovering — restoration efforts, species returning, community stewardship

Do NOT use markdown headers. Write flowing narrative paragraphs only.
Do NOT start with "The" — use an engaging opening."""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def _template_story(watershed: str, ws_name: str, level: str, context: str) -> str:
    """Fallback template when LLM is not available."""
    templates = {
        'mckenzie': {
            'adult': f"In September 2020, the Holiday Farm Fire burned through the McKenzie River corridor, transforming one of Oregon's most beloved rivers overnight. Five years later, the recovery story is remarkable. {context.split(chr(10))[0] if context else ''} Native species are returning to reaches that were barren after the fire, and restoration projects along the corridor have more than doubled species richness in some areas. The McKenzie remains one of Oregon's clearest rivers, fed by Cascade snowmelt and springs that keep water cold even in summer. Chinook salmon spawn in its upper reaches, and the aquatic insect community — the foundation of the food web — is rebuilding. For families visiting today, the river tells a story of resilience: how a landscape can burn and come back stronger, how communities can rally around a river, and how nature's capacity for recovery is more powerful than we often imagine.",
            'kids': f"Imagine you're standing at the edge of the McKenzie River in Oregon. The water is so clear you can see the rocks on the bottom! But just a few years ago, a huge wildfire called the Holiday Farm Fire burned through here. Everything was covered in ash. Now look around — the trees are growing back, the bugs are returning, and fish are swimming upstream again! This river is like a superhero that got knocked down but got right back up. Scientists have found that more than twice as many different animals and plants live here now compared to right after the fire. Pretty amazing, right?",
            'expert': f"The McKenzie River watershed presents a compelling case study in post-disturbance ecological recovery. Following the 2020 Holiday Farm Fire (174,390 acres), monitoring data indicates significant gains in species richness across multiple trophic levels. {context.split(chr(10))[0] if context else ''} Riparian restoration interventions, primarily native replanting and invasive species removal, have measurably accelerated recovery trajectories compared to unmanaged reference sites. Current macroinvertebrate EPT indices suggest the benthic community is approaching pre-fire baseline, though composition has shifted toward more disturbance-tolerant taxa. Continued monitoring of indicator species — particularly bull trout thermal refugia utilization and salmonid redd counts — will be critical for assessing long-term recovery.",
        },
    }

    ws_templates = templates.get(watershed, templates['mckenzie'])
    return ws_templates.get(level, ws_templates['adult'])


@click.command()
@click.option('--watershed', '-w', type=click.Choice(list(WATERSHEDS.keys()) + ['all']), default='all')
@click.option('--level', '-l', type=click.Choice(READING_LEVELS + ['all']), default='all')
def main(watershed: str, level: str):
    """Pre-generate river stories for all watersheds and reading levels."""
    # Ensure table exists
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS river_stories (
                id SERIAL PRIMARY KEY,
                watershed VARCHAR NOT NULL,
                reading_level VARCHAR NOT NULL,
                narrative TEXT NOT NULL,
                generated_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE(watershed, reading_level)
            )
        """))

    watersheds = WATERSHEDS if watershed == 'all' else {watershed: WATERSHEDS[watershed]}
    levels = READING_LEVELS if level == 'all' else [level]

    for ws, ws_name in watersheds.items():
        console.print(f"\n[bold]{ws_name}[/bold]")

        with engine.connect() as conn:
            context = get_watershed_context(conn, ws)

        for lvl in levels:
            # Check if already cached
            with engine.connect() as conn:
                existing = conn.execute(text(
                    "SELECT id FROM river_stories WHERE watershed = :ws AND reading_level = :lvl"
                ), {"ws": ws, "lvl": lvl}).fetchone()

            if existing:
                console.print(f"  {lvl}: already cached (use --force to regenerate)")
                continue

            console.print(f"  {lvl}: generating...")
            narrative = generate_story(ws, ws_name, lvl, context)

            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO river_stories (watershed, reading_level, narrative)
                    VALUES (:ws, :lvl, :narrative)
                    ON CONFLICT (watershed, reading_level) DO UPDATE SET
                        narrative = EXCLUDED.narrative, generated_at = now()
                """), {"ws": ws, "lvl": lvl, "narrative": narrative})

            console.print(f"  {lvl}: cached ({len(narrative)} chars)")

    console.print("\n[bold green]Done![/bold green]")


if __name__ == '__main__':
    main()
