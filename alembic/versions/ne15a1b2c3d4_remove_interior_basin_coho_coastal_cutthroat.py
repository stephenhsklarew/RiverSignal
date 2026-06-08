"""remove FHD coho + coastal cutthroat from interior-basin reaches

Revision ID: ne15a1b2c3d4
Revises: nd14a1b2c3d4
Create Date: 2026-06-07 00:00:00.000000

Prod fish-present audit (2026-06-07) found Coho and Coastal Cutthroat Trout
surfacing for the Metolius and John Day — interior Columbia-basin watersheds
that are redband + (headwater) westslope-cutthroat country, where neither
species occurs. Root cause: pipeline/ingest/fishing.py queried ODFW's statewide
FHD layers 7 (Coho) and 19 (Coastal Cutthroat Trout) for every Oregon
watershed; those layers' features intersect interior reaches. The adapter is
now gated to coastal-draining watersheds (mckenzie, klamath) for those two
layers, so they won't re-ingest here.

This removes the already-ingested fish_habitat observations so the change
surfaces now (re-ingest only upserts — it would not delete them). Scoped to
interior basins (johnday, metolius, deschutes); coastal-draining watersheds
keep their legitimate coho/coastal-cutthroat records. iNat-backed strays in the
lower Deschutes are untouched (different source_type). Refreshes the small
gold.species_by_reach (read live by /catch-probability + /fishing/species).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ne15a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nd14a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# FHD layer 7 = Coho, layer 19 = Coastal Cutthroat Trout.
INTERIOR_WATERSHEDS = ('johnday', 'metolius', 'deschutes')


def upgrade() -> None:
    op.execute("""
        DELETE FROM observations o
         USING sites s
         WHERE o.site_id = s.id
           AND o.source_type = 'fish_habitat'
           AND s.watershed IN ('johnday', 'metolius', 'deschutes')
           AND (o.source_id LIKE 'fhd_7_%' OR o.source_id LIKE 'fhd_19_%')
    """)
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")


def downgrade() -> None:
    # Deleted source rows are re-created by the next `fishing` ingest only for
    # the coastal-draining allowlist, so an interior-basin downgrade cannot
    # restore them. No-op beyond the MV refresh.
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")
