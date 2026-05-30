"""populate sites.boundary for mad_river_oh from watershed_boundaries

Revision ID: mr07a1b2c3d4
Revises: mr06a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

`/riversignal` map page renders each watershed by its `sites.boundary`
polygon. The mad_river_oh bootstrap row left `boundary` NULL. The `wbd`
adapter ingests the HUC12 polygons for mad_river_oh into
`watershed_boundaries`; this migration computes ST_Multi(ST_Union(geometry))
of those polygons and stores it on `sites.boundary` so the homepage map can
render the Mad River outline (and the map doesn't hang awaiting it).

Idempotent — re-runs simply re-derive the same union. No-op if wbd hasn't
run yet (the EXISTS guard).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mr07a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr06a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE sites
           SET boundary = (
               SELECT ST_Multi(ST_Union(geometry))
                 FROM watershed_boundaries
                WHERE site_id = sites.id
                  AND geometry IS NOT NULL
           )
         WHERE watershed = 'mad_river_oh'
           AND EXISTS (SELECT 1 FROM watershed_boundaries WHERE site_id = sites.id)
    """)


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'mad_river_oh'")
