"""create silver.river_reaches table

Revision ID: j1e2f3a4b5c6
Revises: i0d1e2f3a4b5
Create Date: 2026-05-13 00:00:00.000000

Phase A0 of Trip Quality Score (TQS). silver.river_reaches is the
modeling unit for TQS — named angler-friendly stretches within each
watershed. 3-5 reaches per watershed, ~25 total across the 7
currently-supported watersheds. See plan §3.0.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'j1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'i0d1e2f3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS silver.river_reaches (
            id              varchar(80) PRIMARY KEY,
            watershed       varchar(50) NOT NULL,
            name            varchar(120) NOT NULL,
            short_label     varchar(40),
            description     text,
            river_mile_start    double precision,
            river_mile_end      double precision,
            bbox            geometry(POLYGON, 4326),
            centroid_lat    double precision NOT NULL,
            centroid_lon    double precision NOT NULL,
            primary_usgs_site_id        varchar(40),
            primary_snotel_station_id   varchar(40),
            general_flow_bearing        int,
            is_warm_water               boolean DEFAULT false,
            typical_species varchar[],
            notes           text,
            source          text,
            is_active       boolean NOT NULL DEFAULT true,
            created_at      timestamptz DEFAULT now(),
            updated_at      timestamptz DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_reaches_watershed ON silver.river_reaches (watershed)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_reaches_bbox ON silver.river_reaches USING GIST (bbox)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS silver.river_reaches")
