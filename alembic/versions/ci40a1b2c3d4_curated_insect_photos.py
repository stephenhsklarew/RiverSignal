"""curated_insect_photos: per-watershed photo overrides for "What Fish Are Eating Now"

Revision ID: ci40a1b2c3d4
Revises: sv01a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

Fish photos have an admin curation path (gold.curated_species_photos);
insect/prey photos did not. The species-spotter endpoint
(/sites/{watershed}/species-spotter, "What Fish Are Eating Now")
resolved every insect photo live from gold.species_gallery by
genus-prefix match — no editorial override, no per-watershed
specialisation.

This adds a SEPARATE table mirroring the fish one (kept separate so the
fish lookup path is untouched and an insect can share a common name with
a fish without colliding):

  gold.curated_insect_photos          — (species_key, watershed) overrides
  audit.curated_insect_photos_log     — change history

Lookup precedence in app/routers/ai_features.py:species_spotter becomes:
  species_gallery genus match  <  global default ('*')  <  watershed-specific

Backwards-compatible: with the table empty, species-spotter behaves
exactly as before.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ci40a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'sv01a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS gold.curated_insect_photos (
            species_key         varchar(64),
            watershed           varchar(50)  NOT NULL DEFAULT '*',
            common_name         varchar(120) NOT NULL,
            scientific_name     varchar(120),
            photo_url           text         NOT NULL,
            source              varchar(40)  NOT NULL DEFAULT 'inaturalist',
            inat_observation_id bigint,
            inat_user_handle    varchar(80),
            license             varchar(40),
            updated_by_user_id  uuid REFERENCES users(id),
            updated_at          timestamptz  NOT NULL DEFAULT now(),
            PRIMARY KEY (species_key, watershed)
        )
    """)

    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.curated_insect_photos_log (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            species_key         varchar(64) NOT NULL,
            watershed           varchar(50) NOT NULL DEFAULT '*',
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
        CREATE INDEX IF NOT EXISTS ix_audit_cip_species_key
            ON audit.curated_insect_photos_log (species_key, changed_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_cip_changed_at
            ON audit.curated_insect_photos_log (changed_at DESC)
    """)


def downgrade() -> None:
    # Destructive (drops the curation overrides + audit trail). Upgrade-only.
    pass
