"""seed silver.flow_quality_bands per reach (v0 defaults, needs angler review)

Revision ID: t1c2d3e4f5a6
Revises: s0b1c2d3e4f5
Create Date: 2026-05-13 00:00:10.000000

Phase A0 of TQS. Hand-picked defaults per the 22 seeded reaches. Values
informed by plan §3.3 commentary (e.g., upper Deschutes 200-400, lower
Deschutes 4000-6000) and rule-of-thumb angler heuristics. Year-round
(season NULL = 0 in our composite PK).

EVERY ROW NEEDS ANGLER REVIEW. source field flags this explicitly.
Idempotent via ON CONFLICT DO NOTHING.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 't1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 's0b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (reach_id, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high)
BANDS = [
    # McKenzie
    ('mckenzie_upper',         400,  600, 1500, 3500),
    ('mckenzie_middle',        800, 1200, 2800, 6000),
    ('mckenzie_lower',        1200, 2000, 5000, 9000),
    # Deschutes — upper is small, lower is huge
    ('deschutes_upper',         80,  150,  450,  900),
    ('deschutes_middle',       150,  300,  900, 1800),
    ('deschutes_lower',       2500, 4000, 6000, 9000),
    ('deschutes_lower_canyon',3000, 4500, 7500,12000),
    # Metolius — spring-fed, very stable
    ('metolius_headwaters',    900, 1100, 1500, 2200),
    ('metolius_middle',       1000, 1200, 1700, 2500),
    # John Day — flashy
    ('johnday_mainstem',       200,  400, 2000, 6000),
    ('johnday_north_fork',     100,  250, 1500, 4500),
    ('johnday_south_fork',      50,  150,  900, 3000),
    # Klamath
    ('klamath_upper',          150,  300, 1200, 3000),
    ('klamath_wood',           100,  200,  600, 1500),
    ('klamath_williamson',     200,  400, 1500, 4000),
    # Skagit
    ('skagit_upper',           600, 1200, 3500, 9000),
    ('skagit_middle',         3000, 4500, 9000,18000),
    ('skagit_lower',          5000, 7000,15000,30000),
    # Green River (UT) — tailwater, very stable
    ('green_a_section',        700,  900, 2000, 4500),
    ('green_b_section',        700,  900, 2000, 4500),
    ('green_c_section',        700,  900, 2000, 4500),
    ('green_lodore',           600,  900, 2500, 6000),
]


def upgrade() -> None:
    rows = []
    for (rid, lo, ilo, ihi, hi) in BANDS:
        rows.append(f"('{rid}', '', {lo}, {ilo}, {ihi}, {hi}, 0, NULL, 'v0 plan §3.3 defaults — needs angler review')")
    values_sql = ",\n            ".join(rows)
    op.execute(
        f"""
        INSERT INTO silver.flow_quality_bands
            (reach_id, species, cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high,
             season_start_month, season_end_month, source)
        VALUES
            {values_sql}
        ON CONFLICT (reach_id, species, season_start_month) DO NOTHING
        """
    )


def downgrade() -> None:
    ids = ",".join(f"'{r[0]}'" for r in BANDS)
    op.execute(f"DELETE FROM silver.flow_quality_bands WHERE reach_id IN ({ids})")
