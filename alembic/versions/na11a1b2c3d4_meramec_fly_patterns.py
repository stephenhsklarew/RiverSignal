"""seed meramec curated_hatch_chart.fly_patterns (Ozark smallmouth + trout)

Revision ID: na11a1b2c3d4
Revises: mz10a1b2c3d4
Create Date: 2026-06-07 00:00:00.000000

me03 seeded the Meramec hatch chart with empty fly_patterns, so the per-insect
"Recommended flies" list on /path/hatch/meramec rendered no specific match.
Mirror the east-coast pattern (tt20…): set canonical fly patterns per insect —
standard Ozark smallmouth (hellgrammite/crayfish streamers, Isonychia, summer
terrestrials) + Maramec Spring trout (BWO, sulphur, midges, caddis) choices.
Read directly by the hatch-confidence endpoint (no MV refresh needed).
Idempotent (plain UPDATE by common_name). needs_review with the rest of the v0
hatch seed.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'na11a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mz10a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# common_name -> ordered list of canonical fly patterns
FLIES = {
    'Midges': ["Griffith's Gnat", 'Zebra Midge', 'Brassie'],
    'Blue-Winged Olive': ['BWO Parachute', 'Pheasant Tail Nymph', 'Sparkle Dun'],
    'Little Black Caddis': ['Black Elk Hair Caddis', 'Black Caddis Pupa', 'X-Caddis'],
    'Sulphur': ['Sulphur Parachute', 'Sulphur Sparkle Dun', 'Pheasant Tail Nymph'],
    'Slate Drake': ['Isonychia Nymph', 'Mahogany Dun', 'Prince Nymph'],
    'Hellgrammite (Dobsonfly)': ['Black Wooly Bugger', 'Hellgrammite Pattern', 'Clouser Minnow'],
    'Crayfish (forage)': ['Clouser Crayfish', 'Near Nuff Crayfish', 'Olive Wooly Bugger'],
    'White Miller Caddis': ['White Miller', 'Cream Elk Hair Caddis', 'Sparkle Pupa'],
    'Spotted Sedge Caddis': ['Elk Hair Caddis', 'LaFontaine Sparkle Pupa', 'X-Caddis'],
    'Damselfly': ['Damsel Nymph', 'Olive Wooly Bugger'],
    'Light Cahill': ['Light Cahill Dry', "Hare's Ear Nymph"],
    'Terrestrials (ants/beetles/hoppers)': ['Foam Hopper', 'Chernobyl Ant', 'Foam Beetle'],
}


def upgrade() -> None:
    conn = op.get_bind()
    for common_name, flies in FLIES.items():
        conn.execute(
            text("""
                UPDATE curated_hatch_chart
                   SET fly_patterns = CAST(:flies AS text[])
                 WHERE watershed = 'meramec' AND common_name = :cn
            """),
            {"flies": flies, "cn": common_name},
        )


def downgrade() -> None:
    op.execute("""
        UPDATE curated_hatch_chart SET fly_patterns = '{}'::text[]
         WHERE watershed = 'meramec'
    """)
