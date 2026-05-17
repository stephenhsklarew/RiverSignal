"""admin console schema: users.is_admin + curated_species_photos provenance + audit log

Revision ID: af31z2a3b4c5
Revises: ae30y1z2a3b4
Create Date: 2026-05-17 00:00:00.000000

Backing schema for plan-2026-05-17-watershed-admin-console.md (v0).

Adds:
  users.is_admin                              — boolean gate for admin routes
  gold.curated_species_photos.inat_*          — provenance for iNat-sourced photos
  gold.curated_species_photos.license         — CC-BY / CC-BY-SA / CC0 / PD attribution
  gold.curated_species_photos.updated_by_*    — audit columns
  audit (schema)                              — new schema for audit logs
  audit.curated_species_photos_log            — change history

Also bootstraps sklarew@gmail.com as the first admin. Idempotent —
no-op if that user hasn't signed in yet (admin can run the UPDATE
manually post-OAuth).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'af31z2a3b4c5'
down_revision: Union[str, Sequence[str], None] = 'ae30y1z2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Admin flag on users — default false; gated route enforcement is in
    # app/lib/admin_auth.py.
    op.execute("""
        ALTER TABLE users
          ADD COLUMN IF NOT EXISTS is_admin boolean NOT NULL DEFAULT false
    """)

    # Provenance + audit columns on curated_species_photos so the admin
    # editor can attribute photos correctly and roll back if needed.
    op.execute("""
        ALTER TABLE gold.curated_species_photos
          ADD COLUMN IF NOT EXISTS inat_observation_id bigint,
          ADD COLUMN IF NOT EXISTS inat_user_handle    varchar(80),
          ADD COLUMN IF NOT EXISTS license             varchar(40),
          ADD COLUMN IF NOT EXISTS updated_by_user_id  uuid REFERENCES users(id),
          ADD COLUMN IF NOT EXISTS updated_at          timestamptz NOT NULL DEFAULT now()
    """)

    # Separate schema for audit data so retention policies, ACLs, and
    # archival jobs can target it without affecting prod schemas.
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.curated_species_photos_log (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            species_key         varchar(64) NOT NULL,
            action              varchar(16) NOT NULL,
            prev_photo_url      text,
            new_photo_url       text,
            prev_common_name    varchar(120),
            new_common_name     varchar(120),
            prev_scientific     varchar(120),
            new_scientific      varchar(120),
            changed_by_user_id  uuid REFERENCES users(id),
            changed_at          timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_csp_species_key
            ON audit.curated_species_photos_log (species_key, changed_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_csp_changed_at
            ON audit.curated_species_photos_log (changed_at DESC)
    """)

    # Bootstrap the first admin. Idempotent: no-op when the row doesn't
    # exist yet (typical on the very first deploy before OAuth sign-in).
    op.execute("""
        UPDATE users SET is_admin = true
         WHERE email = 'sklarew@gmail.com'
           AND is_admin IS NOT TRUE
    """)


def downgrade() -> None:
    # Tearing this down is destructive (loses audit trail). Keep upgrade-
    # only — restore by deleting the admin column / audit schema by hand
    # if you really need to.
    pass
