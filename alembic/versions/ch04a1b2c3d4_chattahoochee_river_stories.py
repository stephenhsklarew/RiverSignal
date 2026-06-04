"""seed river_stories for chattahoochee (adult/kids/expert)

Revision ID: ch04a1b2c3d4
Revises: ch03a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

LLM-drafted narrative at 3 reading levels, generated via
`python -m pipeline.generate_river_stories --watershed chattahoochee`, shipped as
static .txt so prod gets it on deploy. Idempotent ON CONFLICT (watershed, reading_level).
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ch04a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch03a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATA_DIR = Path(__file__).parent.parent / 'data' / 'chattahoochee_river_stories'


def upgrade() -> None:
    conn = op.get_bind()
    for level in ('adult', 'kids', 'expert'):
        narrative = (DATA_DIR / f'chattahoochee-story-{level}.txt').read_text().rstrip('\n')
        conn.execute(
            text(
                "INSERT INTO river_stories (watershed, reading_level, narrative, generated_at) "
                "VALUES ('chattahoochee', :lvl, :narr, now()) "
                "ON CONFLICT (watershed, reading_level) DO UPDATE "
                "SET narrative = EXCLUDED.narrative, generated_at = now()"
            ),
            {"lvl": level, "narr": narrative},
        )


def downgrade() -> None:
    op.execute("DELETE FROM river_stories WHERE watershed = 'chattahoochee'")
