"""extend gold.stocking_schedule to include va_dwr (VA DWR trout stocking)

Revision ID: hh08c9d0e1f2
Revises: gg07b8c9d0e1
Create Date: 2026-05-15 00:00:00.000000

VA DWR stocking adapter (`pipeline/ingest/virginia.py`) writes interventions
rows with type='fish_stocking' and `description::jsonb ->> 'source' = 'va_dwr'`.
The existing UDWR UNION branch keys on 'udwr', so va_dwr rows are invisible
to the gold MV until we add a parallel branch.

This migration adds a 4th UNION branch (`va_dwr_stocking`). VA DWR's public
schedule does not publish per-event fish counts, so total_fish is left NULL —
the frontend already handles NULL counts (shows event date + waterbody only).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'hh08c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'gg07b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.stocking_schedule AS
-- ODFW (Oregon)
 SELECT t.site_id,
    s.watershed,
    replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text) AS waterbody,
    t."timestamp"::date AS stocking_date,
    t.value::integer AS total_fish,
    'odfw_stocking'::text AS source_type,
    sl.latitude,
    sl.longitude,
    sl.notes AS location_notes
   FROM time_series t
     JOIN sites s ON s.id = t.site_id
     LEFT JOIN stocking_locations sl
       ON sl.watershed = s.watershed
      AND sl.waterbody = replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text)
  WHERE t.source_type::text = 'stocking'::text AND t.value > 0::double precision
UNION ALL
-- UDWR (Green River basin)
 SELECT i.site_id,
    s.watershed,
    (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date,
    NULLIF(regexp_replace(COALESCE((i.description::jsonb) ->> 'quantity'::text, ''), '[^0-9]', '', 'g'), '')::integer AS total_fish,
    'udwr_stocking'::text AS source_type,
    sl.latitude,
    sl.longitude,
    sl.notes AS location_notes
   FROM interventions i
     JOIN sites s ON s.id = i.site_id
     LEFT JOIN stocking_locations sl
       ON sl.watershed = s.watershed
      AND sl.waterbody = (i.description::jsonb) ->> 'waterbody'::text
  WHERE i.type::text = 'fish_stocking'::text
    AND i.description IS NOT NULL
    AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'udwr'::text
UNION ALL
-- WDFW (Skagit)
 SELECT w.site_id,
    s.watershed,
    w.release_location AS waterbody,
    w.release_date AS stocking_date,
    w.number_released AS total_fish,
    'wdfw_stocking'::text AS source_type,
    sl.latitude,
    sl.longitude,
    sl.notes AS location_notes
   FROM wa_fish_stocking w
     JOIN sites s ON s.id = w.site_id
     LEFT JOIN stocking_locations sl
       ON sl.watershed = s.watershed
      AND sl.waterbody = w.release_location
  WHERE w.number_released IS NOT NULL AND w.number_released > 0
UNION ALL
-- VA DWR (Shenandoah — VA-wide schedule, scoped at ingest time by waterbody allowlist)
 SELECT i.site_id,
    s.watershed,
    (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date,
    NULL::integer AS total_fish,
    'va_dwr_stocking'::text AS source_type,
    sl.latitude,
    sl.longitude,
    sl.notes AS location_notes
   FROM interventions i
     JOIN sites s ON s.id = i.site_id
     LEFT JOIN stocking_locations sl
       ON sl.watershed = s.watershed
      AND sl.waterbody = (i.description::jsonb) ->> 'waterbody'::text
  WHERE i.type::text = 'fish_stocking'::text
    AND i.description IS NOT NULL
    AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'va_dwr'::text
"""

OLD_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.stocking_schedule AS
-- ODFW (Oregon)
 SELECT t.site_id,
    s.watershed,
    replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text) AS waterbody,
    t."timestamp"::date AS stocking_date,
    t.value::integer AS total_fish,
    'odfw_stocking'::text AS source_type,
    sl.latitude,
    sl.longitude,
    sl.notes AS location_notes
   FROM time_series t
     JOIN sites s ON s.id = t.site_id
     LEFT JOIN stocking_locations sl
       ON sl.watershed = s.watershed
      AND sl.waterbody = replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text)
  WHERE t.source_type::text = 'stocking'::text AND t.value > 0::double precision
UNION ALL
-- UDWR (Green River basin)
 SELECT i.site_id,
    s.watershed,
    (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date,
    NULLIF(regexp_replace(COALESCE((i.description::jsonb) ->> 'quantity'::text, ''), '[^0-9]', '', 'g'), '')::integer AS total_fish,
    'udwr_stocking'::text AS source_type,
    sl.latitude,
    sl.longitude,
    sl.notes AS location_notes
   FROM interventions i
     JOIN sites s ON s.id = i.site_id
     LEFT JOIN stocking_locations sl
       ON sl.watershed = s.watershed
      AND sl.waterbody = (i.description::jsonb) ->> 'waterbody'::text
  WHERE i.type::text = 'fish_stocking'::text
    AND i.description IS NOT NULL
    AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'udwr'::text
UNION ALL
-- WDFW (Skagit)
 SELECT w.site_id,
    s.watershed,
    w.release_location AS waterbody,
    w.release_date AS stocking_date,
    w.number_released AS total_fish,
    'wdfw_stocking'::text AS source_type,
    sl.latitude,
    sl.longitude,
    sl.notes AS location_notes
   FROM wa_fish_stocking w
     JOIN sites s ON s.id = w.site_id
     LEFT JOIN stocking_locations sl
       ON sl.watershed = s.watershed
      AND sl.waterbody = w.release_location
  WHERE w.number_released IS NOT NULL AND w.number_released > 0
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE")
    op.execute(NEW_VIEW_SQL)
    op.execute("CREATE INDEX ix_gold_stocking_schedule_watershed ON gold.stocking_schedule (watershed)")
    op.execute("CREATE INDEX ix_gold_stocking_schedule_date ON gold.stocking_schedule (stocking_date DESC)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE")
    op.execute(OLD_VIEW_SQL)
    op.execute("CREATE INDEX ix_gold_stocking_schedule_watershed ON gold.stocking_schedule (watershed)")
    op.execute("CREATE INDEX ix_gold_stocking_schedule_date ON gold.stocking_schedule (stocking_date DESC)")
