"""seed river_stories for new_river_va (adult/kids/expert)

Revision ID: nr04a1b2c3d4
Revises: nr03a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

LLM-drafted narrative at 3 reading levels, generated via
`python -m pipeline.generate_river_stories --watershed new_river_va` and shipped
as static .txt under alembic/data/new_river_va_river_stories/ so prod gets it on
deploy. Idempotent: ON CONFLICT (watershed, reading_level) DO UPDATE.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'nr04a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nr03a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DATA_DIR = Path(__file__).parent.parent / 'data' / 'new_river_va_river_stories'


def upgrade() -> None:
    conn = op.get_bind()
    for level in ('adult', 'kids', 'expert'):
        narrative = (DATA_DIR / f'new-story-{level}.txt').read_text().rstrip('\n')
        conn.execute(
            text(
                "INSERT INTO river_stories (watershed, reading_level, narrative, generated_at) "
                "VALUES ('new_river_va', :lvl, :narr, now()) "
                "ON CONFLICT (watershed, reading_level) DO UPDATE "
                "SET narrative = EXCLUDED.narrative, generated_at = now()"
            ),
            {"lvl": level, "narr": narrative},
        )


def downgrade() -> None:
    op.execute("DELETE FROM river_stories WHERE watershed = 'new_river_va'")
