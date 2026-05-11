"""clean wrong UDWR stocking rows from interventions

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-05-11 00:00:00.000000

The UDWR scraper in pipeline/ingest/utah.py had two bugs that landed
junk data in `interventions`:

  1. Column indexes were off-by-one relative to UDWR's current table
     layout. The `waterbody` JSON field actually held the *county* name
     ('PIUTE', 'BOX ELDER', etc.).
  2. The ?sortspecific URL param is a sort key, not a filter, so UDWR
     was returning every Utah stocking row and the adapter saved them
     all as Green River data.

This migration deletes all rows tagged with source='udwr' so the next
pipeline run can repopulate them with the now-correct column mapping
and post-filtered (in-basin only) data.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Wipe all UDWR-sourced fish_stocking rows. Safe to repopulate — the
    # next pipeline run rewrites them with correct data.
    op.execute("""
        DELETE FROM interventions
        WHERE type = 'fish_stocking'
          AND description IS NOT NULL
          AND description LIKE '{%'
          AND (description::jsonb ->> 'source') = 'udwr'
    """)
    # Refresh the downstream views that reference interventions.
    op.execute("REFRESH MATERIALIZED VIEW gold.stocking_schedule")
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")


def downgrade() -> None:
    # Nothing to restore — deleted rows can be repopulated by re-running
    # the Utah ingestion adapter.
    pass
