"""seed recreation_sites for shenandoah (parks, accesses, trails, ramps)

Revision ID: nn14i5j6k7l8
Revises: mm13h4i5j6k7
Create Date: 2026-05-15 00:00:00.000000

`/api/v1/sites/shenandoah/recreation` returned an empty list because the
federal RIDB feed (the source the `recreation` adapter pulls) has very
limited East Coast coverage — none of the Shenandoah-corridor public
fishing accesses, state parks, or NPS picnic areas are in RIDB's data.

This migration seeds a curated v0 set of well-known Shenandoah-corridor
recreation sites so /path/explore renders something useful immediately.
Source: VA DCR state-parks site, NPS Shenandoah NP, USFS George
Washington NF, and VA DWR public fishing access (PFA) program. Each
row is `source_type='curated_shenandoah_v0'` so a future live adapter
can run alongside without colliding (uniqueness is on (source_type,
source_id)).

Replace these with live adapter pulls when VA DCR / NPS / USFS APIs
become integrated (P3 follow-on beads).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'nn14i5j6k7l8'
down_revision: Union[str, Sequence[str], None] = 'mm13h4i5j6k7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_id, name, rec_type, lat, lon, description)
# rec_type values match the FILTERS in ExploreMapPage.tsx
SEED = [
    # ── State parks (VA DCR) ──
    ('shenandoah-river-sp', 'Shenandoah River State Park',
     'state_park', 38.864, -78.302,
     '1,604 ac riverside park, 5+ miles of South Fork frontage, cabins, boat launch.'),
    ('sky-meadows-sp', 'Sky Meadows State Park',
     'state_park', 38.991, -77.973,
     'Blue Ridge foothills, AT access, trout-stocked Goose Creek, primitive camping.'),
    ('douthat-sp', 'Douthat State Park',
     'state_park', 37.890, -79.804,
     'Stocked lake + Wilson Creek trout, AT-adjacent, lodge + cabins (Bath Co.).'),

    # ── NPS Shenandoah NP picnic/access ──
    ('shenandoah-np-bigmeadows', 'Big Meadows (Shenandoah NP)',
     'campground', 38.522, -78.434,
     'Largest SNP campground (217 sites), wayside, lodge, Rose River trail access.'),
    ('shenandoah-np-mathews', 'Mathews Arm Campground (Shenandoah NP)',
     'campground', 38.770, -78.310,
     'North-district SNP campground, Overall Run Falls trail.'),
    ('shenandoah-np-loft', 'Loft Mountain Campground (Shenandoah NP)',
     'campground', 38.249, -78.661,
     'South-district SNP campground, Doyles River trail to falls.'),

    # ── USFS George Washington NF ──
    ('gwnf-elizabeth-furnace', 'Elizabeth Furnace Recreation Area',
     'campground', 38.913, -78.317,
     'GWNF campground on Passage Creek, swimming, stocked trout.'),
    ('gwnf-todd-lake', 'Todd Lake Recreation Area',
     'day_use', 38.366, -79.232,
     'GWNF swim lake, picnic, Shenandoah Mountain access (Augusta Co.).'),

    # ── VA DWR Public Fishing Access (boat ramps) ──
    ('vadwr-bealers-ferry', 'Bealers Ferry Boat Ramp',
     'boat_ramp', 38.940, -78.197,
     'VA DWR PFA — South Fork Shenandoah, Page Co. (NF/SF confluence area).'),
    ('vadwr-karo-landing', 'Karo Landing',
     'boat_ramp', 39.105, -78.063,
     'VA DWR PFA — Main stem Shenandoah, Warren Co. (Front Royal area).'),
    ('vadwr-castlemans-ferry', 'Castlemans Ferry',
     'boat_ramp', 39.184, -77.886,
     'VA DWR PFA — Main stem Shenandoah, Clarke Co.'),
    ('vadwr-andy-guest-park', 'Andy Guest / Shenandoah River SP Boat Launch',
     'boat_ramp', 38.864, -78.300,
     'Shenandoah River SP boat launch (South Fork).'),

    # ── Fishing access trails (PFA + wade fishing) ──
    ('mossy-creek-pfa', 'Mossy Creek Public Fishing Access',
     'fishing_access', 38.341, -78.969,
     'VA DWR fly-fishing-only spring creek, Augusta Co. — single-hook C&R; permit reqd.'),
    ('beaver-creek-pfa', 'Beaver Creek Public Fishing Access',
     'fishing_access', 38.367, -79.012,
     'VA DWR wild trout limestone spring creek, Augusta Co.'),
    ('smith-creek-pfa', 'Smith Creek Public Fishing Access',
     'fishing_access', 38.617, -78.738,
     'VA DWR special-reg trout stream, Rockingham Co. (NF Shenandoah trib).'),

    # ── Trailheads ──
    ('at-rockfish-gap', 'Appalachian Trail — Rockfish Gap',
     'trailhead', 38.034, -78.858,
     'AT trailhead at I-64/Skyline Dr south terminus, Shenandoah NP boundary.'),
    ('old-rag-trailhead', 'Old Rag Mountain Trailhead',
     'trailhead', 38.572, -78.314,
     'Iconic Shenandoah NP day-hike (8.4 mi, granite scramble); permit required.'),
    ('whiteoak-canyon-th', 'Whiteoak Canyon Trailhead',
     'trailhead', 38.564, -78.378,
     'Six-waterfall trail off Skyline Drive (Shenandoah NP).'),
]


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import text
    # Look up shenandoah's site_id once.
    sid_row = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'shenandoah' LIMIT 1")
    ).fetchone()
    if not sid_row:
        return  # shenandoah site not bootstrapped — skip silently
    site_id = sid_row[0]

    for source_id, name, rec_type, lat, lon, desc in SEED:
        conn.execute(
            text("""
                INSERT INTO recreation_sites
                    (site_id, source_type, source_id, name, rec_type,
                     latitude, longitude, geom, description, amenities)
                VALUES
                    (:sid, 'curated_shenandoah_v0', :src_id, :name, :rec_type,
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
    op.execute("DELETE FROM recreation_sites WHERE source_type = 'curated_shenandoah_v0'")
