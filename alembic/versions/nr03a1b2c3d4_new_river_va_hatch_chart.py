"""seed new_river_va curated_hatch_chart (Appalachian baseline; secondary for this warm-water river)

Revision ID: nr03a1b2c3d4
Revises: nr02a1b2c3d4
Create Date: 2026-06-03 00:00:00.000000

Per runbook §2.4 step 3, clone the nearest-analogous Appalachian-VA hatch chart
(same one used for Shenandoah / Clinch). NOTE: the inventory flags hatch as LOW
value for the New — it's a large warm-water river driven by crayfish /
hellgrammite / baitfish forage, not a mayfly-hatch fishery — so this baseline is
secondary and especially needs_review (a forage / seasonal-presentation model
would fit better; tracked as a follow-on). Hellgrammite is the most relevant row.
fly_patterns empty (East-Coast join supplies them). Idempotent on (watershed, common_name).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'nr03a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nr02a1b2c3d4'
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
        f"('new_river_va', '{cn}', '{sn}', '{order}', {sm}, {em}, "
        f"'{peak}'::int[], '{{}}'::text[], "
        f"'v0 Appalachian baseline 2026-06-03 (secondary — warm-water forage fishery) — needs_entomologist_review=true')"
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
    op.execute("DELETE FROM curated_hatch_chart WHERE watershed = 'new_river_va'")
