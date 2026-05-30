"""seed recreation_sites for mad_river_oh (parks, accesses, trails, ramps)

Revision ID: mr08a1b2c3d4
Revises: mr07a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

`/api/v1/sites/mad_river_oh/recreation` returns a near-empty list because
the federal RIDB feed (the `recreation` adapter's source) covers the USACE
C.J. Brown Reservoir but misses the ODNR state parks and Mad River public
fishing accesses that anglers actually use (ODNR uses ReserveOhio, which has
no public API — inventory §1.3).

Curated v0 set of well-known Mad River-corridor recreation sites so
/path/explore renders something useful immediately. Each row is
`source_type='curated_mad_river_oh_v0'` so a future live adapter can run
alongside without colliding (uniqueness on (source_type, source_id)).
Replace with live pulls when an ODNR/ReserveOhio integration lands (P3 bead).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mr08a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr07a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_id, name, rec_type, lat, lon, description)
# rec_type values match the FILTERS in ExploreMapPage.tsx
SEED = [
    # ── ODNR state parks ──
    ('buck-creek-sp', 'Buck Creek State Park',
     'state_park', 39.9690, -83.7110,
     'Clark Co. state park on C.J. Brown Reservoir — campground, beach, boat launch, Mad River basin access.'),
    ('kiser-lake-sp', 'Kiser Lake State Park',
     'state_park', 40.1920, -83.8620,
     'Champaign Co. state park — no-motor lake, swimming, wetland boardwalk.'),
    ('indian-lake-sp', 'Indian Lake State Park',
     'state_park', 40.4900, -83.8900,
     'Logan Co. state park near the upper Mad River headwaters region — boating, camping.'),

    # ── USACE / reservoir ──
    ('cj-brown-reservoir', 'C.J. Brown Reservoir (USACE)',
     'boat_ramp', 39.9750, -83.7330,
     'USACE flood-control reservoir on Buck Creek; multiple boat ramps + dam tailwater fishing.'),

    # ── Nature preserve / day use ──
    ('cedar-bog', 'Cedar Bog State Nature Preserve',
     'day_use', 40.0490, -83.8040,
     "Champaign Co. — Ohio's largest boardwalked fen, spring-fed; rare flora (ODNR / Ohio History Connection)."),
    ('davey-moore-park', 'Davey Moore Park',
     'day_use', 39.9270, -83.8130,
     'Springfield city park on the lower Mad River corridor.'),

    # ── Mad River public fishing access (wade) ──
    ('mad-river-eagle-city', 'Mad River Access — Eagle City (St. Paris Pike)',
     'fishing_access', 39.9900, -83.8500,
     'Clark Co. wade access near USGS gauge 03267900; stocked brown-trout C&R water.'),
    ('mad-river-pimtown', 'Mad River Access — Pimtown Road',
     'fishing_access', 40.0500, -83.8300,
     'Champaign/Clark Co. mainstem wade access in the C&R trout section.'),

    # ── Trails ──
    ('buck-creek-trail', 'Buck Creek Scenic Trail',
     'trailhead', 39.9300, -83.7600,
     'Paved multi-use trail along Buck Creek into Springfield.'),
    ('simon-kenton-trail', 'Simon Kenton Trail (Springfield–Urbana)',
     'trailhead', 40.0500, -83.7800,
     'Rail-trail paralleling the Mad River corridor between Springfield and Urbana.'),
]


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import text
    sid_row = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'mad_river_oh' LIMIT 1")
    ).fetchone()
    if not sid_row:
        return  # mad_river_oh site not bootstrapped — skip silently
    site_id = sid_row[0]

    for source_id, name, rec_type, lat, lon, desc in SEED:
        conn.execute(
            text("""
                INSERT INTO recreation_sites
                    (site_id, source_type, source_id, name, rec_type,
                     latitude, longitude, geom, description, amenities)
                VALUES
                    (:sid, 'curated_mad_river_oh_v0', :src_id, :name, :rec_type,
                     :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :desc,
                     '{}'::jsonb)
                ON CONFLICT (source_type, source_id) DO NOTHING
            """),
            {
                "sid": site_id, "src_id": source_id, "name": name,
                "rec_type": rec_type, "lat": lat, "lon": lon, "desc": desc,
            },
        )


def downgrade() -> None:
    op.execute("DELETE FROM recreation_sites WHERE source_type = 'curated_mad_river_oh_v0'")
