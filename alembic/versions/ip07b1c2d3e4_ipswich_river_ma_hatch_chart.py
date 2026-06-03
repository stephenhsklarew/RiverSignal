"""seed curated_hatch_chart for ipswich_river_ma (East-Coast warmwater/trout baseline)

Revision ID: ip07b1c2d3e4
Revises: ip06b1c2d3e4
Create Date: 2026-06-02 00:00:00.000000

RiverSignal-89e798f7. The hatch endpoint returned 0 insects for Ipswich.
Seed a New-England warmwater-river + put-and-take-trout-tributary hatch
baseline (mayfly / caddis / stonefly / Odonata), flagged
needs_entomologist_review=true. fly_patterns left empty — the East-Coast
fly-pattern join (tt20 east_coast_insect_fly_patterns) supplies patterns by
insect name. Idempotent on (watershed, common_name).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ip07b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'ip06b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (common_name, scientific_name, insect_order, start_month, end_month, peak_months)
HATCHES = [
    ('Blue-Winged Olive', 'Baetis spp.',             'Ephemeroptera', 4, 10, '{4,5,9,10}'),
    ('Hendrickson',       'Ephemerella subvaria',    'Ephemeroptera', 4, 5,  '{4}'),
    ('Sulphur',           'Ephemerella invaria',     'Ephemeroptera', 5, 6,  '{5}'),
    ('March Brown',       'Maccaffertium vicarium',  'Ephemeroptera', 5, 6,  '{5}'),
    ('Light Cahill',      'Stenacron interpunctatum','Ephemeroptera', 6, 7,  '{6}'),
    ('Slate Drake',       'Isonychia bicolor',       'Ephemeroptera', 6, 9,  '{6,9}'),
    ('Tan Caddis',        'Hydropsyche spp.',        'Trichoptera',   5, 8,  '{6}'),
    ('White Miller Caddis','Nectopsyche spp.',       'Trichoptera',   7, 8,  '{7}'),
    ('Golden Stonefly',   'Acroneuria spp.',         'Plecoptera',    5, 7,  '{6}'),
    ('Damselfly',         'Enallagma spp.',          'Odonata',       6, 8,  '{7}'),
]


def upgrade() -> None:
    rows = ",\n            ".join(
        f"('ipswich_river_ma', '{cn}', '{sn}', '{order}', {sm}, {em}, "
        f"'{peak}'::int[], '{{}}'::text[], "
        f"'v0 New-England warmwater/trout baseline 2026-06-02 — needs_entomologist_review=true')"
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
    op.execute("DELETE FROM curated_hatch_chart WHERE watershed = 'ipswich_river_ma'")
