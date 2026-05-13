"""create bronze.weather_observations table

Revision ID: k2f3a4b5c6d7
Revises: j1e2f3a4b5c6
Create Date: 2026-05-13 00:00:01.000000

Phase A of TQS. Daily weather observation table feeding the weather
sub-score. Backfill source: NWS hourly observations API; future
NCEI CDO historical backfill writes to the same table with
source_type='ncei'. See plan §3.1.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'k2f3a4b5c6d7'
down_revision: Union[str, Sequence[str], None] = 'j1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS bronze.weather_observations (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            watershed       varchar(50) NOT NULL,
            date            date NOT NULL,
            temperature_max_f         double precision,
            temperature_min_f         double precision,
            temperature_avg_f         double precision,
            precipitation_in          double precision,
            wind_speed_avg_mph        double precision,
            wind_gust_max_mph         double precision,
            relative_humidity_pct     double precision,
            cloud_cover_avg_pct       double precision,
            snow_depth_in             double precision,
            pressure_avg_mb           double precision,
            source_type     varchar(30) NOT NULL DEFAULT 'nws',
            source_station_id text,
            data_payload    jsonb,
            fetched_at      timestamptz DEFAULT now(),
            UNIQUE (watershed, date, source_type)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_weather_obs_ws_date "
        "ON bronze.weather_observations (watershed, date DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS bronze.weather_observations")
