"""extend gold.stocking_schedule to include ga_trout (GA DNR-WRD / Chattahoochee)

Revision ID: ch09a1b2c3d4
Revises: ch08a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

The ga_trout adapter writes interventions with
`description::jsonb ->> 'source' = 'ga_trout'`, but gold.stocking_schedule's
UNION branches key on odfw/udwr/wdfw/va_dwr/ohio_dnr — so the 7 Chattahoochee
stockings are invisible to the RiverPath stocking panel (verified: 7 interventions
on prod, 0 in stocking_schedule). Add a 6th branch (`ga_trout_stocking`),
mirroring the va_dwr branch (the GA weekly PDF has no quantity → total_fish NULL).

Mirrors the proven mr11 (ohio_dnr) DROP CASCADE + recreate pattern.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'ch09a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch08a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_EXISTING = """
-- ODFW (Oregon)
 SELECT t.site_id, s.watershed,
    replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text) AS waterbody,
    t."timestamp"::date AS stocking_date, t.value::integer AS total_fish,
    'odfw_stocking'::text AS source_type, sl.latitude, sl.longitude, sl.notes AS location_notes
   FROM time_series t JOIN sites s ON s.id = t.site_id
     LEFT JOIN stocking_locations sl ON sl.watershed = s.watershed
      AND sl.waterbody = replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text)
  WHERE t.source_type::text = 'stocking'::text AND t.value > 0::double precision
UNION ALL
-- UDWR (Green River basin)
 SELECT i.site_id, s.watershed, (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date,
    NULLIF(regexp_replace(COALESCE((i.description::jsonb) ->> 'quantity'::text, ''), '[^0-9]', '', 'g'), '')::integer AS total_fish,
    'udwr_stocking'::text AS source_type, sl.latitude, sl.longitude, sl.notes AS location_notes
   FROM interventions i JOIN sites s ON s.id = i.site_id
     LEFT JOIN stocking_locations sl ON sl.watershed = s.watershed AND sl.waterbody = (i.description::jsonb) ->> 'waterbody'::text
  WHERE i.type::text = 'fish_stocking'::text AND i.description IS NOT NULL AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'udwr'::text
UNION ALL
-- WDFW (Skagit)
 SELECT w.site_id, s.watershed, w.release_location AS waterbody, w.release_date AS stocking_date,
    w.number_released AS total_fish, 'wdfw_stocking'::text AS source_type, sl.latitude, sl.longitude, sl.notes AS location_notes
   FROM wa_fish_stocking w JOIN sites s ON s.id = w.site_id
     LEFT JOIN stocking_locations sl ON sl.watershed = s.watershed AND sl.waterbody = w.release_location
  WHERE w.number_released IS NOT NULL AND w.number_released > 0
UNION ALL
-- VA DWR (Shenandoah / Clinch / New)
 SELECT i.site_id, s.watershed, (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date, NULL::integer AS total_fish,
    'va_dwr_stocking'::text AS source_type, sl.latitude, sl.longitude, sl.notes AS location_notes
   FROM interventions i JOIN sites s ON s.id = i.site_id
     LEFT JOIN stocking_locations sl ON sl.watershed = s.watershed AND sl.waterbody = (i.description::jsonb) ->> 'waterbody'::text
  WHERE i.type::text = 'fish_stocking'::text AND i.description IS NOT NULL AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'va_dwr'::text
UNION ALL
-- ODNR (Mad River OH)
 SELECT i.site_id, s.watershed, (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date,
    NULLIF(regexp_replace(COALESCE((i.description::jsonb) ->> 'quantity'::text, ''), '[^0-9]', '', 'g'), '')::integer AS total_fish,
    'ohio_dnr_stocking'::text AS source_type, sl.latitude, sl.longitude, sl.notes AS location_notes
   FROM interventions i JOIN sites s ON s.id = i.site_id
     LEFT JOIN stocking_locations sl ON sl.watershed = s.watershed AND sl.waterbody = (i.description::jsonb) ->> 'waterbody'::text
  WHERE i.type::text = 'fish_stocking'::text AND i.description IS NOT NULL AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'ohio_dnr'::text
"""

_GA_TROUT_BRANCH = """
UNION ALL
-- GA DNR-WRD (Chattahoochee — weekly trout stocking PDF; no quantity reported)
 SELECT i.site_id, s.watershed, (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date, NULL::integer AS total_fish,
    'ga_trout_stocking'::text AS source_type, sl.latitude, sl.longitude, sl.notes AS location_notes
   FROM interventions i JOIN sites s ON s.id = i.site_id
     LEFT JOIN stocking_locations sl ON sl.watershed = s.watershed AND sl.waterbody = (i.description::jsonb) ->> 'waterbody'::text
  WHERE i.type::text = 'fish_stocking'::text AND i.description IS NOT NULL AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'ga_trout'::text
"""

NEW_VIEW_SQL = "CREATE MATERIALIZED VIEW gold.stocking_schedule AS" + _EXISTING + _GA_TROUT_BRANCH
OLD_VIEW_SQL = "CREATE MATERIALIZED VIEW gold.stocking_schedule AS" + _EXISTING


def _recreate(sql: str) -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE")
    op.execute(sql)
    op.execute("CREATE INDEX ix_gold_stocking_schedule_watershed ON gold.stocking_schedule (watershed)")
    op.execute("CREATE INDEX ix_gold_stocking_schedule_date ON gold.stocking_schedule (stocking_date DESC)")


def upgrade() -> None:
    _recreate(NEW_VIEW_SQL)


def downgrade() -> None:
    _recreate(OLD_VIEW_SQL)
