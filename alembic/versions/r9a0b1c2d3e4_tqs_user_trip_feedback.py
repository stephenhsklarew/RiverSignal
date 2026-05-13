"""create user_trip_feedback table

Revision ID: r9a0b1c2d3e4
Revises: q8f9a0b1c2d3
Create Date: 2026-05-13 00:00:08.000000

Phase A of TQS. Feedback loop ground-truth table — one-tap "how was
it?" rating per trip. user_id nullable so anonymous feedback survives
user deletion. See plan §3.0c.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'r9a0b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'q8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_trip_feedback (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         uuid REFERENCES users(id) ON DELETE SET NULL,
            reach_id        varchar(80) NOT NULL REFERENCES silver.river_reaches(id),
            trip_date       date NOT NULL,
            tqs_at_view     int,
            rating          smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
            notes           text,
            submitted_at    timestamptz DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_utf_reach_date ON user_trip_feedback (reach_id, trip_date)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_trip_feedback")
