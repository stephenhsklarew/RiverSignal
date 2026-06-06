"""seed meramec fly_shops_guides (v0 — needs_owner_verification)

Revision ID: me05a1b2c3d4
Revises: me04a1b2c3d4
Create Date: 2026-06-06 00:00:00.000000

Per runbook §2.4 step 6 + inventory §1.4. Verified businesses serving the
Meramec (St. Louis fly shop + Maramec Spring/Meramec trout & smallmouth guides +
Steelville-corridor float outfitters that also guide). type in
{fly_shop, guide_service, both}. Approximate coords; needs_owner_verification.
Idempotent on (name, watershed). id is serial — omit on INSERT.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'me05a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me04a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, type, city, lat, lon, description)
SHOPS = [
    ('Feather-Craft Fly Fishing', 'fly_shop', 'St. Louis', 38.629, -90.255,
     'Long-running St. Louis fly shop (est. 1955) outfitting Meramec-basin smallmouth '
     'and Ozark trout anglers. (needs_owner_verification — v0 2026-06-06; coords approximate.)'),
    ('Missouri on the Fly', 'guide_service', 'St. James', 37.997, -91.617,
     'Guide service for Meramec/Maramec Spring rainbow trout and Ozark smallmouth. '
     '(needs_owner_verification — v0 2026-06-06; coords approximate.)'),
    ('Missouri Fly Life Guide Co.', 'guide_service', 'Steelville', 37.968, -91.353,
     'Smallmouth + trout float-and-wade guiding on the upper Meramec corridor. '
     '(needs_owner_verification — v0 2026-06-06; coords approximate.)'),
    ('Ozark Outdoors Riverfront Resort', 'both', 'Leasburg', 38.099, -91.281,
     'Meramec float/canoe/kayak outfitter and riverfront resort near Onondaga Cave SP. '
     '(needs_owner_verification — v0 2026-06-06; coords approximate.)'),
    ('Bass River Resort', 'both', 'Steelville', 37.985, -91.301,
     'Steelville-corridor Meramec/Huzzah/Courtois float outfitter and resort. '
     '(needs_owner_verification — v0 2026-06-06; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for name, typ, city, lat, lon, desc in SHOPS:
        conn.execute(
            text("""
                INSERT INTO fly_shops_guides
                    (name, type, watersheds, city, state, latitude, longitude, description)
                SELECT CAST(:name AS text), CAST(:type AS text),
                       ARRAY['meramec']::text[],
                       CAST(:city AS text), 'MO',
                       CAST(:lat AS double precision), CAST(:lon AS double precision),
                       CAST(:desc AS text)
                WHERE NOT EXISTS (
                    SELECT 1 FROM fly_shops_guides
                    WHERE name = :name AND 'meramec' = ANY(watersheds)
                )
            """),
            {"name": name, "type": typ, "city": city, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        DELETE FROM fly_shops_guides
        WHERE 'meramec' = ANY(watersheds)
          AND name IN ('Feather-Craft Fly Fishing','Missouri on the Fly',
                       'Missouri Fly Life Guide Co.','Ozark Outdoors Riverfront Resort',
                       'Bass River Resort')
    """)
