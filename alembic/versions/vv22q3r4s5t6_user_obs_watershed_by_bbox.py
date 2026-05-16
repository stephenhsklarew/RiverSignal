"""reassign user_observations to the watershed whose bbox contains their point

Revision ID: uu21p2q3r4s5
Revises: tt20o1p2q3r4
Create Date: 2026-05-16 00:00:00.000000

User-submitted observations were tagged with whatever watershed the
client was viewing when the form was opened, NOT the watershed whose
bbox actually contains the photo's lat/lon. So a photo taken in the
Deschutes while the user had Shenandoah selected got saved under
shenandoah and showed up on /path/saved/shenandoah even though it's
700 miles east of any Shenandoah water.

The companion code fix in app/routers/user_observations.py:create_user_observation
now resolves the watershed from sites.bbox at write time. This
migration cleans up history:

  1. For each user_observation with lat/lon set, find the watershed
     whose sites.bbox contains the point. UPDATE the
     user_observations.watershed column if it differs.
  2. Mirror that update onto the linked rows in `observations`
     (those have a site_id FK rather than a watershed string; rewrite
     site_id to the correct watershed's site).

Idempotent — re-runs on already-corrected rows are no-ops.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'vv22q3r4s5t6'
down_revision: Union[str, Sequence[str], None] = 'uu21p2q3r4s5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Fix user_observations.watershed via bbox containment.
    op.execute("""
        UPDATE user_observations uo
           SET watershed = correct.watershed
          FROM (
            SELECT uo2.id AS uo_id, s.watershed
              FROM user_observations uo2
              JOIN sites s
                ON s.bbox IS NOT NULL
               AND (s.bbox->>'west')::float  <= uo2.longitude
               AND (s.bbox->>'east')::float  >= uo2.longitude
               AND (s.bbox->>'south')::float <= uo2.latitude
               AND (s.bbox->>'north')::float >= uo2.latitude
             WHERE uo2.latitude IS NOT NULL
               AND uo2.longitude IS NOT NULL
          ) AS correct
         WHERE uo.id = correct.uo_id
           AND COALESCE(uo.watershed, '') <> correct.watershed
    """)

    # 2. Mirror onto the bronze `observations` rows linked to those
    # user_observations. user-submitted rows are tagged
    # quality_grade='user_submitted' and have source_id like
    # 'user:<obs_id>' or '<username>:<obs_id>'.
    op.execute("""
        UPDATE observations o
           SET site_id = correct_site.id
          FROM (
            SELECT uo.id AS uo_id, s.id, s.watershed
              FROM user_observations uo
              JOIN sites s
                ON s.bbox IS NOT NULL
               AND (s.bbox->>'west')::float  <= uo.longitude
               AND (s.bbox->>'east')::float  >= uo.longitude
               AND (s.bbox->>'south')::float <= uo.latitude
               AND (s.bbox->>'north')::float >= uo.latitude
             WHERE uo.latitude IS NOT NULL
               AND uo.longitude IS NOT NULL
          ) AS correct_site,
              sites old_s
         WHERE o.quality_grade = 'user_submitted'
           AND o.source_id LIKE '%:' || correct_site.uo_id::text
           AND o.site_id = old_s.id
           AND old_s.watershed <> correct_site.watershed
    """)


def downgrade() -> None:
    # No-op: prior watershed assignments were wrong by definition;
    # reverting would re-introduce mis-tagged rows.
    pass
