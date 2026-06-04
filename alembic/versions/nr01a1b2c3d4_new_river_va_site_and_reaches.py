"""seed new_river_va site + 3 reaches (Upper / Claytor Lake / Lower)

Revision ID: nr01a1b2c3d4
Revises: cl09a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

Phase 1 of New River (VA) onboarding per
docs/helix/06-iterate/watershed-add/new_river_va-source-inventory-2026-06-01.md §1.7.

Second Tennessee/Ohio-basin watershed (Kanawha/Ohio, HUC8 05050001 + 05050002).
Idempotent. Site row first (NOT EXISTS guard). Name seeded WITHOUT a state suffix
("New River") per runbook §2.1.

Three reaches on a large warm-water river. IMPORTANT: NONE of the 5 main-stem
gauges report water temperature (00010 absent) — every reach's temp sub-score
degrades to "no data" (the New's known gap, same as the MA basins); flow still
scores (all 5 gauges report discharge):
  - Upper New: 03164000 Galax (NC line → Ivanhoe/Allisonia); New River Trail corridor.
  - Claytor Lake: reservoir fishery anchored on the 03168000 Allisonia inflow gauge;
    striped/hybrid bass + largemouth + crappie; Alabama bass is an invasive flag here.
  - Lower New: 03171000 Radford (2,767 mi²) → Glen Lyn (3,770 mi²) at the WV line;
    dam-regulated trophy smallmouth + muskellunge. The WV New River Gorge is out of scope.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'nr01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl09a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO sites (id, name, watershed, huc12_codes, bbox)
        SELECT gen_random_uuid(), 'New River', 'new_river_va',
               '[]'::jsonb,
               CAST(:bbox AS jsonb)
        WHERE NOT EXISTS (SELECT 1 FROM sites WHERE watershed = 'new_river_va')
    """).bindparams(bbox='{"north":37.42,"south":36.56,"east":-80.50,"west":-81.15}'))

    op.execute("""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            ('new_river_va_upper', 'new_river_va',
             'Upper New River', 'Upper New',
             36.74, -80.97,
             '03164000', 15, TRUE,
             ARRAY['smallmouth_bass','muskellunge','walleye','rock_bass','redbreast_sunfish','channel_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-03. NC line near Galax/Mouth of Wilson down to Ivanhoe/Allisonia, along the New River Trail State Park rail-trail. Gauge 03164000 Galax reports discharge + gage height only (NO water temp → temp sub-score degrades).',
             'v0 §1.7 new_river_va-source-inventory-2026-06-01.md — needs guide review'),
            ('new_river_va_claytor', 'new_river_va',
             'Claytor Lake', 'Claytor Lake',
             37.00, -80.62,
             '03168000', NULL, TRUE,
             ARRAY['striped_bass','largemouth_bass','smallmouth_bass','walleye','channel_catfish','crappie']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-03. Claytor Lake reservoir (Claytor Dam, 1939, AEP), anchored on the 03168000 Allisonia inflow gauge. Striped / hybrid striped bass, largemouth, crappie. Alabama bass is an invasive concern here. Reservoir gauge reports discharge only (NO water temp).',
             'v0 §1.7 new_river_va-source-inventory-2026-06-01.md — needs guide review'),
            ('new_river_va_lower', 'new_river_va',
             'Lower New River', 'Lower New',
             37.25, -80.62,
             '03171000', 330, TRUE,
             ARRAY['smallmouth_bass','muskellunge','walleye','rock_bass','channel_catfish','flathead_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-03. Radford (DA 2,767 mi²) down through Pearisburg/Pembroke to the WV state line at Glen Lyn (DA 3,770 mi²). Dam-regulated; trophy smallmouth + state-record-class muskellunge. Gauges 03171000 Radford / 03176500 Glen Lyn report discharge only (NO water temp).',
             'v0 §1.7 new_river_va-source-inventory-2026-06-01.md — needs guide review')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM silver.river_reaches
        WHERE id IN ('new_river_va_upper', 'new_river_va_claytor', 'new_river_va_lower')
    """)
    op.execute("DELETE FROM sites WHERE watershed = 'new_river_va'")
