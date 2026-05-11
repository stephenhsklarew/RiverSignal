# Design Plan: Metric History, Trends, and Forecasts

**Date**: 2026-05-10
**Status**: DRAFT (pre-collaborative review)
**Refinement Rounds**: 3 (solo)
**Scope**: Turn the derived scores currently shown on `/path/now` (Catch Probability, Hatch Confidence, Health Score, cold-water refuge availability, etc.) from one-shot point-in-time computations into a queryable time series that can drive trend charts and, eventually, forecasts.

> **Note**: this plan reflects a single-author pass and is intentionally opinionated where decisions could be made differently. Sections marked **OPEN FORK** are explicit decision points to work through collaboratively before committing to implementation, mirroring how the trip-share plan resolved 8 forks with the product owner.

## Problem Statement

Today, the metrics surfaced on `/path/now` fall into two groups:

- **Raw or aggregated inputs** (water temperature, flow, dissolved oxygen, monthly river health score, snowpack, harvest counts) — already stored historically in `time_series`, `observations`, and various `gold.*` matviews. We *could* show trend charts on these today; we just don't.
- **Derived scores** (Catch Probability, Hatch Confidence, "Overall Score", cold-water refuge count) — computed live every request from current inputs by `app/routers/ai_features.py` and `app/routers/fishing.py`. There is no historical record. Tomorrow's score replaces today's, with nothing in between persisted.

The product implication: the InfoTooltip on the Catch Probability card tells the user *what the score means* but cannot tell them *whether it's trending up or down, what last weekend looked like, or what the model expects this Saturday*. That's a feature gap users will notice — the "should I fish this weekend?" question hinges on the *trajectory*, not the snapshot.

Two outcomes desired:

1. **Trends** — a sparkline or chart visible from each metric's tooltip showing the last N days of that score. Same surface, more depth.
2. **Forecasts** — short-horizon (3–7 day) projections of where the score is heading, eventually with confidence bands and narrative.

These are sequential: trends need history; forecasts need trend data plus a model. Trends should ship before forecasts.

## Requirements

### Functional

#### F1. Metric snapshotting
1. A scheduled job records the value of every derived metric for every watershed at least once per day. Snapshot records are immutable.
2. The metrics captured at MVP cover: Catch Probability (overall + per-species), Hatch Confidence, "Overall Score" composite, cold-water refuge count, and active-anomaly-flag count. Other metrics can be added without schema change.
3. Each snapshot record carries supporting context (inputs at the time: water_temp, flow, hatch_count, refuge_count) so a future analyst can answer "why was the score that day what it was."
4. Failed snapshot attempts log an error and skip; they do not retry indefinitely. A missed day shows as a gap in the chart rather than a crash.

#### F2. Historical retrieval
5. New endpoint `GET /api/v1/sites/{ws}/metric-history?metric={type}&days={n}` returns the last N days of that metric's snapshots for the watershed, structured for direct chart binding.
6. Per-species history for Catch Probability is supported: `?metric=catch_probability&species=rainbow_trout` returns the rainbow trout time series specifically.
7. History fetches are cacheable on the SWR layer (TTL ~1 hour for "yesterday and back" data; not cached for "today" which is still in flux).

#### F3. Inline trend UI
8. Each InfoTooltip on `/path/now` gains an optional inline sparkline showing the last 30 days of that metric.
9. Hover/tap on the sparkline reveals point-by-point detail.
10. When fewer than 14 days of history exist, the sparkline renders with a "history still accumulating" caption instead.

#### F4. Forecasting (Phase 2 — after trends ship and we have ≥6 weeks of history)
11. Endpoint `GET /api/v1/sites/{ws}/metric-forecast?metric={type}` returns a structured 3–7 day forward projection with point estimates and uncertainty bands.
12. Forecast results are themselves snapshotted (a "what we predicted today for Saturday" record), enabling later **forecast accuracy** comparison against the realized snapshot.
13. UI extends the sparkline to dashed line for forecast portion, with shaded confidence ribbon.

