"""seed new_river_va fly_shops_guides — needs_review=true

Revision ID: nr05a1b2c3d4
Revises: nr04a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

Per runbook §2.4 step 6 / §2.6.5. The New has the strongest guide market of the
four VA candidates (inventory §1.1). type ∈ {fly_shop, guide_service, both};
id is a serial (omit on INSERT). All needs_owner_verification (approximate
coords). Idempotent via NOT EXISTS on (name, watershed).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'nr05a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nr04a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, type, city, lat, lon, description)
SHOPS = [
    ('Tangent Outfitters', 'both', 'Pembroke', 37.320, -80.638,
     'New River fly shop + smallmouth/musky float-guide service and river outfitter '
     'near Pembroke/Radford. (needs_owner_verification — v0 2026-06-03; coords approximate.)'),
    ('Greasy Creek Outfitters', 'guide_service', 'Willis', 36.880, -80.270,
     'Southwest Virginia fly-fishing guide service (New River smallmouth + mountain '
     'trout tributaries). (needs_owner_verification — v0 2026-06-03; coords approximate.)'),
    ('New River Fly Fishing', 'guide_service', 'Radford', 37.200, -80.580,
     'New River smallmouth-bass and muskellunge float-trip guide. '
     '(needs_owner_verification — v0 2026-06-03; coords approximate.)'),
    ('Appalachian Outdoor Adventures', 'guide_service', 'Pearisburg', 37.330, -80.740,
     'Lower New River (Giles County) guided float trips and paddling outfitter. '
     '(needs_owner_verification — v0 2026-06-03; coords approximate.)'),
    ('New River Outdoor Company', 'guide_service', 'Pearisburg', 37.332, -80.728,
     'Giles County New River shuttle / paddling / fishing-float outfitter. '
     '(needs_owner_verification — v0 2026-06-03; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for name, typ, city, lat, lon, desc in SHOPS:
        conn.execute(
            text("""
                INSERT INTO fly_shops_guides
                    (name, type, watersheds, city, state, latitude, longitude, description)
                SELECT CAST(:name AS text), CAST(:type AS text),
                       ARRAY['new_river_va']::text[],
                       CAST(:city AS text), 'VA',
                       CAST(:lat AS double precision), CAST(:lon AS double precision),
                       CAST(:desc AS text)
                WHERE NOT EXISTS (
                    SELECT 1 FROM fly_shops_guides
                    WHERE name = :name AND 'new_river_va' = ANY(watersheds)
                )
            """),
            {"name": name, "type": typ, "city": city, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        DELETE FROM fly_shops_guides
        WHERE 'new_river_va' = ANY(watersheds)
          AND name IN ('Tangent Outfitters', 'Greasy Creek Outfitters', 'New River Fly Fishing',
                       'Appalachian Outdoor Adventures', 'New River Outdoor Company')
    """)
