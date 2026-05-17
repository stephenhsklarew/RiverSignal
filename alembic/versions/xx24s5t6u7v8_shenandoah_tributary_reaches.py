"""seed 7 Shenandoah trout tributary reaches (VA only, strict drainage)

Revision ID: xx24s5t6u7v8
Revises: ww23r4s5t6u7
Create Date: 2026-05-16 00:00:00.000000

Adds well-known Virginia trout tributaries of the Shenandoah River as
individual reaches in silver.river_reaches. Per user direction
(2026-05-16): only streams that actually drain to the Shenandoah are
included. East-slope SNP streams (Whiteoak Canyon, Rose, Rapidan,
Hughes — Rappahannock drainage) and adjacent Potomac tributaries
(Cacapon, Lost, Tuscarora) are deliberately excluded.

Reaches added (all cold-water, is_warm_water = FALSE):
  1. South River           Augusta Co. — stocked + holdover trout near Waynesboro
  2. North River           Augusta Co. — GWNF headwaters, stocked + delayed-harvest
  3. Mossy Creek           Augusta Co. — famous limestone spring creek, wild brown
  4. Smith Creek           Rockingham/Shenandoah Co. — stocked + wild
  5. Passage Creek         Fort Valley — stocked trout, GWNF
  6. Jeremy's Run          SNP west-slope, native brook trout
  7. Overall Run           SNP west-slope, native brook trout, Overall Run Falls

bbox/centroid values are author-curated approximations (good to ~1 km
for the small streams; ~5 km for South/North River). Each row's `source`
field tags this as `needs_review` so a local guide can refine bounding
boxes once curated. Primary USGS gauges are only included where a known
active gauge serves that specific waterbody.

After insert: REFRESH MATERIALIZED VIEW gold.species_by_reach so the
curated UNION block I added in bb18m9n0o1p2 picks up the new reaches'
typical_species immediately (without this, /path/now/shenandoah Catch
Probability won't surface brook trout on Jeremy's Run etc. until the
next scheduled refresh).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'xx24s5t6u7v8'
down_revision: Union[str, Sequence[str], None] = 'ww23r4s5t6u7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (id, name, short_label, centroid_lat, centroid_lon,
#  bbox_n, bbox_s, bbox_e, bbox_w,
#  primary_usgs_site_id (or None), flow_bearing,
#  typical_species_csv, notes)
REACHES = [
    ('shenandoah_south_river', 'South River', 'South River',
     38.10, -78.92,
     38.32, 37.95, -78.80, -79.00,
     '02019500', 0,  # USGS South River at Waynesboro VA
     'rainbow_trout,brown_trout,brook_trout',
     'Augusta County. Headwaters south of Waynesboro flowing north through town to Port Republic confluence with North River → South Fork Shenandoah. Stocked rainbow + brown, occasional holdovers in deeper pools. Urban section through Waynesboro plus rural meadow runs. Needs guide review.'),

    ('shenandoah_north_river', 'North River', 'North River',
     38.30, -79.00,
     38.42, 38.20, -78.78, -79.25,
     None, 90,  # No single primary gauge — gauges differ between Stokesville (USGS 01624800 area) and Bridgewater
     'rainbow_trout,brown_trout,brook_trout',
     'Augusta County. Drains George Washington National Forest near Stokesville east through Bridgewater to Port Republic where it forms the South Fork Shenandoah. Includes Elkhorn Lake tailwater. Delayed-harvest sections in places. Needs guide review.'),

    ('shenandoah_mossy_creek', 'Mossy Creek', 'Mossy Creek',
     38.33, -79.02,
     38.38, 38.30, -78.97, -79.06,
     None, 45,
     'brown_trout,brook_trout',
     'Augusta County. Limestone spring creek near Mt. Solon — famous for wild self-sustaining brown trout in classic spring-creek style. Flows to Long Glade Run → Cooks Creek → North River → Shenandoah. Fly-fishing only catch-and-release special-regulation water. Needs guide review.'),

    ('shenandoah_smith_creek', 'Smith Creek', 'Smith Creek',
     38.70, -78.72,
     38.80, 38.55, -78.65, -78.78,
     None, 0,
     'rainbow_trout,brown_trout,brook_trout',
     'Rockingham/Shenandoah County line. Flows north through Lacey Spring + New Market to confluence with North Fork Shenandoah at Mt. Jackson. Stocked rainbow + brown, with wild fish in colder upper tributaries. Needs guide review.'),

    ('shenandoah_passage_creek', 'Passage Creek', 'Passage Creek',
     38.90, -78.32,
     38.98, 38.78, -78.25, -78.40,
     '01633000', 0,  # USGS Passage Creek near Buckton VA
     'rainbow_trout,brown_trout',
     'Drains Fort Valley between Massanutten and Three Top Mountains, joins North Fork Shenandoah at Waterlick near Front Royal. Stocked rainbow + brown through George Washington National Forest. Needs guide review.'),

    ('shenandoah_jeremys_run', "Jeremy's Run", "Jeremy's Run",
     38.79, -78.32,
     38.83, 38.75, -78.27, -78.36,
     None, 315,
     'brook_trout',
     'Shenandoah National Park, west slope of Blue Ridge in Mathews Arm District. Drops off Blue Ridge into Page Valley → Pass Run → Hawksbill Creek → Shenandoah. Native wild brook trout — classic SNP freestone fishery. Catch-and-release ethic; consult NPS regs. Needs guide review.'),

    ('shenandoah_overall_run', 'Overall Run', 'Overall Run',
     38.78, -78.34,
     38.82, 38.75, -78.30, -78.38,
     None, 270,
     'brook_trout',
     'Shenandoah National Park, west slope in Mathews Arm District. Steep remote brook trout stream featuring Overall Run Falls (highest waterfall in SNP). Drops into Page Valley → Shenandoah. Native brook trout only — small headwater fish. Long hike-in access. Needs guide review.'),
]


def upgrade() -> None:
    rows = []
    for (rid, name, short, lat, lon, bn, bs, be, bw,
         gauge, bearing, species_csv, notes) in REACHES:
        species_array = "ARRAY[" + ",".join(
            f"'{s}'" for s in species_csv.split(",")
        ) + "]::varchar[]"
        notes_escaped = notes.replace("'", "''")
        name_escaped = name.replace("'", "''")
        short_escaped = short.replace("'", "''")
        gauge_sql = f"'{gauge}'" if gauge else "NULL"
        bbox_sql = (
            f"ST_MakeEnvelope({bw}, {bs}, {be}, {bn}, 4326)"
        )
        rows.append(
            f"('{rid}','shenandoah','{name_escaped}','{short_escaped}',"
            f"{lat},{lon},{bbox_sql},"
            f"{gauge_sql},{bearing},FALSE,"
            f"{species_array},'{notes_escaped}','xx24 auto-seed 2026-05-16 — needs guide review')"
        )
    values_sql = ",\n            ".join(rows)
    op.execute(
        f"""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             bbox,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            {values_sql}
        ON CONFLICT (id) DO NOTHING
        """
    )
    # Surface the new reaches' typical_species in Catch Probability /
    # Fish Present immediately without waiting for the next scheduled
    # matview refresh.
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")


def downgrade() -> None:
    ids = ",".join(f"'{r[0]}'" for r in REACHES)
    op.execute(f"DELETE FROM silver.river_reaches WHERE id IN ({ids})")
    op.execute("REFRESH MATERIALIZED VIEW gold.species_by_reach")