#### F5. Backfill
14. For metrics whose inputs are already historical (catch probability depends on monthly aggregates that go back years), a one-time backfill job can populate snapshots for the past 90–180 days by computing the metric "as of" each historical date.
15. Backfill is opt-in per metric to avoid expensive recomputation for metrics that are not meaningfully retroactively computable.

### Non-Functional

- **Storage**: ≤10 MB / month of snapshot data at MVP scale (7 watersheds × ~50 metric series × 365 days × ~200 bytes/row ≈ 25 MB/year). Trivial.
- **Snapshot job runtime**: full daily job completes in < 5 minutes against production data.
- **History fetch latency**: P95 < 250 ms for a 90-day series.
- **Forecast latency**: P95 < 2 s for simple statistical forecasts; up to 30 s for LLM-narrated ones (deferred to Phase 2 polish).
- **Backwards-compatibility**: existing endpoints (`/catch-probability`, `/hatch-confidence`) continue to return current-snapshot data. The history endpoint is additive.

### Constraints

- Snapshotting must run inside the existing Cloud Run Jobs cron schedule (no new infrastructure).
- Snapshot writes go through SQLAlchemy + the same `pipeline.db` engine, same Postgres instance.
- Schema additions are migration-managed via Alembic.
- Charts use a small dependency (recharts or similar — ~30 KB gzip) rather than a heavyweight library.

## Architecture Decisions

### AD-1: Snapshot vs. retroactive recompute

- **Question**: To get historical metric values, do we **snapshot** computed values daily (eager) or **recompute on demand** from historical inputs (lazy)?
- **Alternatives**:
  - **A1: Snapshot only** — daily job writes computed values. Reads come from snapshot table.
    - Pros: simplest read pattern. One-row-per-day per metric. Stable for charts. Forecast models train on this table directly.
    - Cons: history begins on the day the job turns on. Algorithm changes are not retroactively reflected.
  - **A2: Recompute only** — refactor every scoring function to accept `as_of_date`. Reads call the function for each date in the range.
    - Pros: no snapshot table. Backfill is automatic. Algorithm improvements retroactively improve every chart.
    - Cons: scoring functions must become pure with respect to time. Each chart point is a computation (90 points = 90 computations). Cannot show what we *actually* showed users on a given day if the algorithm has changed since.
  - **A3: Hybrid — snapshot primarily, parametrize for backfill** — daily snapshot writes; scoring functions also accept `as_of_date` so backfill jobs and one-off "what was the score 3 months ago" queries work.
    - Pros: read pattern stays clean (snapshot table); recompute available when needed (backfill, debugging, "what if we changed the algorithm" analysis).
    - Cons: must keep both code paths consistent; risk of drift between live computation and historical recompute.
- **Chosen**: **A3 (hybrid)**.
- **Rationale**: Reads are dominated by chart fetches; those should be cheap and deterministic, which the snapshot table delivers. The parametrization-by-date capability covers backfill, "what was the score last summer" exploratory analysis, and the future "algorithm change comparison" use case. We commit to keeping the live `compute_X()` function and the parameterized `compute_X(at_date)` either identical (trivial case — inputs already are date-keyed) or expressed as a single function with date defaulted to "now."

### AD-2: Single metric_snapshots table vs. typed tables

- **Question**: One wide schema-flex table, or one typed table per metric family?
- **Alternatives**:
  - **B1: Single `metric_snapshots` table** — `metric_type` discriminator column, JSONB `factors`, generic value/level columns.
    - Pros: zero migration cost to add a new metric. Single index, single read pattern. Easy to extend.
    - Cons: typed safety lost — JSONB factor columns can drift across metrics without notice. Cross-metric joins are awkward.
  - **B2: Per-metric tables** — `catch_probability_snapshots`, `hatch_confidence_snapshots`, etc.
    - Pros: strong typing per metric. Joins are natural. Schema-as-contract.
    - Cons: every new metric is a migration. 8+ tables to manage. Read patterns multiply.
  - **B3: Common base + per-metric extension** — shared `metric_snapshots` row + per-metric extension tables joined by id.
    - Pros: typing on the dimension that matters; flex base for common fields.
    - Cons: every read is a join. Complexity.
