"""set chattahoochee sites.boundary from a shipped GeoJSON seed

Revision ID: ch08a1b2c3d4
Revises: ch07a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

Ship the boundary directly as a static GeoJSON seed (the ipswich ip06 / clinch
cl09 / new-river nr07 pattern) — `wbd` is not in any scheduled prod job, so an
ST_Union at migrate time is empty on prod. Geometry = local ST_Union of the two
Chattahoochee-corridor HUC8s (03130001 Upper Chattahoochee + 03130002 Middle
Chattahoochee-Lake Harding), simplified to ~35 KB; the bbox also caught many
adjacent basins (Flint/Ocmulgee/Coosa) which are excluded. Idempotent UPDATE.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ch08a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch07a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GEOJSON = Path(__file__).parent.parent / 'data' / 'chattahoochee_boundary.geojson'


def upgrade() -> None:
    gj = GEOJSON.read_text().strip()
    op.get_bind().execute(
        text("""
            UPDATE sites
            SET boundary = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:gj), 4326))
            WHERE watershed = 'chattahoochee'
        """),
        {"gj": gj},
    )


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'chattahoochee'")
