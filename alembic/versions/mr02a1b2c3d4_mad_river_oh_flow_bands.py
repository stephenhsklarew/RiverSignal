"""seed mad_river_oh flow_quality_bands (v0 from USGS daily-value percentiles)

Revision ID: mr02a1b2c3d4
Revises: mr01a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

cfs bands derived per runbook §2.4 step 2 from each reach's primary-gauge
daily-value discharge percentiles (computed against bronze.time_series,
2026-05-30, ~730 daily values per gauge):
  - 03267900 Eagle City (Upper + Trout Section):
        p10=118  p30=137  p70=288  p90=503
  - 03269500 near Springfield (Lower):
        p10=203  p30=277  p70=499  p90=882

  cfs_low = p10, cfs_ideal_low = p30, cfs_ideal_high = p70, cfs_high = p90.

The Mad is glacial-outwash spring-fed with stable summer baseflow, so the
band spread is much tighter than rainfall-driven Shenandoah. Source field
flags as needs-angler-review. Idempotent via composite PK.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mr02a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high)
BANDS = [
    ('mad_river_oh_upper',         118, 137, 288, 503),
    ('mad_river_oh_trout_section', 118, 137, 288, 503),
    ('mad_river_oh_lower',         203, 277, 499, 882),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('{rid}', '', {lo}, {ilo}, {ihi}, {hi}, 0, NULL, "
        f"'v0 derived from USGS daily-value percentiles 2026-05-30; needs angler review')"
        for (rid, lo, ilo, ihi, hi) in BANDS
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
