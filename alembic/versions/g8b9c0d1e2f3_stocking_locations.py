"""create stocking_locations table + seed Tier 1 + extend stocking_schedule view

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-05-11 00:00:00.000000

Phase B: enable mapping of the Fish Stocking section on /path/now.

  - New `stocking_locations` table: curated lookup of waterbody -> lat/lon.
    Seeded with ~25 headline waters across all supported watersheds.
    Expansion is a CSV edit + re-seed, no code change.

  - `gold.stocking_schedule` view gains optional latitude/longitude columns
    via a LEFT JOIN on (watershed, waterbody). Waterbodies not in the
    lookup still appear in the list with NULL coords — they just don't
    get a map pin.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'g8b9c0d1e2f3'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tier 1 seed: ~25 most-stocked, well-known waters per watershed.
# (watershed, waterbody-as-it-appears-in-stocking-data, lat, lon, notes)
SEED = [
    # ── McKenzie / Willamette zone (ODFW) ──
    ('mckenzie', 'MCKENZIE R-1 (below Leaburg Dam)', 44.105, -122.685, 'Below Leaburg Dam'),
    ('mckenzie', 'MCKENZIE R-2 (above Leaburg Dam)', 44.171, -122.475, 'Above Leaburg Dam'),
    ('mckenzie', 'LEABURG LK',                       44.110, -122.683, 'Leaburg dam impoundment'),
    ('mckenzie', 'CLEAR LK',                         44.376, -121.998, 'McKenzie headwaters'),
    ('mckenzie', 'DEXTER RES',                       43.918, -122.819, 'Middle Fork Willamette'),
    ('mckenzie', 'FARADAY LK',                       45.296, -122.227, 'Clackamas River (Willamette zone)'),

    # ── Deschutes / Central zone (ODFW) ──
    ('deschutes', 'HOSMER LK',          43.962, -121.785, 'Cascade Lakes Hwy'),
    ('deschutes', 'PAULINA LK',         43.717, -121.276, 'Newberry Caldera'),
    ('deschutes', 'EAST LK',            43.728, -121.220, 'Newberry Caldera'),
    ('deschutes', 'WICKIUP RES',        43.689, -121.674, ''),
    ('deschutes', 'CRANE PRAIRIE RES',  43.789, -121.751, ''),
    ('deschutes', 'DEVILS LK',          44.030, -121.781, 'Cascade Lakes Hwy'),
    ('deschutes', 'FALL R',             43.781, -121.640, ''),
    ('deschutes', 'THREE CREEKS LK',    44.106, -121.628, ''),
    ('deschutes', 'WALTON LK',          44.479, -120.738, 'Ochoco NF'),

    # ── Metolius / Central zone (ODFW) ──
    ('metolius',  'METOLIUS PD',  44.484, -121.624, 'Wizard Falls Hatchery area'),
    ('metolius',  'OLALLIE LK',   44.798, -121.795, 'Olallie Scenic Area'),

    # ── Klamath / Southeast zone (ODFW) ──
    ('klamath',   'LAKE OF THE WOODS', 42.371, -122.213, ''),
    ('klamath',   'FOURMILE LK',       42.479, -122.255, ''),
    ('klamath',   'ANA RES',           43.117, -120.778, 'Summer Lake area'),
    ('klamath',   'CAMPBELL LK',       42.547, -120.318, 'Warner Lakes / Lake County'),

    # ── John Day / Northeast zone (ODFW) ──
    ('johnday',   'MAGONE LK',     44.626, -118.916, 'Malheur NF'),
    ('johnday',   'OLIVE LK',      44.812, -118.604, 'Umatilla NF'),
    ('johnday',   'PHILLIPS RES',  44.658, -117.876, 'Powder R basin'),

    # ── Skagit / WDFW ──
    ('skagit',    'LK LOMA (SNOH)',       48.190, -122.300, 'Snohomish County'),
    ('skagit',    'SILVER LK (SNOH) T28', 47.836, -122.270, 'Snohomish County'),
    ('skagit',    'CHAIN LK (SNOH)',      47.870, -121.660, 'Snohomish County'),

    # ── Green River / UDWR ──
    ('green_river', 'FLAMING GORGE RES', 41.115, -109.451, 'Cedar Springs Marina'),
]


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
"""

OLD_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.stocking_schedule AS
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


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS stocking_locations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            watershed VARCHAR(32) NOT NULL,
            waterbody VARCHAR(255) NOT NULL,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            notes TEXT,
            last_verified DATE NOT NULL DEFAULT CURRENT_DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (watershed, waterbody)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_stocking_locations_lookup ON stocking_locations(watershed, waterbody)")

    # Idempotent seed: skip if (watershed, waterbody) already exists.
    for ws, wb, lat, lon, note in SEED:
        op.execute(f"""
            INSERT INTO stocking_locations (watershed, waterbody, latitude, longitude, notes)
            VALUES ('{ws}', '{wb.replace("'", "''")}', {lat}, {lon}, '{note.replace("'", "''")}')
            ON CONFLICT (watershed, waterbody) DO NOTHING
        """)

    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE")
    op.execute(NEW_VIEW_SQL)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.stocking_schedule CASCADE")
    op.execute(OLD_VIEW_SQL)
    op.execute("DROP TABLE IF EXISTS stocking_locations")
