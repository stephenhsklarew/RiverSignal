"""switch curated photo URLs from original (~3MB) to 330px thumbs (~50KB)

Revision ID: ae30y1z2a3b4
Revises: ad29x0y1z2a3
Create Date: 2026-05-17 00:00:00.000000

Smallmouth Bass and Razorback Sucker photos were reported missing from
/path/now/green_river Fish Present. Root cause analysis:

  API returns curated URLs correctly (HTTP 200 verified).
  Photo payloads were ~3-4 MB each (full-resolution Wikimedia originals)
  because ab27v8w9x0y1 stripped /thumb/ in response to the broken
  640px-Npx- failures from the seed.

On mobile, 3-4 MB images can fail to fully decode/render before the
SWR cache returns and the carousel slot renders empty — which the user
perceives as "missing photo."

Spot-tested 330px and 800px on four files (smallmouth, razorback,
bachforelle, esox):
  330px → 200 OK across all
  800px → 400 across all (Wikimedia per-file thumb whitelist excludes it)

330px is the same width Wikipedia's REST summary endpoint serves as the
default infobox thumbnail, so it's universally supported. Payload drops
~60×, making Fish Present cards load reliably on cellular.

Idempotent: regex only matches URLs in `/commons/X/XY/filename` form
(originals), leaving any already-thumbnailed URLs alone.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ae30y1z2a3b4'
down_revision: Union[str, Sequence[str], None] = 'ad29x0y1z2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert /thumb/<X>/<XY>/<filename>/330px-<filename> between the host
    # and the filename. Uses PostgreSQL REGEXP_REPLACE with backrefs.
    op.execute(r"""
        UPDATE gold.curated_species_photos
           SET photo_url = REGEXP_REPLACE(
               photo_url,
               '/commons/([0-9a-f])/([0-9a-f]{2})/([^/]+)$',
               '/commons/thumb/\1/\2/\3/330px-\3',
               'i'
           )
         WHERE photo_url ~ '/commons/[0-9a-f]/[0-9a-f]{2}/[^/]+$'
           AND source = 'wikimedia'
    """)


def downgrade() -> None:
    # No-op: keep small thumbs. Restoring the multi-MB originals would
    # re-introduce the mobile-load failure these were chosen to fix.
    pass
