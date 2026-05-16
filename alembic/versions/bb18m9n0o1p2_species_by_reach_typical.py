"""add silver.river_reaches.typical_species as 5th UNION in gold.species_by_reach

Revision ID: bb18m9n0o1p2
Revises: qq17l8m9n0o1, aa01b2c3d4e5
Create Date: 2026-05-16 00:00:00.000000

Two purposes in one migration:

  1. **Merge** the two parallel alembic heads created when the SMS-alerts
     foundation branch (`aa01b2c3d4e5`) and the Shenandoah-coverage branch
     (`qq17l8m9n0o1`) both forked off `z7d8e9f0a1b2`.
  2. Extend `gold.species_by_reach` with a fifth UNION block that pulls
     curated species from `silver.river_reaches.typical_species`. This
     surfaces warmwater game fish (smallmouth_bass, channel_catfish, etc.)
     on warmwater reaches without waiting for iNaturalist coverage to
     catch up. See `plan-2026-05-15-warmwater-species-coverage.md` Phase 3.

Underscore-separated names in `typical_species` (e.g. `smallmouth_bass`) are
normalised to space-separated common names so substring matching in
`pipeline/predictions/catch_forecast.py::SPECIES_MODELS` picks them up.

Refreshes the MV at the end so the UI sees the new rows immediately.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'bb18m9n0o1p2'
down_revision: Union[str, Sequence[str], None] = ('qq17l8m9n0o1', 'aa01b2c3d4e5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.species_by_reach AS
-- 1. ODFW fish habitat distribution (Oregon)
 SELECT o.site_id,
    s.watershed,
    (o.data_payload ->> 'stream') AS stream_name,
    o.taxon_name AS scientific_name,
    (o.data_payload ->> 'species') AS common_name,
    (o.data_payload ->> 'run') AS run_type,
    (o.data_payload ->> 'use_type') AS use_type,
    (o.data_payload ->> 'origin') AS origin,
    (o.data_payload ->> 'life_history') AS life_history,
    (o.data_payload ->> 'basis') AS data_basis,
    ( SELECT count(*) FROM observations obs
       WHERE obs.site_id = o.site_id AND obs.source_type = 'inaturalist'
         AND obs.taxon_name = o.taxon_name ) AS inat_observation_count,
    ( SELECT max(obs.observed_at)::date FROM observations obs
       WHERE obs.site_id = o.site_id AND obs.source_type = 'inaturalist'
         AND obs.taxon_name = o.taxon_name ) AS last_inat_observation
   FROM observations o JOIN sites s ON s.id = o.site_id
  WHERE o.source_type = 'fish_habitat'
UNION ALL
-- 2. WA SalmonScape
 SELECT w.site_id,
    s.watershed,
    w.stream_name,
    w.species AS scientific_name,
    w.species AS common_name,
    w.species_run AS run_type,
    w.use_type,
    NULL::text AS origin,
    w.life_history,
    w.distribution_type AS data_basis,
    0 AS inat_observation_count,
    NULL::date AS last_inat_observation
   FROM wa_salmonscape w JOIN sites s ON s.id = w.site_id
UNION ALL
-- 3. Stocked fish from interventions (any source)
 SELECT DISTINCT i.site_id,
    s.watershed,
    (i.description)::jsonb ->> 'waterbody' AS stream_name,
    NULL::text AS scientific_name,
    (i.description)::jsonb ->> 'species' AS common_name,
    NULL::text AS run_type,
    'rearing'::text AS use_type,
    'stocked'::text AS origin,
    NULL::text AS life_history,
    (((i.description)::jsonb ->> 'source') || '_stocking')::text AS data_basis,
    0 AS inat_observation_count,
    NULL::date AS last_inat_observation
   FROM interventions i JOIN sites s ON s.id = i.site_id
  WHERE i.type = 'fish_stocking'
    AND i.description IS NOT NULL
    AND i.description LIKE '{%'
    AND ((i.description)::jsonb ->> 'species') IS NOT NULL
    AND ((i.description)::jsonb ->> 'source') IS NOT NULL
UNION ALL
-- 4. iNaturalist research-grade fish observations
 SELECT DISTINCT o.site_id,
    s.watershed,
    NULL::text AS stream_name,
    o.taxon_name AS scientific_name,
    COALESCE(o.data_payload ->> 'common_name', o.taxon_name) AS common_name,
    NULL::text AS run_type,
    NULL::text AS use_type,
    'wild'::text AS origin,
    NULL::text AS life_history,
    'inaturalist'::text AS data_basis,
    ( SELECT count(*) FROM observations obs2
       WHERE obs2.site_id = o.site_id AND obs2.source_type = 'inaturalist'
         AND obs2.taxon_name = o.taxon_name ) AS inat_observation_count,
    ( SELECT max(obs2.observed_at)::date FROM observations obs2
       WHERE obs2.site_id = o.site_id AND obs2.source_type = 'inaturalist'
         AND obs2.taxon_name = o.taxon_name ) AS last_inat_observation
   FROM observations o JOIN sites s ON s.id = o.site_id
  WHERE o.source_type = 'inaturalist'
    AND o.iconic_taxon = 'Actinopterygii'
    AND o.quality_grade = 'research'
UNION ALL
-- 5. Curated species from silver.river_reaches.typical_species
--    Surfaces warmwater game fish (smallmouth_bass, channel_catfish, etc.)
--    on reaches that ecologically support them, independent of iNat
--    coverage or state agency stocking data. Underscore-separated names
--    are normalised to spaces so substring matching in catch_forecast
--    SPECIES_MODELS picks them up.
 SELECT DISTINCT s.id AS site_id,
    r.watershed,
    r.name AS stream_name,
    NULL::text AS scientific_name,
    replace(unnest(r.typical_species), '_', ' ') AS common_name,
    NULL::text AS run_type,
    NULL::text AS use_type,
    (CASE WHEN r.is_warm_water THEN 'warmwater_native' ELSE 'coldwater_native' END)::text AS origin,
    NULL::text AS life_history,
    'reach_curated'::text AS data_basis,
    0 AS inat_observation_count,
    NULL::date AS last_inat_observation
   FROM silver.river_reaches r JOIN sites s ON s.watershed = r.watershed
  WHERE r.is_active IS NOT FALSE
    AND r.typical_species IS NOT NULL
    AND array_length(r.typical_species, 1) > 0
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.species_by_reach CASCADE")
    op.execute(NEW_VIEW_SQL)
    op.execute("CREATE INDEX ix_gold_species_by_reach_watershed ON gold.species_by_reach (watershed)")
    op.execute("CREATE INDEX ix_gold_species_by_reach_common ON gold.species_by_reach (common_name)")
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")


def downgrade() -> None:
    # Downgrade re-runs the prior 4-UNION definition from oo15j6k7l8m9.
    # No-op kept simple — the merge nature of this revision means a true
    # downgrade would have to fork the chain again, which we never want.
    pass
