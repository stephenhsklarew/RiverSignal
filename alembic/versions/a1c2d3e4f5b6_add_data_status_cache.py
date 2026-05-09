"""add data_status_cache table

Revision ID: a1c2d3e4f5b6
Revises: 86345269b77d
Create Date: 2026-05-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1c2d3e4f5b6'
down_revision: Union[str, Sequence[str], None] = '86345269b77d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'data_status_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            'refreshed_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('id = 1', name='data_status_cache_singleton'),
    )


def downgrade() -> None:
    op.drop_table('data_status_cache')
