"""seed chattahoochee curated_hatch_chart.fly_patterns

Revision ID: nb12a1b2c3d4
Revises: na11a1b2c3d4
Create Date: 2026-06-07 00:00:00.000000

ch03 seeded the Chattahoochee hatch chart with empty fly_patterns, so
/path/hatch/chattahoochee showed no specific fly match per insect (same miss as
Shenandoah/Meramec). Set canonical fly patterns for all 10 Chattahoochee hatches
(Buford tailwater + Blue Ridge trout). Read directly by hatch-confidence; no MV
refresh needed. Idempotent (UPDATE by common_name).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'nb12a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'na11a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FLIES = {
    'Black Caddis': ['Black Elk Hair Caddis', 'Black Caddis Pupa', 'X-Caddis'],
    'Blue-Winged Olive': ['BWO Parachute', 'Pheasant Tail Nymph', 'Sparkle Dun'],
    'Hendrickson': ['Hendrickson Dry', 'Hendrickson Sparkle Dun', 'Pheasant Tail Nymph'],
    'Light Cahill': ['Light Cahill Dry', "Hare's Ear Nymph"],
    'March Brown': ['March Brown Dry', "Hare's Ear Nymph", 'Pheasant Tail Nymph'],
    'Midges': ["Griffith's Gnat", 'Zebra Midge', 'Brassie'],
    'Quill Gordon': ['Quill Gordon Dry', 'Pheasant Tail Nymph'],
    'Sulphur': ['Sulphur Parachute', 'Sulphur Sparkle Dun', 'Pheasant Tail Nymph'],
    'Tan Caddis': ['Elk Hair Caddis', 'LaFontaine Sparkle Pupa', 'X-Caddis'],
    'Terrestrials (ants/beetles/hoppers)': ['Foam Hopper', 'Chernobyl Ant', 'Foam Beetle'],
}


def upgrade() -> None:
    conn = op.get_bind()
    for common_name, flies in FLIES.items():
        conn.execute(
            text("""
                UPDATE curated_hatch_chart
                   SET fly_patterns = CAST(:flies AS text[])
                 WHERE watershed = 'chattahoochee' AND common_name = :cn
            """),
            {"flies": flies, "cn": common_name},
        )


def downgrade() -> None:
    op.execute("""
        UPDATE curated_hatch_chart SET fly_patterns = '{}'::text[]
         WHERE watershed = 'chattahoochee'
    """)
