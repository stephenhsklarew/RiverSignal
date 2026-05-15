"""purge ODFW stocking rows attributed to non-Oregon watersheds

Revision ID: jj10e1f2g3h4
Revises: ii09d0e1f2g3
Create Date: 2026-05-15 00:00:00.000000

`pipeline/ingest/fishing.py:_ingest_stocking` previously used a denylist of
("skagit", "green_river") to skip non-Oregon watersheds. When Shenandoah was
onboarded and pipeline_weekly was invoked as `fishing -w all`, the adapter
happily inserted 495 ODFW Oregon stocking rows against shenandoah's site_id.
`gold.stocking_schedule` then surfaced those rows on `/api/v1/sites/
shenandoah/fishing/stocking` (and would have done so for any future
non-Oregon watershed onboarded the same way).

This migration:
  1. Deletes all rows in `time_series` where `source_type='stocking'` and
     the site's watershed is NOT one of the Oregon watersheds covered by
     ODFW (mckenzie, deschutes, metolius, klamath, johnday).
  2. Refreshes `gold.stocking_schedule` so the MV no longer shows the
     polluted rows.

The companion code fix in `pipeline/ingest/fishing.py` converts the
denylist to an allowlist (`OREGON_WATERSHEDS`) so future runs cannot
re-pollute. Together, this migration handles the historic data and the
code change handles future ingests.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'jj10e1f2g3h4'
down_revision: Union[str, Sequence[str], None] = 'ii09d0e1f2g3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OREGON_WATERSHEDS_SQL = "('mckenzie','deschutes','metolius','klamath','johnday')"


def upgrade() -> None:
    op.execute(f"""
        DELETE FROM time_series
        WHERE source_type = 'stocking'
          AND site_id IN (
              SELECT id FROM sites
              WHERE watershed NOT IN {OREGON_WATERSHEDS_SQL}
          )
    """)
    op.execute("REFRESH MATERIALIZED VIEW gold.stocking_schedule")


def downgrade() -> None:
    # No-op: deleted rows came from a buggy adapter run; there is no
    # meaningful state to restore on downgrade. Re-running the corrected
    # adapter against Oregon watersheds will not produce these rows again.
    pass
