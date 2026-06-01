"""index silver.species_observations(site_id, obs_year, taxon_name)

Revision ID: ro2so3idx4567
Revises: rh2optimize01
Create Date: 2026-06-01 00:00:00.000000

gold.restoration_outcomes runs two correlated subqueries per intervention row,
each: count(DISTINCT taxon_name) FROM silver.species_observations WHERE
site_id = i.site_id AND obs_year BETWEEN ... There was no (site_id, obs_year)
index, so each subquery did a BitmapAnd of the site_id index (~224k rows/site)
with the (watershed, obs_year) index (obs_year can't lead it) — a heap-read
storm. On the 4 GB prod instance the working set doesn't fit in cache, so the
refresh ran 13+ min on disk I/O (IO/DataFileRead) and was the post-
river_health_score wall for refresh-heavy.

This covering index turns each subquery into an Index Only Scan over the exact
(site_id, obs_year) range with taxon_name available in the index — no heap.
Measured on prod-scale local data: plan cost 24.2M -> 76k (~318x); subquery
cost 34,037 -> 106 each. Pure index add — restoration_outcomes output is
unchanged (no query rewrite).

Non-unique index on a materialized view; maintained across REFRESH.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ro2so3idx4567'
down_revision: Union[str, Sequence[str], None] = 'rh2optimize01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_so_site_year_taxon
            ON silver.species_observations (site_id, obs_year, taxon_name)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS silver.ix_so_site_year_taxon")
