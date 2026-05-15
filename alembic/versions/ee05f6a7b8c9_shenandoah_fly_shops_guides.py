"""seed shenandoah fly_shops_guides (v0 — well-known regional shops + guides)

Revision ID: ee05f6a7b8c9
Revises: dd04e5f6a7b8
Create Date: 2026-05-15 11:15:00.000000

5 rows from publicly-known fly shops + guide services in the Shenandoah
Valley. ALL marked needs_owner_verification — contact details, areas
served, and business hours should be refreshed by a curator before any
B2C surface treats these as authoritative.

License: project's hand-curated content, commercial:true (per ADR-008).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ee05f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'dd04e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, type, watersheds, city, state, latitude, longitude, website, description)
ROWS = [
    ('Mossy Creek Fly Fishing', 'guide',    ['shenandoah'], 'Bridgewater', 'VA', 38.378, -78.964,
     'https://www.mossycreekflyfishing.com',
     'Limestone-spring trout + smallmouth guide service for the Shenandoah Valley. v0 listing — needs_owner_verification.'),
    ('Murray''s Fly Shop',     'fly_shop', ['shenandoah'], 'Edinburg',    'VA', 38.819, -78.566,
     'https://www.murraysflyshop.com',
     'Long-established fly shop. Harry Murray is the well-known smallmouth-on-the-fly authority for the Shenandoah. v0 listing — needs_owner_verification.'),
    ('Albemarle Angler',       'fly_shop', ['shenandoah'], 'Charlottesville', 'VA', 38.030, -78.479,
     'https://www.albemarleangler.com',
     'Full-service fly shop serving central VA waters including South Fork. v0 listing — needs_owner_verification.'),
    ('Page Valley Fly Fishing','guide',    ['shenandoah'], 'Luray',       'VA', 38.665, -78.460,
     'https://www.pagevalleyflyfishing.com',
     'Guided trips on South Fork Shenandoah + Blue Ridge trout tributaries. v0 listing — needs_owner_verification.'),
    ('Harman''s Trout Fishing','guide',    ['shenandoah'], 'Cabins',      'WV', 38.951, -79.298,
     'https://www.harmans.com',
     'WV side trout-fishing access (Lower N. Fork S. Branch area; tangential to Shenandoah but services Mid-Atlantic anglers). v0 listing — needs_owner_verification.'),
]


def upgrade() -> None:
    values = ",\n            ".join(
        "('{name}', '{type}', ARRAY[{ws}]::text[], '{city}', '{state}', "
        "{lat}, {lon}, '{web}', '{desc}')".format(
            name=name, type=type_, ws=",".join(f"'{w}'" for w in watersheds),
            city=city, state=state, lat=lat, lon=lon, web=website, desc=desc,
        )
        for (name, type_, watersheds, city, state, lat, lon, website, desc) in ROWS
    )
    # No unique constraint on (name, city) so guard with NOT EXISTS for idempotency.
    op.execute(f"""
        INSERT INTO fly_shops_guides
            (name, type, watersheds, city, state, latitude, longitude, website, description)
        SELECT * FROM (VALUES
            {values}
        ) AS v(name, type, watersheds, city, state, latitude, longitude, website, description)
        WHERE NOT EXISTS (
            SELECT 1 FROM fly_shops_guides f
            WHERE f.name = v.name AND f.city = v.city
        )
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM fly_shops_guides
        WHERE 'shenandoah' = ANY(watersheds)
          AND description LIKE '%v0 listing — needs_owner_verification%'
    """)
