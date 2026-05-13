"""create bronze.guide_availability table

Revision ID: s0b1c2d3e4f5
Revises: r9a0b1c2d3e4
Create Date: 2026-05-13 00:00:09.000000

Phase A of TQS. Weekly snapshot of guide booking availability from
public guide/outfitter calendars. Used as a validation signal in the
"why" panel, not as a direct TQS input (chicken-and-egg risk if TQS
gets influential). See plan §3.0d.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 's0b1c2d3e4f5'
down_revision: Union[str, Sequence[str], None] = 'r9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `fetched_at::date` is STABLE (not IMMUTABLE) so it can't be used in an
    # index expression. Use a STORED generated column for the daily granularity
    # and put the unique index on that.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS bronze.guide_availability (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            guide_id        varchar(80) NOT NULL,
            reach_id        varchar(80) REFERENCES silver.river_reaches(id),
            target_date     date NOT NULL,
            availability_pct double precision,
            source_url      text,
            fetched_at      timestamptz NOT NULL DEFAULT now(),
            fetched_date    date GENERATED ALWAYS AS ((fetched_at AT TIME ZONE 'UTC')::date) STORED
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uniq_guide_avail_per_day
            ON bronze.guide_availability (guide_id, reach_id, target_date, fetched_date)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS bronze.guide_availability")
