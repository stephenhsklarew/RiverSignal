"""seed clinch_river_va site + 2 main-stem reaches (Upper / Lower)

Revision ID: cl01a1b2c3d4
Revises: ex01a2b3c4d5
Create Date: 2026-06-03 00:00:00.000000

Phase 1 of Clinch River (VA) onboarding per
docs/helix/06-iterate/watershed-add/clinch_river_va-source-inventory-2026-06-01.md §1.7.

The platform's first Tennessee-River-basin watershed. Idempotent. Site row first
(bronze adapters FK to it; guarded with NOT EXISTS — the local onboarding session
already created it via the CLI; prod gets it here on deploy). Name is seeded
WITHOUT a state suffix ("Clinch River", not "Clinch River (VA)") per the runbook
§2.1 display-name rule, so no later UPDATE-name migration is needed.

Two warm-water main-stem reaches anchored on the two Clinch main-stem gauges:
  - Upper Clinch: 03524000 Cleveland (DA 533 mi²) — reports discharge + water
                  temperature + specific conductance, so this reach gets a FULL
                  flow + temp Go Score.
  - Lower Clinch: 03524740 Dungannon — a water-quality monitor reporting water
                  temperature + specific conductance + pH but NO discharge
                  (00060 absent). So the lower reach's flow sub-score degrades to
                  "no data" (honest — there is no discharge gauge on the lower VA
                  Clinch); temperature still scores. Best WQ telemetry on the river.

Both reaches are warm-water-dominant (smallmouth bass / muskellunge / walleye /
sunfish). The cold Clinch Mountain WMA trout tributaries (Big/Little Tumbling,
Laurel Bed) are a distinct coldwater fishery noted on the upper reach; an
ungauged trout-tributary reach is deferred to a P3 follow-on bead.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'cl01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ex01a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO sites (id, name, watershed, huc12_codes, bbox)
        SELECT gen_random_uuid(), 'Clinch River', 'clinch_river_va',
               '[]'::jsonb,
               CAST(:bbox AS jsonb)
        WHERE NOT EXISTS (SELECT 1 FROM sites WHERE watershed = 'clinch_river_va')
    """).bindparams(bbox='{"north":37.18,"south":36.58,"east":-81.48,"west":-82.85}'))

    op.execute("""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            ('clinch_river_va_upper', 'clinch_river_va',
             'Upper Clinch River', 'Upper Clinch',
             37.03, -81.85,
             '03524000', 230, TRUE,
             ARRAY['smallmouth_bass','muskellunge','walleye','rock_bass','sunfish','channel_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-03. Tazewell headwaters (Little River forks) down to the Cleveland gauge. Gauge 03524000 reports discharge + water temperature + specific conductance (FULL Go Score). Cold Clinch tributaries here include Big Cedar Creek and Indian Creek. NOTE: the Clinch MOUNTAIN WMA waters (Big Tumbling Creek, Laurel Bed) are named for the ridge but drain north to the North Fork Holston, not the Clinch.',
             'v0 §1.7 clinch_river_va-source-inventory-2026-06-01.md — needs guide review'),
            ('clinch_river_va_lower', 'clinch_river_va',
             'Lower Clinch River', 'Lower Clinch',
             36.80, -82.52,
             '03524740', 250, TRUE,
             ARRAY['smallmouth_bass','walleye','muskellunge','largemouth_bass','channel_catfish','flathead_catfish','sunfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-03. Cleveland down through Dungannon to the TN state line near Clinchport. Gauge 03524740 (Dungannon) reports water temperature + specific conductance + pH but NO discharge, so the flow sub-score degrades to no-data for this reach (no discharge gauge on the lower VA Clinch); temperature still scores. Trophy smallmouth + muskellunge ("The Retch") + walleye.',
             'v0 §1.7 clinch_river_va-source-inventory-2026-06-01.md — needs guide review')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM silver.river_reaches
        WHERE id IN ('clinch_river_va_upper', 'clinch_river_va_lower')
    """)
    op.execute("DELETE FROM sites WHERE watershed = 'clinch_river_va'")
