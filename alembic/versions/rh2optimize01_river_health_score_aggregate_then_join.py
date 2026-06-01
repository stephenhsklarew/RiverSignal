"""Rewrite gold.river_health_score to aggregate-then-join (kill the fan-out)

Revision ID: rh2optimize01
Revises: rh1s2c3d4e5f
Create Date: 2026-05-31 00:00:00.000000

The old MV joined silver.water_conditions (filtered to ~143k rows) to
silver.species_observations (~2M rows) on (site_id, obs_year, obs_month)
and THEN aggregated. Because both sides have many rows per
(site, year, month), the LEFT JOIN fanned out to a ~12.6M-row intermediate
that was sorted and grouped back down to a few hundred rows. That fan-out is
what made the refresh take ~30+ min (and, with the CONCURRENTLY delta on top,
blew the 2h refresh-heavy budget).

This rewrite pre-aggregates each source to the (site_id, obs_year, obs_month)
grain in CTEs, then joins the two small aggregates. No fan-out. Measured on
prod-scale local data (9.84M time_series / 2M observations): plan cost
~11.06M -> ~908k, intermediate rows 12.6M -> 249, execution ~45 min -> 3.5 s.

Equivalence verified row-for-row against the prior materialized MV: every
existing group matches exactly (0 value mismatches); the rewrite only adds the
groups the stale MV had not yet picked up. Same columns, same types, same
values. Pure query-plan fix.

DROP ... CASCADE removes the unique index from rh1s2c3d4e5f, so we recreate
river_health_score_uniq_idx after the CREATE to preserve the CONCURRENTLY
(non-blocking) refresh path.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'rh2optimize01'
down_revision: Union[str, Sequence[str], None] = 'rh1s2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_UNIQUE_INDEX = (
    "CREATE UNIQUE INDEX IF NOT EXISTS river_health_score_uniq_idx "
    "ON gold.river_health_score (site_id, obs_year, obs_month)"
)


NEW_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.river_health_score AS
 WITH wc_agg AS (
         SELECT water_conditions.site_id,
            water_conditions.obs_year,
            water_conditions.obs_month,
            avg(
                CASE
                    WHEN (((water_conditions.parameter)::text = 'water_temperature'::text) AND ((water_conditions.source_type)::text = 'usgs'::text)) THEN water_conditions.value
                    ELSE NULL::numeric
                END) AS avg_temp,
            avg(
                CASE
                    WHEN ((water_conditions.parameter)::text = 'dissolved_oxygen'::text) THEN water_conditions.value
                    ELSE NULL::numeric
                END) AS avg_do
           FROM silver.water_conditions
          WHERE ((water_conditions.obs_year >= 2024) AND ((water_conditions.parameter)::text = ANY (ARRAY[('water_temperature'::character varying)::text, ('dissolved_oxygen'::character varying)::text, ('discharge'::character varying)::text])))
          GROUP BY water_conditions.site_id, water_conditions.obs_year, water_conditions.obs_month
        ), so_agg AS (
         SELECT species_observations.site_id,
            species_observations.obs_year,
            species_observations.obs_month,
            count(DISTINCT species_observations.taxon_name) AS monthly_species
           FROM silver.species_observations
          WHERE (species_observations.taxon_name IS NOT NULL)
          GROUP BY species_observations.site_id, species_observations.obs_year, species_observations.obs_month
        )
 SELECT s.id AS site_id,
    s.watershed,
    s.name AS watershed_name,
    wc.obs_year,
    wc.obs_month,
    COALESCE(so.monthly_species, (0)::bigint) AS monthly_species,
    round(wc.avg_temp, 1) AS avg_water_temp,
    round(wc.avg_do, 1) AS avg_do,
    ((30 +
        CASE
            WHEN (wc.avg_temp < (16)::numeric) THEN 20
            ELSE 10
        END) +
        CASE
            WHEN (wc.avg_do > (8)::numeric) THEN 20
            ELSE 10
        END) AS health_score
   FROM ((sites s
     JOIN wc_agg wc ON ((wc.site_id = s.id)))
     LEFT JOIN so_agg so ON (((so.site_id = s.id) AND (so.obs_year = wc.obs_year) AND (so.obs_month = wc.obs_month))))
"""


OLD_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.river_health_score AS
 SELECT s.id AS site_id,
    s.watershed,
    s.name AS watershed_name,
    wc.obs_year,
    wc.obs_month,
    count(DISTINCT so.taxon_name) AS monthly_species,
    round(avg(
        CASE
            WHEN (((wc.parameter)::text = 'water_temperature'::text) AND ((wc.source_type)::text = 'usgs'::text)) THEN wc.value
            ELSE NULL::numeric
        END), 1) AS avg_water_temp,
    round(avg(
        CASE
            WHEN ((wc.parameter)::text = 'dissolved_oxygen'::text) THEN wc.value
            ELSE NULL::numeric
        END), 1) AS avg_do,
    ((30 +
        CASE
            WHEN (avg(
            CASE
                WHEN (((wc.parameter)::text = 'water_temperature'::text) AND ((wc.source_type)::text = 'usgs'::text)) THEN wc.value
                ELSE NULL::numeric
            END) < (16)::numeric) THEN 20
            ELSE 10
        END) +
        CASE
            WHEN (avg(
            CASE
                WHEN ((wc.parameter)::text = 'dissolved_oxygen'::text) THEN wc.value
                ELSE NULL::numeric
            END) > (8)::numeric) THEN 20
            ELSE 10
        END) AS health_score
   FROM ((sites s
     JOIN silver.water_conditions wc ON ((wc.site_id = s.id)))
     LEFT JOIN silver.species_observations so ON (((so.site_id = s.id) AND (so.obs_year = wc.obs_year) AND (so.obs_month = wc.obs_month) AND (so.taxon_name IS NOT NULL))))
  WHERE ((wc.obs_year >= 2024) AND ((wc.parameter)::text = ANY (ARRAY[('water_temperature'::character varying)::text, ('dissolved_oxygen'::character varying)::text, ('discharge'::character varying)::text])))
  GROUP BY s.id, s.watershed, s.name, wc.obs_year, wc.obs_month
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.river_health_score CASCADE")
    op.execute(NEW_VIEW_SQL)
    op.execute(_UNIQUE_INDEX)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.river_health_score CASCADE")
    op.execute(OLD_VIEW_SQL)
    op.execute(_UNIQUE_INDEX)
