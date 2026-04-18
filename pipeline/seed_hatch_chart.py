"""Seed curated hatch chart data for Oregon rivers.

Sources: Published hatch charts from The Caddis Fly Shop, Westfly.com,
The Fly Fisher's Place, Deschutes Angler, and Western Hatches (Hafele/Hughes).

This creates a `curated_hatch_chart` table with month-by-month emergence
timing for the 4 aquatic insect orders that matter for fly fishing:
  - Ephemeroptera (mayflies)
  - Trichoptera (caddisflies)
  - Plecoptera (stoneflies)
  - Diptera (midges, crane flies)
"""

from sqlalchemy import text
from pipeline.db import engine
from rich.console import Console

console = Console()

# Curated hatch data: (watershed, common_name, scientific_name, insect_order,
#   start_month, end_month, peak_months[], fly_patterns[])
# Sources: composite from multiple published Oregon hatch charts
HATCH_DATA = [
    # ── DESCHUTES ──
    # Mayflies
    ("deschutes", "Blue-Winged Olive", "Baetis tricaudatus", "Ephemeroptera", 3, 11, [4,5,9,10], ["Parachute Adams #18-20", "RS2 #20-22", "Pheasant Tail Nymph #18-20"]),
    ("deschutes", "Pale Morning Dun", "Ephemerella infrequens", "Ephemeroptera", 6, 9, [7,8], ["Pale Morning Dun #16-18", "Sparkle Dun #16", "Pheasant Tail Nymph #16-18"]),
    ("deschutes", "March Brown", "Rhithrogena morrisoni", "Ephemeroptera", 3, 5, [4], ["March Brown #12-14", "Hare's Ear Nymph #12-14"]),
    ("deschutes", "Green Drake", "Drunella grandis", "Ephemeroptera", 6, 7, [6], ["Green Drake #10-12", "Western Green Drake #10"]),
    ("deschutes", "Mahogany Dun", "Paraleptophlebia", "Ephemeroptera", 9, 11, [10], ["Mahogany Dun #16", "Pheasant Tail #16-18"]),
    # Caddisflies
    ("deschutes", "October Caddis", "Dicosmoecus", "Trichoptera", 9, 11, [10], ["Orange Stimulator #8-10", "October Caddis #8", "Woolly Bugger #8"]),
    ("deschutes", "Spotted Sedge", "Hydropsyche", "Trichoptera", 5, 9, [6,7], ["Elk Hair Caddis #14-16", "Peacock Caddis #14"]),
    ("deschutes", "Mother's Day Caddis", "Brachycentrus", "Trichoptera", 4, 6, [5], ["Elk Hair Caddis #14-16", "X-Caddis #14-16"]),
    ("deschutes", "Little Olive Caddis", "Glossosoma", "Trichoptera", 6, 9, [7,8], ["CDC Caddis Emerger #16-18", "LaFontaine Sparkle Pupa #16"]),
    # Stoneflies
    ("deschutes", "Salmonfly", "Pteronarcys californica", "Plecoptera", 5, 7, [6], ["Kaufmann Stone #4-6", "Pat's Rubber Legs #4-6", "Sofa Pillow #4"]),
    ("deschutes", "Golden Stonefly", "Hesperoperla pacifica", "Plecoptera", 6, 8, [7], ["Golden Stone #6-8", "Stimulator #6-8"]),
    ("deschutes", "Little Yellow Sally", "Sweltsa", "Plecoptera", 6, 9, [7,8], ["Yellow Sally #14-16", "Yellow Stimulator #14"]),
    ("deschutes", "Skwala", "Skwala parallela", "Plecoptera", 2, 4, [3], ["Skwala Stone #8-10", "Olive Rubberlegs #8"]),
    # Midges
    ("deschutes", "Midges", "Chironomidae", "Diptera", 1, 12, [3,4,11,12], ["Griffith's Gnat #18-22", "Zebra Midge #18-22", "Brassie #18-20"]),
    ("deschutes", "Crane Fly", "Tipula", "Diptera", 5, 9, [6,7], ["Ginger Crane Fly Larva #10", "San Juan Worm #10"]),

    # ── McKENZIE ──
    ("mckenzie", "Blue-Winged Olive", "Baetis tricaudatus", "Ephemeroptera", 3, 11, [4,5,10], ["Parachute Adams #18-20", "RS2 #20-22", "Pheasant Tail Nymph #18"]),
    ("mckenzie", "Pale Morning Dun", "Ephemerella infrequens", "Ephemeroptera", 6, 8, [7], ["PMD #16-18", "Sparkle Dun #16"]),
    ("mckenzie", "Green Drake", "Drunella grandis", "Ephemeroptera", 6, 7, [6,7], ["Green Drake #10-12", "Hare's Ear #10"]),
    ("mckenzie", "March Brown", "Rhithrogena morrisoni", "Ephemeroptera", 3, 5, [4], ["March Brown #12-14"]),
    ("mckenzie", "October Caddis", "Dicosmoecus", "Trichoptera", 9, 11, [10], ["Orange Stimulator #8-10", "October Caddis #8"]),
    ("mckenzie", "Spotted Sedge", "Hydropsyche", "Trichoptera", 5, 9, [6,7], ["Elk Hair Caddis #14-16"]),
    ("mckenzie", "Mother's Day Caddis", "Brachycentrus", "Trichoptera", 4, 6, [5], ["Elk Hair Caddis #14-16"]),
    ("mckenzie", "Salmonfly", "Pteronarcys californica", "Plecoptera", 5, 7, [6], ["Kaufmann Stone #4-6", "Pat's Rubber Legs #4"]),
    ("mckenzie", "Golden Stonefly", "Hesperoperla pacifica", "Plecoptera", 6, 8, [7], ["Golden Stone #6-8"]),
    ("mckenzie", "Midges", "Chironomidae", "Diptera", 1, 12, [3,4,11], ["Griffith's Gnat #18-22", "Zebra Midge #18-22"]),

    # ── METOLIUS ──
    ("metolius", "Blue-Winged Olive", "Baetis tricaudatus", "Ephemeroptera", 3, 11, [5,9,10], ["Parachute Adams #18-20", "Comparadun #18-20"]),
    ("metolius", "Pale Morning Dun", "Ephemerella infrequens", "Ephemeroptera", 6, 8, [7], ["PMD #16-18"]),
    ("metolius", "Green Drake", "Drunella grandis", "Ephemeroptera", 6, 7, [6], ["Green Drake #10-12"]),
    ("metolius", "Spotted Sedge", "Hydropsyche", "Trichoptera", 5, 9, [6,7], ["Elk Hair Caddis #14-16"]),
    ("metolius", "October Caddis", "Dicosmoecus", "Trichoptera", 9, 11, [10], ["Orange Stimulator #8-10"]),
    ("metolius", "Golden Stonefly", "Hesperoperla pacifica", "Plecoptera", 6, 8, [7], ["Golden Stone #6-8", "Stimulator #6-8"]),
    ("metolius", "Salmonfly", "Pteronarcys californica", "Plecoptera", 5, 7, [5,6], ["Kaufmann Stone #4-6"]),
    ("metolius", "Midges", "Chironomidae", "Diptera", 1, 12, [4,5,10], ["Griffith's Gnat #18-22", "Zebra Midge #20"]),

    # ── KLAMATH (Williamson / Wood / Sprague) ──
    ("klamath", "Blue-Winged Olive", "Baetis tricaudatus", "Ephemeroptera", 4, 10, [5,9], ["Parachute Adams #18-20", "RS2 #20"]),
    ("klamath", "Pale Morning Dun", "Ephemerella infrequens", "Ephemeroptera", 6, 8, [7], ["PMD #16-18"]),
    ("klamath", "Callibaetis", "Callibaetis", "Ephemeroptera", 6, 9, [7,8], ["Callibaetis Spinner #14-16", "Adams #14-16"]),
    ("klamath", "Hexagenia", "Hexagenia limbata", "Ephemeroptera", 6, 7, [6], ["Hex Dun #6-8"]),
    ("klamath", "Spotted Sedge", "Hydropsyche", "Trichoptera", 5, 9, [6,7], ["Elk Hair Caddis #14-16"]),
    ("klamath", "October Caddis", "Dicosmoecus", "Trichoptera", 9, 11, [10], ["Orange Stimulator #8-10"]),
    ("klamath", "Golden Stonefly", "Hesperoperla pacifica", "Plecoptera", 6, 8, [7], ["Golden Stone #6-8"]),
    ("klamath", "Midges", "Chironomidae", "Diptera", 1, 12, [4,5,6], ["Griffith's Gnat #18-22", "Zebra Midge #20"]),

    # ── JOHN DAY ──
    ("johnday", "Blue-Winged Olive", "Baetis tricaudatus", "Ephemeroptera", 3, 11, [4,5,10], ["Parachute Adams #18-20", "RS2 #20"]),
    ("johnday", "Pale Morning Dun", "Ephemerella infrequens", "Ephemeroptera", 6, 8, [7], ["PMD #16-18"]),
    ("johnday", "March Brown", "Rhithrogena morrisoni", "Ephemeroptera", 3, 5, [4], ["March Brown #12-14"]),
    ("johnday", "October Caddis", "Dicosmoecus", "Trichoptera", 9, 11, [10], ["Orange Stimulator #8-10"]),
    ("johnday", "Spotted Sedge", "Hydropsyche", "Trichoptera", 5, 9, [6,7], ["Elk Hair Caddis #14-16"]),
    ("johnday", "Salmonfly", "Pteronarcys californica", "Plecoptera", 6, 7, [6], ["Kaufmann Stone #4-6", "Sofa Pillow #4"]),
    ("johnday", "Golden Stonefly", "Hesperoperla pacifica", "Plecoptera", 6, 8, [7], ["Golden Stone #6-8"]),
    ("johnday", "Skwala", "Skwala parallela", "Plecoptera", 2, 4, [3], ["Skwala Stone #8-10"]),
    ("johnday", "Midges", "Chironomidae", "Diptera", 1, 12, [3,4,11], ["Griffith's Gnat #18-22", "Zebra Midge #20"]),

    # ── SKAGIT (Skagit / Sauk / Cascade / Baker, Washington) ──
    # Mayflies
    ("skagit", "Blue-Winged Olive", "Baetis tricaudatus", "Ephemeroptera", 3, 11, [4,5,9,10], ["Parachute Adams #18-20", "RS2 #20-22", "Pheasant Tail Nymph #18-20"]),
    ("skagit", "Pale Morning Dun", "Ephemerella infrequens", "Ephemeroptera", 6, 8, [7], ["Pale Morning Dun #16-18", "Sparkle Dun #16"]),
    ("skagit", "March Brown", "Rhithrogena morrisoni", "Ephemeroptera", 3, 5, [3,4], ["March Brown #12-14", "Hare's Ear Nymph #12"]),
    ("skagit", "Green Drake", "Drunella grandis", "Ephemeroptera", 6, 7, [6], ["Green Drake #10-12", "Hare's Ear #10"]),
    # Caddisflies
    ("skagit", "October Caddis", "Dicosmoecus", "Trichoptera", 9, 11, [10], ["Orange Stimulator #8-10", "October Caddis #8"]),
    ("skagit", "Spotted Sedge", "Hydropsyche", "Trichoptera", 5, 9, [6,7], ["Elk Hair Caddis #14-16", "Peacock Caddis #14"]),
    ("skagit", "Mother's Day Caddis", "Brachycentrus", "Trichoptera", 4, 6, [5], ["Elk Hair Caddis #14-16", "X-Caddis #14-16"]),
    # Stoneflies
    ("skagit", "Salmonfly", "Pteronarcys californica", "Plecoptera", 5, 7, [6], ["Kaufmann Stone #4-6", "Pat's Rubber Legs #4-6"]),
    ("skagit", "Golden Stonefly", "Hesperoperla pacifica", "Plecoptera", 6, 8, [7], ["Golden Stone #6-8", "Stimulator #6-8"]),
    ("skagit", "Skwala", "Skwala parallela", "Plecoptera", 2, 4, [3], ["Skwala Stone #8-10", "Olive Rubberlegs #8"]),
    ("skagit", "Little Yellow Sally", "Sweltsa", "Plecoptera", 6, 9, [7,8], ["Yellow Sally #14-16", "Yellow Stimulator #14"]),
    # Midges
    ("skagit", "Midges", "Chironomidae", "Diptera", 1, 12, [2,3,11,12], ["Griffith's Gnat #18-22", "Zebra Midge #18-22", "Brassie #18-20"]),
    ("skagit", "Crane Fly", "Tipula", "Diptera", 5, 9, [6,7], ["Ginger Crane Fly Larva #10", "San Juan Worm #10"]),
]


