"""merge bb18m9n0o1p2 (warmwater species UNION) + rr18m9n0o1p2 (unique MV indexes)

Revision ID: ss19n0o1p2q3
Revises: bb18m9n0o1p2, rr18m9n0o1p2
Create Date: 2026-05-16 00:00:00.000000

Pure no-op merge — two unrelated migrations independently chained off
qq17l8m9n0o1, leaving alembic with two heads. This merge converges them
so `alembic upgrade head` succeeds.

`bb18m9n0o1p2` was already applied on prod before `rr18m9n0o1p2` landed,
so on the next deploy alembic will apply rr18m9n0o1p2 (adds UNIQUE
indexes to species_gallery + hatch_chart) and then this merge.
"""
from typing import Sequence, Union


revision: str = 'ss19n0o1p2q3'
down_revision: Union[str, Sequence[str], None] = ('bb18m9n0o1p2', 'rr18m9n0o1p2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
