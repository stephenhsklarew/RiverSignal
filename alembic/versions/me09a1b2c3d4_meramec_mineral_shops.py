"""seed meramec mineral_shops (v0 — needs_owner_verification)

Revision ID: me09a1b2c3d4
Revises: me08a1b2c3d4
Create Date: 2026-06-07 00:00:00.000000

Per runbook §2.4 step 7 + bead RiverSignal-c1417f15. St. Louis-metro / Meramec-
corridor rock & mineral shops so DeepTrail's mineral-shop list isn't empty.
Verified businesses; approximate (city-level) coords; needs_owner_verification.
id is serial — omit on INSERT. Idempotent on (name, watershed).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'me09a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me08a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, city, lat, lon, website, description)
SHOPS = [
    ('B & J Rock Shop', 'Ballwin', 38.595, -90.546, 'https://www.bandjrockshop.com/',
     'Long-running rock, mineral, fossil and lapidary/jewelry-supply shop in Ballwin, on the lower Meramec corridor. (needs_owner_verification — v0 2026-06-07; coords approximate.)'),
    ('Fall Creek Rock Shop', 'St. Clair', 38.345, -90.980, 'https://www.fallcreekrockshop.com/',
     'Mineral and fossil specimens on historic Route 66 in the Meramec corridor. (needs_owner_verification — v0 2026-06-07; coords approximate.)'),
    ('Prospectors Crystals, Rocks & Gift Shop', 'Murphy', 38.492, -90.483, None,
     'Family-owned crystals, rocks, gems, fossils and geodes shop in south St. Louis County near the lower Meramec. (needs_owner_verification — v0 2026-06-07; coords approximate.)'),
    ("Jerry's Rock and Gem", 'St. Peters', 38.780, -90.630, 'https://jerrysrockandgem.com/',
     'Large lapidary and rock/fossil-hound supply store serving the greater St. Louis / Meramec region. (needs_owner_verification — v0 2026-06-07; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for name, city, lat, lon, website, desc in SHOPS:
        conn.execute(
            text("""
                INSERT INTO mineral_shops
                    (name, city, latitude, longitude, website, description, watersheds)
                SELECT CAST(:name AS varchar), CAST(:city AS varchar),
                       CAST(:lat AS double precision), CAST(:lon AS double precision),
                       CAST(:website AS varchar), CAST(:desc AS text),
                       ARRAY['meramec']::text[]
                WHERE NOT EXISTS (
                    SELECT 1 FROM mineral_shops
                    WHERE name = :name AND 'meramec' = ANY(watersheds)
                )
            """),
            {"name": name, "city": city, "lat": lat, "lon": lon, "website": website, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        DELETE FROM mineral_shops
        WHERE 'meramec' = ANY(watersheds)
          AND name IN ('B & J Rock Shop','Fall Creek Rock Shop',
                       'Prospectors Crystals, Rocks & Gift Shop','Jerry''s Rock and Gem')
    """)
