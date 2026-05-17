"""flow_quality_bands + USGS gauges for South River, Passage Creek, Mossy Creek

Revision ID: zz26u7v8w9x0
Revises: yy25t6u7v8w9
Create Date: 2026-05-17 00:00:00.000000

Wires real USGS discharge into the TQS flow sub-score for three named
Shenandoah trout tributaries:

  - South River      USGS 02019500 South River at Waynesboro VA
                     ~200 cfs annual mean discharge
  - Passage Creek    USGS 01633000 Passage Creek near Buckton VA
                     ~75 cfs annual mean discharge
  - Mossy Creek      USGS 01620842 Mossy Creek at RT 613 near Mt Solon VA
                     ~25 cfs estimated stable spring flow

Two changes:

  1. INSERT silver.flow_quality_bands rows so the TQS flow scoring path
     has CFS targets per reach. Without bands, the reach falls back to
     fl=50 (the universal default) which was producing identical "68 /
     flow" scores across very different streams.
  2. UPDATE silver.river_reaches.primary_usgs_site_id for Mossy Creek
     (South River + Passage Creek already had IDs from xx24).

Heuristic from cc03d4e5f6a7_shenandoah_flow_bands.py:
  - cfs_low       = ~25% of mean (drought low)
  - cfs_ideal_low = ~50% of mean (start of fishable band)
  - cfs_ideal_high= ~200% of mean (top of fishable band)
  - cfs_high      = ~500% of mean (blowout)

Spring creeks (Mossy) get a tighter band because flow is stable
year-round — fishability isn't bracketed by drought/blowout extremes
the way freestone streams are. Mossy Creek band derived from guide
reports + USGS partial-record data; flagged needs-angler-review.

A companion code change in pipeline/predictions/trip_quality.py now
looks up live discharge from gold.time_series for each reach's
primary_usgs_site_id and uses that as the proxy_cfs (falling back to
mid-of-ideal when no recent reading is available).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'zz26u7v8w9x0'
down_revision: Union[str, Sequence[str], None] = 'yy25t6u7v8w9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high, source_note)
BANDS = [
    ('shenandoah_south_river',  50, 100, 400, 1000,
     'v0 — USGS 02019500 ~200 cfs mean × 25/50/200/500% heuristic; needs angler review'),
    ('shenandoah_passage_creek', 18, 37, 150, 375,
     'v0 — USGS 01633000 ~75 cfs mean × 25/50/200/500% heuristic; needs angler review'),
    ('shenandoah_mossy_creek',   8, 15, 60, 150,
     'v0 — spring creek, stable ~25 cfs flow; ideal band tighter than freestone formula; needs angler review'),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('{rid}', '', {lo}, {ilo}, {ihi}, {hi}, 0, NULL, '{src}')"
        for (rid, lo, ilo, ihi, hi, src) in BANDS
    )
    op.execute(f"""
        INSERT INTO silver.flow_quality_bands
            (reach_id, species, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high,
             season_start_month, season_end_month, source)
        VALUES
            {rows}
        ON CONFLICT (reach_id, species, season_start_month) DO NOTHING
    """)
    # Wire Mossy Creek's USGS gauge. South River and Passage Creek already
    # have IDs from xx24s5t6u7v8.
    op.execute("""
        UPDATE silver.river_reaches
           SET primary_usgs_site_id = '01620842'
         WHERE id = 'shenandoah_mossy_creek'
           AND primary_usgs_site_id IS NULL
    """)


def downgrade() -> None:
    ids = ",".join(f"'{r[0]}'" for r in BANDS)
    op.execute(f"DELETE FROM silver.flow_quality_bands WHERE reach_id IN ({ids})")
    op.execute("""
        UPDATE silver.river_reaches
           SET primary_usgs_site_id = NULL
         WHERE id = 'shenandoah_mossy_creek'
           AND primary_usgs_site_id = '01620842'
    """)
