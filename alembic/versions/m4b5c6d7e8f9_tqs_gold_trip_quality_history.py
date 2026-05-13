"""create gold.trip_quality_history snapshot table

Revision ID: m4b5c6d7e8f9
Revises: l3a4b5c6d7e8
Create Date: 2026-05-13 00:00:03.000000

Phase A of TQS. Daily snapshot of the previous day's
gold.trip_quality_daily per (reach_id, target_date). Used by the
alert engine to compute slopes (trend detection) and by the why-panel
to render 30-day sparklines. See plan §3.4c.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'm4b5c6d7e8f9'
down_revision: Union[str, Sequence[str], None] = 'l3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS gold.trip_quality_history (
            reach_id        varchar(80) NOT NULL,
            target_date     date NOT NULL,
            snapshot_date   date NOT NULL,
            tqs             int NOT NULL,
            confidence      int,
            PRIMARY KEY (reach_id, target_date, snapshot_date)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tqs_hist_recent "
        "ON gold.trip_quality_history (reach_id, target_date, snapshot_date DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gold.trip_quality_history")
