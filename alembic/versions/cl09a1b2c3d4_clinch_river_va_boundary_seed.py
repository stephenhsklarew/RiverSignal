"""set clinch_river_va sites.boundary from a shipped GeoJSON seed

Revision ID: cl09a1b2c3d4
Revises: cl08a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

cl07 (union at migrate-time, pre-wbd) and cl08 (re-union after the Gate-2 prod
wbd run) both left prod sites.boundary NULL — cl08 matched 0 rows, i.e. prod's
wbd-landed watershed_boundaries for this site did not satisfy the HUC8
06010205 filter the way the local rows did (a prod/local watershed_boundaries
discrepancy worth a follow-on, but not worth blocking the launch on).

So ship the boundary geometry DIRECTLY as a static GeoJSON seed (the same
approach ipswich ip06 / shenandoah bd01 used), computed from the local DB's
correct ST_Union of the HUC8-06010205 HUC12 polygons and simplified to ~28 KB
at ~80 m tolerance. No dependency on the prod wbd adapter. Idempotent UPDATE.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'cl09a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl08a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


GEOJSON = Path(__file__).parent.parent / 'data' / 'clinch_river_va_boundary.geojson'


def upgrade() -> None:
    gj = GEOJSON.read_text().strip()
    op.get_bind().execute(
        text("""
            UPDATE sites
            SET boundary = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:gj), 4326))
            WHERE watershed = 'clinch_river_va'
        """),
        {"gj": gj},
    )


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'clinch_river_va'")
