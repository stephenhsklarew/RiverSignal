"""seed ipswich_river_ma site + 2 freshwater reaches (Upper / Lower)

Revision ID: ip01a1b2c3d4
Revises: ro2so3idx4567
Create Date: 2026-06-02 00:00:00.000000

Phase 1 of Ipswich River (MA) onboarding per
docs/helix/06-iterate/watershed-add/ipswich_river_ma-source-inventory-2026-06-01.md §1.7.

First New-England-coastal-region watershed on the platform. Idempotent.
Site row first (bronze adapters FK to it; guarded with NOT EXISTS — the local
onboarding session already created it via the CLI; prod gets it here on deploy).

Two FRESHWATER reaches anchored on the two active mainstem USGS gauges:
  - Upper Ipswich: 01101500 (Ipswich R at South Middleton; DA 44.5 mi²) — the
                   most flow-stressed reach (municipal groundwater withdrawals).
  - Lower Ipswich: 01102000 (Ipswich R near Ipswich; DA 125 mi²) — freshwater
                   down to the Ipswich Mills head-of-tide dam.

The estuary (Plum Island Sound / Ipswich Bay; striped bass) is intentionally
EXCLUDED from v0 TQS: it has no USGS gauge and is a tide/bait-driven fishery the
freshwater Go-Score model does not represent (see inventory §Model-fit). Both
reaches are warm-water-dominant (smallmouth/largemouth/pickerel/panfish) with a
put-and-take stocked-trout overlay. NOTE: neither gauge reports water
temperature (00010 absent), so the TQS temp sub-score degrades to "no data".
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'ip01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ro2so3idx4567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO sites (id, name, watershed, huc12_codes, bbox)
        SELECT gen_random_uuid(), 'Ipswich River (MA)', 'ipswich_river_ma',
               '[]'::jsonb,
               CAST(:bbox AS jsonb)
        WHERE NOT EXISTS (SELECT 1 FROM sites WHERE watershed = 'ipswich_river_ma')
    """).bindparams(bbox='{"north":42.78,"south":42.46,"east":-70.80,"west":-71.25}'))

    # Two freshwater reaches. general_flow_bearing NULL (low-gradient, sinuous
    # meander through marsh — a single bearing is misleading at reach scale).
    op.execute("""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            ('ipswich_river_ma_upper', 'ipswich_river_ma',
             'Upper Ipswich River', 'Upper Ipswich',
             42.54, -71.05,
             '01101500', NULL, TRUE,
             ARRAY['smallmouth_bass','largemouth_bass','chain_pickerel','rainbow_trout','brown_trout','yellow_perch','bluegill']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-02. Wilmington/Burlington headwaters to the South Middleton gauge. Most flow-stressed reach — municipal groundwater withdrawals draw it down / dry in summer (American Rivers #8 Most Endangered, 2021; USGS FS 00-160). Gauge 01101500 reports discharge + gage height only (NO water temp).',
             'v0 §1.7 ipswich_river_ma-source-inventory-2026-06-01.md — needs guide review'),
            ('ipswich_river_ma_lower', 'ipswich_river_ma',
             'Lower Ipswich River', 'Lower Ipswich',
             42.66, -70.92,
             '01102000', NULL, TRUE,
             ARRAY['largemouth_bass','smallmouth_bass','white_perch','chain_pickerel','river_herring','brown_bullhead']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-02. Middleton/Topsfield/Hamilton down to the Ipswich Mills head-of-tide dam. Anadromous river-herring run. Gauge 01102000 reports discharge + gage height only (NO water temp). Estuary below the dam (striped bass) is out of v0 TQS scope.',
             'v0 §1.7 ipswich_river_ma-source-inventory-2026-06-01.md — needs guide review')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM silver.river_reaches
        WHERE id IN ('ipswich_river_ma_upper', 'ipswich_river_ma_lower')
    """)
    op.execute("DELETE FROM sites WHERE watershed = 'ipswich_river_ma'")
