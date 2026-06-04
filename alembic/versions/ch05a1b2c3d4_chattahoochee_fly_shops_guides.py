"""seed chattahoochee fly_shops_guides — needs_review=true

Revision ID: ch05a1b2c3d4
Revises: ch04a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

Per runbook §2.4 step 6 / §2.6.5. Strong market (inventory §1.1): Buford Dam
tailwater + Blue Ridge headwaters + Lanier striper guides. type ∈
{fly_shop, guide_service, both}; id serial (omit). needs_owner_verification;
coords approximate. Idempotent via NOT EXISTS on (name, watershed).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ch05a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch04a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, type, city, lat, lon, description)
SHOPS = [
    ('Unicoi Outfitters', 'both', 'Helen', 34.700, -83.725,
     'North Georgia fly shop + guide service (Chattahoochee headwaters, Soque, '
     'and Buford tailwater). (needs_owner_verification — v0 2026-06-04; coords approximate.)'),
    ('Cohutta Fishing Company', 'fly_shop', 'Blue Ridge', 34.864, -84.324,
     'North Georgia fly shop + guide outfitter serving the Chattahoochee tailwater '
     'and Blue Ridge trout waters. (needs_owner_verification — v0 2026-06-04; coords approximate.)'),
    ('The Fish Hawk', 'fly_shop', 'Atlanta', 33.842, -84.379,
     'Long-running Atlanta fly shop outfitting the Chattahoochee tailwater. '
     '(needs_owner_verification — v0 2026-06-04; coords approximate.)'),
    ('River Through Atlanta Guide Service', 'guide_service', 'Roswell', 34.020, -84.360,
     'Buford Dam tailwater trout float + wade guide service through the CRNRA. '
     '(needs_owner_verification — v0 2026-06-04; coords approximate.)'),
    ('Reel Job Fishing Adventures', 'guide_service', 'Buford', 34.120, -84.010,
     'Chattahoochee tailwater + Lake Lanier striped-bass guide service. '
     '(needs_owner_verification — v0 2026-06-04; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for name, typ, city, lat, lon, desc in SHOPS:
        conn.execute(
            text("""
                INSERT INTO fly_shops_guides
                    (name, type, watersheds, city, state, latitude, longitude, description)
                SELECT CAST(:name AS text), CAST(:type AS text),
                       ARRAY['chattahoochee']::text[],
                       CAST(:city AS text), 'GA',
                       CAST(:lat AS double precision), CAST(:lon AS double precision),
                       CAST(:desc AS text)
                WHERE NOT EXISTS (
                    SELECT 1 FROM fly_shops_guides
                    WHERE name = :name AND 'chattahoochee' = ANY(watersheds)
                )
            """),
            {"name": name, "type": typ, "city": city, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        DELETE FROM fly_shops_guides
        WHERE 'chattahoochee' = ANY(watersheds)
          AND name IN ('Unicoi Outfitters','Cohutta Fishing Company','The Fish Hawk',
                       'River Through Atlanta Guide Service','Reel Job Fishing Adventures')
    """)