- **Chosen**: **B1**.
- **Rationale**: At this scale (~25 MB/year total), the storage difference is irrelevant. The dominant force is the cost of adding a new metric type — B2 makes that a 3-step process every time, B1 makes it zero. We accept the JSONB-factor flexibility cost; document the convention; review snapshots monthly in a "metric_type catalog" doc that keeps factor shapes legible. If we ever hit cross-metric joins as a real pattern, B3 is a forward-compatible upgrade.

### AD-3: Snapshot frequency

- **Question**: Daily, hourly, or sub-hourly?
- **Alternatives**:
  - **C1: Daily** — one snapshot per (watershed, metric) per day, at a fixed time (e.g., midnight PT after pipeline + matview refresh).
    - Pros: dirt simple. 7 × 50 = 350 writes/day. Sufficient granularity for trends shown over weeks.
    - Cons: doesn't capture intra-day variation (catch probability *can* shift if water_temp shifts midday). Users won't notice for trend charts.
  - **C2: Hourly** — 24× the writes. Captures conditions intraday.
    - Pros: finer granularity. Possible to plot "today's hourly conditions" once we have it.
    - Cons: 24× the storage. No clear product use today.
  - **C3: Daily + on-change** — daily as baseline; additional snapshot if an underlying input shifts >10% within a day.
    - Pros: catches "the gauge updated mid-day, the score moved" without 24× cost.
    - Cons: trigger detection logic; not clearly worth the complexity.
- **Chosen**: **C1 (daily)**.
- **Rationale**: Charts will show daily resolution either way for trends measured in days/weeks. Hourly granularity is real-time decisional ("flow just spiked, what does it mean") and is already covered by the existing `/conditions/live` endpoint. The two layers serve different questions.

### AD-4: Forecast approach

- **OPEN FORK — this one I want to talk through with you.** Multiple credible approaches, each with different shape and cost. Listed in order of increasing complexity:
  - **D1: No forecast in MVP** — ship trends only; defer forecasts indefinitely.
    - Pros: cheapest. Users get half the value of the feature now, full value can come later.
    - Cons: leaves the trajectory question unanswered, which is the user-facing reason for this entire feature.
  - **D2: Simple statistical** — 7-day exponential smoothing or linear regression on the last N weeks of the metric. Plot dashed-line projection with ±1σ band.
    - Pros: ~1 day to implement. Mathematically conservative. No surprise outputs.
    - Cons: useless for inflection points. A regression on a stable score predicts stability and misses obvious regime changes.
  - **D3: Phenology-aware** — for hatch confidence specifically, project degree-day accumulation forward using NWS 7-day forecast temperatures; predict hatch emergence windows.
    - Pros: actually models the underlying biology. The right answer for hatch confidence specifically.
    - Cons: only applies to hatch confidence. Other metrics still need a different approach.
  - **D4: LLM-narrated** — feed Claude the 30-day history + 7-day weather forecast + current conditions; ask for a structured projection with prose narrative.
    - Pros: handles regime changes contextually. The narrative output ("warming forecast through Thursday should push catch probability up for rainbow trout") is exactly the user value. Reuses existing Anthropic infrastructure.
    - Cons: non-deterministic. Cost (tokens per forecast × snapshots × watersheds). Hallucination risk — model could project things that aren't supported by the inputs.
  - **D5: ML model** — gradient-boosted regressor (LightGBM) trained on snapshot history + weather forecasts predicting next-day score per metric.
    - Pros: best accuracy once trained. Real ML feature for marketing.
    - Cons: requires ≥6 months of snapshot history before it's even trainable. Operational complexity (model versioning, retraining, monitoring). Out of scope for a 3-week implementation.
