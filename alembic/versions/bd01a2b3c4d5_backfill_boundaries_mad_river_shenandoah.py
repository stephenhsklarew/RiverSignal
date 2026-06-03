"""backfill sites.boundary for mad_river_oh + shenandoah from GeoJSON seeds

Revision ID: bd01a2b3c4d5
Revises: mh01a2b3c4d5
Create Date: 2026-06-02 00:00:00.000000

RiverSignal-bbc43b1b (boundary platform-fix). sites.boundary was NULL for every
watershed on prod because `wbd` isn't a scheduled prod job and the
ST_Union-from-watershed_boundaries migrations are no-ops at deploy time. ip06
fixed Ipswich via a GeoJSON seed; this backfills the other two affected
watersheds the same way (simplified ~50m MultiPolygons), so all onboarded
watersheds have a real prod boundary. Companion change: `wbd -w all` added to
the monthly Cloud Run job so watershed_boundaries stays populated going forward.
Idempotent UPDATE.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'bd01a2b3c4d5'
down_revision: Union[str, Sequence[str], None] = 'mh01a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATA = Path(__file__).parent.parent / 'data'
WATERSHEDS = ['mad_river_oh', 'shenandoah']


def upgrade() -> None:
    conn = op.get_bind()
    for ws in WATERSHEDS:
        gj = (DATA / f'{ws}_boundary.geojson').read_text().strip()
        conn.execute(
            text("""
                UPDATE sites
                SET boundary = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:gj), 4326))
                WHERE watershed = :ws
            """),
            {"gj": gj, "ws": ws},
        )


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed IN ('mad_river_oh', 'shenandoah')")
