"""create bronze.weather_forecasts table with horizon_days generated column

Revision ID: l3a4b5c6d7e8
Revises: k2f3a4b5c6d7
Create Date: 2026-05-13 00:00:02.000000

Phase A of TQS. Stores NWS forecast snapshots so we can use the
forecast at the time we computed TQS for any future target_date.
horizon_days is a STORED GENERATED column for fast filtering. See
plan §3.2.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'l3a4b5c6d7e8'
down_revision: Union[str, Sequence[str], None] = 'k2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS bronze.weather_forecasts (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            watershed       varchar(50) NOT NULL,
            issued_date     date NOT NULL,
            target_date     date NOT NULL,
            horizon_days    int GENERATED ALWAYS AS ((target_date - issued_date)) STORED,
            temperature_max_f         double precision,
            temperature_min_f         double precision,
            precipitation_in          double precision,
            wind_speed_avg_mph        double precision,
            cloud_cover_avg_pct       double precision,
            data_payload    jsonb,
            fetched_at      timestamptz DEFAULT now(),
            UNIQUE (watershed, issued_date, target_date)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_weather_fc_target "
        "ON bronze.weather_forecasts (watershed, target_date DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS bronze.weather_forecasts")
