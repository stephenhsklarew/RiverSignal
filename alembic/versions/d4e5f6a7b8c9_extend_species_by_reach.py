"""extend gold.species_by_reach with UDWR stocking + iNat fallback

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-10 00:00:00.000000

Adds two UNION blocks to gold.species_by_reach so non-PNW watersheds
(e.g. Green River) get species coverage:

  Block A — UDWR fish stocking from `interventions` (already ingested by
            pipeline.ingest.utah). Surfaces stocked species in the
            Green River / Flaming Gorge area.

  Block C — iNaturalist research-grade Actinopterygii. Acts as a
            global safety net for any watershed without StreamNet,
            SalmonScape, or fish_stocking data. Scoped via NOT IN to
            avoid duplicating species in watersheds that already have
            structured coverage.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.species_by_reach AS
-- ODFW StreamNet (Pacific Northwest)
 SELECT o.site_id,
    s.watershed,
    o.data_payload ->> 'stream'::text AS stream_name,
    o.taxon_name AS scientific_name,
    o.data_payload ->> 'species'::text AS common_name,
    o.data_payload ->> 'run'::text AS run_type,
    o.data_payload ->> 'use_type'::text AS use_type,
    o.data_payload ->> 'origin'::text AS origin,
    o.data_payload ->> 'life_history'::text AS life_history,
    o.data_payload ->> 'basis'::text AS data_basis,
    ( SELECT count(*) FROM observations obs
       WHERE obs.site_id = o.site_id AND obs.source_type::text = 'inaturalist'::text AND obs.taxon_name::text = o.taxon_name::text) AS inat_observation_count,
    ( SELECT max(obs.observed_at)::date FROM observations obs
       WHERE obs.site_id = o.site_id AND obs.source_type::text = 'inaturalist'::text AND obs.taxon_name::text = o.taxon_name::text) AS last_inat_observation
   FROM observations o
     JOIN sites s ON s.id = o.site_id
  WHERE o.source_type::text = 'fish_habitat'::text
UNION ALL
-- WDFW SalmonScape (Washington)
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
   FROM wa_salmonscape w
     JOIN sites s ON s.id = w.site_id
UNION ALL
-- UDWR Fish Stocking (Utah / Green River basin).
-- pipeline.ingest.utah stores the JSON payload as text in interventions.description,
-- so we cast through jsonb. Filter defensively to JSON-shaped descriptions.
 SELECT DISTINCT
    i.site_id,
    s.watershed,
    (i.description::jsonb) ->> 'waterbody'::text AS stream_name,
    NULL::text AS scientific_name,
    (i.description::jsonb) ->> 'species'::text AS common_name,
    NULL::text AS run_type,
    'rearing'::text AS use_type,
    'stocked'::text AS origin,
    NULL::text AS life_history,
    'udwr_stocking'::text AS data_basis,
    0 AS inat_observation_count,
    NULL::date AS last_inat_observation
   FROM interventions i
     JOIN sites s ON s.id = i.site_id
  WHERE i.type::text = 'fish_stocking'::text
    AND i.description IS NOT NULL
    AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'udwr'::text
    AND ((i.description::jsonb) ->> 'species'::text) IS NOT NULL
UNION ALL
-- iNaturalist Actinopterygii fallback for watersheds with no structured fish data
 SELECT DISTINCT
    o.site_id,
    s.watershed,
    NULL::text AS stream_name,
    o.taxon_name AS scientific_name,
    COALESCE(o.data_payload ->> 'common_name'::text, o.taxon_name) AS common_name,
    NULL::text AS run_type,
    NULL::text AS use_type,
    'wild'::text AS origin,
    NULL::text AS life_history,
    'inaturalist'::text AS data_basis,
    ( SELECT count(*) FROM observations obs2
       WHERE obs2.site_id = o.site_id AND obs2.source_type::text = 'inaturalist'::text AND obs2.taxon_name::text = o.taxon_name::text) AS inat_observation_count,
    ( SELECT max(obs2.observed_at)::date FROM observations obs2
       WHERE obs2.site_id = o.site_id AND obs2.source_type::text = 'inaturalist'::text AND obs2.taxon_name::text = o.taxon_name::text) AS last_inat_observation
   FROM observations o
     JOIN sites s ON s.id = o.site_id
  WHERE o.source_type::text = 'inaturalist'::text
    AND o.iconic_taxon::text = 'Actinopterygii'::text
    AND o.quality_grade::text = 'research'::text
    AND s.watershed NOT IN (
        SELECT DISTINCT s2.watershed
          FROM observations o2 JOIN sites s2 ON s2.id = o2.site_id
         WHERE o2.source_type::text = 'fish_habitat'::text
        UNION
        SELECT DISTINCT s2.watershed
          FROM wa_salmonscape w2 JOIN sites s2 ON s2.id = w2.site_id
        UNION
        SELECT DISTINCT s2.watershed
          FROM interventions i2 JOIN sites s2 ON s2.id = i2.site_id
         WHERE i2.type::text = 'fish_stocking'::text
    );
"""

OLD_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.species_by_reach AS
 SELECT o.site_id,
    s.watershed,
    o.data_payload ->> 'stream'::text AS stream_name,
    o.taxon_name AS scientific_name,
    o.data_payload ->> 'species'::text AS common_name,
    o.data_payload ->> 'run'::text AS run_type,
    o.data_payload ->> 'use_type'::text AS use_type,
    o.data_payload ->> 'origin'::text AS origin,
    o.data_payload ->> 'life_history'::text AS life_history,
    o.data_payload ->> 'basis'::text AS data_basis,
    ( SELECT count(*) FROM observations obs
       WHERE obs.site_id = o.site_id AND obs.source_type::text = 'inaturalist'::text AND obs.taxon_name::text = o.taxon_name::text) AS inat_observation_count,
    ( SELECT max(obs.observed_at)::date FROM observations obs
       WHERE obs.site_id = o.site_id AND obs.source_type::text = 'inaturalist'::text AND obs.taxon_name::text = o.taxon_name::text) AS last_inat_observation
   FROM observations o
     JOIN sites s ON s.id = o.site_id
  WHERE o.source_type::text = 'fish_habitat'::text
UNION ALL
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
   FROM wa_salmonscape w
     JOIN sites s ON s.id = w.site_id;
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.species_by_reach CASCADE")
    op.execute(NEW_VIEW_SQL)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.species_by_reach CASCADE")
    op.execute(OLD_VIEW_SQL)
