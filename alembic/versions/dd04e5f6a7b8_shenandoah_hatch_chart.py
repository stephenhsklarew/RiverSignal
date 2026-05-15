"""seed shenandoah curated_hatch_chart (v0 East-Coast / Mid-Atlantic baseline)

Revision ID: dd04e5f6a7b8
Revises: cc03d4e5f6a7
Create Date: 2026-05-15 11:10:00.000000

First Atlantic-slope watershed on the platform — no existing hatch chart
to clone. Seeded from established Mid-Atlantic / Appalachian limestone-
spring + freestone trout-stream hatches (Mossy Creek / Penns Creek /
Spruce Creek style) plus warm-water smallmouth diet items
(hellgrammite, crayfish patterns).

10 entries cover the year. ALL FLAGGED `needs_entomologist_review=true`
via the `source` field. A Shenandoah-specific aquatic-entomology review
should adjust peak months for the watershed's microclimate.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'dd04e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'cc03d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (common_name, scientific_name, insect_order, start_month, end_month, peak_months)
HATCHES = [
    ('Midges',              'Chironomidae',           'Diptera',       1, 12, '{2,3,11,12}'),
    ('Little Black Stonefly','Capniidae',             'Plecoptera',    1, 3,  '{2}'),
    ('Blue-Winged Olive',   'Baetis spp.',            'Ephemeroptera', 3, 11, '{4,5,9,10}'),
    ('Quill Gordon',        'Epeorus pleuralis',      'Ephemeroptera', 4, 5,  '{4}'),
    ('Hendrickson',         'Ephemerella subvaria',   'Ephemeroptera', 4, 5,  '{4,5}'),
    ('Sulphur',             'Ephemerella invaria',    'Ephemeroptera', 5, 7,  '{5,6}'),
    ('Light Cahill',        'Stenacron interpunctatum','Ephemeroptera',5, 8,  '{6,7}'),
    ('Trico',               'Tricorythodes',          'Ephemeroptera', 7, 10, '{8,9}'),
    ('Caddisflies',         'Hydropsyche / Brachycentrus','Trichoptera',4, 10,'{5,6,7}'),
    ('Hellgrammite (smallmouth)','Corydalus cornutus','Megaloptera',   5, 9,  '{6,7,8}'),
]


def upgrade() -> None:
    # Empty arrays for fly_patterns + curated source string so future
    # entomologist review can grep this row out by source.
    rows = ",\n            ".join(
        f"('shenandoah', '{cn}', '{sn}', '{order}', {sm}, {em}, "
        f"'{peak}'::int[], '{{}}'::text[], "
        f"'v0 Mid-Atlantic baseline 2026-05-15 — needs_entomologist_review=true')"
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
    op.execute("DELETE FROM curated_hatch_chart WHERE watershed = 'shenandoah'")
