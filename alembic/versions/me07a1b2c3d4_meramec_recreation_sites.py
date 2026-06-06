"""seed meramec recreation_sites (v0 curated — RIDB-light Missouri region)

Revision ID: me07a1b2c3d4
Revises: me06a1b2c3d4
Create Date: 2026-06-06 00:00:00.000000

Per runbook §2.4 + §2.6.5. Missouri state parks + Maramec Spring are NOT in RIDB
(Recreation.gov covers only the Mark Twain NF portion), so seed the well-known
access points so /path/explore isn't empty. rec_type MUST be one of the
ExploreMapPage filter keys: campground, trailhead, boat_ramp, fishing_access,
day_use. Idempotent ON CONFLICT (source_type, source_id).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'me07a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me06a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_id, name, rec_type, lat, lon, description)
SEED = [
    ('meramec-sp', 'Meramec State Park', 'campground', 38.211, -91.097,
     'Sullivan — flagship Meramec SP; camping, river access, 40+ caves (Fisher Cave), canoe/raft concession. (v0 curated; coords approximate.)'),
    ('meramec-sp-launch', 'Meramec State Park River Access', 'boat_ramp', 38.208, -91.090,
     'Sullivan — float put-in/takeout on the Meramec at Meramec SP. (v0 curated; coords approximate.)'),
    ('onondaga-cave-sp', 'Onondaga Cave State Park', 'campground', 38.062, -91.231,
     'Leasburg — Meramec-side state park; campground, show caves (Onondaga, Cathedral), river + millpond fishing. (v0 curated; coords approximate.)'),
    ('maramec-spring-park', 'Maramec Spring Park', 'fishing_access', 37.957, -91.531,
     'St. James — private (James Foundation) trout park; MDC-stocked rainbow trout daily Mar 1-Oct 31, camping, nature center. (v0 curated; coords approximate.)'),
    ('castlewood-sp', 'Castlewood State Park', 'trailhead', 38.549, -90.538,
     'Ballwin — popular St. Louis-suburb Meramec park; bluff trails, mountain biking, riverside access. (v0 curated; coords approximate.)'),
    ('route-66-sp', 'Route 66 State Park', 'day_use', 38.503, -90.609,
     'Eureka — Meramec-side day-use park at the former Times Beach; trails, river overlooks, visitor center. (v0 curated; coords approximate.)'),
    ('robertsville-sp', 'Robertsville State Park', 'campground', 38.423, -90.820,
     'Robertsville — Meramec-bottom state park; campground, river + Calvey Creek fishing, trails. (v0 curated; coords approximate.)'),
    ('red-bluff-cg', 'Red Bluff Campground (Mark Twain NF)', 'campground', 37.844, -91.158,
     'Davisville — USFS campground on Huzzah Creek (upper Meramec basin); Recreation.gov #232391. (v0 curated; coords approximate.)'),
    ('huzzah-ca', 'Huzzah Conservation Area', 'fishing_access', 38.052, -91.150,
     'Steelville area — MDC conservation area with Huzzah/Courtois/Meramec access, camping, floating. (v0 curated; coords approximate.)'),
    ('pacific-palisades-ca', 'Pacific Palisades Conservation Area', 'fishing_access', 38.480, -90.738,
     'Pacific — MDC area on the lower Meramec; bank fishing and bluff access. (v0 curated; coords approximate.)'),
    ('greensfelder-park', 'Greensfelder County Park', 'trailhead', 38.523, -90.652,
     'Near Eureka — large St. Louis County park adjoining the lower Meramec corridor; extensive trails. (v0 curated; coords approximate.)'),
    ('birds-nest-access', "Bird's Nest / Scotts Ford Access (Upper Meramec)", 'boat_ramp', 37.935, -91.290,
     'Crawford County — upper-Meramec float access bounding the Smallmouth Bass Special Management Area. (v0 curated; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    sid_row = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'meramec' LIMIT 1")
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
                    (:sid, 'curated_meramec_v0', :src_id, :name, :rec_type,
                     :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :desc,
                     '{}'::jsonb)
                ON CONFLICT (source_type, source_id) DO NOTHING
            """),
            {"sid": site_id, "src_id": source_id, "name": name,
             "rec_type": rec_type, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("DELETE FROM recreation_sites WHERE source_type = 'curated_meramec_v0'")