- **Recommended**: **D1 in Phase 1 (trends only)**, then **D2 + D3 combined in Phase 2**: simple statistical for everything as a baseline, phenology-aware for hatch confidence specifically. Defer D4 (LLM narration) to a Phase 3 polish where the narrative wraps the structured forecast.
- **Reason for the recommendation**: the value-per-effort curve is clear. D1 ships trends; that alone is valuable and validates the snapshot infrastructure. D2+D3 in Phase 2 gives forecasting with low complexity and zero LLM cost — sufficient for the "should I fish this weekend" question. D4 is the future polish that turns numbers into narrative, but it's not the load-bearing piece.
- **Why this is open**: my recommendation is heavily weighted toward shipping incrementally and avoiding ML complexity. If you have stronger product opinions ("the LLM-narrated forecast is THE feature, build that first") the order changes substantially.

### AD-5: UI surface for trends

- **OPEN FORK.**
  - **E1: Sparkline inline in InfoTooltip card** — tapping ⓘ now reveals not just the explanation paragraph but also a small chart of the last 30 days.
    - Pros: same affordance users already know. Zero new navigation surface. Minimal IA change.
    - Cons: tooltip cards are small; sparkline is necessarily small.
  - **E2: Dedicated "History" modal per metric** — separate full-screen view triggered from the info tooltip or from tapping the metric card itself.
    - Pros: full-screen real estate for richer charts, multiple-axis comparison, date range pickers.
    - Cons: extra navigation step. New page to design.
  - **E3: Watershed-level Trends tab** — a `/path/now/trends` route with all metrics for the watershed displayed together as a dashboard.
    - Pros: cross-metric narrative ("flow up, temp up, catch probability down — yes, exactly what we'd expect").
    - Cons: significant UX investment. Risks duplicating /path/now functionality.
- **Recommended**: **E1 for MVP, E2 as a tap-through "see more"**. E3 is its own product surface; out of scope for this plan but possible future direction.
- **Rationale**: the sparkline-in-tooltip pattern is well established (GitHub uses it for contribution charts; financial sites use it everywhere). Users land on a metric card, want to know "is this normal or unusual," and the sparkline answers that without leaving the page. E2 as a "see more" path covers the user who wants to dig in.

### AD-6: Backfill — how far back?

- **OPEN FORK.**
  - **F1: No backfill** — history starts on day-of-launch. Six weeks from launch, you have six weeks of data.
  - **F2: 90-day backfill** — one-time job recomputes the past 90 days of metrics using historical inputs. Sparklines work on day 1.
  - **F3: 1-year backfill** — same but a year of history. Enables seasonal comparison ("how does this October compare to last October").
- **Recommended**: **F2 (90 days)** if the backfill is mechanically straightforward (it is for catch probability, hatch confidence, and most derived metrics — the inputs are already historical). F1 if it turns out to be hard or risky.
- **Rationale**: 90 days is enough for trend charts to be useful from day 1 without launching with an "empty" UI. The compute cost is bounded (7 watersheds × 50 metric_types × 90 days × ~few-ms-per-compute = roughly an hour of CPU one-time). 1-year is more nice-to-have than necessary; can be added later.

## Interface Contracts

### REST endpoints

#### Read
- `GET /api/v1/sites/{ws}/metric-history?metric={type}&species={species}&days={n}` — return historical snapshots.
  - Response:
    ```json
    {
      "watershed": "deschutes",
      "metric_type": "catch_probability",
      "species": "rainbow_trout",
      "snapshots": [
        {"date": "2026-04-12", "value": 75, "level": "good", "factors": {"water_temp_c": 12.4, "hatch_count": 23}},
        ...
      ],
      "fetched_at": "2026-05-10T14:00:00Z"
    }
    ```
  - Auth: none (same as other site endpoints).
  - Caching: 1h dedupe on SWR; server-side `Cache-Control: max-age=3600, stale-while-revalidate=86400`.

