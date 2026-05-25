"""seed Shenandoah rockhounding sites (conservative — viewing-only on NPS land)

Revision ID: am38a9b0c1d2
Revises: al37f8a9b0c1
Create Date: 2026-05-25 00:00:00.000000

The Shenandoah source-inventory (shenandoah-source-inventory-2026-05-15.md,
§1.3) flagged `rockhounding_sites` as `✗` requiring manual curation. The
table was never seeded, so DeepTrail's Rock Sites surface for
shenandoah is empty.

Conservative seed — three sites, every one explicitly tagged with the
land-owner + collecting rules. Most Shenandoah-area rock-hunting
folklore points at NPS land (Shenandoah National Park), where
collecting is federally prohibited; those are listed as
land_owner='NPS' with collecting_rules='VIEWING ONLY'.

Idempotent via ON CONFLICT (id) DO NOTHING on a deterministic UUID
(crypto.digest of the site name) — re-runs won't double-insert.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'am38a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'al37f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Resolve the shenandoah site_id at migration time so this works on
    # any environment where shenandoah is configured. If the watershed
    # doesn't exist yet (e.g. a fresh DB without the watershed config),
    # this is a no-op — the seed is shenandoah-specific.
    op.execute("""
        INSERT INTO rockhounding_sites
            (id, name, rock_type, latitude, longitude, location,
             land_owner, collecting_rules, nearest_town, description,
             watersheds, site_id)
        SELECT
            md5(name)::uuid,
            name, rock_type, latitude, longitude,
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326),
            land_owner, collecting_rules, nearest_town, description,
            ARRAY['shenandoah']::text[],
            s.id
        FROM (VALUES
            (
                'Blackrock Springs — Garnet Schist Outcrop',
                'almandine garnet, biotite schist, metamorphic basement',
                38.2335, -78.7592,
                'NPS — Shenandoah National Park',
                'VIEWING ONLY. Collecting is federally prohibited inside Shenandoah NP (36 CFR 2.1). Visit to observe well-known garnet schist exposures along the Blackrock Summit area.',
                'Crozet, VA',
                'Shenandoah NP exposes garnet-bearing pelitic schist along the Blue Ridge crest. Blackrock Summit and adjacent overlooks let visitors see almandine garnet porphyroblasts in outcrop — but every rock stays on the mountain.'
            ),
            (
                'Roses Mill — Unakite (historic locality)',
                'unakite (pink orthoclase + green epidote + quartz)',
                37.7889, -78.9931,
                'Private — permission required',
                'PRIVATE LAND. Surface specimens of unakite (Virginia''s state rock) are known from Roses Mill area river cobbles. Collecting only with documented land-owner permission. Do not collect from road cuts or active quarries.',
                'Amherst, VA',
                'Unakite — a granitic rock named for the Unaka Mountains — outcrops in the Blue Ridge of central Virginia. The Roses Mill area is the type-locality region. Treat as a viewing/educational stop unless you can document permission.'
            ),
            (
                'Tye River — Quartz Crystals (historic locality)',
                'milky quartz, smoky quartz, quartz crystals',
                37.8456, -79.0211,
                'Private / mixed — permission required',
                'PRIVATE LAND in most reaches. River gravel and tributary cuts in the Tye River have historically yielded loose quartz crystals. Do not collect without documented permission from the streambed owner; do not collect in Shenandoah NP or GWNF wilderness sections.',
                'Massies Mill, VA',
                'The Tye River watershed cuts through the Blue Ridge greenstones and granitoids; historic accounts mention loose quartz crystals in gravel bars. Best treated as a knowledge-of locality rather than a collecting destination.'
            )
        ) AS seed(name, rock_type, latitude, longitude, land_owner, collecting_rules, nearest_town, description)
        CROSS JOIN (SELECT id FROM sites WHERE watershed = 'shenandoah' LIMIT 1) s
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM rockhounding_sites
         WHERE 'shenandoah' = ANY(watersheds)
           AND name IN (
             'Blackrock Springs — Garnet Schist Outcrop',
             'Roses Mill — Unakite (historic locality)',
             'Tye River — Quartz Crystals (historic locality)'
           )
    """)
