"""seed shenandoah site + 3 reaches (North Fork / South Fork / Main Stem)

Revision ID: bb02c3d4e5f6
Revises: aa01b2c3d4e5
Create Date: 2026-05-15 11:00:00.000000

Phase 1 of Shenandoah onboarding per
docs/helix/06-iterate/watershed-add/shenandoah-source-inventory-2026-05-15.md.

Idempotent. Site row first (bronze adapters FK to it). Three reaches
anchored on USGS gauges:
  - North Fork:  01634000 (NF Shenandoah nr Strasburg, VA)
  - South Fork:  01631000 (SF Shenandoah at Front Royal, VA)
  - Main Stem:   01636500 (Shenandoah River at Millville, WV)

All reaches flagged needs_guide_review=true. Main stem is warm-water
(smallmouth-dominant); forks default to cold-water (brook/brown/rainbow).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'bb02c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'aa01b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Bootstrap the site row (everything else FKs to it).
    # No unique constraint on watershed slug, so guard with NOT EXISTS to
    # keep the migration idempotent and avoid duplicate-site bugs that
    # would split bronze inserts across two site_ids.
    # JSON literal passed as a bind to avoid psycopg parsing ":N" in the
    # JSON body as a SQL parameter placeholder.
    op.execute(sa.text("""
        INSERT INTO sites (id, name, watershed, huc12_codes, bbox)
        SELECT gen_random_uuid(), 'Shenandoah River', 'shenandoah',
               '[]'::jsonb,
               CAST(:bbox AS jsonb)
        WHERE NOT EXISTS (SELECT 1 FROM sites WHERE watershed = 'shenandoah')
    """).bindparams(bbox='{"north":39.35,"south":37.70,"east":-77.65,"west":-79.40}'))

    # 2. Three reaches anchored on USGS gauges.
    op.execute("""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            ('shenandoah_north_fork', 'shenandoah',
             'North Fork Shenandoah', 'North Fork',
             38.85, -78.45,
             '01634000', 0, FALSE,
             ARRAY['brook_trout','brown_trout','rainbow_trout','smallmouth_bass']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-05-15. Cold tributaries support wild brook trout; lower reaches warm-water smallmouth.',
             'v0 plan §3.0 + shenandoah-source-inventory-2026-05-15.md — needs guide review'),
            ('shenandoah_south_fork', 'shenandoah',
             'South Fork Shenandoah', 'South Fork',
             38.55, -78.60,
             '01631000', 0, FALSE,
             ARRAY['brown_trout','rainbow_trout','smallmouth_bass','channel_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-05-15. Includes limestone-spring tributaries (Mossy Creek, Beaver Creek) — flag for sub-reach curation in v1.',
             'v0 plan §3.0 + shenandoah-source-inventory-2026-05-15.md — needs guide review'),
            ('shenandoah_main_stem', 'shenandoah',
             'Shenandoah Main Stem', 'Main Stem',
             39.10, -78.00,
             '01636500', 0, TRUE,
             ARRAY['smallmouth_bass','channel_catfish','fallfish','sunfish','musky']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-05-15. Warm-water river from Front Royal confluence to Potomac at Harpers Ferry, WV. Smallmouth dominant.',
             'v0 plan §3.0 + shenandoah-source-inventory-2026-05-15.md — needs guide review')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM silver.river_reaches
        WHERE id IN ('shenandoah_north_fork', 'shenandoah_south_fork', 'shenandoah_main_stem')
    """)
    op.execute("DELETE FROM sites WHERE watershed = 'shenandoah'")
