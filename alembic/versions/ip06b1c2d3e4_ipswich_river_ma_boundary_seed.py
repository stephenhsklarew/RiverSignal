"""set ipswich_river_ma sites.boundary from a shipped GeoJSON seed

Revision ID: ip06b1c2d3e4
Revises: ip05b1c2d3e4
Create Date: 2026-06-02 00:00:00.000000

ip05 populated sites.boundary by ST_Union-ing watershed_boundaries, but `wbd`
is not part of any scheduled prod job, so on prod that table is empty at
migrate time and ip05 is a no-op → boundary stays NULL (true for EVERY
watershed on prod today). This ships the boundary geometry directly as a
static GeoJSON seed (simplified to ~836 points / ~24 KB at ~50 m tolerance)
so prod gets a real outline on deploy without depending on the `wbd` adapter.

Idempotent UPDATE. Follow-on bead: make `wbd` a scheduled job (or ship boundary
seeds for all watersheds) and backfill mad_river_oh / shenandoah.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ip06b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'ip05b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


GEOJSON = Path(__file__).parent.parent / 'data' / 'ipswich_river_ma_boundary.geojson'


def upgrade() -> None:
    gj = GEOJSON.read_text().strip()
    op.get_bind().execute(
        text("""
            UPDATE sites
            SET boundary = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:gj), 4326))
            WHERE watershed = 'ipswich_river_ma'
        """),
        {"gj": gj},
    )


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'ipswich_river_ma'")
