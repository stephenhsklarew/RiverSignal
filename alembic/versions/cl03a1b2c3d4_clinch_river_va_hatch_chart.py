"""seed clinch_river_va curated_hatch_chart (clone of Shenandoah VA-Appalachian baseline)

Revision ID: cl03a1b2c3d4
Revises: cl02a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

Per runbook §2.4 step 3, clone the nearest-analogous watershed's hatch chart.
Shenandoah is the closest analogue — same VA Valley-&-Ridge / Appalachian
ecoregion, same freestone-trout-tributary + warm-water-smallmouth fishery mix
that the Clinch has (cold Clinch Mtn WMA trout tribs + warm main-stem
smallmouth, with hellgrammite/crayfish forage). 10 entries cover the year, ALL
FLAGGED needs_entomologist_review=true. fly_patterns left empty — the East-Coast
fly-pattern join supplies patterns by insect name. Idempotent on
(watershed, common_name).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'cl03a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'cl02a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (common_name, scientific_name, insect_order, start_month, end_month, peak_months)
HATCHES = [
    ('Midges',                   'Chironomidae',              'Diptera',       1, 12, '{2,3,11,12}'),
    ('Little Black Stonefly',    'Capniidae',                 'Plecoptera',    1, 3,  '{2}'),
    ('Blue-Winged Olive',        'Baetis spp.',               'Ephemeroptera', 3, 11, '{4,5,9,10}'),
    ('Quill Gordon',             'Epeorus pleuralis',         'Ephemeroptera', 4, 5,  '{4}'),
    ('Hendrickson',              'Ephemerella subvaria',      'Ephemeroptera', 4, 5,  '{4,5}'),
    ('Sulphur',                  'Ephemerella invaria',       'Ephemeroptera', 5, 7,  '{5,6}'),
    ('Light Cahill',             'Stenacron interpunctatum',  'Ephemeroptera', 5, 8,  '{6,7}'),
    ('Trico',                    'Tricorythodes',             'Ephemeroptera', 7, 10, '{8,9}'),
    ('Caddisflies',              'Hydropsyche / Brachycentrus','Trichoptera',  4, 10, '{5,6,7}'),
    ('Hellgrammite (smallmouth)','Corydalus cornutus',        'Megaloptera',   5, 9,  '{6,7,8}'),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('clinch_river_va', '{cn}', '{sn}', '{order}', {sm}, {em}, "
        f"'{peak}'::int[], '{{}}'::text[], "
        f"'v0 cloned from Shenandoah VA-Appalachian baseline 2026-06-03 — needs_entomologist_review=true')"
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
    op.execute("DELETE FROM curated_hatch_chart WHERE watershed = 'clinch_river_va'")
