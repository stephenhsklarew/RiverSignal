"""populate sites.boundary for ipswich_river_ma from watershed_boundaries

Revision ID: ip05b1c2d3e4
Revises: ip04b1c2d3e4
Create Date: 2026-06-02 00:00:00.000000

ST_Union the HUC12 polygons the `wbd` adapter landed in watershed_boundaries
into sites.boundary (MultiPolygon), so the /riversignal homepage map renders
the watershed outline. Idempotent.

PROD CAVEAT: on a first deploy the migrate job runs BEFORE the Gate-2 `wbd`
ingest, so watershed_boundaries is empty and this UPDATE sets NULL. After the
Gate-2 wbd job populates prod boundaries, re-run the same UPDATE as an explicit
Gate-4 prod write (the runbook §2.6.5 note). Locally the boundary is already
set (wbd ran first), so this is a no-op re-affirmation.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ip05b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'ip04b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE sites
        SET boundary = (
            SELECT ST_Multi(ST_Union(geometry))
            FROM watershed_boundaries
            WHERE site_id = sites.id
        )
        WHERE watershed = 'ipswich_river_ma'
          AND EXISTS (SELECT 1 FROM watershed_boundaries WHERE site_id = sites.id)
    """)


def downgrade() -> None:
    op.execute("UPDATE sites SET boundary = NULL WHERE watershed = 'ipswich_river_ma'")
