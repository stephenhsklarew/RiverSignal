"""curated_species_photos: per-watershed scoping with '*' = global default

Revision ID: ah33b4c5d6e7
Revises: ag32a3b4c5d6
Create Date: 2026-05-17 00:00:00.000000

v0 of the admin console modelled photos as one-per-species globally.
Product intent is per-watershed curation with optional sharing: most
species use the same photo everywhere, but a curator can choose to
specialise (e.g. an Oregon-shot Brown Trout for /path/now/mckenzie
distinct from a Mossy-Creek Brown Trout for /path/now/shenandoah).

Schema:
- Add `watershed varchar(50) NOT NULL DEFAULT '*'` to
  gold.curated_species_photos.
- Existing rows default to watershed='*' = global default.
- Composite PK changes from (species_key) to (species_key, watershed).
- Audit log gains a watershed column too.

Lookup precedence in app/routers/fishing.py becomes:
  iNat (species_gallery) < global default ('*') < watershed-specific.

Backwards-compatible: 100% of existing seeded rows become '*' = global
and the public API behaves identically until a curator creates a
watershed-specific override.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ah33b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'ag32a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the watershed column with the '*' default. Existing rows
    #    pick up '*' automatically.
    op.execute("""
        ALTER TABLE gold.curated_species_photos
          ADD COLUMN IF NOT EXISTS watershed varchar(50) NOT NULL DEFAULT '*'
    """)

    # 2. Swap the PK from (species_key) to (species_key, watershed).
    #    The auto-generated constraint name is curated_species_photos_pkey.
    op.execute("""
        ALTER TABLE gold.curated_species_photos
          DROP CONSTRAINT IF EXISTS curated_species_photos_pkey
    """)
    op.execute("""
        ALTER TABLE gold.curated_species_photos
          ADD PRIMARY KEY (species_key, watershed)
    """)

    # 3. Audit log gets watershed too so the timeline can record which
    #    scope was changed.
    op.execute("""
        ALTER TABLE audit.curated_species_photos_log
          ADD COLUMN IF NOT EXISTS watershed varchar(50) NOT NULL DEFAULT '*'
    """)


def downgrade() -> None:
    # No safe downgrade — collapsing back to species_key-only PK would
    # silently drop watershed-specific rows.
    pass
