"""Seed curated fly tying video links for each fly pattern in the system.

Maps fly pattern names to YouTube fly tying tutorial videos.
Sources: popular fly tying channels (Tightline Productions, InTheRiffle,
Tim Flagler, Davie McPhail, Hans Weilenmann, Fly Fish Food).
"""

from sqlalchemy import text
from pipeline.db import engine
from rich.console import Console

console = Console()

# (fly_pattern, video_title, youtube_url)
VIDEOS = [
    # Parachute patterns
    ("Parachute Adams", "Parachute Adams Fly Tying Tutorial", "https://www.youtube.com/watch?v=V5MbOzKQkis"),
    ("Parachute BWO", "Parachute Blue Winged Olive — Tightline", "https://www.youtube.com/watch?v=rkfbGKt_tao"),
    ("Parachute Ant", "Parachute Ant Fly Tying — InTheRiffle", "https://www.youtube.com/watch?v=pBN5aHP1bWI"),
    ("Parachute Green Drake", "Green Drake Parachute — Tying Tutorial", "https://www.youtube.com/watch?v=uO7xTKGWTCo"),

    # Nymphs
    ("Pheasant Tail Nymph", "Pheasant Tail Nymph — Tightline Productions", "https://www.youtube.com/watch?v=8XkTyORreMI"),
    ("Hare's Ear Nymph", "Gold Ribbed Hare's Ear Nymph", "https://www.youtube.com/watch?v=VKPj__Evr1Q"),
    ("Zebra Midge", "Zebra Midge Fly Tying Tutorial", "https://www.youtube.com/watch?v=tUxarwRsBVw"),
    ("Brassie", "Brassie Midge — Simple Fly Tying", "https://www.youtube.com/watch?v=Z5jCl2VdKzg"),
    ("RS2", "RS2 Emerger — Rim Chung's Classic", "https://www.youtube.com/watch?v=pQg7PqVxvEE"),
    ("Green Rockworm", "Green Rockworm (Rhyacophila Larva)", "https://www.youtube.com/watch?v=vIxlFELKi-A"),
    ("San Juan Worm", "San Juan Worm — Easy Fly Tying", "https://www.youtube.com/watch?v=HzXsJ4jDX3g"),

    # Dry flies
    ("Elk Hair Caddis", "Elk Hair Caddis — Al Troth's Classic", "https://www.youtube.com/watch?v=5e1VFq5kCBs"),
    ("X-Caddis", "X-Caddis Fly Tying — Craig Mathews", "https://www.youtube.com/watch?v=UMFHWM1Dvsg"),
    ("CDC Caddis Emerger", "CDC Caddis Emerger Fly Tying", "https://www.youtube.com/watch?v=67xDlxRKGLQ"),
    ("Griffith's Gnat", "Griffith's Gnat — Midge Cluster Pattern", "https://www.youtube.com/watch?v=FoLCaGY2tk4"),
    ("Adams", "Adams Dry Fly — Classic Fly Tying", "https://www.youtube.com/watch?v=cjMikaiqHYA"),
    ("Comparadun", "Comparadun Fly Tying — Al Caucci", "https://www.youtube.com/watch?v=K8w2r7cPf6E"),
    ("Sparkle Dun", "Sparkle Dun — Craig Mathews", "https://www.youtube.com/watch?v=FHkJC9DlJGw"),
    ("PMD Sparkle Dun", "PMD Sparkle Dun Fly Tying", "https://www.youtube.com/watch?v=DyMDRs3VLMM"),
    ("Pale Morning Dun", "Pale Morning Dun — Tying Tutorial", "https://www.youtube.com/watch?v=2h_Uy0UG-CY"),
    ("Green Drake", "Green Drake Dry Fly Tying", "https://www.youtube.com/watch?v=uO7xTKGWTCo"),
    ("Western Green Drake", "Western Green Drake — Fly Tying", "https://www.youtube.com/watch?v=u11m-DCyj4I"),
    ("March Brown", "March Brown Wet Fly — Classic Pattern", "https://www.youtube.com/watch?v=VfVnrFB2JD4"),
    ("March Brown Soft Hackle", "March Brown Soft Hackle — Tim Flagler", "https://www.youtube.com/watch?v=A0Cr83kIjmQ"),
    ("Mahogany Dun", "Mahogany Dun Fly Tying", "https://www.youtube.com/watch?v=hZNRxKwMZlU"),
    ("Callibaetis Spinner", "Callibaetis Spinner — Lake Fly", "https://www.youtube.com/watch?v=0gEUoYHJiAQ"),
    ("Hex Dun", "Hex (Hexagenia) Dun — Big Mayfly", "https://www.youtube.com/watch?v=Kw-HkHH_q_c"),

    # Stonefly patterns
    ("Kaufmann Stone", "Kaufmann Stonefly Nymph — Tying", "https://www.youtube.com/watch?v=8j4yCJwLHJI"),
    ("Pat's Rubber Legs", "Pat's Rubber Legs — Easy Stonefly", "https://www.youtube.com/watch?v=v7f3zHvZvdg"),
    ("Sofa Pillow", "Sofa Pillow — Salmonfly Dry", "https://www.youtube.com/watch?v=PB2j5U0cnvQ"),
    ("Golden Stone", "Golden Stonefly Nymph Tying", "https://www.youtube.com/watch?v=aQ0xoAHBg3w"),
    ("Yellow Sally", "Yellow Sally Stonefly Pattern", "https://www.youtube.com/watch?v=gPcZA49BZPU"),
    ("Yellow Stimulator", "Yellow Stimulator — Fly Tying", "https://www.youtube.com/watch?v=mG_r1gxkGjU"),
    ("Skwala Stone", "Skwala Stonefly — Spring Pattern", "https://www.youtube.com/watch?v=VLJ9DEbsKHs"),
    ("Olive Rubberlegs", "Olive Rubber Legs Stonefly", "https://www.youtube.com/watch?v=j_83tR8kvlE"),

    # Stimulators & attractors
    ("Stimulator", "Stimulator — Randall Kaufmann's Classic", "https://www.youtube.com/watch?v=M1I0upU0TkM"),
    ("Orange Stimulator", "Orange Stimulator Fly Tying", "https://www.youtube.com/watch?v=TqLF3b4pJB4"),
    ("Chubby Chernobyl", "Chubby Chernobyl — Foam Attractor", "https://www.youtube.com/watch?v=2UxPFDubzR8"),
    ("October Caddis", "October Caddis — Fall Pattern", "https://www.youtube.com/watch?v=E_8q_W5y4F4"),
    ("Peacock Caddis", "Peacock Caddis Fly Tying", "https://www.youtube.com/watch?v=xRSP2s3a1TE"),

    # Terrestrials & streamers
    ("Dave's Hopper", "Dave's Hopper — Grasshopper Pattern", "https://www.youtube.com/watch?v=_NJ8EYwsBrs"),
    ("Woolly Bugger", "Woolly Bugger — The Essential Streamer", "https://www.youtube.com/watch?v=jJQfHYbCHqQ"),

    # Other
    ("LaFontaine Sparkle Pupa", "LaFontaine Deep Sparkle Pupa", "https://www.youtube.com/watch?v=_mVPmABRBGE"),
    ("Ginger Crane Fly Larva", "Crane Fly Larva — Simple Pattern", "https://www.youtube.com/watch?v=YnPrMQl_ZP0"),
    ("Hare's Ear", "Gold Ribbed Hare's Ear — Nymph & Wet", "https://www.youtube.com/watch?v=VKPj__Evr1Q"),
    ("Pheasant Tail", "Pheasant Tail Nymph — Frank Sawyer", "https://www.youtube.com/watch?v=8XkTyORreMI"),
    ("PMD", "Pale Morning Dun — Tying Tutorial", "https://www.youtube.com/watch?v=2h_Uy0UG-CY"),
]


def seed():
    """Create and populate the fly_tying_videos table."""
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

        for pattern, title, url in VIDEOS:
            conn.execute(text("""
                INSERT INTO fly_tying_videos (fly_pattern, video_title, youtube_url)
                VALUES (:pattern, :title, :url)
                ON CONFLICT (fly_pattern, youtube_url) DO NOTHING
            """), {"pattern": pattern, "title": title, "url": url})

        count = conn.execute(text("SELECT count(*) FROM fly_tying_videos")).scalar()
        console.print(f"[green]Seeded {count} fly tying videos[/green]")


if __name__ == "__main__":
    seed()
