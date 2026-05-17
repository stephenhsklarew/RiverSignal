"""river_stories provenance columns + audit log for admin editor

Revision ID: ai34c5d6e7f8
Revises: ah33b4c5d6e7
Create Date: 2026-05-17 00:00:00.000000

Backing schema for the river_story admin surface (v1 of the watershed
admin console per plan-2026-05-17-watershed-admin-console.md, OF-1).

Adds:
  river_stories.updated_by_user_id  — uuid of the admin who last saved
  river_stories.updated_at          — timestamptz
  audit.river_stories_log           — change history
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ai34c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'ah33b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE river_stories
          ADD COLUMN IF NOT EXISTS updated_by_user_id  uuid REFERENCES users(id),
          ADD COLUMN IF NOT EXISTS updated_at          timestamptz NOT NULL DEFAULT now()
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.river_stories_log (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            watershed           varchar(50) NOT NULL,
            reading_level       varchar(20) NOT NULL,
            action              varchar(32) NOT NULL,
              -- 'narrative_update' | 'audio_regenerate' | 'narrative_delete'
            prev_narrative      text,
            new_narrative       text,
            prev_audio_path     text,
            new_audio_path      text,
            changed_by_user_id  uuid REFERENCES users(id),
            changed_at          timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_rs_ws_level
            ON audit.river_stories_log (watershed, reading_level, changed_at DESC)
    """)


def downgrade() -> None:
    pass
