"""replace Brown Trout photo (again) — prior pick is also a dead/mangled fish

Revision ID: ad29x0y1z2a3
Revises: ac28w9x0y1z2
Create Date: 2026-05-17 00:00:00.000000

ac28's swap to `How_now_brown_trout?_(3613014011).jpg` was also a held/
mangled fish despite the file description suggesting otherwise. Going
with `Bachforelle_5956.JPG` from the Commons Salmo_trutta category —
Saxony mountain stream, live fish, German Wikipedia uses similar
in-habitat shots as the species reference.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ad29x0y1z2a3'
down_revision: Union[str, Sequence[str], None] = 'ac28w9x0y1z2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


URL = "https://upload.wikimedia.org/wikipedia/commons/a/a2/Bachforelle_5956.JPG"


def upgrade() -> None:
    op.execute(f"""
        UPDATE gold.curated_species_photos
           SET photo_url = '{URL}',
               scientific_name = 'Salmo trutta',
               source = 'wikimedia'
         WHERE species_key = 'brown trout'
    """)


def downgrade() -> None:
    pass
