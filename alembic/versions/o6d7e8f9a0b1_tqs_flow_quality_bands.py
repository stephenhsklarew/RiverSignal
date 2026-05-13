"""create silver.flow_quality_bands table

Revision ID: o6d7e8f9a0b1
Revises: n5c6d7e8f9a0
Create Date: 2026-05-13 00:00:05.000000

Phase A0 of TQS. Per-reach (× optional species, × optional season) cfs
ranges encoding "what flow is good for this reach". Curated data, not
derived. Seeded in a separate migration (A0_4). See plan §3.3.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'o6d7e8f9a0b1'
down_revision: Union[str, Sequence[str], None] = 'n5c6d7e8f9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS silver.flow_quality_bands (
            reach_id    varchar(80) NOT NULL REFERENCES silver.river_reaches(id) ON DELETE CASCADE,
            species     varchar(80) NOT NULL DEFAULT '',
            cfs_low         int NOT NULL,
            cfs_ideal_low   int NOT NULL,
            cfs_ideal_high  int NOT NULL,
            cfs_high    int NOT NULL,
            season_start_month  int NOT NULL DEFAULT 0,
            season_end_month    int,
            source      text,
            PRIMARY KEY (reach_id, species, season_start_month),
            CHECK (cfs_low <= cfs_ideal_low),
            CHECK (cfs_ideal_low <= cfs_ideal_high),
            CHECK (cfs_ideal_high <= cfs_high)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS silver.flow_quality_bands")
