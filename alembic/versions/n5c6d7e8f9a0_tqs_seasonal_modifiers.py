"""create + seed silver.tqs_seasonal_modifiers

Revision ID: n5c6d7e8f9a0
Revises: m4b5c6d7e8f9
Create Date: 2026-05-13 00:00:04.000000

Phase A0 of TQS. Seasonal sub-score weight modifiers applied on top
of the §2 baseline weights. v1 seeds three modifiers:
- Dry-fly summer (Jun-Sep): hatch +0.05, catch -0.05
- Winter steelhead (Dec-Feb, steelhead reaches only): catch +0.10, hatch -0.10
- Spring runoff (Apr-May): flow +0.05, catch -0.05

Sum of deltas in any one modifier is exactly 0. See plan §2.7.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'n5c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'm4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS silver.tqs_seasonal_modifiers (
            id                  serial PRIMARY KEY,
            season_label        varchar(80) NOT NULL,
            month_start         int NOT NULL CHECK (month_start BETWEEN 1 AND 12),
            month_end           int NOT NULL CHECK (month_end BETWEEN 1 AND 12),
            applies_to_species  varchar[],
            w_catch_delta       double precision NOT NULL DEFAULT 0,
            w_water_temp_delta  double precision NOT NULL DEFAULT 0,
            w_flow_delta        double precision NOT NULL DEFAULT 0,
            w_weather_delta     double precision NOT NULL DEFAULT 0,
            w_hatch_delta       double precision NOT NULL DEFAULT 0,
            w_access_delta      double precision NOT NULL DEFAULT 0,
            notes               text,
            CONSTRAINT season_label_unique UNIQUE (season_label)
        )
        """
    )
    op.execute(
        """
        INSERT INTO silver.tqs_seasonal_modifiers
            (season_label, month_start, month_end, applies_to_species,
             w_catch_delta, w_hatch_delta, w_flow_delta, notes)
        VALUES
            ('dry_fly_summer',     6, 9,  NULL,
             -0.05, 0.05, 0,
             'Hatch dominates fishability in summer'),
            ('winter_steelhead',  12, 2,  ARRAY['steelhead']::varchar[],
              0.10,-0.10, 0,
             'Catch baseline matters more on coastal steelhead reaches in winter'),
            ('spring_runoff',     4, 5,  NULL,
             -0.05, 0,    0.05,
             'Flow dominates during runoff; catch model less reliable')
        ON CONFLICT (season_label) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS silver.tqs_seasonal_modifiers")
