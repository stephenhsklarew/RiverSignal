"""seed ~25 river_reaches across 7 watersheds (v0, needs_guide_review)

Revision ID: p7e8f9a0b1c2
Revises: o6d7e8f9a0b1
Create Date: 2026-05-13 00:00:06.000000

Phase A0 of TQS. v0 seed data: 22 reaches across 7 watersheds, using
the names from the plan §3.0 table. primary_usgs_site_id and
general_flow_bearing are best-known approximations and are marked
"needs_guide_review=true" in notes for rows that need angler validation.
Idempotent via ON CONFLICT (id) DO NOTHING.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'p7e8f9a0b1c2'
down_revision: Union[str, Sequence[str], None] = 'o6d7e8f9a0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (id, watershed, name, short_label, centroid_lat, centroid_lon,
#  primary_usgs_site_id, general_flow_bearing, is_warm_water,
#  typical_species_csv, notes)
REACHES = [
    # McKenzie — Upper / Middle / Lower
    ('mckenzie_upper',  'mckenzie',  'Upper McKenzie',  'Upper',  44.30, -122.05, '14159200', 270, False,
     'rainbow_trout,cutthroat',
     'Clear Lake to Trail Bridge. Cold-water spring-fed. needs_guide_review=true'),
    ('mckenzie_middle', 'mckenzie',  'Middle McKenzie', 'Middle', 44.18, -122.45, '14162200', 270, False,
     'rainbow_trout,cutthroat,chinook',
     'Blue River to Leaburg. needs_guide_review=true'),
    ('mckenzie_lower',  'mckenzie',  'Lower McKenzie',  'Lower',  44.10, -122.85, '14165500', 270, False,
     'rainbow_trout,cutthroat,chinook,steelhead',
     'Leaburg to Willamette confluence. needs_guide_review=true'),

    # Deschutes — Upper / Middle / Lower / Lower Canyon
    ('deschutes_upper',        'deschutes', 'Upper Deschutes',        'Upper',         43.80, -121.75, '14056500', 360, False,
     'rainbow_trout,brown_trout',
     'Above Wickiup Reservoir. needs_guide_review=true'),
    ('deschutes_middle',       'deschutes', 'Middle Deschutes',       'Middle',        44.06, -121.31, '14070500', 360, False,
     'rainbow_trout,brown_trout,whitefish',
     'Wickiup to Bend. needs_guide_review=true'),
    ('deschutes_lower',        'deschutes', 'Lower Deschutes',        'Lower',         44.78, -120.95, '14076500', 360, False,
     'rainbow_trout,steelhead,smallmouth_bass',
     'Bend to Maupin. needs_guide_review=true'),
    ('deschutes_lower_canyon', 'deschutes', 'Lower Deschutes Canyon', 'Lower Canyon',  45.30, -120.85, '14103000', 360, False,
     'steelhead,smallmouth_bass,rainbow_trout',
     'Maupin to Columbia confluence. needs_guide_review=true'),

    # Metolius — Headwaters / Middle
    ('metolius_headwaters',  'metolius', 'Metolius Headwaters',         'Headwaters',  44.50, -121.63, '14091500', 360, False,
     'rainbow_trout,bull_trout',
     'Camp Sherman to Bridge 99. needs_guide_review=true'),
    ('metolius_middle',      'metolius', 'Camp Sherman to Lake',        'Lower',       44.62, -121.55, '14091500', 360, False,
     'rainbow_trout,bull_trout',
     'Camp Sherman to Lake Billy Chinook. needs_guide_review=true'),

    # John Day — Mainstem / North Fork / South Fork
    ('johnday_mainstem',  'johnday', 'John Day Mainstem',   'Mainstem',    44.60, -119.15, '14048000',  90, True,
     'smallmouth_bass,steelhead',
     'Mainstem; warm-water for much of the year. needs_guide_review=true'),
    ('johnday_north_fork','johnday', 'John Day North Fork', 'North Fork',  45.00, -118.95, '14043500', 270, False,
     'steelhead,rainbow_trout',
     'North Fork. needs_guide_review=true'),
    ('johnday_south_fork','johnday', 'John Day South Fork', 'South Fork',  44.30, -119.30, '14036500', 360, False,
     'redband_trout,bull_trout',
     'South Fork. needs_guide_review=true'),

    # Klamath — Upper Klamath / Wood / Williamson
    ('klamath_upper',       'klamath', 'Upper Klamath Lake tribs', 'Upper',      42.50, -121.80, '11503500', 180, True,
     'redband_trout,sucker',
     'Upper Klamath Lake tributaries. needs_guide_review=true'),
    ('klamath_wood',        'klamath', 'Wood River',                'Wood',       42.70, -121.95, '11504100', 180, False,
     'redband_trout,brown_trout',
     'Wood River meadows. needs_guide_review=true'),
    ('klamath_williamson',  'klamath', 'Williamson River',         'Williamson', 42.80, -121.75, '11497500', 180, False,
     'redband_trout,bull_trout',
     'Williamson River. needs_guide_review=true'),

    # Skagit — Upper / Middle / Lower
    ('skagit_upper',  'skagit', 'Upper Skagit',  'Upper',  48.60, -121.10, '12181000', 270, False,
     'rainbow_trout,bull_trout',
     'Above Marblemount. needs_guide_review=true'),
    ('skagit_middle', 'skagit', 'Middle Skagit', 'Middle', 48.50, -121.60, '12194000', 270, False,
     'steelhead,chinook,coho,rainbow_trout',
     'Marblemount to Concrete. needs_guide_review=true'),
    ('skagit_lower',  'skagit', 'Lower Skagit',  'Lower',  48.40, -122.20, '12200500', 270, False,
     'steelhead,chinook,coho,chum',
     'Concrete to Puget Sound. needs_guide_review=true'),

    # Green River (UT) — Dam to Little Hole / Little Hole to Browns Park / Browns Park to Canyonlands
    ('green_a_section',  'green_river', 'Green A Section', 'A',  40.91, -109.42, '09234500', 180, False,
     'rainbow_trout,brown_trout,cutthroat',
     'Flaming Gorge Dam to Little Hole. needs_guide_review=true'),
    ('green_b_section',  'green_river', 'Green B Section', 'B',  40.82, -109.30, '09234500', 180, False,
     'rainbow_trout,brown_trout,cutthroat',
     'Little Hole to Browns Park. needs_guide_review=true'),
    ('green_c_section',  'green_river', 'Green C Section', 'C',  40.75, -109.20, '09234500', 180, False,
     'rainbow_trout,brown_trout',
     'Browns Park to Canyonlands. needs_guide_review=true'),
    ('green_lodore',     'green_river', 'Gates of Lodore', 'Lodore',  40.72, -108.95, '09251000', 180, False,
     'rainbow_trout,brown_trout',
     'Lodore Canyon. needs_guide_review=true'),
]


def upgrade() -> None:
    rows = []
    for (rid, ws, name, short, lat, lon, gauge, bearing, warm, species_csv, notes) in REACHES:
        species_array = "ARRAY[" + ",".join(f"'{s}'" for s in species_csv.split(",")) + "]::varchar[]"
        rows.append(
            f"('{rid}','{ws}','{name}','{short}',{lat},{lon},'{gauge}',{bearing},{str(warm).lower()},"
            f"{species_array},'{notes}','v0 plan §3.0 draft')"
        )
    values_sql = ",\n            ".join(rows)
    op.execute(
        f"""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            {values_sql}
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    ids = ",".join(f"'{r[0]}'" for r in REACHES)
    op.execute(f"DELETE FROM silver.river_reaches WHERE id IN ({ids})")
