"""seed chattahoochee curated_hatch_chart (Buford tailwater + Blue Ridge headwater baseline)

Revision ID: ch03a1b2c3d4
Revises: ch02a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

Per runbook §2.4 step 3 + inventory §1.4. The Buford Dam tailwater fishes
tailwater-style — midges year-round, Blue-Winged Olive, sulphurs, caddis, and
summer terrestrials — while the Blue Ridge headwater tribs add freestone mayflies
(Quill Gordon, March Brown). v0 seeds ONE combined chart, flagged
needs_entomologist_review=true; the inventory notes a single chart may not fit
both the tailwater and the headwaters, so a 2-chart split is a curator follow-on.
fly_patterns empty (East-Coast join supplies them). Idempotent on (watershed, common_name).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ch03a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch02a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (common_name, scientific_name, insect_order, start_month, end_month, peak_months)
HATCHES = [
    ('Midges',                'Chironomidae',            'Diptera',       1, 12, '{1,2,12}'),   # tailwater staple, year-round
    ('Blue-Winged Olive',     'Baetis spp.',             'Ephemeroptera', 2, 11, '{3,4,10,11}'),
    ('Quill Gordon',          'Epeorus pleuralis',       'Ephemeroptera', 3, 4,  '{4}'),         # headwater freestone
    ('Hendrickson',           'Ephemerella subvaria',    'Ephemeroptera', 3, 5,  '{4}'),
    ('Sulphur',               'Ephemerella invaria',     'Ephemeroptera', 4, 6,  '{5}'),
    ('March Brown',           'Maccaffertium vicarium',  'Ephemeroptera', 4, 6,  '{5}'),         # headwater
    ('Tan Caddis',            'Hydropsyche spp.',        'Trichoptera',   4, 9,  '{5,6}'),
    ('Light Cahill',          'Stenacron interpunctatum','Ephemeroptera', 5, 8,  '{6,7}'),
    ('Terrestrials (ants/beetles/hoppers)', 'Formicidae / Acrididae', 'Terrestrial', 6, 9, '{7,8}'),  # summer
    ('Black Caddis',          'Brachycentrus spp.',      'Trichoptera',   3, 5,  '{4}'),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        "('chattahoochee', '{cn}', '{sn}', '{order}', {sm}, {em}, "
        "'{peak}'::int[], '{{}}'::text[], "
        "'v0 Buford-tailwater + Blue Ridge baseline 2026-06-04 — needs_entomologist_review=true')".format(
            cn=cn.replace("'", "''"), sn=sn, order=order, sm=sm, em=em, peak=peak)
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
    op.execute("DELETE FROM curated_hatch_chart WHERE watershed = 'chattahoochee'")
