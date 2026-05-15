"""seed shenandoah flow_quality_bands (v0 from USGS annual-mean discharge)

Revision ID: cc03d4e5f6a7
Revises: bb02c3d4e5f6
Create Date: 2026-05-15 11:05:00.000000

cfs bands derived from each reach's primary-gauge annual-mean discharge
(USGS NWIS stat endpoint, 2026-05-15):
  - NF Strasburg  (01634000): mean 612 cfs
  - SF Front Royal(01631000): mean 793 cfs
  - Main Millville(01636500): mean 2735 cfs

Heuristic per the runbook §2.4 step 2:
  - cfs_low       = ~25% of mean (drought low)
  - cfs_ideal_low = ~50% of mean (start of fishable band)
  - cfs_ideal_high= ~200% of mean (top of fishable band)
  - cfs_high      = ~500% of mean (blowout)

Source field flags as needs-angler-review. Idempotent via composite PK.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'cc03d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'bb02c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, low, ideal_low, ideal_high, high)
BANDS = [
    ('shenandoah_north_fork',  150,  300, 1200, 3000),
    ('shenandoah_south_fork',  200,  400, 1600, 4000),
    ('shenandoah_main_stem',   700, 1400, 5500, 14000),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('{rid}', '', {lo}, {ilo}, {ihi}, {hi}, 0, NULL, "
        f"'v0 derived from USGS annual-mean discharge; needs angler review')"
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
