"""seed meramec flow_quality_bands (v0 from USGS daily-value percentiles)

Revision ID: me02a1b2c3d4
Revises: me01a1b2c3d4
Create Date: 2026-06-06 00:00:00.000000

cfs bands per runbook §2.4 step 2 from each reach's primary-gauge discharge
percentiles (NWIS daily values, parameterCd=00060, 2019-06-01..2024-06-01,
n=1828/gauge):
  - 07014000 Huzzah Cr (Upper):       p10=57   p30=88   p70=247  p90=508
  - 07014500 Sullivan (Middle):       p10=401  p30=522  p70=1350 p90=2690
  - 07019000 Eureka (Lower):          p10=730  p30=1100 p70=3100 p90=7368
  - 07018500 Big R Byrnesville:       p10=167  p30=258  p70=793  p90=1863

low=p10, ideal_low=p30, ideal_high=p70, high=p90. needs-angler-review.
Idempotent via composite PK.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'me02a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high, note)
BANDS = [
    ('meramec_upper', 57, 88, 247, 508,
     'v0 from USGS 07014000 Huzzah Cr daily-value percentiles 2019-2024; needs angler review'),
    ('meramec_middle', 401, 522, 1350, 2690,
     'v0 from USGS 07014500 near Sullivan daily-value percentiles 2019-2024; needs angler review'),
    ('meramec_lower', 730, 1100, 3100, 7368,
     'v0 from USGS 07019000 near Eureka daily-value percentiles 2019-2024; needs angler review'),
    ('big_river', 167, 258, 793, 1863,
     'v0 from USGS 07018500 Big R at Byrnesville daily-value percentiles 2019-2024; needs angler review'),
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
