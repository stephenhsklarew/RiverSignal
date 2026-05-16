"""seed stocking_locations with Shenandoah waterbody coords

Revision ID: mm13h4i5j6k7
Revises: ll12g3h4i5j6
Create Date: 2026-05-15 00:00:00.000000

The Fish Stocking "View map" surface on /path/now/<ws> renders pins by
LEFT-JOINing `gold.stocking_schedule` to `stocking_locations` on
(watershed, waterbody). Shenandoah had no stocking_locations rows so
all 12 unique VA DWR waterbodies surfaced in the list view with NULL
lat/lon, resulting in 0 pins.

Seed coords come from public USGS NHD reach centroids / state-park GPS
on the VA DWR-listed stocking accesses. Includes the VA DWR annotation
strings (e.g. " [Heritage Day Water]", " [Youth-Only]") so the JOIN
matches exactly what the adapter writes to `interventions.description`.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mm13h4i5j6k7'
down_revision: Union[str, Sequence[str], None] = 'll12g3h4i5j6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (watershed, waterbody-as-stored-in-stocking-event, lat, lon, notes)
# Curated from VA DWR stocking access points + USGS NHD/Google Maps for
# canonical river-mile centroids of each named stocking section.
SEED = [
    ('shenandoah', 'Dry River [NSF]',
     38.448, -79.040, 'Dry River, GWNF — North River drainage'),
    ('shenandoah', 'Hughes River',
     38.563, -78.319, 'Hughes River, Madison Co. (SF Shenandoah)'),
    ('shenandoah', 'Mill Creek',
     38.829, -78.557, 'Mill Creek, Shenandoah Co. (NF Shenandoah)'),
    ('shenandoah', 'Moormans River (S. Fork)',
     38.069, -78.602, 'South Fork Moormans, Albemarle Co. (Sugar Hollow)'),
    ('shenandoah', 'Passage Creek [Heritage Day Water][National Forest Water]',
     38.911, -78.319, 'Passage Creek, GWNF, Shenandoah Co.'),
    ('shenandoah', 'Robinson River [Heritage Day Water]',
     38.487, -78.302, 'Robinson River, Madison Co.'),
    ('shenandoah', 'Rose River [Heritage Day Water]',
     38.467, -78.355, 'Rose River, Madison Co. (heritage trout water)'),
    ('shenandoah', 'South River',
     37.952, -79.018, 'South River, Augusta Co. (Waynesboro area)'),
    ('shenandoah', 'South River (Basic Park) [Youth-Only]',
     37.997, -79.097, 'South River — Basic Park, Waynesboro (youth-only)'),
    ('shenandoah', 'South River (Grottoes)',
     38.265, -78.831, 'South River — Grottoes Park'),
    ('shenandoah', 'South River (Ridgeview Park)',
     38.066, -78.892, 'South River — Ridgeview Park, Waynesboro'),
    ('shenandoah', 'Swift Run',
     38.378, -78.510, 'Swift Run, Greene Co. (SF Shenandoah)'),
]


def upgrade() -> None:
    for ws, wb, lat, lon, note in SEED:
        op.execute(f"""
            INSERT INTO stocking_locations (watershed, waterbody, latitude, longitude, notes)
            VALUES ('{ws}', '{wb.replace("'", "''")}', {lat}, {lon}, '{note.replace("'", "''")}')
            ON CONFLICT (watershed, waterbody) DO NOTHING
        """)


def downgrade() -> None:
    op.execute("DELETE FROM stocking_locations WHERE watershed = 'shenandoah'")
