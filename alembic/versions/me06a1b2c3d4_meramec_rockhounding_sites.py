"""seed meramec rockhounding_sites (v0 — needs_curator_review; conservative)

Revision ID: me06a1b2c3d4
Revises: me05a1b2c3d4
Create Date: 2026-06-06 00:00:00.000000

Per runbook §2.4 step 8 + inventory §1.4. High-care: legal-collecting sites carry
liability. Lean conservative — two documented Meramec-basin targets only:
  - Washington County barite "tiff" district (Potosi/Old Mines) — historic
    barite, tiff roses; collect on private land BY PERMISSION only.
  - Meramec/Huzzah gravel-bar chert, agate, druzy quartz near Steelville —
    common-rock surface collecting on public gravel bars.
Galena from the Old Lead Belt is deliberately EXCLUDED (Superfund lead
contamination + access restrictions — see Big River advisory). Idempotent on
(name, watershed).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'me06a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me05a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (name, rock_type, lat, lon, land_owner, collecting_rules, nearest_town, description)
SITES = [
    ('Washington County Barite District (Potosi/Old Mines)',
     'Barite ("tiff"), barite roses, calcite', 37.931, -90.788,
     'Mixed private — historic mining district',
     'Barite/tiff occurs on private land and old mine dumps; collect ONLY with the '
     'landowner''s permission. No collecting on posted or reclaimed mine land. '
     'Verify ownership locally before entry.',
     'Potosi',
     'Missouri''s historic "Tiff Belt" — Washington County led the world in barite; tiff '
     'roses and crystalline barite still weather out. (v0 curated; needs_curator_review; '
     'coords approximate; permission required.)'),
    ('Meramec & Huzzah Gravel Bars (Steelville)',
     'Chert, Ozark agate, druzy quartz, jasper', 37.968, -91.300,
     'Public stream gravel bars (MDC stream access / Mark Twain NF reaches)',
     'Casual surface collecting of common chert/agate/quartz on public gravel bars is '
     'generally allowed; no digging into banks, no commercial collecting, and do not '
     'collect on private frontage or in state parks. Confirm the specific access is public.',
     'Steelville',
     'Ozark float-stream gravel bars weather out chert, banded agate, and druzy-quartz-lined '
     'vugs from the surrounding dolomites. (v0 curated; needs_curator_review; coords approximate.)'),
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
                       CAST(:desc AS text), ARRAY['meramec']::text[]
                WHERE NOT EXISTS (
                    SELECT 1 FROM rockhounding_sites
                    WHERE name = :name AND 'meramec' = ANY(watersheds)
                )
            """),
            {"name": name, "rt": rock_type, "lat": lat, "lon": lon,
             "owner": owner, "rules": rules, "town": town, "desc": desc},
        )


def downgrade() -> None:
    op.execute("""
        DELETE FROM rockhounding_sites
        WHERE 'meramec' = ANY(watersheds)
          AND name IN ('Washington County Barite District (Potosi/Old Mines)',
                       'Meramec & Huzzah Gravel Bars (Steelville)')
    """)
