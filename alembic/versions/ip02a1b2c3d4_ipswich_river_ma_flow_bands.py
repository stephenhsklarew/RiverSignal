"""seed ipswich_river_ma flow_quality_bands (v0 from USGS daily-value percentiles)

Revision ID: ip02a1b2c3d4
Revises: ip01a1b2c3d4
Create Date: 2026-06-02 00:00:00.000000

cfs bands derived per runbook §2.4 step 2 from each reach's primary-gauge
daily-value discharge percentiles (computed against bronze.time_series,
2026-06-02, ~700-730 daily values per gauge):
  - 01101500 South Middleton (Upper): p10=1  p30=7   p70=33  p90=103
  - 01102000 near Ipswich    (Lower): p10=2  p30=19  p70=83  p90=249

  cfs_low = p10, cfs_ideal_low = p30, cfs_ideal_high = p70, cfs_high = p90.

The very low p10 (1-2 cfs) is real — the Ipswich is drawn down / runs dry in
summer from municipal groundwater withdrawals (American Rivers #8 Most
Endangered, 2021; USGS FS 00-160). The flow Go-Score sub-score will correctly
flag low-flow stress on this watershed. Source flags needs-angler-review.
Idempotent via composite PK (reach_id, species, season_start_month).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ip02a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ip01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high)
BANDS = [
    ('ipswich_river_ma_upper', 1, 7, 33, 103),
    ('ipswich_river_ma_lower', 2, 19, 83, 249),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('{rid}', '', {lo}, {ilo}, {ihi}, {hi}, 0, NULL, "
        f"'v0 derived from USGS daily-value percentiles 2026-06-02; needs angler review')"
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
