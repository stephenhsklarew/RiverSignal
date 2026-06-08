"""remove extirpated brook_trout from chattahoochee + mad_river_oh reaches

Revision ID: nd14a1b2c3d4
Revises: nc13a1b2c3d4
Create Date: 2026-06-07 00:00:00.000000

Fish Present (← gold.species_by_reach `reach_curated` branch ← river_reaches.
typical_species) listed Brook Trout for the Chattahoochee — but brook trout are
extirpated from the modeled reaches (last iNat record ~1970s). Same for the Mad
River OH (a brown-trout spring creek; brook trout absent — the only species in
its list with zero observations).

Scoped fix: drop 'brook_trout' from ONLY chattahoochee_headwaters and
mad_river_oh_upper. Brook trout is intentionally KEPT for metolius_headwaters and
the 7 Shenandoah native-trout tributaries (Smith/Mossy Creek, N/S Fork, etc.),
where it's a real, observation-backed population. typical_species is unfiltered
in the MV, so it must reflect currently-present species (see runbook §2.4).
Refreshes the small (~3k-row) gold.species_by_reach so the change surfaces.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'nd14a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nc13a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REACHES = ('chattahoochee_headwaters', 'mad_river_oh_upper')


def upgrade() -> None:
    op.execute("""
        UPDATE silver.river_reaches
           SET typical_species = array_remove(typical_species, 'brook_trout')
         WHERE id IN ('chattahoochee_headwaters', 'mad_river_oh_upper')
    """)
    # Small MV (~3k rows) — non-concurrent refresh is fast; surfaces the change
    # to /catch-probability and /fishing/species (both read it live).
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")


def downgrade() -> None:
    op.execute("""
        UPDATE silver.river_reaches
           SET typical_species = array_append(typical_species, 'brook_trout')
         WHERE id IN ('chattahoochee_headwaters', 'mad_river_oh_upper')
           AND NOT ('brook_trout' = ANY(typical_species))
    """)
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")
