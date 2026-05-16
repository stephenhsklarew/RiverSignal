"""explode existing va_dwr stocking interventions from array species → per-species rows

Revision ID: pp16k7l8m9n0
Revises: oo15j6k7l8m9
Create Date: 2026-05-15 00:00:00.000000

The first VA DWR adapter pass stored `species` in `interventions.description`
as a JSON ARRAY (e.g. `["Brook Trout","Tiger Trout"]`). The downstream
`gold.species_by_reach` MV extracts it with `description::jsonb ->> 'species'`,
which returns the literal array TEXT for arrays — so the Catch Probability
panel rendered species names as `["Brook Trout","Tiger Trout"]` instead of
"Brook Trout". The photo-lookup join in `/sites/<ws>/fishing/species`
also failed because `common_name = '["Brook Trout","Tiger Trout"]'` matched
nothing in species_gallery.

The corrected adapter (`pipeline/ingest/virginia.py`) now emits one
intervention per species (UDWR-style scalar). This migration normalises
the existing rows by:

  1. For each va_dwr intervention whose description has an ARRAY `species`,
     INSERT one new intervention per element (preserving all other fields).
  2. DELETE the original array-shape rows.

Idempotent — re-runs on already-normalised data are no-ops because
`jsonb_typeof((description)::jsonb -> 'species')` won't be 'array' anymore.

Refreshes `gold.species_by_reach` and `gold.stocking_schedule` so the UI
picks up clean rows on next load.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'pp16k7l8m9n0'
down_revision: Union[str, Sequence[str], None] = 'oo15j6k7l8m9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: explode arrays into per-species rows.
    op.execute("""
        INSERT INTO interventions (id, site_id, type, description, started_at, created_at, location)
        SELECT gen_random_uuid(),
               i.site_id,
               i.type,
               jsonb_set(
                   (i.description)::jsonb,
                   '{species}',
                   to_jsonb(spec)
               )::text AS description,
               i.started_at,
               i.created_at,
               i.location
          FROM interventions i,
               LATERAL jsonb_array_elements_text((i.description)::jsonb -> 'species') AS spec
         WHERE i.type = 'fish_stocking'
           AND i.description LIKE '{%'
           AND ((i.description)::jsonb ->> 'source') = 'va_dwr'
           AND jsonb_typeof((i.description)::jsonb -> 'species') = 'array'
    """)
    # Step 2: drop the original array-shape rows.
    op.execute("""
        DELETE FROM interventions
         WHERE type = 'fish_stocking'
           AND description LIKE '{%'
           AND ((description)::jsonb ->> 'source') = 'va_dwr'
           AND jsonb_typeof((description)::jsonb -> 'species') = 'array'
    """)
    # Step 3: refresh dependent gold MVs so the UI sees the fix immediately
    # (otherwise the change waits for the next scheduled refresh).
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")
    op.execute("REFRESH MATERIALIZED VIEW gold.stocking_schedule")


def downgrade() -> None:
    # No-op: the array shape was an early-onboarding regression that we never
    # want to recreate. Running this migration's upgrade() against already-
    # normalised data is harmless.
    pass
