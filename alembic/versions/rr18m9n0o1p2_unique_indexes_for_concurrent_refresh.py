"""add unique indexes on heavy MVs so REFRESH CONCURRENTLY works

Revision ID: rr18m9n0o1p2
Revises: qq17l8m9n0o1
Create Date: 2026-05-16 00:00:00.000000

Partial closure of bead RiverSignal-6a76a3ae. `pipeline/medallion.py`'s
_refresh_view tries REFRESH MATERIALIZED VIEW CONCURRENTLY but falls back
to the blocking form when an MV has no UNIQUE index — which is every
heavy MV today. Blocking refresh holds an exclusive lock that makes
/path/now/* and /riversignal unreadable for the duration.

Duplicate analysis (run 2026-05-16 on local 2.0M-obs dataset):

  MV                       total    distinct(natural-key)   dups
  -----------------------  -------  ----------------------  ----
  species_gallery          56,730   56,730                  0 ✓
  hatch_chart              13,880   13,880                  0 ✓
  species_by_reach          2,600    2,517                  83
  stocking_schedule        12,110   12,050                  60
  river_miles             114,461  111,360                3,101

The first two have natural keys that are already unique — this migration
adds UNIQUE indexes on them, unblocking CONCURRENT refresh for the two
biggest MVs in user-visible request paths.

The remaining three need MV-shape fixes (outer SELECT DISTINCT / GROUP
BY) before a unique index can be created. Tracked as a residual subtask
under bead RiverSignal-6a76a3ae.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'rr18m9n0o1p2'
down_revision: Union[str, Sequence[str], None] = 'qq17l8m9n0o1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # species_gallery: SELECT DISTINCT ON (s.watershed, o.taxon_name) ...
    # The DISTINCT ON guarantees one row per (watershed, taxon_name).
    # site_id is functionally determined by watershed for our schema (one
    # site per watershed), so (site_id, taxon_name) is equivalent and also
    # unique — pick that since both fields are already NOT NULL.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_species_gallery_site_taxon
            ON gold.species_gallery (site_id, taxon_name)
    """)

    # hatch_chart: GROUP BY site_id, watershed, taxon_name, common_name,
    # obs_month — the unique key is (site_id, taxon_name, obs_month) since
    # common_name is functionally determined by taxon_name.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_hatch_chart_site_taxon_month
            ON gold.hatch_chart (site_id, taxon_name, obs_month)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS gold.uq_species_gallery_site_taxon")
    op.execute("DROP INDEX IF EXISTS gold.uq_hatch_chart_site_taxon_month")
