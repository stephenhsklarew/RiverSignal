"""create user_reach_watches and user_alert_deliveries tables

Revision ID: q8f9a0b1c2d3
Revises: p7e8f9a0b1c2
Create Date: 2026-05-13 00:00:07.000000

Phase A of TQS push surface. Per-user watchlist of reaches with
per-reach alert thresholds; audit log of every alert delivery for
dedupe + analytics. See plan §3.0b.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'q8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'p7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_reach_watches (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reach_id        varchar(80) NOT NULL REFERENCES silver.river_reaches(id),
            alert_threshold int NOT NULL DEFAULT 70 CHECK (alert_threshold BETWEEN 0 AND 100),
            alert_trend     boolean NOT NULL DEFAULT true,
            muted_until     timestamptz,
            created_at      timestamptz DEFAULT now(),
            UNIQUE (user_id, reach_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_uw_user ON user_reach_watches (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_uw_reach ON user_reach_watches (reach_id)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_alert_deliveries (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reach_id        varchar(80) NOT NULL,
            alert_type      varchar(40) NOT NULL,
            target_date     date NOT NULL,
            tqs_at_alert    int NOT NULL,
            channel         varchar(20) NOT NULL,
            delivered_at    timestamptz DEFAULT now(),
            seen_at         timestamptz
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_uad_user_unseen ON user_alert_deliveries (user_id) "
        "WHERE seen_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_alert_deliveries")
    op.execute("DROP TABLE IF EXISTS user_reach_watches")
