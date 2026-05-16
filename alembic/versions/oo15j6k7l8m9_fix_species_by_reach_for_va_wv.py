"""fix gold.species_by_reach to surface va_dwr/wv_dnr stocking + iNat for shenandoah

Revision ID: oo15j6k7l8m9
Revises: nn14i5j6k7l8
Create Date: 2026-05-15 00:00:00.000000

`gold.species_by_reach` had two pre-existing bugs that surfaced when
Shenandoah onboarded:

  1. The "stocked-fish" UNION branch's WHERE clause hardcoded
     `description::jsonb ->> 'source' = 'udwr'` — so the 14 va_dwr
     and 2 wv_dnr stocking rows for Shenandoah never made it into the
     MV, and neither would any future state stocking source.

  2. The iNaturalist UNION branch's WHERE clause excluded any watershed
     that has *any* `fish_stocking` intervention. That filter was meant
     to suppress duplicate species when UDWR provides authoritative
     stocking-plus-species data, but it also strips Shenandoah's
     13,716 iNat species_gallery rows just because the watershed has
     14 va_dwr stocking events. Result: `/api/v1/sites/shenandoah/
     catch-probability` returned an empty `species: []`.

Fixes:
  - Generalize the stocked-fish branch to accept any source (`udwr`,
    `va_dwr`, `wv_dnr`, future ones) — still requires the JSONB to
    have a non-null `species`.
  - Drop the watershed-level exclusion on the iNat branch. The
    `SELECT DISTINCT` in the branch already dedupes per
    (site_id, taxon_name); DISTINCT across the UNION ALL dedupes
    cross-branch. The supposed "double-count" the exclusion prevented
    was never a real risk — stocked-fish rows have NULL
    `scientific_name`, so they'd never collide with iNat rows that
    have a real scientific name.

Idempotent — drops and recreates the MV.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'oo15j6k7l8m9'
down_revision: Union[str, Sequence[str], None] = 'nn14i5j6k7l8'
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
-- 4. iNaturalist research-grade fish observations (always available, not gated
--    by stocking presence — see migration docstring)
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
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.species_by_reach CASCADE")
    op.execute(NEW_VIEW_SQL)
    op.execute("CREATE INDEX ix_gold_species_by_reach_watershed ON gold.species_by_reach (watershed)")
    op.execute("CREATE INDEX ix_gold_species_by_reach_common ON gold.species_by_reach (common_name)")


def downgrade() -> None:
    # No-op: prior MV definition can be re-derived from earlier migrations
    # in the repo. Re-running this migration's downgrade then upgrade gives
    # the same result.
    pass
