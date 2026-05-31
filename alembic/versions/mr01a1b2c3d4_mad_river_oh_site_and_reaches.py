"""seed mad_river_oh site + 3 reaches (Upper / Trout Section / Lower)

Revision ID: mr01a1b2c3d4
Revises: am38a9b0c1d2
Create Date: 2026-05-30 00:00:00.000000

Phase 1 of Mad River (OH) onboarding per
docs/helix/06-iterate/watershed-add/mad_river_oh-source-inventory-2026-05-25.md §1.7.

First Midwest / Ohio-River-Basin watershed on the platform. Idempotent.
Site row first (bronze adapters FK to it; guarded with NOT EXISTS).
Three reaches anchored on the two active mainstem USGS gauges:
  - Upper Mad:     03267900 (Mad R at St Paris Pike at Eagle City — downstream
                   proxy until/if an upper-basin gauge is identified)
  - Trout Section: 03267900 (the stocked C&R brown-trout stretch, Champaign/Clark)
  - Lower Mad:     03269500 (Mad R near Springfield → Great Miami at Dayton)

All reaches flagged needs_guide_review=true. Lower is warm-water
(smallmouth-dominant below Springfield); upper + trout section are
cold spring-fed (brown trout).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'mr01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'am38a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Bootstrap the site row (everything else FKs to it). NOT EXISTS guard
    # keeps the migration idempotent (the local onboarding session created the
    # site via the CLI; prod gets it here on deploy).
    op.execute(sa.text("""
        INSERT INTO sites (id, name, watershed, huc12_codes, bbox)
        SELECT gen_random_uuid(), 'Mad River', 'mad_river_oh',
               '[]'::jsonb,
               CAST(:bbox AS jsonb)
        WHERE NOT EXISTS (SELECT 1 FROM sites WHERE watershed = 'mad_river_oh')
    """).bindparams(bbox='{"north":40.60,"south":39.65,"east":-83.45,"west":-84.30}'))

    # 2. Three reaches anchored on USGS gauges. general_flow_bearing left NULL
    # (the Mad meanders SSW but is sinuous enough that a single bearing is
    # misleading at reach scale — per runbook §2.4 step 1).
    op.execute("""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            ('mad_river_oh_upper', 'mad_river_oh',
             'Upper Mad River', 'Upper Mad',
             40.25, -83.75,
             '03267900', NULL, FALSE,
             ARRAY['brown_trout','brook_trout','creek_chub','smallmouth_bass']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-05-30. Logan Co. headwater springs (Campbell Hill) to Urbana. Cold, spring-fed. Gauge 03267900 is a downstream proxy — verify if an upper-basin gauge exists.',
             'v0 §1.7 mad_river_oh-source-inventory-2026-05-25.md — needs guide review'),
            ('mad_river_oh_trout_section', 'mad_river_oh',
             'Mad River C&R Trout Section', 'Trout Section',
             40.00, -83.85,
             '03267900', NULL, FALSE,
             ARRAY['brown_trout','rainbow_trout','smallmouth_bass']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-05-30. The stocked brown-trout C&R stretch (Champaign/Clark Co). Confirm exact C&R boundaries + special regs with ODNR. ~11,500 brown-trout yearlings stocked annually every mid-October.',
             'v0 §1.7 mad_river_oh-source-inventory-2026-05-25.md — needs guide review'),
            ('mad_river_oh_lower', 'mad_river_oh',
             'Lower Mad River', 'Lower Mad',
             39.85, -84.05,
             '03269500', NULL, TRUE,
             ARRAY['smallmouth_bass','rock_bass','channel_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-05-30. Springfield to the Great Miami confluence at Dayton. Warm-water dominant below Springfield.',
             'v0 §1.7 mad_river_oh-source-inventory-2026-05-25.md — needs guide review')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM silver.river_reaches
        WHERE id IN ('mad_river_oh_upper', 'mad_river_oh_trout_section', 'mad_river_oh_lower')
    """)
    op.execute("DELETE FROM sites WHERE watershed = 'mad_river_oh'")