#### Forecast (Phase 2)
- `GET /api/v1/sites/{ws}/metric-forecast?metric={type}&species={species}&horizon={days}`
  - Response includes point estimates per day, ±1σ band, optional narrative.

#### Internal/admin (no public exposure)
- `POST /admin/metric-snapshots/run-now?watershed={ws}` — manually trigger snapshot for a watershed (debugging, immediate post-fix).
- `POST /admin/metric-snapshots/backfill?metric={type}&start={date}&end={date}` — one-shot recompute.

### Job interface
- New Cloud Run Job `riversignal-snapshot-metrics`, cron schedule `0 8 * * *` UTC (00:00 PT, after the daily pipeline + matview refresh at ~03:00 PT — gives 5h margin).
- Runs `python -m pipeline.cli snapshot-metrics` which iterates watersheds × metric_types and inserts rows.

### Type contract (Pydantic / TypeScript)

```ts
type MetricSnapshot = {
  date: string             // YYYY-MM-DD
  value: number | null     // numeric value (e.g., 75 for catch probability score)
  level?: string           // optional categorical (excellent|good|fair|poor)
  factors: Record<string, unknown>  // metric-specific supporting data
}

type MetricHistoryResponse = {
  watershed: string
  metric_type: string
  species?: string
  snapshots: MetricSnapshot[]
  fetched_at: string
}
```

## Data Model

### New table

```sql
CREATE TABLE metric_snapshots (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watershed     VARCHAR(32) NOT NULL,
    metric_type   VARCHAR(64) NOT NULL,
    species       VARCHAR(255),
    value         NUMERIC,
    level         VARCHAR(16),
    factors       JSONB NOT NULL DEFAULT '{}'::jsonb,
    snapshot_date DATE NOT NULL,
    snapshot_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Defensive: prevent double-snapshotting the same metric for the same day
    UNIQUE (watershed, metric_type, species, snapshot_date)
);
CREATE INDEX ix_metric_snapshots_lookup
    ON metric_snapshots(watershed, metric_type, snapshot_date DESC);
CREATE INDEX ix_metric_snapshots_species
    ON metric_snapshots(watershed, metric_type, species, snapshot_date DESC)
    WHERE species IS NOT NULL;
```

### Metric type catalog (documentation-as-code)

A `pipeline/metric_catalog.py` module declares each known metric type with its factor schema, refresh frequency, and computation function reference. New metrics added by editing this file (no migration needed since `metric_type` is just a string).

```python
METRICS = {
    "catch_probability": {
        "computer": "app.routers.ai_features.catch_probability",
        "per_species": True,
        "factors_schema": {"water_temp_c": float, "flow_cfs": float, "hatch_count": int, ...},
    },
    "hatch_confidence": {
        "computer": "app.routers.fishing.hatch_confidence",
        "per_species": False,
        "factors_schema": {"degree_days_accumulated": float, "active_insects": int, ...},
    },
    # ...
}
```

### Backwards compatibility

No changes to existing tables. No changes to existing endpoints. Additive only.

## Error Handling

| Class | Examples | Strategy |
|---|---|---|
| Computation failure during snapshot | DB read timeout, metric function raises | log error, skip that (watershed, metric), continue. Missed day = gap in chart. |
| Backfill date range out of bounds | requested start before earliest input data | clamp to earliest available; log a notice; return what we have. |
| History fetch with no data | metric type never snapshotted, or watershed has no rows | return empty `snapshots: []` with 200; UI shows "history still accumulating." |
| Duplicate snapshot attempt | job runs twice for same day | unique constraint catches it; `ON CONFLICT DO NOTHING`. |
| Forecast unavailable | < 14 days of history for that metric | endpoint returns 422 with "insufficient history" reason; UI falls back to "forecast available in N days." |

## Security

