"""set new_river_va sites.boundary from a shipped GeoJSON seed

Revision ID: nr07a1b2c3d4
Revises: nr06a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

Ship the boundary geometry directly as a static GeoJSON seed (the ipswich ip06 /
clinch cl09 pattern) rather than ST_Union-ing watershed_boundaries at migrate
time — `wbd` is not in any scheduled prod job, and the Clinch onboarding showed
the on-prod union can match 0 rows even after a manual wbd run. The geometry is
the local ST_Union of the New's HUC8 05050001 (Upper New) + 05050002 (Middle New)
HUC12 polygons, simplified to ~33 KB at ~80 m tolerance. No wbd dependency.
Idempotent UPDATE.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'nr07a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nr06a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


GEOJSON = Path(__file__).parent.parent / 'data' / 'new_river_va_boundary.geojson'


def upgrade() -> None:
    gj = GEOJSON.read_text().strip()
    op.get_bind().execute(
        text("""
            UPDATE sites
            SET boundary = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:gj), 4326))
            WHERE watershed = 'new_river_va'
        """),
        {"gj": gj},
    )


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'new_river_va'")
