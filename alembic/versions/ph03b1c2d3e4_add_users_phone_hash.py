"""add users.phone_hash for inbound STOP lookups

Revision ID: ph03b1c2d3e4
Revises: ip06b1c2d3e4
Create Date: 2026-06-02 00:00:00.000000

The inbound SMS webhook (STOP/UNSUBSCRIBE) must pause only the user who
sent the message. AES-GCM phone ciphertext is non-deterministic, so it
can't be queried by; we store a deterministic, key-bound hash
(hash_phone_for_lookup = sha256(key || phone)) at confirm-verification and
match on it in the webhook.

Backfill: existing verified users predate this column and have a NULL
phone_hash, so their first STOP won't match until they re-verify. There is
no in-DB backfill (the hash needs the plaintext, which only the app can
decrypt) — run the one-off app-side script after deploying this migration:

    python -m pipeline.sms.backfill_phone_hash --dry-run   # preview
    python -m pipeline.sms.backfill_phone_hash             # apply

It is idempotent. Telnyx's messaging-profile STOP enforcement is the safety
net in the interim.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ph03b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'ip06b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_hash bytea")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_phone_hash ON users (phone_hash) "
        "WHERE phone_hash IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_phone_hash")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone_hash")
