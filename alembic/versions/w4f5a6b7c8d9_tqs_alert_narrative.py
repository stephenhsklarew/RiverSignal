"""add narrative_text column to user_alert_deliveries

Revision ID: w4f5a6b7c8d9
Revises: v3e4f5a6b7c8
Create Date: 2026-05-13 00:00:13.000000

Phase B.5 of TQS. ADR-007 grounded LLM narrative cached per alert
delivery — generated once, never regenerated. See plan §3.7.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'w4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'v3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE user_alert_deliveries "
        "ADD COLUMN IF NOT EXISTS narrative_text text"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE user_alert_deliveries DROP COLUMN IF EXISTS narrative_text")
