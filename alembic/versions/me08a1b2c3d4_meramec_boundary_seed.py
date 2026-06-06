"""seed meramec sites.boundary (MultiPolygon from wbd HUC12 union)

Revision ID: me08a1b2c3d4
Revises: me07a1b2c3d4
Create Date: 2026-06-06 00:00:00.000000

Per runbook §2.6.5. Ships the unioned HUC12 boundary as a static GeoJSON so prod
gets the /riversignal map outline on deploy (the wbd adapter hasn't run on prod
yet at migrate time). v0 from the local wbd ingest; prod's full wbd run at Gate 2
can refine. Idempotent (UPDATE).
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'me08a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me07a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GEOJSON = Path(__file__).parent.parent / 'data' / 'meramec_boundary.geojson'


def upgrade() -> None:
    gj = GEOJSON.read_text().strip()
    op.get_bind().execute(
        text("""
            UPDATE sites
            SET boundary = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:gj), 4326))
            WHERE watershed = 'meramec'
        """),
        {"gj": gj},
    )


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'meramec'")
