"""Rewrite gold.post_fire_recovery to use sargable date-range predicates

Revision ID: ak36e7f8a9b0
Revises: aj35d6e7f8a9
Create Date: 2026-05-24 13:30:00.000000

The old MV used two correlated subqueries against observations with
`WHERE EXTRACT(year FROM o.observed_at) = fy.obs_year`. EXTRACT() on the
indexed column is non-sargable — it prevents the planner from using the
existing `ix_obs_site_observed` btree on `(site_id, observed_at)`. With
Shenandoah onboarding adding ~1M observations to one site, each
correlated scan had to evaluate EXTRACT() on every row for that site;
459 fire-year rows × 2 subqueries × full-site-scan = ~37 minutes per
refresh. That ate the bulk of the refresh_views budget.

This migration rewrites the two subqueries to use:
    WHERE site_id = fy.site_id
      AND observed_at >= make_date(fy.obs_year,     1, 1)
      AND observed_at <  make_date(fy.obs_year + 1, 1, 1)
which the planner CAN serve from `ix_obs_site_observed` as a tight range
scan. Expected refresh time: seconds, not minutes.

No data shape changes — same columns, same values. Pure query-plan fix.

Downgrade restores the EXTRACT-based form for completeness (and so the
migration is reversible) but you really wouldn't want to.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ak36e7f8a9b0'
down_revision: Union[str, Sequence[str], None] = 'aj35d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.post_fire_recovery AS
 WITH fire_years AS (
         SELECT fp.site_id,
            fp.fire_name,
            fp.fire_year,
            fp.acres,
            fp.fire_year + gs.yr_delta AS obs_year,
            gs.yr_delta AS years_since_fire
           FROM fire_perimeters fp
             CROSS JOIN generate_series('-2'::integer, 6) gs(yr_delta)
          WHERE fp.fire_year >= 2015
            AND fp.acres > 1000::double precision
            AND (fp.fire_year + gs.yr_delta) >= 2013
            AND (fp.fire_year + gs.yr_delta) <= 2026
        )
 SELECT DISTINCT ON (fy.site_id, fy.fire_name, fy.obs_year)
    fy.site_id,
    s.watershed,
    fy.fire_name,
    fy.fire_year,
    fy.acres,
    fy.obs_year AS observation_year,
    fy.years_since_fire,
    ( SELECT count(DISTINCT o.taxon_name) AS count
        FROM observations o
       WHERE o.site_id = fy.site_id
         AND o.observed_at >= make_date(fy.obs_year, 1, 1)
         AND o.observed_at <  make_date(fy.obs_year + 1, 1, 1)
         AND o.taxon_name IS NOT NULL
    ) AS species_total_watershed,
    ( SELECT count(*) AS count
        FROM observations o
       WHERE o.site_id = fy.site_id
         AND o.observed_at >= make_date(fy.obs_year, 1, 1)
         AND o.observed_at <  make_date(fy.obs_year + 1, 1, 1)
         AND o.taxon_name IS NOT NULL
    ) AS total_obs_that_year
   FROM fire_years fy
     JOIN sites s ON s.id = fy.site_id
  ORDER BY fy.site_id, fy.fire_name, fy.obs_year
"""


OLD_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.post_fire_recovery AS
 WITH fire_years AS (
         SELECT fp.site_id,
            fp.fire_name,
            fp.fire_year,
            fp.acres,
            fp.fire_year + gs.yr_delta AS obs_year,
            gs.yr_delta AS years_since_fire
           FROM fire_perimeters fp
             CROSS JOIN generate_series('-2'::integer, 6) gs(yr_delta)
          WHERE fp.fire_year >= 2015
            AND fp.acres > 1000::double precision
            AND (fp.fire_year + gs.yr_delta) >= 2013
            AND (fp.fire_year + gs.yr_delta) <= 2026
        )
 SELECT DISTINCT ON (fy.site_id, fy.fire_name, fy.obs_year)
    fy.site_id,
    s.watershed,
    fy.fire_name,
    fy.fire_year,
    fy.acres,
    fy.obs_year AS observation_year,
    fy.years_since_fire,
    ( SELECT count(DISTINCT o.taxon_name) AS count
        FROM observations o
       WHERE o.site_id = fy.site_id
         AND EXTRACT(year FROM o.observed_at) = fy.obs_year::numeric
         AND o.taxon_name IS NOT NULL
    ) AS species_total_watershed,
    ( SELECT count(*) AS count
        FROM observations o
       WHERE o.site_id = fy.site_id
         AND EXTRACT(year FROM o.observed_at) = fy.obs_year::numeric
         AND o.taxon_name IS NOT NULL
    ) AS total_obs_that_year
   FROM fire_years fy
     JOIN sites s ON s.id = fy.site_id
  ORDER BY fy.site_id, fy.fire_name, fy.obs_year
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.post_fire_recovery CASCADE")
    op.execute(NEW_VIEW_SQL)
    op.execute("REFRESH MATERIALIZED VIEW gold.post_fire_recovery")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.post_fire_recovery CASCADE")
    op.execute(OLD_VIEW_SQL)
    op.execute("REFRESH MATERIALIZED VIEW gold.post_fire_recovery")
