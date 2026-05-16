"""seed gold.curated_species_photos for game species iNat won't cover

Revision ID: uu21p2q3r4s5
Revises: tt20o1p2q3r4
Create Date: 2026-05-16 00:00:00.000000

Why this exists
---------------
`gold.species_gallery` is fed exclusively by research-grade iNaturalist
photos. For game species we list in `silver.river_reaches.typical_species`
but that no one has photographed inside one of our 8 watershed bboxes
(musky on Shenandoah, fallfish, channel cat in some PNW reaches, etc.),
the Fish Present carousel renders the row with a 🐟 placeholder.

This migration adds a small curated lookup of Wikimedia Commons fish
photos keyed by the same `common_name` shape that `gold.species_by_reach`
emits (lower-case, space-separated). The fishing/species endpoint
consults it after the gallery-based photo_map fails to match.

URLs are stable Wikimedia thumbnail paths sourced via the Wikipedia REST
API summary endpoint on 2026-05-16. Wikimedia Commons content is
permissively licensed (CC BY-SA / CC0 / public domain). Each
file's specific license is on its Commons page if attribution is needed.

Species included
----------------
Salmonids (already well-covered by iNat in PNW watersheds, but seeded
as a national safety net for Shenandoah cold tribs etc.):
  brook trout, brown trout, rainbow trout, cutthroat trout,
  bull trout, chinook salmon, chum salmon, mountain whitefish

Warmwater game (low iNat coverage in our bboxes):
  smallmouth bass, largemouth bass, striped bass, white bass,
  walleye, musky / muskellunge, channel catfish, bluegill,
  fallfish, razorback sucker

Skipped (no clean Wikipedia infobox image): coho salmon, colorado
pikeminnow. Those still rely on iNat or genus-prefix fallback.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'uu21p2q3r4s5'
down_revision: Union[str, Sequence[str], None] = 'tt20o1p2q3r4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (species_key, common_name, scientific_name, photo_url)
# species_key matches the common_name shape emitted by gold.species_by_reach
# after underscores are normalised to spaces. Some species have multiple
# names that all need to resolve (e.g. "musky" and "muskellunge") — those
# are seeded as separate rows pointing at the same photo.
SEED = [
    # Salmonids
    ("brook trout",        "Brook Trout",        "Salvelinus fontinalis",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Brook_trout_in_water.jpg/640px-Brook_trout_in_water.jpg"),
    ("brown trout",        "Brown Trout",        "Salmo trutta",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Brown_Trout_%28Salmo_trutta%29_%2853678765394%29.jpg/640px-Brown_Trout_%28Salmo_trutta%29_%2853678765394%29.jpg"),
    ("rainbow trout",      "Rainbow Trout",      "Oncorhynchus mykiss",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Close_up_of_rainbow_trout_fish_underwater_oncorhynchus_mykiss.jpg/640px-Close_up_of_rainbow_trout_fish_underwater_oncorhynchus_mykiss.jpg"),
    ("steelhead",          "Steelhead",          "Oncorhynchus mykiss",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Close_up_of_rainbow_trout_fish_underwater_oncorhynchus_mykiss.jpg/640px-Close_up_of_rainbow_trout_fish_underwater_oncorhynchus_mykiss.jpg"),
    ("redband trout",      "Redband Trout",      "Oncorhynchus mykiss gairdneri",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Close_up_of_rainbow_trout_fish_underwater_oncorhynchus_mykiss.jpg/640px-Close_up_of_rainbow_trout_fish_underwater_oncorhynchus_mykiss.jpg"),
    ("cutthroat",          "Cutthroat Trout",    "Oncorhynchus clarkii",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Trout_cutthroat_fish_oncorhynchus_clarkii_clarkii.jpg/640px-Trout_cutthroat_fish_oncorhynchus_clarkii_clarkii.jpg"),
    ("cutthroat trout",    "Cutthroat Trout",    "Oncorhynchus clarkii",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Trout_cutthroat_fish_oncorhynchus_clarkii_clarkii.jpg/640px-Trout_cutthroat_fish_oncorhynchus_clarkii_clarkii.jpg"),
    ("bull trout",         "Bull Trout",         "Salvelinus confluentus",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Bull_trout_fish_salvelinus_confluentus.jpg/640px-Bull_trout_fish_salvelinus_confluentus.jpg"),
    ("chinook",            "Chinook Salmon",     "Oncorhynchus tshawytscha",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Chinook_Salmon_Adult_Male.jpg/640px-Chinook_Salmon_Adult_Male.jpg"),
    ("chinook salmon",     "Chinook Salmon",     "Oncorhynchus tshawytscha",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Chinook_Salmon_Adult_Male.jpg/640px-Chinook_Salmon_Adult_Male.jpg"),
    ("chum",               "Chum Salmon",        "Oncorhynchus keta",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Dog_Salmon_Breeding_Male.jpg/640px-Dog_Salmon_Breeding_Male.jpg"),
    ("chum salmon",        "Chum Salmon",        "Oncorhynchus keta",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Dog_Salmon_Breeding_Male.jpg/640px-Dog_Salmon_Breeding_Male.jpg"),
    ("whitefish",          "Mountain Whitefish", "Prosopium williamsoni",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Prosopium_williamsoni.jpg/640px-Prosopium_williamsoni.jpg"),
    ("mountain whitefish", "Mountain Whitefish", "Prosopium williamsoni",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Prosopium_williamsoni.jpg/640px-Prosopium_williamsoni.jpg"),

    # Warmwater game fish
    ("smallmouth bass",    "Smallmouth Bass",    "Micropterus dolomieu",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Smallmouth_Bass_%2849561724026%29.jpg/640px-Smallmouth_Bass_%2849561724026%29.jpg"),
    ("largemouth bass",    "Largemouth Bass",    "Micropterus salmoides",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/Largemouth_Bass_%28Micropterus_salmoides%29_June_2023_%28cropped%29.jpg/640px-Largemouth_Bass_%28Micropterus_salmoides%29_June_2023_%28cropped%29.jpg"),
    ("striped bass",       "Striped Bass",       "Morone saxatilis",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Morone_saxatilis_SI2.jpg/640px-Morone_saxatilis_SI2.jpg"),
    ("walleye",            "Walleye",            "Sander vitreus",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Walleye_%28Sander_vitreus%29_%281%29.jpg/640px-Walleye_%28Sander_vitreus%29_%281%29.jpg"),
    ("musky",              "Muskellunge",        "Esox masquinongy",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Esox_masquinongyeditcrop.jpg/640px-Esox_masquinongyeditcrop.jpg"),
    ("muskellunge",        "Muskellunge",        "Esox masquinongy",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Esox_masquinongyeditcrop.jpg/640px-Esox_masquinongyeditcrop.jpg"),
    ("channel catfish",    "Channel Catfish",    "Ictalurus punctatus",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Channel_Catfish_%28Ictalurus_punctatus%29_white_background.jpg/640px-Channel_Catfish_%28Ictalurus_punctatus%29_white_background.jpg"),
    ("bluegill",           "Bluegill",           "Lepomis macrochirus",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Bluegill_%28cropped%29.jpg/640px-Bluegill_%28cropped%29.jpg"),
    # "sunfish" is generic — point at bluegill, the most commonly photographed
    # Lepomis. iNat data, when present, will outrank this in the photo_map.
    ("sunfish",            "Bluegill",           "Lepomis macrochirus",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Bluegill_%28cropped%29.jpg/640px-Bluegill_%28cropped%29.jpg"),
    ("fallfish",           "Fallfish",           "Semotilus corporalis",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Semotilus_corporalis.JPG/640px-Semotilus_corporalis.JPG"),
    ("razorback sucker",   "Razorback Sucker",   "Xyrauchen texanus",
     "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Razorback_Sucker_%28Xyrauchen_texanus_%29_Gavins_Point.jpg/640px-Razorback_Sucker_%28Xyrauchen_texanus_%29_Gavins_Point.jpg"),
]


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS gold.curated_species_photos (
            species_key      varchar(64)  PRIMARY KEY,
            common_name      varchar(120) NOT NULL,
            scientific_name  varchar(120),
            photo_url        text         NOT NULL,
            source           varchar(40)  NOT NULL DEFAULT 'wikimedia',
            notes            text,
            created_at       timestamptz  NOT NULL DEFAULT now()
        )
    """)

    for species_key, common_name, scientific_name, photo_url in SEED:
        # Use parameterized exec via raw INSERT — no apostrophes in this seed
        # but defence in depth: escape single quotes by doubling.
        ck = species_key.replace("'", "''")
        cn = common_name.replace("'", "''")
        sn = scientific_name.replace("'", "''") if scientific_name else None
        pu = photo_url.replace("'", "''")
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
    op.execute("DROP TABLE IF EXISTS gold.curated_species_photos")
