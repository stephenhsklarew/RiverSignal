"""seed meramec curated_hatch_chart (Ozark smallmouth + Maramec Spring trout baseline)

Revision ID: me03a1b2c3d4
Revises: me02a1b2c3d4
Create Date: 2026-06-06 00:00:00.000000

Per runbook §2.4 step 3 + inventory §1.4. The Meramec fishes as an Ozark
smallmouth float stream — hellgrammites (Dobsonfly), crayfish, Isonychia slate
drakes, White Miller caddis, and summer terrestrials — while the spring-fed
Maramec Spring trout fishery adds tailwater/spring staples (midges year-round,
BWO, sulphurs). v0 seeds ONE combined chart flagged needs_entomologist_review=true;
the inventory notes a single chart may not fit both the warmwater float reaches
and the cold spring trout fishery, so a 2-chart split is a curator follow-on.
fly_patterns empty (join supplies them). Idempotent on (watershed, common_name).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'me03a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me02a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (common_name, scientific_name, insect_order, start_month, end_month, peak_months)
HATCHES = [
    ('Midges',                'Chironomidae',           'Diptera',       1, 12, '{1,2,12}'),    # Maramec Spring trout staple, year-round
    ('Blue-Winged Olive',     'Baetis spp.',            'Ephemeroptera', 2, 11, '{3,4,10,11}'),
    ('Little Black Caddis',   'Brachycentrus spp.',     'Trichoptera',   3, 5,  '{4}'),         # Mother's Day caddis
    ('Sulphur',               'Ephemerella invaria',    'Ephemeroptera', 4, 6,  '{5}'),         # Maramec Spring
    ('Slate Drake',           'Isonychia bicolor',      'Ephemeroptera', 5, 10, '{6,9}'),       # Ozark smallmouth classic
    ('Hellgrammite (Dobsonfly)', 'Corydalus cornutus',  'Megaloptera',   5, 9,  '{6,7}'),       # premier smallmouth forage
    ('Crayfish (forage)',     'Faxonius spp.',          'Crustacean',    1, 12, '{5,6,7,8,9}'), # the dominant smallmouth food
    ('White Miller Caddis',   'Nectopsyche spp.',       'Trichoptera',   6, 9,  '{7,8}'),       # Ozark evening caddis
    ('Spotted Sedge Caddis',  'Hydropsyche spp.',       'Trichoptera',   4, 9,  '{5,6}'),
    ('Damselfly',             'Coenagrionidae',         'Odonata',       5, 9,  '{6,7}'),
    ('Light Cahill',          'Stenacron interpunctatum','Ephemeroptera',5, 8,  '{6,7}'),
    ('Terrestrials (ants/beetles/hoppers)', 'Formicidae / Acrididae', 'Terrestrial', 6, 10, '{7,8,9}'),  # huge for summer smallmouth
]


def upgrade() -> None:
    rows = ",\n            ".join(
        "('meramec', '{cn}', '{sn}', '{order}', {sm}, {em}, "
        "'{peak}'::int[], '{{}}'::text[], "
        "'v0 Ozark smallmouth + Maramec Spring trout baseline 2026-06-06 — needs_entomologist_review=true')".format(
            cn=cn.replace("'", "''"), sn=sn.replace("'", "''"), order=order, sm=sm, em=em, peak=peak)
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
    op.execute("DELETE FROM curated_hatch_chart WHERE watershed = 'meramec'")
