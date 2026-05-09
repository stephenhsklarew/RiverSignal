"""add visibility and scientific_name to user_observations

Revision ID: c3d4e5f6a7b8
Revises: a1c2d3e4f5b6
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'a1c2d3e4f5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_observations',
                  sa.Column('visibility', sa.String(10), server_default='public', nullable=True))
    op.add_column('user_observations',
                  sa.Column('scientific_name', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('user_observations', 'scientific_name')
    op.drop_column('user_observations', 'visibility')
