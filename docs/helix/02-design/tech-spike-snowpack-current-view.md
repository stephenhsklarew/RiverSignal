# Technical Spike: gold.snowpack_current materialized view

**Spike ID**: SPIKE-001 | **Lead**: Founder | **Time Budget**: 1 day | **Status**: Completed (2026-05-09)

## Objective

**Technical Question**: Why is the "Snowpack & Mountain Conditions" card not rendering on `/path/now`, and what's the minimal-risk fix?

**Goals**:
- [x] Identify the data path the API is using and confirm the actual source of failure.
- [x] Decide whether to fix at the API, view, or ingestion layer.
- [x] Apply the fix in production without introducing regressions.

**Success Criteria**: The card renders on every watershed page; production data is correct; the fix is captured in source-of-truth medallion definitions.

**Out of Scope**: New ingestion sources for snowpack normals (would unlock `pct_of_normal`); UI polish on the card.

## Hypothesis

**Primary**: The API endpoint queries a gold view that doesn't exist; the SNOTEL bronze data is fine.
**Assumptions**: SNOTEL ingestion is running per cron; the issue is downstream of bronze.
**Expected Outcome**: Add the missing materialized view; populate; card renders.

## Approach

**Method**: Integration debugging — trace the API call → SQL → bronze data path; then write the missing view.

**Activities**:

| Day | Activity | Objective |
|-----|----------|-----------|
| 1 (AM) | Hit each watershed's `/api/v1/sites/{ws}/snowpack` endpoint; log responses | Confirm what the API returns vs expected schema |
| 1 (mid) | grep for `snowpack_current` across the codebase | Find where it's read vs written |
| 1 (PM) | Confirm bronze has SNOTEL data; design the missing view; write DDL; deploy via Cloud Run Job override | Resolve |

## Findings

**FINDING 1**: API endpoint at `app/routers/weather.py:201` queries `gold.snowpack_current`, but this view is never defined anywhere in the codebase.
- **Evidence**: `grep -rn "snowpack_current" --include="*.sql" --include="*.py"` returns only the read site.
- **Implications**: The endpoint's `try/except` silently catches the missing-relation error and returns an empty payload; the frontend gate (`station_count > 0`) fails, hiding the card.

**FINDING 2**: Bronze SNOTEL data is fine.
- **Evidence**: 8.4M rows in `bronze.time_series`; SNOTEL ingestion ran today at 02:00 PT; parameter values include `snow_water_equivalent`, `snow_depth`, `precipitation_cumulative`, `air_temperature` per `pipeline/ingest/snotel.py:16-24`.
- **Implications**: Fix is at the gold layer, not ingestion.

**FINDING 3**: Local `cloud-sql-proxy` cannot reach the production DB.
- **Evidence**: Cloud SQL is private-VPC only (`ipv4_enabled = false`); proxy on a laptop can't dial 10.146.0.3:3307.
- **Implications**: Need to apply the fix from inside the VPC. Options: alembic migration via `riversignal-migrate` Cloud Run Job, or `--args` override on an existing pipeline Cloud Run Job.

### Measurements

| Metric | Before fix | After fix | Notes |
|--------|------------|-----------|--------|
| `/api/v1/sites/skagit/snowpack` station_count | null | 16 | 11 stations with snow |
| `/api/v1/sites/green_river/snowpack` station_count | null | 141 | 65 with snow |
| `/api/v1/sites/mckenzie/snowpack` station_count | null | 15 | 1 with snow (May, melted) |
| Card render on `/path/now/skagit` | hidden | visible | gate now true |

## Analysis

**Hypothesis**: CONFIRMED
**Rationale**: View was never defined; bronze data was always there; adding the view + populating produced the expected card render.

### Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Manual production DDL drifts from `medallion_views.sql` | M | M | Append the same DDL to source-of-truth file; commit |
| Adding to GOLD_LIGHT may slow daily refresh | L | L | View is small (~236 rows); negligible cost |
| Production hot-fix without normal alembic flow sets bad precedent | L | M | Document the technique in `05-deploy/`; reserve for emergency-only paths |

## Conclusions

**Primary Conclusion**: The missing view is the root cause and the fix is a small, well-scoped DDL addition. The Cloud Run Job override pattern (using `gcloud run jobs execute --args=...`) is a viable emergency-fix path for in-VPC database changes when local proxy access is unavailable.

**Confidence**: High
**Limitations**: `pct_of_normal` is null in the new view because we don't yet ingest historical SNOTEL normals. The frontend handles null gracefully, so this is a non-blocker that gets addressed when we add the normals source.

## Recommendations

**RECOMMENDATION**: Adopt the medallion-DDL-via-pipeline-job override as a documented emergency-fix path; add the view to `medallion_views.sql` + `pipeline/medallion.py` GOLD_LIGHT for future-proofing.
- **Rationale**: Local proxy access is unavailable by design (private VPC); this technique avoids the need to expose the DB or run alembic for view-only changes.
- **Next Steps**: (1) Document the override technique in `05-deploy/`; (2) Add a P2 backlog item for ingesting SNOTEL historical normals so `pct_of_normal` populates; (3) Audit `app/routers/weather.py`'s `try/except` to log on missing-relation rather than silently returning empty.
- **Concern Impact**: Reinforces `medallion-data-warehouse` (ADR-002): the pattern of "API queries gold view → view materializes from bronze" works, and the *only* missing piece was the view itself.
