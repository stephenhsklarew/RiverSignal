"""shared_collections — 24h-expiring shareable Saved collections

Revision ID: sc01a1b2c3d4
Revises: ch10a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

Backs the Saved "share with a friend" feature: a user selects sections/items in
their Saved area, we snapshot them into a row with a random token and a 24h TTL,
and return a shareable link. The recipient resolves the token (public GET) and
the items land in their own Saved (client-side, 24h) until they sign in to keep
them. owner_user_id is nullable (anonymous users can share too). payload is the
JSONB snapshot of the shared items + which sections.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'sc01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch10a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS shared_collections (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            share_token   varchar(64) NOT NULL UNIQUE,
            owner_user_id uuid NULL,
            watershed     varchar(64) NULL,
            payload       jsonb NOT NULL,
            item_count    integer NOT NULL DEFAULT 0,
            created_at    timestamptz NOT NULL DEFAULT now(),
            expires_at    timestamptz NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_shared_collections_token ON shared_collections (share_token)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_shared_collections_expires ON shared_collections (expires_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS shared_collections")
