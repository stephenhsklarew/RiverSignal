"""distinct photos for Redband Trout, Steelhead variants; replace Brown Trout photo

Revision ID: ac28w9x0y1z2
Revises: ab27v8w9x0y1
Create Date: 2026-05-17 00:00:00.000000

Two issues to fix in gold.curated_species_photos:

1. **Redband Trout, Steelhead, Summer Steelhead all rendered with the
   same Rainbow Trout photo.** The seed migration uu21p2q3r4s5 pointed
   each life-history variant of Oncorhynchus mykiss at the same
   originalimage URL. Distinct photos go in:

     redband trout    → Redband_trout.jpg (subspecies — pink-stripe form)
     steelhead        → Coleman_NFH_steelhead_jumping_holding_pond.png
                        (anadromous form, jumping action shot)
     summer steelhead → Oncorhynchus_mykiss,_John_Day_River.JPG
                        (wild fish in PNW summer-run river)
     winter steelhead → kept on Steelhead photo (user didn't call out)

2. **Brown Trout photo shows a killed fish.** Replace with the live
   "How now brown trout?" photo (Avon River, UK — described as a fish
   "immediately returned unscathed to the icy waters" after the photo).

All URLs verified HTTP 200 on 2026-05-17. URLs use the originalimage
form (no /thumb/) per the ab27 migration's policy.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ac28w9x0y1z2'
down_revision: Union[str, Sequence[str], None] = 'ab27v8w9x0y1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (species_key, common_name, scientific_name, photo_url, note)
UPDATES = [
    ("redband trout", "Redband Trout", "Oncorhynchus mykiss gairdneri",
     "https://upload.wikimedia.org/wikipedia/commons/6/68/Redband_trout.jpg",
     "subspecies-specific photo"),
    ("steelhead", "Steelhead", "Oncorhynchus mykiss",
     "https://upload.wikimedia.org/wikipedia/commons/c/ca/Coleman_NFH_steelhead_jumping_holding_pond.png",
     "anadromous form, jumping in pond"),
    ("summer steelhead", "Summer Steelhead", "Oncorhynchus mykiss",
     "https://upload.wikimedia.org/wikipedia/commons/0/0f/Oncorhynchus_mykiss%2C_John_Day_River.JPG",
     "wild PNW summer-run fish in river"),
    ("winter steelhead", "Winter Steelhead", "Oncorhynchus mykiss",
     "https://upload.wikimedia.org/wikipedia/commons/c/ca/Coleman_NFH_steelhead_jumping_holding_pond.png",
     "shares Steelhead photo; visually equivalent run-timing variant"),
    ("brown trout", "Brown Trout", "Salmo trutta",
     "https://upload.wikimedia.org/wikipedia/commons/e/e2/How_now_brown_trout%3F_%283613014011%29.jpg",
     "live fish, released after photo; replaces prior killed-fish image"),
]


def upgrade() -> None:
    for species_key, common_name, sci, url, _ in UPDATES:
        ck = species_key.replace("'", "''")
        cn = common_name.replace("'", "''")
        sn = sci.replace("'", "''") if sci else None
        pu = url.replace("'", "''")
        sn_sql = f"'{sn}'" if sn else "NULL"
        op.execute(f"""
            INSERT INTO gold.curated_species_photos
                (species_key, common_name, scientific_name, photo_url, source)
            VALUES ('{ck}', '{cn}', {sn_sql}, '{pu}', 'wikimedia')
            ON CONFLICT (species_key) DO UPDATE
              SET common_name = EXCLUDED.common_name,
                  scientific_name = EXCLUDED.scientific_name,
                  photo_url = EXCLUDED.photo_url,
                  source = EXCLUDED.source
        """)


def downgrade() -> None:
    # No-op: don't restore the rainbow-trout-everywhere / killed-fish state.
    pass