- Snapshot table is read-only via public API; writes are server-internal only.
- Admin endpoints require existing auth + an admin role check (we don't currently have admin roles; for now, restrict via service-account-only Cloud Run access OR add a minimal admin-role check on the user).
- Factor JSONB is sanitized: no user-provided strings ever flow into it; only computed numeric/categorical values.

## Test Strategy

### Unit
- `pipeline.metrics.snapshot_one(watershed, metric_type, date)` — produces a row given test inputs; handles missing inputs gracefully.
- Each metric's parametrized-by-date function called with stub data returns deterministic value.
- `metric_catalog` schema validation.

### Integration
- End-to-end: pipeline runs snapshot job against test data → rows inserted → `GET /metric-history` returns expected shape.
- Backfill: with seeded `time_series` data covering 30 days, backfill produces 30 snapshot rows for catch_probability.
- Duplicate snapshot for same day is no-op (unique constraint).

### E2E (Playwright)
- /path/now page, tap on Catch Probability ⓘ → sparkline renders → hover reveals tooltip with value.

## Implementation Plan

### Dependency graph

```
Phase 0 (foundation)
├── Alembic migration: metric_snapshots table
├── metric_catalog.py module
└── snapshot_one() core function + tests

Phase 1 (trends — ship without forecasts)
├── Parametrize each existing scoring function by as_of_date
├── Snapshot job: pipeline.cli snapshot-metrics command
├── Cloud Run Job riversignal-snapshot-metrics + cron schedule
├── Backfill: one-shot 90-day recompute via admin endpoint
├── GET /metric-history endpoint
├── Sparkline component (recharts or hand-rolled D3)
├── Integrate sparkline into InfoTooltip on /path/now
└── "History still accumulating" empty state

Phase 2 (forecasts, after ~6 weeks of accumulated history)
├── Simple statistical forecast endpoint (exp smoothing)
├── Phenology-aware forecast for hatch_confidence
├── Sparkline extension with dashed forecast portion + confidence band
└── Forecast accuracy tracking (snapshot forecasts, compare to realized later)

Phase 3 (polish)
├── LLM-narrated forecast wrapper
├── Per-metric "see more" modal (E2)
└── Cross-metric correlations on the modal
```

### Issue breakdown (suggested HELIX issues)

1. **Migration**: create `metric_snapshots` table + indexes. AC: alembic upgrade head succeeds.
2. **Metric catalog module**: `pipeline/metric_catalog.py` with initial metric type definitions. AC: catalog enumerates all metrics currently shown in InfoTooltips on /path/now; schema is validated at import time.
3. **Parametrize-by-date for scoring functions**: refactor catch_probability, hatch_confidence, and refuge_count computations to accept an optional `as_of_date` parameter. AC: tests pass with both default (now) and historical dates; output identical when called with current date.
4. **Snapshot core + job command**: `pipeline.metrics.snapshot_one()` + `pipeline.cli snapshot-metrics`. AC: running locally against dev DB produces rows; idempotent on same day.
5. **Cloud Run Job + scheduler**: terraform resource for `riversignal-snapshot-metrics` job + Cloud Scheduler cron. AC: job runs nightly, completes in < 5 min.
6. **Backfill endpoint + admin command**: one-shot 90-day recompute. AC: backfill seeds 90 days of catch_probability snapshots; idempotent on re-run.
7. **GET /metric-history endpoint**: query metric_snapshots, return structured JSON. AC: returns last N days for any (watershed, metric_type[, species]) combination; handles "no data" with empty array.
8. **Sparkline component**: small chart accepting `MetricSnapshot[]`. AC: renders 30 points cleanly; hover/tap reveals point detail; gracefully handles fewer than 14 points with "accumulating" message.
9. **InfoTooltip integration**: add sparkline to existing tooltips on /path/now. AC: every tooltip whose `sources` map to a snapshotted metric renders a sparkline; tooltip layout adapts gracefully when sparkline is empty.

Phase 2 issues (forecasts) deferred until after Phase 1 ships and ~6 weeks of history have accumulated. Specifications written closer to that point so we can incorporate what we learn from real users + real data.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Parameterizing scoring functions introduces drift between live and historical compute | M | M | Write the live path as `compute(at_date=date.today())` to use the same code; integration tests assert equality |
| Forecast model produces obviously wrong outputs (e.g., negative scores) that erode trust | M | H | Defer forecasts to Phase 2; ship trends only first; validate forecast against held-out backfill before exposing |
| Snapshot job fails silently, gaps in chart go unnoticed | M | L | Alert on `snapshot_metrics` Cloud Run Job non-zero exit; daily report email to ops |
| Backfill of catch_probability requires monthly aggregates that don't exist for old dates | L | M | Audit `gold.fishing_conditions` coverage before backfill; if gaps exist, document the gap and clamp |
| Storage growth surprises | L | L | At ~25 MB/year, no concern for 5+ years |
| LLM-narrated forecasts (Phase 3) hallucinate trajectory | M | M | Constrain LLM with statistical baseline as input; reject narratives that contradict the numeric forecast |

## Observability

- **Metrics** (PostHog):
  - `metric_history.fetched` (watershed, metric_type, days, days_returned)
  - `metric_sparkline.viewed` (watershed, metric_type)
  - `snapshot_job.completed` (rows_written, duration_seconds, errors_count)
  - Phase 2: `forecast.fetched`, `forecast.accuracy_checked`
- **Alerts**: Cloud Monitoring alert when snapshot job exits non-zero, or if a daily snapshot produces < 80% expected row count (watersheds × metric_types).
- **Logging**: structured JSON; per-metric per-watershed timing in INFO logs.

## Open Forks (for collaborative review)

These are the highest-leverage decisions I'd want to discuss before locking the plan, listed with my current lean:

1. **AD-4 Forecasting approach** — recommend simple statistical + phenology-aware (D2+D3) in Phase 2; LLM narration deferred. The question: how important is forecast narrative versus forecast accuracy? My recommendation prioritizes accuracy; you might prioritize narrative.
2. **AD-5 UI surface** — recommend sparkline-in-tooltip (E1) + see-more modal (E2). The question: do you want trends visible on the page without a tap (always-on sparkline next to the metric value), or behind the existing ⓘ affordance?
3. **AD-6 Backfill depth** — recommend 90 days. Could go zero, 90, or 365. Tradeoff is one-time compute cost vs. day-1 chart quality.
4. **Granularity of "metric"** — Catch Probability is per-species *and* has an overall score. Per-species captures the most nuance but balloons the row count. Worth talking through which species to snapshot or whether to snapshot only the top-N per watershed.
5. **Phase 2 timing** — when do we say there's "enough" history to ship forecasts? I said 6 weeks. Could be 4 weeks or 12 depending on how confident you want statistical baselines to be.

## Governing Artifacts

- **PRD**: `docs/helix/01-frame/prd.md`
- **FEAT-007 Fishing Intelligence**: source of the catch-probability and hatch-confidence metrics this plan stores historically.
- **FEAT-017 Predictive Intelligence**: existing predictions infrastructure (restoration outcome forecasting). Note: this plan does **not** repurpose the existing `predictions` table — that's about restoration-intervention outcomes, a different domain. We add a separate `metric_snapshots` table.
- **Architecture**: `docs/helix/02-design/architecture.md` — adds a "Historical Metrics" subsection in the data tier.
- **Trip-share plan**: `plan-2026-05-10-trip-share.md` — independent feature; no coupling, but both are Saved-screen surfaces and could share UX patterns.

## Refinement Log

- **Round 1** (initial): captured the core idea (snapshot + history endpoint + sparkline), enumerated metrics, sketched table schema.
- **Round 2**: differentiated raw-input metrics (already historical) from derived scores (not historical); resolved AD-1 (hybrid snapshot + recompute); deferred forecasts to Phase 2; added backfill plan.
- **Round 3**: tightened the open-forks section; identified that this plan's `predictions` neighbor is unrelated (restoration domain, not metric trends); added Phase 2/3 sequencing; storage estimate; alert criteria.
