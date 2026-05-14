"""extend trip_quality_history with sub-scores + forecast_inputs_payload

Revision ID: x5b6c7d8e9f0
Revises: w4f5a6b7c8d9
Create Date: 2026-05-14 13:30:00.000000

Phase 2 of plan-2026-05-14-tqs-forecast-history.md.

  - gold.trip_quality_history gains the six sub-scores, forecast metadata
    (source, horizon, primary factor), and a JSONB snapshot of the
    inputs consumed at scoring time. Going-forward sub-score history
    enables ML feature engineering and forecast-accuracy decomposition.

  - gold.trip_quality_daily gains the forecast_inputs_payload column
    (the other new fields already exist on this table). The scoring
    writer assembles the JSON from NWS + water-temp + flow inputs it
    consumed during compute.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'x5b6c7d8e9f0'
down_revision: Union[str, Sequence[str], None] = 'w4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # trip_quality_history: add the six sub-scores + forecast metadata + payload.
    op.execute("""
        ALTER TABLE gold.trip_quality_history
          ADD COLUMN IF NOT EXISTS catch_score             integer,
          ADD COLUMN IF NOT EXISTS water_temp_score        integer,
          ADD COLUMN IF NOT EXISTS flow_score              integer,
          ADD COLUMN IF NOT EXISTS weather_score           integer,
          ADD COLUMN IF NOT EXISTS hatch_score             integer,
          ADD COLUMN IF NOT EXISTS access_score            integer,
          ADD COLUMN IF NOT EXISTS forecast_source         text,
          ADD COLUMN IF NOT EXISTS horizon_days            integer,
          ADD COLUMN IF NOT EXISTS primary_factor          text,
          ADD COLUMN IF NOT EXISTS forecast_inputs_payload jsonb
    """)

    # trip_quality_daily: the sub-scores + forecast_source + horizon_days +
    # primary_factor columns already exist (added in u2d3e4f5a6b7). Only
    # forecast_inputs_payload is new.
    op.execute("""
        ALTER TABLE gold.trip_quality_daily
          ADD COLUMN IF NOT EXISTS forecast_inputs_payload jsonb
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE gold.trip_quality_history
          DROP COLUMN IF EXISTS forecast_inputs_payload,
          DROP COLUMN IF EXISTS primary_factor,
          DROP COLUMN IF EXISTS horizon_days,
          DROP COLUMN IF EXISTS forecast_source,
          DROP COLUMN IF EXISTS access_score,
          DROP COLUMN IF EXISTS hatch_score,
          DROP COLUMN IF EXISTS weather_score,
          DROP COLUMN IF EXISTS flow_score,
          DROP COLUMN IF EXISTS water_temp_score,
          DROP COLUMN IF EXISTS catch_score
    """)
    op.execute("""
        ALTER TABLE gold.trip_quality_daily
          DROP COLUMN IF EXISTS forecast_inputs_payload
    """)
