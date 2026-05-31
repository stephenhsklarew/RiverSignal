"""seed river_stories for mad_river_oh (adult/kids/expert)

Revision ID: mr09a1b2c3d4
Revises: mr08a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

`/api/v1/sites/mad_river_oh/river-story` would 404 without these rows, and
the RiverStoryCard could bleed a prior watershed's prose via stale SWR cache.

Three reading-level narratives, generated locally with the corrected
generate_river_stories.py (the watershed name is disambiguated to
'Mad River (Ohio)' — the bare 'Mad River' made the LLM hallucinate the
California river). Content lives in
alembic/data/mad_river_oh_river_stories/mad-story-*.txt so a future
regeneration only overwrites those files + adds a revision-stub migration.

NOTE: marked is_draft via the generated_at flow; the kids narrative slightly
misreads the "11,500 stocked brown trout" stat as a species count — flagged
for the curator pass (needs_review).
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'mr09a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr08a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DATA_DIR = Path(__file__).parent.parent / 'data' / 'mad_river_oh_river_stories'


def upgrade() -> None:
    conn = op.get_bind()
    for level in ('adult', 'kids', 'expert'):
        narrative = (DATA_DIR / f'mad-story-{level}.txt').read_text().rstrip('\n')
        conn.execute(
            text(
                "INSERT INTO river_stories (watershed, reading_level, narrative, generated_at) "
                "VALUES ('mad_river_oh', :lvl, :narr, now()) "
                "ON CONFLICT (watershed, reading_level) DO UPDATE "
                "SET narrative = EXCLUDED.narrative, generated_at = now()"
            ),
            {"lvl": level, "narr": narrative},
        )


def downgrade() -> None:
    op.execute("DELETE FROM river_stories WHERE watershed = 'mad_river_oh'")
