"""seed chattahoochee flow_quality_bands (v0 from USGS daily-value percentiles)

Revision ID: ch02a1b2c3d4
Revises: ch01a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

cfs bands per runbook §2.4 step 2 from each reach's primary-gauge discharge
percentiles (bronze.time_series, 2026-06-04, ~400 daily values):
  - 02331600 Cornelia (Headwaters): p10=290  p30=329  p70=475  p90=707
  - 02334430 Buford Tailwater:       p10=843  p30=958  p70=1560 p90=2291
  - 02336000 Atlanta (Metro):        p10=930  p30=1237 p70=2053 p90=3092

Lake Lanier's gauge (02334401) is gage-height only (no discharge); its band uses
the Cornelia headwaters inflow as a documented proxy (a reservoir's "flow" isn't
a river cfs — flagged for review; flow degrades there regardless). needs-angler-review.
Idempotent via composite PK.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ch02a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high, note)
BANDS = [
    ('chattahoochee_headwaters', 290, 329, 475, 707,
     'v0 from USGS 02331600 Cornelia daily-value percentiles 2026-06-04; needs angler review'),
    ('chattahoochee_lanier', 290, 329, 475, 707,
     'v0 PROXY from USGS 02331600 headwaters inflow (Lanier 02334401 is gage-height only; reservoir, flow degrades); needs review'),
    ('chattahoochee_tailwater', 843, 958, 1560, 2291,
     'v0 from USGS 02334430 Buford tailwater daily-value percentiles 2026-06-04; needs angler review'),
    ('chattahoochee_metro', 930, 1237, 2053, 3092,
     'v0 from USGS 02336000 Atlanta daily-value percentiles 2026-06-04; needs angler review'),
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
