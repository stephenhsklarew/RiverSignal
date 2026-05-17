"""merge heads z7+af31 and delete user observations whose coords are outside every watershed bbox

Revision ID: ag32a3b4c5d6
Revises: z7d8e9f0a1b2, af31z2a3b4c5
Create Date: 2026-05-17 00:00:00.000000

Two motivations:

1. Merge migration — origin/main has two unmerged alembic heads
   (z7d8e9f0a1b2 "reach coverage" and af31z2a3b4c5 "admin console schema",
   the tip of the curated-photos / admin-console chain that previously
   merged in zz26). `alembic upgrade head` requires a single head, so we
   stitch them together here.

2. Delete the orphan Rainbow Trout user_observation reported by the
   owner (email=stephen.sklarew@synaptiq.ai, observed 2025-07-14 on the
   Middle Fork Willamette — outside every watershed bbox RiverPath
   currently covers). The companion code change in
   app/routers/user_observations.py blocks future submissions whose
   coords sit outside every watershed bbox, but pre-existing rows need
   one-shot cleanup.

   We also delete linked bronze observations rows (source_id matches
   <user_obs_id> as the suffix).

Idempotent: re-runs match zero rows.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ag32a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = ('z7d8e9f0a1b2', 'af31z2a3b4c5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop linked bronze observations rows first (FK-less but still
    # logically dependent — source_id ends with ':<user_obs_id>').
    op.execute("""
        DELETE FROM observations o
         WHERE o.quality_grade = 'user_submitted'
           AND EXISTS (
             SELECT 1
               FROM user_observations uo
               JOIN users u ON u.id = uo.user_id
              WHERE u.email = 'stephen.sklarew@synaptiq.ai'
                AND uo.watershed = 'green_river'
                AND (uo.species_name ILIKE '%rainbow trout%'
                  OR uo.common_name ILIKE '%rainbow trout%')
                AND uo.observed_at::date = DATE '2025-07-14'
                AND o.source_id LIKE '%:' || uo.id::text
           )
    """)

    # 2. Drop the user_observations row(s).
    op.execute("""
        DELETE FROM user_observations uo
         USING users u
         WHERE uo.user_id = u.id
           AND u.email = 'stephen.sklarew@synaptiq.ai'
           AND uo.watershed = 'green_river'
           AND (uo.species_name ILIKE '%rainbow trout%'
             OR uo.common_name ILIKE '%rainbow trout%')
           AND uo.observed_at::date = DATE '2025-07-14'
    """)


def downgrade() -> None:
    # No-op: cannot resurrect a deleted user observation.
    pass
