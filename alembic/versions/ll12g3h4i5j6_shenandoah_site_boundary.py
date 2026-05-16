"""populate sites.boundary for shenandoah from watershed_boundaries

Revision ID: ll12g3h4i5j6
Revises: kk11f2g3h4i5
Create Date: 2026-05-15 00:00:00.000000

`/riversignal` map page renders each watershed by its `sites.boundary`
polygon. Shenandoah's bootstrap row in `bb02c3d4e5f6_shenandoah_site_and_reaches.py`
left `boundary` NULL (no other watershed has it either via the bootstrap
flow — they were each populated post-hoc from WBD). The `wbd` adapter
ingests 359 HUC12 polygons for shenandoah into `watershed_boundaries`;
this migration computes ST_Multi(ST_Union(geometry)) of those polygons
and stores it on `sites.boundary` so the homepage map can render
shenandoah's outline.

Idempotent — re-runs simply re-derive the same union.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'll12g3h4i5j6'
down_revision: Union[str, Sequence[str], None] = 'kk11f2g3h4i5'
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
         WHERE watershed = 'shenandoah'
           AND EXISTS (SELECT 1 FROM watershed_boundaries WHERE site_id = sites.id)
    """)


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'shenandoah'")
