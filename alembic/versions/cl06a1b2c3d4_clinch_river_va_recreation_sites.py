"""seed recreation_sites for clinch_river_va (Clinch River State Park blueway, DWR launches, Jefferson NF)

Revision ID: cl06a1b2c3d4
Revises: cl05a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

`/api/v1/sites/clinch_river_va/recreation` is empty — the federal RIDB feed +
the OR-centric `recreation` ArcGIS sources created 0 rows for this SW-VA
watershed. Curated v0 set of well-known Clinch-corridor recreation sites: the
Clinch River State Park (VA's first "blueway", 2021), VA DWR canoe/boat launches
along the blueway, and nearby Jefferson NF rec areas.

LESSON FROM ipswich ip04 (which used rec_type='state_park' and then needed a fix
migration): every rec_type here is one of the ExploreMapPage FILTER keys
(campground / trailhead / boat_ramp / fishing_access / day_use), so each row
shows up under its chip — NOT 'state_park'.

source_type='curated_clinch_river_va_v0' (uniqueness on (source_type,
source_id)) so a future live adapter can run alongside. Coords approximate v0 —
needs_review.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'cl06a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl05a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_id, name, rec_type, lat, lon, description) — rec_type ∈ ExploreMapPage FILTER keys.
SEED = [
    ('clinch-sp-sugar-hill', 'Clinch River State Park — Sugar Hill (St. Paul)',
     'trailhead', 36.905, -82.312,
     'St. Paul — Clinch River State Park Sugar Hill area; trails + river overlooks on the blueway. (v0 curated; coords approximate.)'),
    ('clinch-sp-cleveland', 'Clinch River State Park — Cleveland Access',
     'fishing_access', 36.945, -82.155,
     'Cleveland (Russell Co) — Clinch River State Park access; bank fishing + wading at the gauge reach. (v0 curated; coords approximate.)'),
    ('artrip-access', 'Artrip Access (VA DWR)',
     'boat_ramp', 37.02, -81.86,
     'Upper Clinch near Cedar Bluff — VA DWR canoe/boat launch on the Clinch River blueway. (v0 curated; coords approximate.)'),
    ('carbo-access', 'Carbo Access (VA DWR)',
     'boat_ramp', 37.04, -81.83,
     'Upper Clinch DWR canoe/kayak put-in near the former Carbo plant (Tazewell Co). (v0 curated; coords approximate.)'),
    ('castlewood-access', 'Castlewood Access (VA DWR)',
     'boat_ramp', 36.89, -82.27,
     'Castlewood (Russell Co) — Clinch River blueway launch. (v0 curated; coords approximate.)'),
    ('nash-ford-access', 'Nash Ford Access (VA DWR)',
     'fishing_access', 36.92, -82.20,
     'Russell Co — Clinch River wade + bank fishing access. (v0 curated; coords approximate.)'),
    ('st-paul-oxbow', 'St. Paul Oxbow Lake & Riverway',
     'day_use', 36.906, -82.310,
     'St. Paul — Oxbow Lake, Sugar Hill trail network, and Clinch riverfront day-use. (v0 curated; coords approximate.)'),
    ('dungannon-launch', 'Dungannon Access (VA DWR)',
     'boat_ramp', 36.831, -82.461,
     'Dungannon (Scott Co) — Clinch River blueway launch near the Dungannon water-quality gauge. (v0 curated; coords approximate.)'),
    ('speers-ferry-access', 'Speers Ferry / Clinchport Access',
     'fishing_access', 36.66, -82.75,
     'Scott Co — lower Clinch access near the TN state line at Clinchport / Speers Ferry. (v0 curated; coords approximate.)'),
    ('high-knob-rec', 'High Knob Recreation Area (Jefferson NF)',
     'campground', 36.88, -82.62,
     'Jefferson NF near Norton — campground, lake, and trails above the upper Clinch tributaries. (v0 curated; coords approximate.)'),
    ('bark-camp-lake', 'Bark Camp Lake Recreation Area (Jefferson NF)',
     'campground', 36.84, -82.42,
     'Jefferson NF (Scott/Wise Co) — lake campground + trails near the Clinch corridor. (v0 curated; coords approximate.)'),
    ('guest-river-gorge-trail', 'Guest River Gorge Trail (Jefferson NF)',
     'trailhead', 36.86, -82.50,
     'Jefferson NF near Coeburn — rail-trail through the Guest River Gorge, a Clinch tributary. (v0 curated; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    sid_row = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'clinch_river_va' LIMIT 1")
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
                    (:sid, 'curated_clinch_river_va_v0', :src_id, :name, :rec_type,
                     :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :desc,
                     '{}'::jsonb)
                ON CONFLICT (source_type, source_id) DO NOTHING
            """),
            {"sid": site_id, "src_id": source_id, "name": name,
             "rec_type": rec_type, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("DELETE FROM recreation_sites WHERE source_type = 'curated_clinch_river_va_v0'")
