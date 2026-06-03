"""populate sites.boundary for clinch_river_va from watershed_boundaries (HUC8 06010205 only)

Revision ID: cl07a1b2c3d4
Revises: cl06a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

ST_Union the HUC12 polygons the `wbd` adapter landed into sites.boundary
(MultiPolygon) so the /riversignal homepage map renders the watershed outline.

IMPORTANT — filter to HUC8 06010205 (Upper Clinch). The Clinch's rectangular
bbox caught HUC12s from ~10 adjacent HUC8s (Holston 06010101/102, New 05050001,
Powell 06010206, etc.). Unioning ALL of them would render a multi-basin blob
(this is exactly what forced ipswich to abandon its union-all boundary for a
curated GeoJSON in ip06). Restricting to huc12 LIKE '06010205%' yields the true
VA Upper-Clinch outline (33 HUC12s, ~3,290 km²). Idempotent.

PROD CAVEAT: on a first deploy the migrate job runs BEFORE the Gate-2 `wbd`
ingest, so watershed_boundaries is empty and this UPDATE is a no-op (guarded by
EXISTS). After the Gate-2 wbd job populates prod boundaries, re-run the same
UPDATE as an explicit Gate-4 prod write (runbook §2.6.5). Locally wbd ran first,
so this sets the outline now.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'cl07a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl06a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE sites
        SET boundary = (
            SELECT ST_Multi(ST_Union(geometry))
            FROM watershed_boundaries
            WHERE site_id = sites.id
              AND huc12 LIKE '06010205%'
        )
        WHERE watershed = 'clinch_river_va'
          AND EXISTS (
            SELECT 1 FROM watershed_boundaries
            WHERE site_id = sites.id AND huc12 LIKE '06010205%'
          )
    """)


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'clinch_river_va'")
