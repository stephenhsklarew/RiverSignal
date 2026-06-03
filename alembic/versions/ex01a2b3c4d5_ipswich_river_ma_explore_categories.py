"""fix ipswich_river_ma /path/explore: recategorize state_park rows + seed fly shops/guides

Revision ID: ex01a2b3c4d5
Revises: sn01a2b3c4d5
Create Date: 2026-06-03 00:00:00.000000

RiverSignal-c2a82bde. /path/explore chips were empty for Ipswich:
  1. The ip04 recreation seed used rec_type='state_park', which is NOT one of
     the ExploreMapPage FILTER keys (campground/trailhead/boat_ramp/
     fishing_access/fly_shop/guide_service/day_use), so those 3 rows only
     showed under "All". Remap them to real chips.
  2. fly_shops_guides had zero Ipswich rows, so the Fly Shops + Guides chips
     were empty. Seed the verified Ipswich-area businesses (research-sourced;
     coords approximate; market is saltwater-skewed — no inland trout guide).
     type values match the ExploreMapPage filter ('fly_shop'/'guide_service').

All flagged needs_owner_verification. Idempotent.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ex01a2b3c4d5'
down_revision: Union[str, Sequence[str], None] = 'sn01a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Remap the 3 state_park rows to real /path/explore chips.
RECAT = [
    ('harold-parker-sf', 'campground'),     # Harold Parker SF has camping
    ('bradley-palmer-sp', 'fishing_access'),# Ipswich River frontage / wading
    ('willowdale-sf', 'trailhead'),         # trails + river access
]

# (name, type, city, lat, lon, description) — verified businesses, approximate coords.
SHOPS = [
    ('Greasy Beaks Fly Fishing', 'guide_service', 'Hamilton', 42.638, -70.858,
     'Ipswich Bay striped-bass / bluefish fly + light-tackle guide. (needs_owner_verification — v0 2026-06-03; coords approximate; local guide market is saltwater-skewed — no notable inland-trout guide.)'),
    ("Rocco's Bait & Tackle", 'fly_shop', 'Rowley', 42.726, -70.879,
     'North Shore bait & tackle serving the Ipswich/Parker area. (needs_owner_verification — v0 2026-06-03; coords approximate.)'),
    ('Surfland Bait & Tackle', 'fly_shop', 'Newbury', 42.795, -70.817,
     'Plum Island Turnpike saltwater tackle shop serving the North Shore. (needs_owner_verification — v0 2026-06-03; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for source_id, rec_type in RECAT:
        conn.execute(
            text("""
                UPDATE recreation_sites SET rec_type = :rt
                WHERE source_type = 'curated_ipswich_river_ma_v0' AND source_id = :sid
            """),
            {"rt": rec_type, "sid": source_id},
        )
    for name, typ, city, lat, lon, desc in SHOPS:
        conn.execute(
            text("""
                INSERT INTO fly_shops_guides
                    (name, type, watersheds, city, state, latitude, longitude, description)
                SELECT :name::text, :type::text, ARRAY['ipswich_river_ma']::text[],
                       :city::text, 'MA', :lat::double precision, :lon::double precision, :desc::text
                WHERE NOT EXISTS (
                    SELECT 1 FROM fly_shops_guides
                    WHERE name = :name AND 'ipswich_river_ma' = ANY(watersheds)
                )
            """),
            {"name": name, "type": typ, "city": city, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        UPDATE recreation_sites SET rec_type = 'state_park'
        WHERE source_type = 'curated_ipswich_river_ma_v0'
          AND source_id IN ('harold-parker-sf', 'bradley-palmer-sp', 'willowdale-sf')
    """)
    op.execute("""
        DELETE FROM fly_shops_guides
        WHERE 'ipswich_river_ma' = ANY(watersheds)
          AND name IN ('Greasy Beaks Fly Fishing', 'Rocco''s Bait & Tackle', 'Surfland Bait & Tackle')
    """)
