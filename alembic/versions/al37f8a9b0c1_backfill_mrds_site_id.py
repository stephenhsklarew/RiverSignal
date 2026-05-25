"""heal mineral_deposits rows missing site_id + image_url (Shenandoah and any future watershed)

Revision ID: al37f8a9b0c1
Revises: ak36e7f8a9b0
Create Date: 2026-05-25 00:00:00.000000

Two MRDS-adapter regressions surfaced when Shenandoah landed:

1. Commit 5eb5484 ("Link fossils and minerals to watersheds via
   site_id foreign key") added the FK column + backfilled existing
   rows + wired site_id into the PBDB and iDigBio adapters. It MISSED
   the MRDS adapter, so every MRDS ingest after 2026-05-05 produced
   rows with site_id = NULL — invisible to every watershed-scoped
   query (the entire mineral_deposits API path joins through sites).

2. Commit 6cfc671 ("Add fossil/mineral image enrichment …") raised
   mineral image coverage to 100% via Wikimedia Commons matched by
   commodity. The enrichment was apparently an ad-hoc script that
   never landed in the repo, so any new MRDS rows ingested after
   that commit had image_url = NULL.

The companion code fix in pipeline/ingest/geology.py:MRDSAdapter now
wires site_id into the INSERT + ON CONFLICT update. This migration
heals on-disk rows by:

  a) re-linking site_id via bbox containment (same approach as the
     5eb5484 backfill)
  b) propagating image_url / image_license / image_source from any
     existing row with the same commodity string

Step (b) doesn't cover every commodity in Shenandoah (~84% of rows by
count get an image; the remaining ~16% are commodities not seen in
other watersheds and need a separate Wikimedia lookup pass — handled
by the fossil-images backfill's Wikimedia step in a follow-on).

Idempotent — re-runs match zero rows.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'al37f8a9b0c1'
down_revision: Union[str, Sequence[str], None] = 'ak36e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # (a) Re-link orphan minerals to a site by bbox containment.
    op.execute("""
        UPDATE mineral_deposits m
           SET site_id = matched.id
          FROM (
            SELECT m2.id AS m_id, s.id
              FROM mineral_deposits m2
              JOIN sites s
                ON s.bbox IS NOT NULL
               AND (s.bbox->>'west')::float  <= m2.longitude
               AND (s.bbox->>'east')::float  >= m2.longitude
               AND (s.bbox->>'south')::float <= m2.latitude
               AND (s.bbox->>'north')::float >= m2.latitude
             WHERE m2.site_id IS NULL
               AND m2.latitude IS NOT NULL
               AND m2.longitude IS NOT NULL
          ) AS matched
         WHERE m.id = matched.m_id
    """)

    # (b) Propagate image_url from any existing row with the same
    # commodity string. Picks an arbitrary matching row's URL — any of
    # them is a category-representative photo (e.g. all "Gold" rows
    # share the same Wikimedia URL anyway). Leaves rows whose commodity
    # is unseen elsewhere untouched (~16% on Shenandoah at the time of
    # writing).
    op.execute("""
        UPDATE mineral_deposits m
           SET image_url     = picked.image_url,
               image_license = picked.image_license,
               image_source  = picked.image_source
          FROM (
            SELECT commodity,
                   (array_agg(image_url     ORDER BY ingested_at))[1] AS image_url,
                   (array_agg(image_license ORDER BY ingested_at))[1] AS image_license,
                   (array_agg(image_source  ORDER BY ingested_at))[1] AS image_source
              FROM mineral_deposits
             WHERE image_url IS NOT NULL
             GROUP BY commodity
          ) AS picked
         WHERE m.image_url IS NULL
           AND m.commodity = picked.commodity
    """)


def downgrade() -> None:
    pass
