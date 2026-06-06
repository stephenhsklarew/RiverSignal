"""watershed_splash: admin-editable image + description for the /path splash cards

Revision ID: ws50a1b2c3d4
Revises: ci40a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

The /path splash page renders one card per watershed (HomePage.tsx) with a
photo, a short tagline, and a longer narrative. Those were hardcoded in the
frontend (PHOTOS / WATERSHED_META constants) with no way for an admin to
change them.

This adds a per-watershed override table the admin console writes to and
GET /sites/{watershed} reads from; the frontend falls back to its built-in
defaults when no row exists.

  gold.watershed_splash          — (watershed) overrides: image_url, tagline, narrative
  audit.watershed_splash_log     — change history
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ws50a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ci40a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS gold.watershed_splash (
            watershed           varchar(50) PRIMARY KEY,
            image_url           text,
            tagline             varchar(300),
            narrative           text,
            updated_by_user_id  uuid REFERENCES users(id),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
    """)

    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.watershed_splash_log (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            watershed           varchar(50) NOT NULL,
            action              varchar(16) NOT NULL,
            prev_image_url      text,
            new_image_url       text,
            prev_tagline        text,
            new_tagline         text,
            prev_narrative      text,
            new_narrative       text,
            changed_by_user_id  uuid REFERENCES users(id),
            changed_at          timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_wsplash_watershed
            ON audit.watershed_splash_log (watershed, changed_at DESC)
    """)


def downgrade() -> None:
    # Destructive (drops overrides + audit trail). Upgrade-only.
    pass