def seed():
    """Create and populate the curated_hatch_chart table."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS curated_hatch_chart (
                id SERIAL PRIMARY KEY,
                watershed VARCHAR NOT NULL,
                common_name VARCHAR NOT NULL,
                scientific_name VARCHAR NOT NULL,
                insect_order VARCHAR NOT NULL,
                start_month INTEGER NOT NULL,
                end_month INTEGER NOT NULL,
                peak_months INTEGER[] NOT NULL,
                fly_patterns TEXT[] NOT NULL,
                source VARCHAR DEFAULT 'curated',
                UNIQUE(watershed, common_name)
            )
        """))

        # Clear and re-seed
        conn.execute(text("DELETE FROM curated_hatch_chart"))

        for row in HATCH_DATA:
            conn.execute(text("""
                INSERT INTO curated_hatch_chart
                    (watershed, common_name, scientific_name, insect_order,
                     start_month, end_month, peak_months, fly_patterns)
                VALUES (:ws, :name, :sci, :ord, :sm, :em, :peaks, :flies)
            """), {
                "ws": row[0], "name": row[1], "sci": row[2], "ord": row[3],
                "sm": row[4], "em": row[5], "peaks": row[6], "flies": row[7],
            })

        count = conn.execute(text("SELECT count(*) FROM curated_hatch_chart")).scalar()
        console.print(f"[green]Seeded {count} curated hatch chart entries[/green]")


if __name__ == "__main__":
    seed()
