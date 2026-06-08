"""species_aliases — admin override map for long-tail fish names (FEAT-026 P2)

Revision ID: sa30a1b2c3d4
Revises: sk20a1b2c3d4
Create Date: 2026-06-08 00:00:00.000000

The deterministic canonicalizer (app/lib/species_canonical.py) collapses the
common variants automatically, but can't infer the long tail (e.g. "Columbia
River Redband Trout" → Rainbow Trout). This table lets an admin map a raw name
to a canonical label without a code change; canonicalize() consults it first.

  gold.species_aliases (raw_name PK, canonical_label, created_by_user_id, created_at)

raw_name is the lowercased raw common_name. Global (applies to every watershed).
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'sa30a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'sk20a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS gold.species_aliases (
            raw_name           varchar(160) PRIMARY KEY,
            canonical_label    varchar(120) NOT NULL,
            created_by_user_id uuid NULL,
            created_at         timestamptz NOT NULL DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gold.species_aliases")
