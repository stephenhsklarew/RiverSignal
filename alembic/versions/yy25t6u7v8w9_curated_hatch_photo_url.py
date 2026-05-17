"""curated_hatch_chart: add explicit photo_url + seed iNat taxon photos for shenandoah

Revision ID: xx24s5t6u7v8
Revises: ww23r4s5t6u7
Create Date: 2026-05-17 00:00:00.000000

The hatch_confidence endpoint was picking insect photos by joining
gold.species_gallery on genus (split_part(scientific_name, ' ', 1)).
For genus-shared hatches (Hendrickson = Ephemerella subvaria, Sulphur
= Ephemerella invaria) the species-level photos that DO exist are
visually similar generic Ephemerella macros, and to anglers they
look indistinguishable.

Fix: give curated_hatch_chart its OWN photo_url column and seed it
with iNat-curated "default photo" URLs (pulled from
api.inaturalist.org/v1/taxa) — these are vetted by iNat as the most
representative shot of each taxon, so Hendrickson gets a reddish-brown
specimen and Sulphur gets a pale-yellow specimen. The endpoint will
prefer c.photo_url when set, falling back to the existing
species_gallery join when null.

Companion code change in app/routers/fishing.py:hatch_confidence
adds the COALESCE.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'yy25t6u7v8w9'
down_revision: Union[str, Sequence[str], None] = 'xx24s5t6u7v8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (watershed, common_name, iNat taxon default photo URL — visually
# distinctive for each species; pulled 2026-05-17 from
# api.inaturalist.org/v1/taxa?q=<name>).
SHEN_HATCH_PHOTOS = [
    ("shenandoah", "Hendrickson",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/3519220/medium.jpg"),
    ("shenandoah", "Sulphur",
     "https://static.inaturalist.org/photos/89669598/medium.jpg"),
    ("shenandoah", "Light Cahill",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/410106629/medium.jpeg"),
    ("shenandoah", "Trico",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/118434105/medium.jpg"),
    ("shenandoah", "Quill Gordon",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/118192900/medium.jpeg"),
    ("shenandoah", "Little Black Stonefly",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/416569/medium.JPG"),
    ("shenandoah", "Caddisflies",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/1631938/medium.jpeg"),
    ("shenandoah", "Hellgrammite (smallmouth)",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/213779572/medium.jpeg"),
    ("shenandoah", "Blue-Winged Olive",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/413477255/medium.jpeg"),
    ("shenandoah", "Midges",
     "https://inaturalist-open-data.s3.amazonaws.com/photos/131906/medium.jpg"),
]


def upgrade() -> None:
    # Add the column if it doesn't already exist (idempotent).
    op.execute("""
        ALTER TABLE curated_hatch_chart
          ADD COLUMN IF NOT EXISTS photo_url text
    """)
    for ws, name, url in SHEN_HATCH_PHOTOS:
        op.execute(f"""
            UPDATE curated_hatch_chart
               SET photo_url = '{url}'
             WHERE watershed = '{ws}'
               AND common_name = '{name.replace("'", "''")}'
        """)


def downgrade() -> None:
    op.execute("ALTER TABLE curated_hatch_chart DROP COLUMN IF EXISTS photo_url")
