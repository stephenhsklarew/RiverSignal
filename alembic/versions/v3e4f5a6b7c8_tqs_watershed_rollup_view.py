"""create gold.trip_quality_watershed_daily MAX-rollup view

Revision ID: v3e4f5a6b7c8
Revises: u2d3e4f5a6b7
Create Date: 2026-05-13 00:00:12.000000

Phase A of TQS. Per plan §3.4b, a view over gold.trip_quality_daily
that picks the best reach per (watershed, target_date) and exposes the
reach_spread affordance for the home-page watershed cards and the
ranking page.

Implemented as a VIEW (not materialized) because the underlying table is
already small (~2000 rows) and refreshed daily; this view costs almost
nothing per query and stays in sync automatically.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'v3e4f5a6b7c8'
down_revision: Union[str, Sequence[str], None] = 'u2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW gold.trip_quality_watershed_daily AS
        WITH ranked AS (
            SELECT
                watershed,
                target_date,
                reach_id,
                tqs,
                confidence,
                primary_factor,
                horizon_days,
                forecast_source,
                computed_at,
                is_hard_closed,
                ROW_NUMBER() OVER (
                    PARTITION BY watershed, target_date
                    ORDER BY tqs DESC, reach_id
                ) AS rn,
                COUNT(*) FILTER (WHERE tqs < 50) OVER (
                    PARTITION BY watershed, target_date
                ) AS unfavorable_count,
                COUNT(*) OVER (PARTITION BY watershed, target_date) AS total_reaches
            FROM gold.trip_quality_daily
        )
        SELECT
            watershed,
            target_date,
            tqs                                AS watershed_tqs,
            reach_id                           AS best_reach_id,
            confidence,
            primary_factor,
            is_hard_closed                     AS best_reach_is_hard_closed,
            unfavorable_count,
            total_reaches,
            CASE WHEN total_reaches > 0
                 THEN unfavorable_count::float / total_reaches
                 ELSE 0 END                     AS reach_spread,
            horizon_days,
            forecast_source,
            computed_at
        FROM ranked
        WHERE rn = 1
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS gold.trip_quality_watershed_daily")
