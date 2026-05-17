"""replace /thumb/Npx- curated photo URLs with their originalimage form

Revision ID: ab27v8w9x0y1
Revises: zz26u7v8w9x0
Create Date: 2026-05-17 00:00:00.000000

Wikimedia maintains a per-file whitelist of allowed thumbnail widths.
The seed migration uu21p2q3r4s5_curated_species_photos.py wrote
`/thumb/.../640px-<filename>` URLs that fail with HTTP 400 for many
files (rainbow trout, fallfish, channel catfish — and consequently the
aliased Redband Trout and Summer Steelhead rows on the Deschutes
Fish Present carousel).

Spot-check confirmed inconsistent support across widths for the
rainbow_trout file:
  330px  200 OK
  440px  400
  500px  200 OK
  640px  400  ← seeded
  660px  400
  800px  400
  original (no /thumb/)  200 OK

Strip `/thumb/.../{N}px-{filename}` down to the originalimage URL
(`/wikipedia/commons/<X>/<XY>/<filename>`) which always loads. Trade-off:
larger payload per fish image (~1-3 MB unscaled) on first load, but
they're CDN-cached and only displayed when the user opens a card.

Idempotent: the UPDATE filter `WHERE photo_url LIKE '%/thumb/%'` is a
no-op once the rows are migrated.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ab27v8w9x0y1'
down_revision: Union[str, Sequence[str], None] = 'zz26u7v8w9x0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Strip `/thumb/` from the path and remove the `/{N}px-{filename}`
    # suffix to land on the originalimage URL.
    op.execute(r"""
        UPDATE gold.curated_species_photos
           SET photo_url = REGEXP_REPLACE(
               REPLACE(photo_url, '/commons/thumb/', '/commons/'),
               '/[0-9]+px-[^/]+$',
               '',
               'i'
           )
         WHERE photo_url LIKE '%/thumb/%'
    """)


def downgrade() -> None:
    # No-op: we never want the broken thumb URLs back. If you really need
    # to revert, restore from the prior seed migration.
    pass
