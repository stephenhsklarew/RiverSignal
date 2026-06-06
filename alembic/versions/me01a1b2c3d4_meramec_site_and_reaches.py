"""seed meramec site + 4 reaches (Upper / Middle / Lower / Big River)

Revision ID: me01a1b2c3d4
Revises: ws50a1b2c3d4
Create Date: 2026-06-06 00:00:00.000000

Phase 1 of Meramec (MO) onboarding per
docs/helix/06-iterate/watershed-add/meramec-source-inventory-2026-06-05.md §1.7.

The platform's first Missouri / mid-continent karst watershed. Idempotent; site
row NOT EXISTS-guarded. Name seeded suffix-free ("Meramec River").

Four reaches:
  - Upper (07014000 Huzzah Cr near Steelville): the ONLY basin gauge reporting
    real-time water TEMPERATURE — so this reach gets a full flow+temp Go Score.
    Smallmouth/goggle-eye float corridor (Steelville "Floating Capital") plus the
    Maramec Spring rainbow-trout park nearby. Cooler/spring-influenced → not flagged
    warm-water.
  - Middle (07014500 Meramec near Sullivan): Meramec SP / Onondaga Cave karst reach;
    smallmouth + largemouth + catfish. Gauge = discharge + gage height (NO temp →
    temp sub-score uses the climatology proxy).
  - Lower (07019000 Meramec near Eureka): St. Louis suburbs (Castlewood, Route 66 SP)
    → Mississippi confluence near Arnold. Warm-water; flash-flood prone. Gauge =
    discharge + gage height (NO temp).
  - Big River (07018500 Big R at Byrnesville): Old Lead Belt tributary. Structurally
    distinct because of a MO DNR lead/zinc/sediment 303(d) TMDL + active
    fish-consumption advisory (Big River Mine Tailings Superfund) — surfaced as a
    reach health note. Gauge = discharge + gage height (NO temp).

No main-stem dam (Meramec Park Dam defeated by 1978 referendum) → no tailwater
dam-release safety hazard.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'me01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ws50a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO sites (id, name, watershed, huc12_codes, bbox)
        SELECT gen_random_uuid(), 'Meramec River', 'meramec',
               '[]'::jsonb, CAST(:bbox AS jsonb)
        WHERE NOT EXISTS (SELECT 1 FROM sites WHERE watershed = 'meramec')
    """).bindparams(bbox='{"north":38.65,"south":37.55,"east":-90.25,"west":-91.65}'))

    op.execute("""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            ('meramec_upper', 'meramec',
             'Upper Meramec & Steelville Float Corridor', 'Upper',
             37.97, -91.22,
             '07014000', 45, FALSE,
             ARRAY['smallmouth_bass','rock_bass','spotted_bass','rainbow_trout','longear_sunfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-06. Steelville/Huzzah/Courtois smallmouth float corridor + Maramec Spring rainbow-trout park (one of MO''s 4 trout parks, daily-stocked Mar 1-Oct 31). Smallmouth Bass Special Mgmt Area (Hwy 8 -> Bird''s Nest) + Red Ribbon trout area. Gauge 07014000 (Huzzah Cr) is the ONLY basin gauge reporting real-time water temperature -> full flow+temp Go Score here.',
             'v0 §1.7 meramec-source-inventory-2026-06-05.md — needs guide review'),
            ('meramec_middle', 'meramec',
             'Middle Meramec (Meramec & Onondaga Cave SP)', 'Middle',
             38.13, -91.00,
             '07014500', 45, TRUE,
             ARRAY['smallmouth_bass','largemouth_bass','rock_bass','channel_catfish','longear_sunfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-06. Sullivan -> Meramec State Park (Fisher Cave) -> Onondaga Cave SP karst reach; classic float water. Gauge 07014500 (near Sullivan) reports discharge + gage height only (NO water temp -> temp sub-score uses climatology proxy).',
             'v0 §1.7 meramec-source-inventory-2026-06-05.md — needs guide review'),
            ('meramec_lower', 'meramec',
             'Lower Meramec (St. Louis suburbs -> mouth)', 'Lower',
             38.48, -90.50,
             '07019000', 45, TRUE,
             ARRAY['smallmouth_bass','largemouth_bass','channel_catfish','walleye','white_bass','flathead_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-06. Eureka -> Mississippi River confluence near Arnold; St. Louis suburbs (Castlewood SP, Route 66 SP at former Times Beach). Heavily used, flash-flood prone (record floods 2015/2017). Gauge 07019000 (near Eureka) reports discharge + gage height only (NO water temp).',
             'v0 §1.7 meramec-source-inventory-2026-06-05.md — needs guide review'),
            ('big_river', 'meramec',
             'Big River (Old Lead Belt tributary)', 'Big River',
             38.39, -90.64,
             '07018500', 30, TRUE,
             ARRAY['smallmouth_bass','spotted_bass','rock_bass','channel_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-06. HEALTH ADVISORY: Big River drains the historic Old Lead Belt; the Big River Mine Tailings Superfund site drives a MO DNR lead/zinc/sediment 303(d) TMDL and an ACTIVE fish-consumption advisory (do not eat fish from Big River downstream of the tailings site). Gauge 07018500 (at Byrnesville) reports discharge + gage height only (NO water temp).',
             'v0 §1.7 meramec-source-inventory-2026-06-05.md — needs guide review; LEAD ADVISORY')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM silver.river_reaches
        WHERE id IN ('meramec_upper','meramec_middle','meramec_lower','big_river')
    """)
    op.execute("DELETE FROM sites WHERE watershed = 'meramec'")
