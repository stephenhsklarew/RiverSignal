"""create gold.trip_quality_daily serving table + reach/date indexes

Revision ID: u2d3e4f5a6b7
Revises: t1c2d3e4f5a6
Create Date: 2026-05-13 00:00:11.000000

Phase A of TQS. Plan §3.4 specifies a materialized view, but the compute
logic lives in Python (pipeline/predictions/trip_quality.py — complex
piecewise sub-scores are awkward in SQL). So this is a regular table
populated by a daily refresh job that TRUNCATE+INSERTs from the Python
compute output. Same serving semantics as an MV; one keyed lookup per
(reach_id, target_date).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'u2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 't1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS gold.trip_quality_daily (
            reach_id            varchar(80) NOT NULL,
            watershed           varchar(50) NOT NULL,
            target_date         date NOT NULL,
            tqs                 int NOT NULL,
            confidence          int NOT NULL,
            is_hard_closed      boolean NOT NULL DEFAULT false,
            catch_score         int NOT NULL,
            water_temp_score    int NOT NULL,
            flow_score          int NOT NULL,
            weather_score       int NOT NULL DEFAULT 0,
            hatch_score         int NOT NULL,
            access_score        int NOT NULL,
            primary_factor      text NOT NULL,
            partial_access_flag boolean NOT NULL DEFAULT false,
            horizon_days        int NOT NULL,
            forecast_source     text NOT NULL,
            computed_at         timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (reach_id, target_date)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tqs_ws_date "
        "ON gold.trip_quality_daily (watershed, target_date)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gold.trip_quality_daily")
