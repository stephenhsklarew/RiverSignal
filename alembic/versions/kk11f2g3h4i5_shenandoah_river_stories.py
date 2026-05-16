"""seed river_stories for shenandoah (adult/kids/expert)

Revision ID: kk11f2g3h4i5
Revises: jj10e1f2g3h4
Create Date: 2026-05-15 00:00:00.000000

`/api/v1/sites/shenandoah/river-story` was returning 404 because
`pipeline.generate_river_stories` had a hardcoded WATERSHEDS dict that
didn't include shenandoah. The frontend's RiverStoryCard then showed
empty content, which (with stale SWR cache from prior watershed views)
manifested as Deschutes content bleeding through.

This migration seeds the three reading-level rows for shenandoah from
the actual LLM output generated locally with the corrected
generate_river_stories.py script. Content lives in
`alembic/data/shenandoah_river_stories/shen-story-*.txt` so a future
regeneration only needs to overwrite those files + add a new
revision-stub migration that re-applies them.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'kk11f2g3h4i5'
down_revision: Union[str, Sequence[str], None] = 'jj10e1f2g3h4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DATA_DIR = Path(__file__).parent.parent / 'data' / 'shenandoah_river_stories'


def upgrade() -> None:
    conn = op.get_bind()
    for level in ('adult', 'kids', 'expert'):
        narrative = (DATA_DIR / f'shen-story-{level}.txt').read_text()
        conn.execute(
            text(
                "INSERT INTO river_stories (watershed, reading_level, narrative, generated_at) "
                "VALUES ('shenandoah', :lvl, :narr, now()) "
                "ON CONFLICT (watershed, reading_level) DO UPDATE "
                "SET narrative = EXCLUDED.narrative, generated_at = now()"
            ),
            {"lvl": level, "narr": narrative},
        )


def downgrade() -> None:
    op.execute("DELETE FROM river_stories WHERE watershed = 'shenandoah'")
