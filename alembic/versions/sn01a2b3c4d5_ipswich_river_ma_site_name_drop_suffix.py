"""drop the (MA) suffix from the ipswich_river_ma sites.name

Revision ID: sn01a2b3c4d5
Revises: bd01a2b3c4d5
Create Date: 2026-06-03 00:00:00.000000

The ip01 seed inserted sites.name = 'Ipswich River (MA)'. The UI derives the
watershed-picker label from sites.name (shortName strips ' River'), so the
picker rendered 'Ipswich (MA)' on /path/now. Align the DB row with the
suffix-free display name (config + frontend labels were already updated in
PR #22). Mad River's row was already 'Mad River' (no suffix). Idempotent.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'sn01a2b3c4d5'
down_revision: Union[str, Sequence[str], None] = 'bd01a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE sites SET name = 'Ipswich River'
        WHERE watershed = 'ipswich_river_ma' AND name = 'Ipswich River (MA)'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE sites SET name = 'Ipswich River (MA)'
        WHERE watershed = 'ipswich_river_ma' AND name = 'Ipswich River'
    """)
