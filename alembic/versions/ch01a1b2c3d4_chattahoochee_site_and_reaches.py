"""seed chattahoochee site + 4 reaches (Headwaters / Lanier / Tailwater / Metro)

Revision ID: ch01a1b2c3d4
Revises: nr07a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

Phase 1 of Chattahoochee (GA) onboarding per
docs/helix/06-iterate/watershed-add/chattahoochee-source-inventory-2026-05-25.md §1.7.

The platform's first urban + first Southeast-US watershed. Idempotent; site row
NOT EXISTS-guarded (already created locally via the CLI; prod gets it here).
Name seeded suffix-free ("Chattahoochee River").

Four reaches — one more than a typical river because the Buford Dam tailwater is
structurally distinct from both the cold headwaters and the warm metro/lake reaches:
  - Headwaters (02331600 near Cornelia): cold Blue Ridge trout + redeye/smallmouth.
    Gauge has discharge + gage height only (NO temp).
  - Lake Sidney Lanier (02334401 Buford Dam): warm-water reservoir — striped/spotted/
    largemouth bass + crappie. Impoundment gauge is gage-height only (NO discharge →
    flow sub-score degrades, like New River's Claytor Lake).
  - Buford Dam Tailwater (02334430): the SIGNATURE reach — cold-release rainbow +
    brown trout through the CRNRA. Gauge reports discharge + water TEMPERATURE + DO +
    conductance, so this reach gets a full flow+temp Go Score. SAFETY: hydropower
    releases raise the tailwater 2–4 ft within minutes — a STATIC USACE-schedule
    safety banner renders here (TailwaterSafetyCard); the LIVE release feed is
    deferred to Phase B (RiverSignal-c8155522 / plan-2026-06-04-...-dam-release-safety.md).
  - Metro Atlanta (02336000 at Atlanta): warm-water striped/spotted/smallmouth bass +
    sunfish + catfish; E. coli (BacteriALERT 99407) surges after metro rainfall.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'ch01a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'nr07a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO sites (id, name, watershed, huc12_codes, bbox)
        SELECT gen_random_uuid(), 'Chattahoochee River', 'chattahoochee',
               '[]'::jsonb, CAST(:bbox AS jsonb)
        WHERE NOT EXISTS (SELECT 1 FROM sites WHERE watershed = 'chattahoochee')
    """).bindparams(bbox='{"north":34.65,"south":33.10,"east":-83.55,"west":-84.95}'))

    op.execute("""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            ('chattahoochee_headwaters', 'chattahoochee',
             'Blue Ridge Headwaters', 'Headwaters',
             34.55, -83.65,
             '02331600', 225, FALSE,
             ARRAY['brook_trout','brown_trout','rainbow_trout','redeye_bass','smallmouth_bass']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-04. Blue Ridge headwaters (White/Habersham/Union co., above Lake Lanier) near Helen. Gauge 02331600 (near Cornelia) reports discharge + gage height only (NO water temp).',
             'v0 §1.7 chattahoochee-source-inventory-2026-05-25.md — needs guide review'),
            ('chattahoochee_lanier', 'chattahoochee',
             'Lake Sidney Lanier', 'Lake Lanier',
             34.22, -84.05,
             '02334401', NULL, TRUE,
             ARRAY['striped_bass','spotted_bass','largemouth_bass','crappie','channel_catfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-04. Lake Sidney Lanier (Buford Dam, USACE Mobile District). Warm-water reservoir fishery. Gauge 02334401 (Buford Dam) reports gage height only (NO discharge → flow sub-score degrades).',
             'v0 §1.7 chattahoochee-source-inventory-2026-05-25.md — needs guide review'),
            ('chattahoochee_tailwater', 'chattahoochee',
             'Buford Dam Tailwater', 'Tailwater',
             34.05, -84.25,
             '02334430', 200, FALSE,
             ARRAY['rainbow_trout','brown_trout']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-04. SIGNATURE REACH. Cold-release trout water Buford Dam → Morgan Falls through the Chattahoochee River NRA. Gauge 02334430 reports discharge + water temperature + DO + conductance (FULL Go Score). SAFETY: dam generation raises the river 2–4 ft within minutes — a static USACE-schedule safety banner renders here; the live release feed is Phase B (RiverSignal-c8155522).',
             'v0 §1.7 chattahoochee-source-inventory-2026-05-25.md — needs guide review'),
            ('chattahoochee_metro', 'chattahoochee',
             'Metro Atlanta', 'Metro',
             33.75, -84.60,
             '02336000', 225, TRUE,
             ARRAY['striped_bass','spotted_bass','smallmouth_bass','largemouth_bass','channel_catfish','redbreast_sunfish']::varchar[],
             'needs_guide_review=true; auto-seeded 2026-06-04. Morgan Falls → Whitesburg through metro Atlanta. Gauge 02336000 (Atlanta) reports discharge + water temperature. Urban water-quality nuance: E. coli (BacteriALERT 99407) surges after metro rainfall — feeds the swim-safety panel.',
             'v0 §1.7 chattahoochee-source-inventory-2026-05-25.md — needs guide review')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM silver.river_reaches
        WHERE id IN ('chattahoochee_headwaters','chattahoochee_lanier',
                     'chattahoochee_tailwater','chattahoochee_metro')
    """)
    op.execute("DELETE FROM sites WHERE watershed = 'chattahoochee'")
