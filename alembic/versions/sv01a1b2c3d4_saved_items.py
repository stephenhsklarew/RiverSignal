"""saved_items — per-user server-side persistence of Saved bookmarks

Revision ID: sv01a1b2c3d4
Revises: sc01a1b2c3d4
Create Date: 2026-06-05 00:00:00.000000

Backs cross-device sync of RiverPath "Saved" items. Saved items (species, flies,
recreation, geology, and observation *bookmarks*) previously lived only in the
browser's localStorage. This table persists them per user account so they follow
the user across devices.

A saved item is a bookmark, not ownership: a kept *shared observation* is stored
here as a snapshot (payload carries the original photographer, source, observed
date, and visibility) — it is never written to user_observations for the
recipient, so the original attribution and privacy are preserved.

payload is the JSONB snapshot the Saved UI needs to render the item:
label, sublabel, thumbnail, latitude, longitude, and for observations
observer, source, observedAt, visibility, originObservationId.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'sv01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'sc01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS saved_items (
            id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id   uuid NOT NULL,
            item_type varchar(32)  NOT NULL,
            item_id   varchar(256) NOT NULL,
            watershed varchar(64)  NULL,
            payload   jsonb NOT NULL DEFAULT '{}',
            saved_at  timestamptz NOT NULL DEFAULT now(),
            UNIQUE (user_id, item_type, item_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_saved_items_user ON saved_items (user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS saved_items")
