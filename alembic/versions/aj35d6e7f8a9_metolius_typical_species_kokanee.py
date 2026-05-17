"""Metolius typical_species: kokanee + reintroduced salmon below Bridge 99, brook + brown trout in headwaters

Revision ID: aj35d6e7f8a9
Revises: ai34c5d6e7f8
Create Date: 2026-05-17 12:00:00.000000

The two Metolius reaches in `silver.river_reaches` were seeded with only
`rainbow_trout,bull_trout`, which understated what's actually in the river:

  - **Kokanee** (Oncorhynchus nerka, landlocked form) run up from Lake Billy
    Chinook every fall to spawn in the lower / middle Metolius. Long-standing
    wild population, no stocking.
  - **Chinook** and **Sockeye** (anadromous forms) have been reintroduced
    via the Pelton-Round Butte fish-passage program: smolts are trapped
    above the dam and trucked downstream, adults return to the lower river.
  - **Brook trout** — small wild population, mostly in the upper Metolius
    (Camp Sherman to Bridge 99).
  - **Brown trout** — limited population, headwaters reach.

Per-reach distribution honours the river's ecology rather than blanketing
both reaches:

  metolius_headwaters  + brook_trout, brown_trout
                       (cold headwaters; salmon don't make it this far up)
  metolius_middle      + kokanee, sockeye_salmon, chinook_salmon
                       (anadromous reach below Bridge 99 toward Lake Billy
                        Chinook; spawning kokanee + reintroduced salmon
                        both terminate here)

`gold.species_by_reach` is refreshed so Fish Present picks up the new rows
immediately. Photos for kokanee fall through the alias map in
`app/routers/fishing.py` (`kokanee -> sockeye salmon`); chinook + sockeye
photos are already in `gold.species_gallery` from iNat coverage. Brook +
brown trout photos similarly come from existing curated entries.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'aj35d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'ai34c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE silver.river_reaches
           SET typical_species = ARRAY['rainbow_trout','bull_trout','brook_trout','brown_trout']::text[]
         WHERE id = 'metolius_headwaters'
    """)
    op.execute("""
        UPDATE silver.river_reaches
           SET typical_species = ARRAY['rainbow_trout','bull_trout','kokanee','sockeye_salmon','chinook_salmon']::text[]
         WHERE id = 'metolius_middle'
    """)
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")


def downgrade() -> None:
    op.execute("""
        UPDATE silver.river_reaches
           SET typical_species = ARRAY['rainbow_trout','bull_trout']::text[]
         WHERE id IN ('metolius_headwaters', 'metolius_middle')
    """)
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")
