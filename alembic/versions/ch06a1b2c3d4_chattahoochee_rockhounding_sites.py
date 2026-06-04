"""seed chattahoochee rockhounding_sites (Dahlonega Gold Belt) — needs_curator_review=true

Revision ID: ch06a1b2c3d4
Revises: ch05a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

Per runbook §2.4 step 8 (high-care: legal-collecting liability). The standout
DeepTrail content for this watershed is the Dahlonega Gold Belt (Lumpkin Co., in
the Chestatee/Lanier headwaters of the Chattahoochee system). Seed only the two
unambiguous, tourist-operated, fee-based gold-panning attractions — both are
PRIVATE pay-to-pan operations (no wild/public collecting implied), which keeps
the liability posture conservative. needs_curator_review=true.

(Graves Mountain — the other GA dig the inventory mentioned — is in Lincoln Co.,
the Savannah basin, OUTSIDE the Chattahoochee watershed, so it is NOT seeded here.
Atlanta-metro mineral shops are deferred to a curation follow-on bead.)
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ch06a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch05a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, rock_type, lat, lon, land_owner, collecting_rules, nearest_town, description)
SITES = [
    ('Crisson Gold Mine', 'Gold (placer + lode), quartz, pyrite', 34.547, -83.985,
     'Private — tourist-operated gold mine (fee)',
     'Pay-to-pan gold + gemstone buckets on-site only; private operation, no wild/public collecting. Open to visitors.',
     'Dahlonega',
     'Historic Dahlonega Gold Belt mine, now a tourist gold-panning + gemstone attraction near the Chattahoochee/Lanier headwaters. (v0 curated; needs_curator_review; coords approximate.)'),
    ('Consolidated Gold Mine', 'Gold (lode), quartz', 34.532, -83.980,
     'Private — tourist-operated gold mine (fee)',
     'Guided underground mine tour + supervised gold panning; private, fee-based, no wild collecting.',
     'Dahlonega',
     'Once the largest gold mine east of the Mississippi; now a guided mine tour + panning attraction in the Dahlonega Gold Belt. (v0 curated; needs_curator_review; coords approximate.)'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for name, rock_type, lat, lon, owner, rules, town, desc in SITES:
        conn.execute(
            text("""
                INSERT INTO rockhounding_sites
                    (id, name, rock_type, latitude, longitude, location,
                     land_owner, collecting_rules, nearest_town, description, watersheds)
                SELECT gen_random_uuid(), CAST(:name AS text), CAST(:rt AS text),
                       CAST(:lat AS double precision), CAST(:lon AS double precision),
                       ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                       CAST(:owner AS text), CAST(:rules AS text), CAST(:town AS text),
                       CAST(:desc AS text), ARRAY['chattahoochee']::text[]
                WHERE NOT EXISTS (
                    SELECT 1 FROM rockhounding_sites
                    WHERE name = :name AND 'chattahoochee' = ANY(watersheds)
                )
            """),
            {"name": name, "rt": rock_type, "lat": lat, "lon": lon,
             "owner": owner, "rules": rules, "town": town, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        DELETE FROM rockhounding_sites
        WHERE 'chattahoochee' = ANY(watersheds)
          AND name IN ('Crisson Gold Mine', 'Consolidated Gold Mine')
    """)
