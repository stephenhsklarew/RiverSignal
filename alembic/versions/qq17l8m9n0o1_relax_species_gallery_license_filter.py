"""relax gold.species_gallery photo_license filter so shenandoah rows surface

Revision ID: qq17l8m9n0o1
Revises: pp16k7l8m9n0
Create Date: 2026-05-16 00:00:00.000000

The /sites/<ws>/species endpoint (SitePanel "Species" tab on /riversignal)
returned 0 rows for shenandoah on prod even though there are 437,600 iNat
observations for the watershed and 99.5% of them have a photo URL.

Root cause: the prod iNaturalist adapter writes `photo_url` to
`observations.data_payload` but not `photo_license` (locally 72% of
observations have license; on prod the sample we checked has none).
`gold.species_gallery` requires BOTH:

  WHERE source_type = 'inaturalist'
    AND taxon_name IS NOT NULL
    AND data_payload ->> 'photo_url' IS NOT NULL
    AND data_payload ->> 'photo_license' IS NOT NULL   <-- this killed it

The license field is for attribution UI ("Photo by X, CC-BY-NC"); not
having it shouldn't hide the species entirely. This migration drops the
license predicate. The /sites/<ws>/species endpoint still returns the
license field — frontends already handle null license gracefully (they
just don't render the license badge).

After upgrade, REFRESH MATERIALIZED VIEW gold.species_gallery to backfill
the rows the filter was excluding. Run as REFRESH (not CONCURRENTLY) on
prod under the same caveat tracked in bead RiverSignal-6a76a3ae (no
unique index yet) — but only ~30s lock since species_gallery isn't
that big.

(A follow-on bead should investigate WHY the prod iNat adapter is
dropping license. The fix here is just for the MV.)
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'qq17l8m9n0o1'
down_revision: Union[str, Sequence[str], None] = 'pp16k7l8m9n0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VIEW_SQL = """
CREATE MATERIALIZED VIEW gold.species_gallery AS
 SELECT DISTINCT ON (s.watershed, o.taxon_name)
    o.site_id,
    s.watershed,
    o.taxon_name,
    o.iconic_taxon AS taxonomic_group,
    (o.data_payload ->> 'common_name')          AS common_name,
    (o.data_payload ->> 'photo_url')            AS photo_url,
    (o.data_payload ->> 'photo_license')        AS photo_license,
    (o.data_payload ->> 'user')                 AS observer,
    (o.data_payload ->> 'conservation_status')  AS conservation_status,
    o.quality_grade,
    (o.observed_at)::date AS photo_date
   FROM observations o
   JOIN sites s ON s.id = o.site_id
  WHERE o.source_type = 'inaturalist'
    AND o.taxon_name IS NOT NULL
    AND (o.data_payload ->> 'photo_url') IS NOT NULL
  ORDER BY s.watershed, o.taxon_name,
           CASE WHEN o.quality_grade = 'research' THEN 0 ELSE 1 END,
           o.observed_at DESC
"""


HATCH_CHART_SQL = """
CREATE MATERIALIZED VIEW gold.hatch_chart AS
 SELECT site_id, watershed, taxon_name, common_name, obs_month,
    count(*) AS observation_count,
    count(DISTINCT obs_year) AS years_observed,
    rank() OVER (PARTITION BY site_id, taxon_name ORDER BY count(*) DESC) AS month_rank,
    CASE WHEN rank() OVER (PARTITION BY site_id, taxon_name ORDER BY count(*) DESC) <= 2
         THEN 'peak' ELSE 'present' END AS activity_level,
    (SELECT g.photo_url FROM gold.species_gallery g
      WHERE g.taxon_name = o.taxon_name AND g.watershed = o.watershed LIMIT 1) AS photo_url
   FROM silver.species_observations o
  WHERE taxonomic_group = 'Insecta'
    AND taxon_name IS NOT NULL
    AND taxon_rank IN ('species','genus','subfamily')
  GROUP BY site_id, watershed, taxon_name, common_name, obs_month
 HAVING count(*) >= 3
"""

SPECIES_BY_RIVER_MILE_SQL = """
CREATE MATERIALIZED VIEW gold.species_by_river_mile AS
WITH named_rivers AS (
  SELECT DISTINCT river_name FROM gold.river_miles
   WHERE river_name IS NOT NULL AND length_km > 0.5
), river_obs AS (
  SELECT rm.watershed, rm.river_name,
    (floor(rm.segment_start_mile / 5) * 5)::integer       AS mile_section_start,
    ((floor(rm.segment_start_mile / 5) * 5) + 5)::integer AS mile_section_end,
    o.taxon_name, o.iconic_taxon,
    (o.data_payload ->> 'common_name') AS common_name,
    o.observed_at, o.quality_grade
   FROM gold.river_miles rm
   JOIN named_rivers nr ON nr.river_name = rm.river_name
   JOIN observations o  ON ST_DWithin(o.location, rm.flowline, 0.005)
  WHERE o.taxon_name IS NOT NULL AND o.source_type = 'inaturalist'
)
SELECT watershed, river_name, mile_section_start, mile_section_end,
    taxon_name, common_name, iconic_taxon AS taxonomic_group,
    count(*) AS observation_count,
    count(CASE WHEN quality_grade = 'research' THEN 1 END) AS research_grade_count,
    min(observed_at)::date AS first_seen,
    max(observed_at)::date AS last_seen,
    (SELECT g.photo_url FROM gold.species_gallery g
      WHERE g.taxon_name = ro.taxon_name AND g.watershed = ro.watershed LIMIT 1) AS photo_url
FROM river_obs ro
GROUP BY watershed, river_name, mile_section_start, mile_section_end, taxon_name, common_name, iconic_taxon
HAVING count(*) >= 2
"""


def upgrade() -> None:
    # CASCADE drop kills hatch_chart and species_by_river_mile too —
    # recreate them right after so the gold layer stays whole.
    op.execute("DROP MATERIALIZED VIEW IF EXISTS gold.species_gallery CASCADE")
    op.execute(NEW_VIEW_SQL)
    op.execute("CREATE INDEX ix_species_gallery_watershed ON gold.species_gallery (watershed)")
    op.execute("CREATE INDEX ix_species_gallery_taxon ON gold.species_gallery (taxon_name)")
    op.execute("CREATE INDEX ix_species_gallery_taxgroup ON gold.species_gallery (taxonomic_group)")

    op.execute(HATCH_CHART_SQL)
    op.execute("CREATE INDEX ix_hatch_chart_watershed ON gold.hatch_chart (watershed)")
    op.execute("CREATE INDEX ix_hatch_chart_taxon ON gold.hatch_chart (taxon_name)")

    op.execute(SPECIES_BY_RIVER_MILE_SQL)
    op.execute("CREATE INDEX ix_sbrm_watershed ON gold.species_by_river_mile (watershed)")
    op.execute("CREATE INDEX ix_sbrm_river ON gold.species_by_river_mile (river_name)")


def downgrade() -> None:
    # No-op: the prior MV definition has the over-strict license filter
    # that hid shenandoah's 13k species. Running this migration's
    # upgrade() on already-relaxed data is harmless.
    pass
