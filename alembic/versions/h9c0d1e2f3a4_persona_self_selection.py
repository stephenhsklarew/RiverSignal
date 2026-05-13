"""create user_personas_catalog and add persona columns to users

Revision ID: h9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-05-13 00:00:00.000000

Phase A1 of persona self-selection (docs/helix/02-design/plan-2026-05-13-persona-self-selection.md):

  - New `user_personas_catalog` reference table: stable persona keys
    plus display label, description, icon, sort order, and active flag.
    Renaming a label or adding a persona doesn't require touching user
    rows; user rows reference the stable `key`.

  - `users` gains three columns to record self-selections:
      * personas         varchar[]   the user's selected keys (default '{}')
      * personas_set_at  timestamptz  null until user submits; set even
                                       when user submits empty array (skip)
      * personas_version smallint    bumped when the catalog gains a
                                       material new option so we know
                                       whose digests need a re-prompt

  - GIN index on users.personas for fast `'guide_professional' = ANY(personas)`
    feature gating checks.

Seed data lives in the next migration (A2) so the schema migration can
ship and roll back cleanly without coupling to specific persona content.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h9c0d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'g8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_personas_catalog',
        sa.Column('key', sa.String(40), primary_key=True),
        sa.Column('display_label', sa.String(80), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.add_column(
        'users',
        sa.Column(
            'personas',
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
    )
    op.add_column(
        'users',
        sa.Column('personas_set_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'users',
        sa.Column(
            'personas_version',
            sa.SmallInteger(),
            nullable=False,
            server_default='1',
        ),
    )

    op.create_index(
        'idx_users_personas',
        'users',
        ['personas'],
        postgresql_using='gin',
    )


def downgrade() -> None:
    op.drop_index('idx_users_personas', table_name='users')
    op.drop_column('users', 'personas_version')
    op.drop_column('users', 'personas_set_at')
    op.drop_column('users', 'personas')
    op.drop_table('user_personas_catalog')
