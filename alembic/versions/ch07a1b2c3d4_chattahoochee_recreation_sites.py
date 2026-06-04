"""seed recreation_sites for chattahoochee (CRNRA, Lake Lanier, Chattahoochee NF, state parks)

Revision ID: ch07a1b2c3d4
Revises: ch06a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

RIDB returned only ~2 curated rows for this bbox. Curated v0 set: Chattahoochee
River National Recreation Area (CRNRA) units, Lake Sidney Lanier (USACE) access,
Chattahoochee NF campgrounds, and nearby GA state parks. Every rec_type is an
ExploreMapPage FILTER key (campground/trailhead/boat_ramp/fishing_access/day_use)
— the ipswich ip04 lesson. source_type='curated_chattahoochee_v0'. Coords approximate.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ch07a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch06a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_id, name, rec_type, lat, lon, description)
SEED = [
    ('crnra-bowmans-island', 'CRNRA — Bowmans Island (Buford Dam Tailwater Put-in)',
     'boat_ramp', 34.150, -84.075,
     'Below Buford Dam — the cold tailwater trout put-in (CRNRA). ⚠ Dam-release water; check USACE schedule. (v0 curated; coords approximate.)'),
    ('crnra-island-ford', 'CRNRA — Island Ford (Park HQ)',
     'trailhead', 34.030, -84.320,
     'Sandy Springs — Chattahoochee River NRA headquarters; riverside trails + bank fishing. (v0 curated; coords approximate.)'),
    ('crnra-jones-bridge', 'CRNRA — Jones Bridge',
     'day_use', 34.000, -84.250,
     'Peachtree Corners — CRNRA day-use, paddling, and trails on the Chattahoochee. (v0 curated; coords approximate.)'),
    ('crnra-johnson-ferry', 'CRNRA — Johnson Ferry',
     'boat_ramp', 33.950, -84.400,
     'Marietta/Sandy Springs — popular raft/kayak launch on the metro Chattahoochee. (v0 curated; coords approximate.)'),
    ('crnra-cochran-shoals', 'CRNRA — Cochran Shoals',
     'trailhead', 33.910, -84.450,
     'Cobb/Fulton — CRNRA fitness trails + wetlands boardwalk on the river. (v0 curated; coords approximate.)'),
    ('crnra-paces-mill', 'CRNRA — Paces Mill (Vinings)',
     'day_use', 33.870, -84.460,
     'Vinings — southern CRNRA unit; raft takeout + trails near US-41. (v0 curated; coords approximate.)'),
    ('lanier-buford-dam-park', 'Lake Lanier — Buford Dam Park (USACE)',
     'day_use', 34.158, -84.073,
     'Buford — USACE day-use park below/at Buford Dam on Lake Lanier. (v0 curated; coords approximate.)'),
    ('lanier-clarks-bridge', 'Lake Lanier — Clarks Bridge Park',
     'boat_ramp', 34.320, -83.830,
     'Gainesville — Lake Lanier boat ramp + Olympic rowing venue. (v0 curated; coords approximate.)'),
    ('don-carter-sp', 'Don Carter State Park (Lake Lanier)',
     'campground', 34.400, -83.780,
     'Gainesville — GA state park on upper Lake Lanier; campground, beach, ramp. (v0 curated; coords approximate.)'),
    ('upper-chattahoochee-cg', 'Upper Chattahoochee Campground (Chattahoochee NF)',
     'campground', 34.700, -83.790,
     'Helen area — USFS campground on the Chattahoochee headwaters. (v0 curated; coords approximate.)'),
    ('unicoi-sp', 'Unicoi State Park',
     'campground', 34.720, -83.720,
     'Helen — GA state park; campground + Smith Creek + Unicoi Lake trout. (v0 curated; coords approximate.)'),
    ('smithgall-woods', 'Smithgall Woods State Park (Dukes Creek)',
     'fishing_access', 34.700, -83.780,
     'Helen — catch-and-release Dukes Creek trophy-trout fishing (reservation) + trails. (v0 curated; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    sid_row = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'chattahoochee' LIMIT 1")
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
                    (:sid, 'curated_chattahoochee_v0', :src_id, :name, :rec_type,
                     :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :desc,
                     '{}'::jsonb)
                ON CONFLICT (source_type, source_id) DO NOTHING
            """),
            {"sid": site_id, "src_id": source_id, "name": name,
             "rec_type": rec_type, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("DELETE FROM recreation_sites WHERE source_type = 'curated_chattahoochee_v0'")
