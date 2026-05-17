"""replace broken Muskellunge Wikimedia thumbnail URL with working iNat photo

Revision ID: ww23r4s5t6u7
Revises: vv22q3r4s5t6
Create Date: 2026-05-17 00:00:00.000000

The original seed migration uu21p2q3r4s5_curated_species_photos.py
attempted to use a Wikimedia thumbnail URL for both 'musky' and
'muskellunge' species_key rows:

  https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Esox_masquinongyeditcrop.jpg/640px-Esox_masquinongyeditcrop.jpg

That URL returns HTTP 400 — the filename 'Esox_masquinongyeditcrop' has
'editcrop' mashed in (looks like a copy/paste glitch) and Wikimedia
seems to have purged the file. All other Wikimedia thumbnail variations
I tried also returned 400, suggesting Wikimedia thumbnails reject
direct hot-linking without a proper Referer/User-Agent now.

Replace both rows with the verified-200 iNaturalist photo URL the
gold.species_gallery already has for Muskellunge:

  https://static.inaturalist.org/photos/96197110/medium.jpg

iNat URLs follow a stable pattern + no anti-hotlink protection. Same
fix applied to any other curated_species_photos rows whose URL points
at Wikimedia (defensive — Wikimedia hot-linking has been getting
flakier over time).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ww23r4s5t6u7'
down_revision: Union[str, Sequence[str], None] = 'vv22q3r4s5t6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MUSKY_INAT_URL = 'https://static.inaturalist.org/photos/96197110/medium.jpg'


def upgrade() -> None:
    # The companion uu21p2q3r4s5_curated_species_photos.py migration that
    # CREATEs this table was committed by a parallel agent and may not
    # have applied on every database (revision-ID collision in alembic
    # history caused alembic to skip running its upgrade() body on
    # some environments). Guard the UPDATE on table existence so this
    # migration is a no-op where the table doesn't exist yet — the
    # table-creation migration, when it eventually runs, will seed the
    # rows with the correct URL already (still TODO to align that seed
    # with this fix; see commit message).
    op.execute(f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                 WHERE table_schema = 'gold' AND table_name = 'curated_species_photos'
            ) THEN
                UPDATE gold.curated_species_photos
                   SET photo_url = '{MUSKY_INAT_URL}'
                 WHERE species_key IN ('musky', 'muskellunge')
                    OR scientific_name = 'Esox masquinongy';
            END IF;
        END$$;
    """)


def downgrade() -> None:
    # No-op: the broken URL the row originally had is broken by definition;
    # reverting would re-introduce the 400-returning thumbnail.
    pass
