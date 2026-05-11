"""fix stocking watershed scoping + extend stocking_schedule to UDWR/WDFW

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-05-11 00:00:00.000000

Phase A of the Fish Stocking map work:

  1. ODFW stocking ingestion was inserting unfiltered Oregon-wide results
     for any watershed not present in its zone_map (notably johnday,
     skagit, green_river). Pipeline fix is in pipeline/ingest/fishing.py;
     this migration deletes the wrong-watershed rows that accumulated.

  2. gold.stocking_schedule is extended with two new UNION blocks so each
     watershed surfaces the right source's stocking data:
       - ODFW   → mckenzie / deschutes / metolius / klamath / johnday
       - UDWR   → green_river  (from interventions, written by utah adapter)
       - WDFW   → skagit       (from wa_fish_stocking)
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.stocking_schedule AS
-- ODFW (Oregon, via time_series source_type='stocking')
 SELECT t.site_id,
    s.watershed,
    replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text) AS waterbody,
    t."timestamp"::date AS stocking_date,
    t.value::integer AS total_fish,
    'odfw_stocking'::text AS source_type
   FROM time_series t
     JOIN sites s ON s.id = t.site_id
  WHERE t.source_type::text = 'stocking'::text AND t.value > 0::double precision
UNION ALL
-- UDWR (Utah / Green River basin)
 SELECT i.site_id,
    s.watershed,
    (i.description::jsonb) ->> 'waterbody'::text AS waterbody,
    i.started_at::date AS stocking_date,
    NULLIF(regexp_replace(COALESCE((i.description::jsonb) ->> 'quantity'::text, ''), '[^0-9]', '', 'g'), '')::integer AS total_fish,
    'udwr_stocking'::text AS source_type
   FROM interventions i
     JOIN sites s ON s.id = i.site_id
  WHERE i.type::text = 'fish_stocking'::text
    AND i.description IS NOT NULL
    AND i.description LIKE '{%'
    AND ((i.description::jsonb) ->> 'source'::text) = 'udwr'::text
UNION ALL
-- WDFW (Washington / Skagit)
 SELECT w.site_id,
    s.watershed,
    w.release_location AS waterbody,
    w.release_date AS stocking_date,
    w.number_released AS total_fish,
    'wdfw_stocking'::text AS source_type
   FROM wa_fish_stocking w
     JOIN sites s ON s.id = w.site_id
  WHERE w.number_released IS NOT NULL AND w.number_released > 0
"""

OLD_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.stocking_schedule AS
 SELECT t.site_id,
    s.watershed,
    replace(replace(t.station_id::text, 'stocking_'::text, ''::text), '_'::text, ' '::text) AS waterbody,
    t."timestamp"::date AS stocking_date,
    t.value::integer AS total_fish,
    t.source_type
   FROM time_series t
     JOIN sites s ON s.id = t.site_id
  WHERE t.source_type::text = 'stocking'::text AND t.value > 0::double precision
"""


def upgrade() -> None:
    # 1) Delete ODFW stocking rows that were mis-attributed to watersheds
    #    outside Oregon, or to the John Day watershed (where unfiltered
    #    Oregon-wide data was leaking through due to a missing zone_map
    #    entry). The next pipeline run will repopulate John Day correctly
    #    using the Northeast zone filter.
    op.execute("""
        DELETE FROM time_series
        WHERE source_type = 'stocking'
          AND site_id IN (
            SELECT id FROM sites
            WHERE watershed IN ('johnday', 'skagit', 'green_river')
          )
    """)

    # 2) Rebuild gold.stocking_schedule with UNION across ODFW / UDWR / WDFW.
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE")
    op.execute(NEW_VIEW_SQL)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE")
    op.execute(OLD_VIEW_SQL)
    # Note: deleted time_series rows are not restored on downgrade.
    # They would repopulate from the upstream ODFW scrape on the next run.
