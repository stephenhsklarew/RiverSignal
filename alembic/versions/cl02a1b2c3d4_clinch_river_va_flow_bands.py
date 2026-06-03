"""seed clinch_river_va flow_quality_bands (v0 from USGS daily-value percentiles)

Revision ID: cl02a1b2c3d4
Revises: cl01a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

cfs bands per runbook §2.4 step 2 from the Clinch main-stem discharge gauge's
daily-value percentiles (bronze.time_series, 2026-06-03, ~400 daily values):
  - 03524000 Cleveland: p10=148  p30=255  p70=548  p90=1181

  cfs_low = p10, cfs_ideal_low = p30, cfs_ideal_high = p70, cfs_high = p90.

The lower reach's primary gauge (03524740 Dungannon) reports NO discharge, so
there are no lower-reach percentiles to derive from. Cleveland (the next gauge
upstream, DA 533 mi²) is used as a documented PROXY for the lower reach's bands
so thresholds exist; live flow at Dungannon is absent (the flow sub-score
degrades there regardless). Real lower-Clinch flow is somewhat higher (more
drainage) — flag for angler review.

Source flags needs-angler-review. Idempotent via composite PK
(reach_id, species, season_start_month).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'cl02a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high, source_note)
BANDS = [
    ('clinch_river_va_upper', 148, 255, 548, 1181,
     'v0 derived from USGS 03524000 Cleveland daily-value percentiles 2026-06-03; needs angler review'),
    ('clinch_river_va_lower', 148, 255, 548, 1181,
     'v0 PROXY from USGS 03524000 Cleveland (Dungannon 03524740 has no discharge gauge; real lower flow is higher); needs angler review'),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('{rid}', '', {lo}, {ilo}, {ihi}, {hi}, 0, NULL, '{note}')"
        for (rid, lo, ilo, ihi, hi, note) in BANDS
    )
    op.execute(f"""
        INSERT INTO silver.flow_quality_bands
            (reach_id, species, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high,
             season_start_month, season_end_month, source)
        VALUES
            {rows}
        ON CONFLICT (reach_id, species, season_start_month) DO NOTHING
    """)


def downgrade() -> None:
    ids = ",".join(f"'{r[0]}'" for r in BANDS)
    op.execute(f"DELETE FROM silver.flow_quality_bands WHERE reach_id IN ({ids})")
