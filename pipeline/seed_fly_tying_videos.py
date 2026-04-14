"""Seed fly tying video search links for each fly pattern in the system.

Instead of linking to specific YouTube video IDs (which can go stale),
links to YouTube search results for each pattern name + "fly tying".
This always returns current, relevant results.
"""

from sqlalchemy import text
from pipeline.db import engine
from rich.console import Console
from urllib.parse import quote_plus

console = Console()

# All fly patterns in the system (from gold.hatch_fly_recommendations + curated_hatch_chart)
FLY_PATTERNS = [
    "Parachute Adams", "Parachute BWO", "Parachute Ant", "Parachute Green Drake",
    "Pheasant Tail Nymph", "Hare's Ear Nymph", "Zebra Midge", "Brassie",
    "RS2", "Green Rockworm", "San Juan Worm",
    "Elk Hair Caddis", "X-Caddis", "CDC Caddis Emerger", "Griffith's Gnat",
    "Adams", "Comparadun", "Sparkle Dun", "PMD Sparkle Dun",
    "Pale Morning Dun", "Green Drake", "Western Green Drake",
    "March Brown", "March Brown Soft Hackle", "Mahogany Dun",
    "Callibaetis Spinner", "Hex Dun",
    "Kaufmann Stone", "Pat's Rubber Legs", "Sofa Pillow",
    "Golden Stone", "Yellow Sally", "Yellow Stimulator",
    "Skwala Stone", "Olive Rubberlegs",
    "Stimulator", "Orange Stimulator", "Chubby Chernobyl",
    "October Caddis", "Peacock Caddis",
    "Dave's Hopper", "Woolly Bugger",
    "LaFontaine Sparkle Pupa", "Ginger Crane Fly Larva",
    "Hare's Ear", "Pheasant Tail", "PMD",
]


def seed():
    """Create and populate the fly_tying_videos table with YouTube search links."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fly_tying_videos (
                id SERIAL PRIMARY KEY,
                fly_pattern VARCHAR NOT NULL,
                video_title VARCHAR NOT NULL,
                youtube_url VARCHAR NOT NULL,
                source VARCHAR DEFAULT 'curated',
                UNIQUE(fly_pattern, youtube_url)
            )
        """))

        conn.execute(text("DELETE FROM fly_tying_videos"))

        for pattern in FLY_PATTERNS:
            search_query = quote_plus(f"{pattern} fly tying tutorial")
            url = f"https://www.youtube.com/results?search_query={search_query}"
            title = f"How to tie: {pattern}"

            conn.execute(text("""
                INSERT INTO fly_tying_videos (fly_pattern, video_title, youtube_url)
                VALUES (:pattern, :title, :url)
                ON CONFLICT (fly_pattern, youtube_url) DO NOTHING
            """), {"pattern": pattern, "title": title, "url": url})

        count = conn.execute(text("SELECT count(*) FROM fly_tying_videos")).scalar()
        console.print(f"[green]Seeded {count} fly tying video search links[/green]")


if __name__ == "__main__":
    seed()
