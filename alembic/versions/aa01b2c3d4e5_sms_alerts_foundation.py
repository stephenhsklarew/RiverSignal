"""sms alerts foundation: phone columns + subscriptions + history + send_log

Revision ID: aa01b2c3d4e5
Revises: z7d8e9f0a1b2
Create Date: 2026-05-15 00:00:00.000000

Phase 0 of plan-2026-05-15-sms-alerts.md. Adds the schema needed for
phone verification, per-watershed SMS subscriptions, send dedup, and
budget tracking.

Note: phone_number_e164_encrypted holds AES-GCM ciphertext, keyed by a
secret in Secret Manager (sms-encryption-key). The plain-text number
is reconstructed only at send time inside the dispatcher.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'aa01b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'z7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend users table — phone number lives encrypted at rest.
    op.execute("""
        ALTER TABLE users
          ADD COLUMN IF NOT EXISTS phone_number_e164_encrypted bytea,
          ADD COLUMN IF NOT EXISTS phone_verified_at           timestamptz,
          ADD COLUMN IF NOT EXISTS sms_paused                  boolean NOT NULL DEFAULT false
    """)

    # Per-watershed subscriptions. Threshold is 70 (Good+) or 80 (Excellent).
    op.create_table(
        'sms_alert_subscriptions',
        sa.Column('id',           postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id',      postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('watershed',    sa.String(32), nullable=False),
        sa.Column('threshold',    sa.Integer, nullable=False, server_default=sa.text('80')),
        sa.Column('muted_until',  sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at',   sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'watershed', name='uq_sms_subs_user_watershed'),
        sa.CheckConstraint('threshold IN (70, 80)', name='ck_sms_subs_threshold'),
    )
    # Partial index on un-muted subscriptions only. Postgres requires index
    # predicates to be IMMUTABLE, and now() is STABLE — so the original
    # `muted_until < now()` clause was rejected. The runtime query layer
    # adds the `OR muted_until < now()` filter at SELECT time; the index
    # accelerates the common-case `muted_until IS NULL` lookup, which is
    # the majority of subscriptions.
    op.create_index('ix_sms_subs_watershed_active', 'sms_alert_subscriptions', ['watershed'],
                    postgresql_where=sa.text('muted_until IS NULL'))
    op.create_index('ix_sms_subs_user', 'sms_alert_subscriptions', ['user_id'])

    # Send-history dedup: prevent re-alerting the same (user, watershed, target_date)
    # within 48h. Composite uniqueness is the primary guard against duplicates.
    op.create_table(
        'sms_alert_history',
        sa.Column('id',                 postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id',            postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('watershed',          sa.String(32), nullable=False),
        sa.Column('target_date',        sa.Date,       nullable=False),
        sa.Column('tqs_at_send',        sa.Integer,    nullable=False),
        sa.Column('forecast_source',    sa.String(32), nullable=True),
        sa.Column('sent_at',            sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
        sa.Column('telnyx_message_id',  sa.Text, nullable=True),
        sa.Column('delivery_status',    sa.String(16), nullable=False,
                  server_default=sa.text("'queued'")),
        sa.UniqueConstraint('user_id', 'watershed', 'target_date',
                            name='uq_sms_history_user_ws_date'),
    )
    op.create_index('ix_sms_history_user_recent', 'sms_alert_history',
                    ['user_id', sa.text('sent_at DESC')])
    op.create_index('ix_sms_history_msg_id', 'sms_alert_history', ['telnyx_message_id'],
                    postgresql_where=sa.text('telnyx_message_id IS NOT NULL'))

    # Budget tracking. Tiny row per send so daily/monthly caps can aggregate cheaply.
    op.create_table(
        'sms_send_log',
        sa.Column('id',         postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('sent_at',    sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
        sa.Column('cost_cents', sa.Numeric(8, 4), nullable=True),
        sa.Column('success',    sa.Boolean, nullable=False),
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sms_send_log_day ON sms_send_log ((sent_at::date))"
    )


def downgrade() -> None:
    op.drop_table('sms_send_log')
    op.drop_index('ix_sms_history_msg_id', table_name='sms_alert_history')
    op.drop_index('ix_sms_history_user_recent', table_name='sms_alert_history')
    op.drop_table('sms_alert_history')
    op.drop_index('ix_sms_subs_user', table_name='sms_alert_subscriptions')
    op.drop_index('ix_sms_subs_watershed_active', table_name='sms_alert_subscriptions')
    op.drop_table('sms_alert_subscriptions')
    op.execute("""
        ALTER TABLE users
          DROP COLUMN IF EXISTS sms_paused,
          DROP COLUMN IF EXISTS phone_verified_at,
          DROP COLUMN IF EXISTS phone_number_e164_encrypted
    """)
