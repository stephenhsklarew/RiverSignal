---
dun:
  id: ADR-002
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-002: Medallion (bronze/silver/gold) warehouse for unified public-data integration

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-04-10 | Accepted | Founder | FEAT-005, FEAT-006 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | We ingest 30+ heterogeneous public data sources with different schemas, freshness requirements, license terms, and quality levels. Reading them ad-hoc per request is slow, expensive, and impossible to reconcile. |
| Current State | Postgres 17 on Cloud SQL is the chosen relational store. Need a structure that lets us ingest cheaply, normalize incrementally, and serve fast. |
| Requirements | Each source's raw payload must be auditable (data provenance), queries from the API must complete in <500ms, and we must be able to swap individual ingestion adapters without breaking downstream. |

## Decision

We will use the medallion architecture pattern (bronze → silver → gold) within a single Postgres database:

- **Bronze**: raw tables, one row per source record, including original `data_payload` JSONB. Written by adapters; never queried by the API.
- **Silver**: materialized views that clean, deduplicate, and standardize across sources (e.g., `silver.species_observations` unifies iNaturalist + agency surveys + GBIF).
- **Gold**: materialized views that pre-aggregate per-watershed or per-feature snapshots used by the API (e.g., `gold.snowpack_current`, `gold.hatch_chart`).

**Key Points**: One database, three schemas (`public` for bronze, `silver`, `gold`) | Refresh cadence: daily for light gold views, weekly for heavy aggregations, on-demand for ad-hoc | Refresh CONCURRENTLY where unique indexes exist.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Single normalized schema; no medallion | Simpler mental model; one source of truth | Couples ingestion to API schema; every adapter change ripples to the UI; can't preserve raw provenance | Rejected: violates "data has provenance" principle |
| Real-time queries to public APIs (no storage) | Always fresh; no warehouse to maintain | Latency disaster; rate-limit blowups; offline = no data; AI grounding impossible | Rejected: not viable at any scale |
| External tool (BigQuery / dbt / Airflow) | Industry-standard; rich tooling | Extra services to manage; overkill for our scale; adds cost; complicates local dev | Rejected: solo-engineer total-ownership wins over best-in-class tooling at our size |
| **Medallion pattern in Postgres** | Single DB to manage; SQL as the lingua franca; raw + clean + serve all observable | Materialized view refresh cost; manual orchestration via Cloud Run jobs | **Selected: maximum value at minimum operational complexity** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | API queries are fast and predictable; bronze provenance is preserved for audit and re-reconciliation; new ingestion adapters don't break downstream until silver/gold are updated |
| Negative | Materialized view refresh is the bottleneck — heavy gold views can take minutes; adding a new view requires DDL change + refresh registration |
| Neutral | View definitions live in `medallion_views.sql` (source of truth) and are replayed via `pipeline.medallion_ddl`; refresh schedule lives in `pipeline.medallion` |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Materialized view goes stale silently | M | M | Refresh job failures alert; `/status` endpoint shows freshness per view |
| View definition diverges from `medallion_views.sql` (manual DB tweak) | L | M | `medallion_ddl.py` re-runs file as authoritative; PR check |
| Heavy view refresh stalls the daily job | L | M | Split into LIGHT vs HEAVY refresh jobs (already done) |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| API p99 latency < 800ms for warehouse-backed endpoints | Quarterly; investigate if exceeded |
| Daily refresh completes within 2h | Weekly; investigate if exceeded |
| All bronze tables have `source_type` and `data_payload` provenance | Per-PR check; new adapters verified |

## Concern Impact

- **Concern selection**: Selects `medallion-data-warehouse` (data) — see `01-frame/concerns.md`.

## References

- `medallion_views.sql` — source of truth for view definitions
- `pipeline/medallion.py` — refresh orchestration
- `pipeline/medallion_ddl.py` — view DDL replay
- `app/routers/data_status.py` — freshness reporting
