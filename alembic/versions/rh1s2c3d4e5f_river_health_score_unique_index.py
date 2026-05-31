"""unique index on gold.river_health_score for CONCURRENTLY refresh

Revision ID: rh1s2c3d4e5f
Revises: mr12a1b2c3d4
Create Date: 2026-05-31 00:00:00.000000

`gold.river_health_score` had no unique index, so the heavy-mode medallion
refresh fell back to a plain (blocking) REFRESH MATERIALIZED VIEW that takes an
ACCESS EXCLUSIVE lock and stalls reads while it rebuilds (full scans over the
~9.5M-row time_series). Adding a unique index lets _refresh_view() use
REFRESH MATERIALIZED VIEW CONCURRENTLY (non-blocking).

The MV is GROUP BY s.id, s.watershed, s.name, wc.obs_year, wc.obs_month;
watershed/name are functionally dependent on s.id, so each row is uniquely
identified by (site_id, obs_year, obs_month).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'rh1s2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = 'mr12a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS river_health_score_uniq_idx
            ON gold.river_health_score (site_id, obs_year, obs_month)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS gold.river_health_score_uniq_idx")
