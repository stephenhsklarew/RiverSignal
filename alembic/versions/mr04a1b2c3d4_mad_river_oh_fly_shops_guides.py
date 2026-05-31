"""seed mad_river_oh fly_shops_guides (v0 — verifiable regional shops/clubs)

Revision ID: mr04a1b2c3d4
Revises: mr03a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

Small Ohio trout market. Only publicly-verifiable businesses/clubs are
seeded — per the runbook's "don't invent listings" rule, uncertain shop
names from the inventory (e.g. "Mike's Place") are left to curator research
rather than fabricated. ALL marked needs_owner_verification — contact
details + areas served should be refreshed by a curator before any B2C
surface treats these as authoritative.

License: project's hand-curated content, commercial:true (per ADR-008).

Follow-on curator targets (not seeded — verify before adding):
  - Springfield / Urbana area fly shops serving the Mad River C&R section
  - Trout Unlimited (Mad Men / CFRTU) chapter contact for guided access
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mr04a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr03a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, type, watersheds, city, state, latitude, longitude, website, description)
ROWS = [
    ('Mad River Outfitters', 'fly_shop', ['mad_river_oh'], 'Columbus', 'OH', 40.0698, -83.0680,
     'https://www.madriveroutfitters.com',
     'Long-established full-service Columbus fly shop; the best-known fly-fishing '
     'outfitter for the Mad River brown-trout fishery. v0 listing — needs_owner_verification.'),
    ('Buckeye United Fly Fishers', 'guide', ['mad_river_oh'], 'Cincinnati', 'OH', 39.1620, -84.4569,
     'https://www.buckeyeflyfishers.com',
     'Nonprofit fly-fishing club (not a commercial guide) active across Ohio waters '
     'including the Mad River; runs outings + education. Listed for community access. '
     'v0 listing — needs_owner_verification.'),
]


def upgrade() -> None:
    values = ",\n            ".join(
        "('{name}', '{type}', ARRAY[{ws}]::text[], '{city}', '{state}', "
        "{lat}, {lon}, '{web}', '{desc}')".format(
            name=name.replace("'", "''"), type=type_,
            ws=",".join(f"'{w}'" for w in watersheds),
            city=city, state=state, lat=lat, lon=lon, web=website,
            desc=desc.replace("'", "''"),
        )
        for (name, type_, watersheds, city, state, lat, lon, website, desc) in ROWS
    )
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
        WHERE 'mad_river_oh' = ANY(watersheds)
          AND description LIKE '%v0 listing — needs_owner_verification%'
    """)
