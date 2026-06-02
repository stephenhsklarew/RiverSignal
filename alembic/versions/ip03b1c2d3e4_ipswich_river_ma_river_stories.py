"""seed river_stories for ipswich_river_ma (adult/kids/expert)

Revision ID: ip03b1c2d3e4
Revises: ph03b1c2d3e4
Create Date: 2026-06-02 00:00:00.000000

LLM-drafted river narrative at 3 reading levels, generated locally via
`python -m pipeline.generate_river_stories --watershed ipswich_river_ma` and
shipped as static .txt under alembic/data/ipswich_river_ma_river_stories/ so
prod gets it on deploy (there is no prod job that runs the generator).
Without this, /api/v1/sites/ipswich_river_ma/river-story 404s and the River
Story card renders blank (or shows a stale prior-watershed cache).
Idempotent: ON CONFLICT (watershed, reading_level) DO UPDATE.

Chains onto ph03b1c2d3e4 (the current shared-chain head at authoring time).
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ip03b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'ph03b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DATA_DIR = Path(__file__).parent.parent / 'data' / 'ipswich_river_ma_river_stories'


def upgrade() -> None:
    conn = op.get_bind()
    for level in ('adult', 'kids', 'expert'):
        narrative = (DATA_DIR / f'ipswich-story-{level}.txt').read_text().rstrip('\n')
        conn.execute(
            text(
                "INSERT INTO river_stories (watershed, reading_level, narrative, generated_at) "
                "VALUES ('ipswich_river_ma', :lvl, :narr, now()) "
                "ON CONFLICT (watershed, reading_level) DO UPDATE "
                "SET narrative = EXCLUDED.narrative, generated_at = now()"
            ),
            {"lvl": level, "narr": narrative},
        )


def downgrade() -> None:
    op.execute("DELETE FROM river_stories WHERE watershed = 'ipswich_river_ma'")
