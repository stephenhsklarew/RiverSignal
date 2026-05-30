"""seed mad_river_oh curated_hatch_chart (v0 Midwest limestone-spring baseline)

Revision ID: mr03a1b2c3d4
Revises: mr02a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

First Midwest watershed — no existing OH hatch chart to clone. The Mad is a
limestone-influenced spring creek (structurally closer to Mossy Creek /
Shenandoah than to a Pacific-NW freestone), so the v0 seed is the
Mid-Atlantic / Appalachian limestone-spring + freestone trout-stream hatch
set, plus a warm-water smallmouth diet item for the lower reach.

10 entries cover the year. ALL FLAGGED `needs_entomologist_review=true` via
the `source` field — the Ohio mayfly mix (esp. peak windows) genuinely needs
an Ohio aquatic-entomologist's review (the inventory's Q5 caveat). Greppable
by source for that follow-on review.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mr03a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr02a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (common_name, scientific_name, insect_order, start_month, end_month, peak_months)
HATCHES = [
    ('Midges',                'Chironomidae',               'Diptera',       1, 12, '{1,2,3,12}'),
    ('Blue-Winged Olive',     'Baetis spp.',                'Ephemeroptera', 3, 11, '{4,5,10}'),
    ('Hendrickson',           'Ephemerella subvaria',       'Ephemeroptera', 4, 5,  '{4,5}'),
    ('Sulphur',               'Ephemerella invaria',        'Ephemeroptera', 5, 7,  '{5,6}'),
    ('Light Cahill',          'Stenacron interpunctatum',   'Ephemeroptera', 5, 8,  '{6,7}'),
    ('Slate Drake',           'Isonychia bicolor',          'Ephemeroptera', 6, 10, '{6,9}'),
    ('Trico',                 'Tricorythodes',              'Ephemeroptera', 7, 10, '{8,9}'),
    ('Caddisflies',           'Hydropsyche / Brachycentrus','Trichoptera',   4, 10, '{5,6,7}'),
    ('Cranefly',              'Tipulidae',                  'Diptera',       3, 10, '{4,9}'),
    ('Hellgrammite (smallmouth)','Corydalus cornutus',      'Megaloptera',   5, 9,  '{6,7,8}'),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('mad_river_oh', '{cn}', '{sn}', '{order}', {sm}, {em}, "
        f"'{peak}'::int[], '{{}}'::text[], "
        f"'v0 Midwest limestone-spring baseline 2026-05-30 — needs_entomologist_review=true')"
        for (cn, sn, order, sm, em, peak) in HATCHES
    )
    op.execute(f"""
        INSERT INTO curated_hatch_chart
            (watershed, common_name, scientific_name, insect_order,
             start_month, end_month, peak_months, fly_patterns, source)
        VALUES
            {rows}
        ON CONFLICT (watershed, common_name) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM curated_hatch_chart WHERE watershed = 'mad_river_oh'")
