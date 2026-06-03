"""set clinch_river_va sites.boundary now that prod wbd has populated watershed_boundaries

Revision ID: cl08a1b2c3d4
Revises: cl07a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

cl07 ran at migrate-time on the first deploy, BEFORE the Gate-2 `wbd` ingest, so
prod `watershed_boundaries` was empty and `sites.boundary` stayed NULL (the
documented PROD CAVEAT in cl07). The Gate-2 recovery ran `wbd -w clinch_river_va`
on prod (121 HUC12 rows landed), so re-run the same HUC8-06010205-filtered
ST_Union now via this follow-up migration. The prod DB is private (no direct
psql), so a migration deployed via the migrate job is the way to apply it.

Idempotent + a no-op locally (boundary already set by cl07 where wbd ran first).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'cl08a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl07a1b2c3d4'
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
          AND boundary IS NULL
          AND EXISTS (
            SELECT 1 FROM watershed_boundaries
            WHERE site_id = sites.id AND huc12 LIKE '06010205%'
          )
    """)


def downgrade() -> None:
    # No-op: cl07 owns the boundary lifecycle for this watershed.
    pass
