"""seed new_river_va flow_quality_bands (v0 from USGS daily-value percentiles)

Revision ID: nr02a1b2c3d4
Revises: nr01a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

cfs bands per runbook §2.4 step 2 from each reach's primary-gauge discharge
percentiles (bronze.time_series, 2026-06-03, ~400 daily values per gauge).
Large river — bands are in the hundreds/thousands of cfs:
  - 03164000 Galax     (Upper):   p10=634  p30=856  p70=1453 p90=2040
  - 03168000 Allisonia (Claytor): p10=1120 p30=1417 p70=2409 p90=3551
  - 03171000 Radford   (Lower):   p10=1270 p30=1687 p70=3009 p90=4511

cfs_low=p10, cfs_ideal_low=p30, cfs_ideal_high=p70, cfs_high=p90. Claytor is a
reservoir (the inflow-gauge bands are a rough proxy for a lake — flagged for
review). needs-angler-review. Idempotent via composite PK.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'nr02a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nr01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high, note)
BANDS = [
    ('new_river_va_upper',   634,  856, 1453, 2040,
     'v0 from USGS 03164000 Galax daily-value percentiles 2026-06-03; needs angler review'),
    ('new_river_va_claytor', 1120, 1417, 2409, 3551,
     'v0 from USGS 03168000 Allisonia (Claytor inflow) percentiles 2026-06-03; reservoir proxy, needs review'),
    ('new_river_va_lower',   1270, 1687, 3009, 4511,
     'v0 from USGS 03171000 Radford daily-value percentiles 2026-06-03; needs angler review'),
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
