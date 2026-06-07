"""perf: pg_trgm GIN index on gold.species_gallery.taxon_name

Revision ID: mz10a1b2c3d4
Revises: me09a1b2c3d4
Create Date: 2026-06-07 00:00:00.000000

The /sites/<ws>/fishing/hatch-confidence endpoint (the /path/hatch page) resolves
an insect photo per curated hatch row via a correlated subquery:

    SELECT g.photo_url FROM gold.species_gallery g
     WHERE g.taxon_name ILIKE '%'||scientific_name||'%' OR ... LIKE '%'||genus||'%'

With no curated photo_url (every watershed except shenandoah), this runs ~12
full seq scans of gold.species_gallery (155k rows on prod) per request. On the
2-vCPU prod instance that's ~40-56s, so the Hatch page shows "No hatch data"
until it finally loads. EXPLAIN: 59ms seq scan -> 0.44ms bitmap index scan with
a pg_trgm GIN index (~130x). Benefits every watershed, no endpoint logic change.

Robust: CREATE EXTENSION is privilege-guarded (Cloud SQL app users may lack the
cloudsqlsuperuser role) so a missing privilege can never abort the deploy — the
index is created only if pg_trgm is present. The index survives REFRESH
MATERIALIZED VIEW (non-concurrent refresh keeps index definitions).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mz10a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'me09a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm if we can; never fail the migration if the role lacks
    # privilege (we fall back to the existing seq-scan behaviour).
    op.execute("""
        DO $$
        BEGIN
            CREATE EXTENSION IF NOT EXISTS pg_trgm;
        EXCEPTION WHEN insufficient_privilege THEN
            RAISE NOTICE 'pg_trgm requires elevated privilege; trgm index skipped';
        END$$;
    """)
    # Create the trigram GIN index only when pg_trgm is available.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
                CREATE INDEX IF NOT EXISTS ix_species_gallery_taxon_trgm
                    ON gold.species_gallery USING gin (taxon_name gin_trgm_ops);
            END IF;
        END$$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS gold.ix_species_gallery_taxon_trgm")
