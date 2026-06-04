"""seed recreation_sites for new_river_va (New River Trail SP, Claytor Lake SP, DWR ramps)

Revision ID: nr06a1b2c3d4
Revises: nr05a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

The federal RIDB / OR-centric ArcGIS sources created ~0 curated rows for this
SW-VA watershed. Curated v0 set: the New River Trail State Park (57-mi rail-trail,
Galax→Pulaski), Claytor Lake State Park, and VA DWR access ramps along the New.
Every rec_type is an ExploreMapPage FILTER key (campground/trailhead/boat_ramp/
fishing_access/day_use) — NOT 'state_park' (the ipswich ip04 lesson).
source_type='curated_new_river_va_v0'. Coords approximate v0 — needs_review.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'nr06a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nr05a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_id, name, rec_type, lat, lon, description)
SEED = [
    ('nrt-galax', 'New River Trail State Park — Galax Trailhead',
     'trailhead', 36.661, -80.920,
     'Galax — southern terminus of the 57-mi New River Trail rail-trail. (v0 curated; coords approximate.)'),
    ('nrt-fries', 'New River Trail State Park — Fries Trailhead',
     'trailhead', 36.713, -80.980,
     'Fries — New River Trail spur trailhead on the New. (v0 curated; coords approximate.)'),
    ('nrt-ivanhoe', 'New River Trail — Ivanhoe Access',
     'fishing_access', 36.835, -80.953,
     'Ivanhoe — New River Trail river access + bank fishing near the gauge. (v0 curated; coords approximate.)'),
    ('nrt-foster-falls', 'New River Trail State Park — Foster Falls',
     'day_use', 36.883, -80.710,
     'Foster Falls — New River Trail hub: historic village, horse livery, river day-use. (v0 curated; coords approximate.)'),
    ('nrt-allisonia', 'New River Trail — Allisonia Access',
     'boat_ramp', 36.938, -80.746,
     'Allisonia — New River / upper Claytor Lake canoe + boat access. (v0 curated; coords approximate.)'),
    ('nrt-draper', 'New River Trail State Park — Draper Trailhead',
     'trailhead', 36.954, -80.652,
     'Draper — northern New River Trail trailhead near Pulaski. (v0 curated; coords approximate.)'),
    ('claytor-lake-sp', 'Claytor Lake State Park',
     'campground', 37.063, -80.622,
     'Dublin — Claytor Lake State Park: campground, beach, marina on the New River reservoir. (v0 curated; coords approximate.)'),
    ('claytor-lake-ramp', 'Claytor Lake State Park Boat Ramp',
     'boat_ramp', 37.061, -80.630,
     'Claytor Lake State Park public boat ramp + marina. (v0 curated; coords approximate.)'),
    ('bissett-park-radford', 'Bissett Park (Radford)',
     'day_use', 37.130, -80.550,
     'Radford — riverfront city park + New River Trail (Radford section) day-use. (v0 curated; coords approximate.)'),
    ('whitethorne-access', 'Whitethorne / McCoy Access (VA DWR)',
     'boat_ramp', 37.190, -80.610,
     'Montgomery Co — VA DWR New River boat ramp below Radford. (v0 curated; coords approximate.)'),
    ('pembroke-access', 'Pembroke / Bluff City Access (VA DWR)',
     'boat_ramp', 37.320, -80.635,
     'Giles Co — VA DWR New River access near Pembroke. (v0 curated; coords approximate.)'),
    ('glen-lyn-access', 'Glen Lyn Access (VA DWR)',
     'fishing_access', 37.372, -80.861,
     'Giles Co — lower New River access at Glen Lyn near the WV state line. (v0 curated; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    sid_row = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'new_river_va' LIMIT 1")
    ).fetchone()
    if not sid_row:
        return
    site_id = sid_row[0]

    for source_id, name, rec_type, lat, lon, desc in SEED:
        conn.execute(
            text("""
                INSERT INTO recreation_sites
                    (site_id, source_type, source_id, name, rec_type,
                     latitude, longitude, geom, description, amenities)
                VALUES
                    (:sid, 'curated_new_river_va_v0', :src_id, :name, :rec_type,
                     :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :desc,
                     '{}'::jsonb)
                ON CONFLICT (source_type, source_id) DO NOTHING
            """),
            {"sid": site_id, "src_id": source_id, "name": name,
             "rec_type": rec_type, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("DELETE FROM recreation_sites WHERE source_type = 'curated_new_river_va_v0'")
