"""seed clinch_river_va fly_shops_guides — needs_review=true

Revision ID: cl05a1b2c3d4
Revises: cl04a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

Per runbook §2.4 step 6 / §2.6.5: seed the verified Clinch-area fly shops +
guide services so /path/explore's Fly Shops + Guides chips populate. Sources:
inventory §1.1 (Clinch Life Outfitters, Riverfeet Fly Fishing) + the Abingdon
fly-fishing market. type ∈ {fly_shop, guide_service, both} to match the
ExploreMapPage filter; id is a serial — omit on INSERT. All flagged
needs_owner_verification (approximate coords). Idempotent via NOT EXISTS on
(name, watershed). The Clinch is a warm-water smallmouth/musky float fishery
plus cold trout tributaries — the local market is float-guide-skewed.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'cl05a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl04a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, type, city, lat, lon, description)
SHOPS = [
    ('Clinch Life Outfitters', 'guide_service', 'St. Paul', 36.905, -82.312,
     'Clinch River smallmouth-bass / muskellunge float-trip guide service on the '
     'main stem at St. Paul, gateway to the Clinch River State Park blueway. '
     '(needs_owner_verification — v0 2026-06-03; coords approximate.)'),
    ('Riverfeet Fly Fishing', 'guide_service', 'Abingdon', 36.712, -81.972,
     'SW Virginia wade + float fly-fishing guide (Clinch smallmouth/musky + '
     'Clinch Mountain WMA stocked trout tributaries). '
     '(needs_owner_verification — v0 2026-06-03; coords approximate.)'),
    ('Virginia Creeper Fly Shop', 'fly_shop', 'Abingdon', 36.709, -81.977,
     'Abingdon fly shop serving SW Virginia trout + smallmouth waters near the '
     'Virginia Creeper Trail. (needs_owner_verification — v0 2026-06-03; coords '
     'approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for name, typ, city, lat, lon, desc in SHOPS:
        conn.execute(
            text("""
                INSERT INTO fly_shops_guides
                    (name, type, watersheds, city, state, latitude, longitude, description)
                SELECT CAST(:name AS text), CAST(:type AS text),
                       ARRAY['clinch_river_va']::text[],
                       CAST(:city AS text), 'VA',
                       CAST(:lat AS double precision), CAST(:lon AS double precision),
                       CAST(:desc AS text)
                WHERE NOT EXISTS (
                    SELECT 1 FROM fly_shops_guides
                    WHERE name = :name AND 'clinch_river_va' = ANY(watersheds)
                )
            """),
            {"name": name, "type": typ, "city": city, "lat": lat, "lon": lon, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        DELETE FROM fly_shops_guides
        WHERE 'clinch_river_va' = ANY(watersheds)
          AND name IN ('Clinch Life Outfitters', 'Riverfeet Fly Fishing', 'Virginia Creeper Fly Shop')
    """)
