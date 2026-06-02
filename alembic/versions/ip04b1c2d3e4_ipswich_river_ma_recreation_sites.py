"""seed recreation_sites for ipswich_river_ma (parks, accesses, paddling put-ins)

Revision ID: ip04b1c2d3e4
Revises: ip03b1c2d3e4
Create Date: 2026-06-02 00:00:00.000000

`/api/v1/sites/ipswich_river_ma/recreation` returns empty because the federal
RIDB feed (the `recreation` adapter) has no coverage for the MA state
parks / forests / Mass Audubon sanctuaries that anglers and paddlers actually
use on the Ipswich (verified: the `recreation` adapter created 0 rows for this
watershed). Curated v0 set of well-known Ipswich-corridor recreation sites so
/path/explore renders something useful immediately.

source_type='curated_ipswich_river_ma_v0' (uniqueness on (source_type,
source_id)) so a future live adapter can run alongside without colliding.
Coordinates are approximate v0 placements — needs_review. Replace/verify with
a live MassGIS / Mass Audubon pull (P3 bead).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ip04b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'ip03b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_id, name, rec_type, lat, lon, description) — rec_type values match
# the FILTERS in ExploreMapPage.tsx. Coords approximate (needs_review).
SEED = [
    ('bradley-palmer-sp', 'Bradley Palmer State Park',
     'state_park', 42.6480, -70.9300,
     'Topsfield/Hamilton — riverside trails along the Ipswich River; wading + canoe access. (v0 curated; coords approximate.)'),
    ('willowdale-sf', 'Willowdale State Forest',
     'state_park', 42.6620, -70.9450,
     'Topsfield/Ipswich — trails and Ipswich River frontage; paddling access. (v0 curated; coords approximate.)'),
    ('harold-parker-sf', 'Harold Parker State Forest',
     'state_park', 42.6200, -71.0800,
     'North Andover/Middleton — ponds + trails in the upper Ipswich basin; pond fishing. (v0 curated; coords approximate.)'),
    ('ipswich-river-wildlife-sanctuary', 'Ipswich River Wildlife Sanctuary (Mass Audubon)',
     'day_use', 42.6360, -70.9080,
     'Topsfield — Mass Audubon sanctuary on the Ipswich River; canoe/kayak launch + trails. (v0 curated; coords approximate.)'),
    ('foote-brothers-canoe', 'Foote Brothers Canoe & Kayak Rental',
     'boat_ramp', 42.6700, -70.9100,
     'Ipswich (Topsfield Rd) — canoe/kayak rental and Ipswich River put-in. (v0 curated; coords approximate.)'),
    ('topsfield-town-landing', 'Topsfield Town Landing',
     'boat_ramp', 42.6380, -70.9500,
     'Topsfield — town paddling/boat landing on the Ipswich River. (v0 curated; coords approximate.)'),
    ('ipswich-riverwalk', 'Ipswich Riverwalk',
     'trailhead', 42.6790, -70.8410,
     'Ipswich town — riverwalk along the lower Ipswich River near the head of tide. (v0 curated; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    sid_row = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'ipswich_river_ma' LIMIT 1")
    ).fetchone()
    if not sid_row:
        return  # site not bootstrapped — skip silently
    site_id = sid_row[0]

    for source_id, name, rec_type, lat, lon, desc in SEED:
        conn.execute(
            text("""
                INSERT INTO recreation_sites
                    (site_id, source_type, source_id, name, rec_type,
                     latitude, longitude, geom, description, amenities)
                VALUES
                    (:sid, 'curated_ipswich_river_ma_v0', :src_id, :name, :rec_type,
                     :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :desc,
                     '{}'::jsonb)
                ON CONFLICT (source_type, source_id) DO NOTHING
            """),
            {"sid": site_id, "src_id": source_id, "name": name,
             "rec_type": rec_type, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("DELETE FROM recreation_sites WHERE source_type = 'curated_ipswich_river_ma_v0'")
