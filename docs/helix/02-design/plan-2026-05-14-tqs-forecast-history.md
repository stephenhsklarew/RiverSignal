# Design Plan: TQS Forecast — History, Backcast, and Forecast Modal

**Date**: 2026-05-14
**Status**: CONVERGED (post-collaborative review)
**Refinement Rounds**: 3 + 6 collaborative forks resolved with product owner

## Collaborative Review Outcomes (2026-05-14)

Six forks worked through with the product owner:

| Fork | Decision | Key implication |
|---|---|---|
| OF-1 Endpoint shape | Single endpoint returns all 14 days at once | One SWR cache key; ~14 KB payload; trivial server cost |
| OF-2 Carousel | CSS `scroll-snap`, swipe + tap-pagination-dot nav | Zero dependencies; native momentum; mobile-native feel |
| OF-3 Confidence | Bucketed labels (High/Medium/Low) + border treatment | Today's card gets "Today" badge instead of confidence chip |
| OF-4 Backfill start | 2021-01-01 (year-aligned) | 5 complete calendar years + partial 2026; clean seasonal cycles for future ML |
| OF-5 Unrecognized reaches | Drop, log counter in post-flight report | Backfill is bounded to current `sites` table; gaps surfaced for review |
| OF-6 ML phase | Separate lightweight readiness doc to follow | This plan ends at rule-based forecast UI; ML decisions await real data |

**Scope**: Extend the Trip Quality Score (TQS) feature with (a) a 5-year backfill of all feasible raw input sources, (b) a backcast of historical TQS sub-scores using current scoring logic against the backfilled inputs, (c) sub-score history capture going forward, and (d) a user-facing forecast modal accessed from `TripQualityCard` that shows expected TQS over the next 14 days with swipeable day cards.

> Sections marked **OPEN FORK** are decision points to work through collaboratively, mirroring earlier HELIX plans.

## Problem Statement

The Trip Quality Score is the headline metric users see on `/path/now`. Today it answers "is today good for fishing?" but not "will tomorrow be better?" or "what's the rest of the week look like?" — even though the underlying scoring pipeline (`pipeline/predictions/trip_quality.py`) already accepts a `target_date` parameter and writes forecast rows at multiple horizons into `gold.trip_quality_daily`.

Three gaps prevent us from turning that capability into product:

1. **Forecast data isn't surfaced.** The frontend `TripQualityCard` shows only today's TQS. The forecast rows exist but aren't queried or rendered.
2. **Sub-score history isn't preserved.** `gold.trip_quality_history` records only `(reach_id, target_date, snapshot_date, tqs, confidence)` — not the six sub-scores (catch / water_temp / flow / weather / hatch / access). That means a future ML model has the composite to train against, but can't decompose "why did the score move." It also means analysts can't ask "how often does high hatch_score correlate with high tqs."
3. **Historical inputs only go back ~2 years.** The USGS adapter defaults to 2 years on first sync; iNaturalist, SNOTEL, PRISM, and others use similar windows. We don't have enough history for proper predictive modeling (a regressor wants 3+ seasonal cycles minimum; ideally 5+ years).

Desired outcomes:

- A user opening `/path/now/<watershed>` taps a "Forecast" button on `TripQualityCard` → modal opens → swipeable day cards show TQS forecast for today + 13 days ahead, each with TQS value, confidence indicator, primary-factor reasoning, and supporting weather (incl. wind).
- A 5-year history of raw inputs in the database, accessible for both retrospective analysis and ML training data.
- Backcast sub-scores for the past 5 years, so today's scoring logic has a synthetic-but-internally-consistent historical record.
- Sub-score history going forward (real, not synthetic) so the next 6 months of operational data is decomposable.
- Foundation for a true ML-driven forecast model in a follow-up plan.

## Requirements

### Functional

#### F1. Raw-input backfill (5 years)
1. **USGS gauge data** (`time_series`): extend ingestion to pull water_temperature, discharge, and dissolved_oxygen daily values for the past 5 years for every watershed bbox. Idempotent on re-run.
2. **iNaturalist observations**: extend ingestion to 5 years for every watershed. Honour iNat's rate limit (1 req/s).
3. **SNOTEL snowpack**: 5 years for all stations within each watershed bbox.
4. **PRISM climate**: 5 years of daily gridded climate (temp_max, temp_min, precip) per watershed centroid.
5. **NWS daily observations** (`pipeline/ingest/nws_observations.py`): 5 years of station observations for every watershed-relevant NOAA station. Coverage will be patchy in older years; record what's available, document gaps.
6. **State stocking history**:
   - **ODFW**: skip — only 12-week schedule is publicly available; older history would need a PR request.
   - **UDWR**: extend `years` range in `_ingest_udwr_stocking` from `current-2..current` to `current-5..current`.
   - **WDFW**: extend the Socrata `where` clause to remove year cap (or expand to 5 years).
7. **MTBS fire perimeters**: ensure full historical extent is pulled (already a static layer; verify).
8. Run all backfill adapters as a single Cloud Run Job (`riversignal-backfill-5y`) that runs unattended for ~24 hours and writes telemetry per source.

#### F2. Backcast TQS sub-scores
9. After F1 completes, run `pipeline.predictions.trip_quality.compute_for_date(reach_id, target_date)` for every (reach, date) tuple over the 5-year window. Each call writes one row to `gold.trip_quality_daily` (current snapshot) AND one row to `gold.trip_quality_history` with `snapshot_date = target_date` (i.e., as-of-actual).
10. Backcast rows are tagged with `forecast_source = 'backcast'` so they're distinguishable from real-time forecasts and future ML predictions.
11. Backcast is idempotent — re-running for the same (reach, target_date) updates the row in place.
12. Total: ~30 reaches × ~1825 days = ~55k compute calls. At ~50ms per compute, ~45 min wall-clock.

#### F3. Sub-score history capture (going forward)
13. Extend `gold.trip_quality_history` schema to include all six sub-scores plus `forecast_source` and `horizon_days`. Existing rows backfilled with NULL sub-scores (which is fine — they'll just be sparse historical points).
14. The hourly scoring job writes the full row (composite + sub-scores) into history on every snapshot.
15. The `(reach_id, target_date, snapshot_date)` primary key remains; replace-on-conflict semantics preserved.

#### F4. Forecast modal UI
16. New "Forecast" button on `TripQualityCard` next to the existing score display.
17. Tapping opens a full-screen modal (mobile-native, slide-up from bottom).
18. Modal shows day cards in a horizontal swipeable carousel: today, +1, +2, ..., +13 (14 cards total).
19. Each card displays:
    - Date (e.g., "Thu, May 16")
    - TQS value (large, color-coded by band: Excellent/Good/Fair/Poor)
    - Confidence indicator (narrowing rays for tomorrow, widening for day +13)
    - Primary factor (e.g., "Strong hatch activity expected")
    - Supporting metrics chip row: water temp, flow, weather (with wind callout if notable)
    - Sub-score bar chart (catch / water_temp / flow / weather / hatch / access)
20. Swipe-left advances to next day; swipe-right goes back. Pagination dots at bottom.
21. "Day 0" (today) shows actual same as `TripQualityCard`.
22. Days with no forecast (e.g., beyond NWS 7-day horizon) show climatological fallback with an "Approximate" badge.
23. A small "Why this score?" link opens an expandable explanation drawn from the primary_factor + sub-score breakdown.
24. Forecast endpoint: `GET /api/v1/sites/{ws}/trip-quality/forecast?days=14` returns the array of day cards.

#### F5. Wind exposure on day cards
25. Each day card surfaces wind separately in the weather chip when it's a notable factor (≥10 mph average, ≥25 mph gusts, or upstream-direction at any speed).
26. The "Why this score?" drawer breaks weather_score into its components (temp, precip, wind speed, wind direction, thunderstorm) — already computable from the existing `weather_score()` function; just needs to return the breakdown alongside the final value.

#### F6. Future ML model foundation (out of scope for this plan, but prepared)
27. The backfilled raw inputs + backcast sub-scores + ongoing real-time sub-scores form a labeled dataset suitable for training a gradient-boosted regressor (or similar) that predicts TQS from inputs. Separate plan to follow.
28. Captured input snapshots become the model features; user-reported `TripFeedbackPrompt` ratings become the supervised target.

### Non-Functional

- **Backfill duration**: complete within 48 hours of kickoff. Single Cloud Run Job; restart-safe.
- **Backcast duration**: complete within 1 hour after backfill finishes. Single job.
- **Forecast modal time-to-first-render**: < 200ms with cached endpoint response; < 1.5s cold.
- **Forecast endpoint latency**: P95 < 250ms.
- **Storage**: 5-year backfill is the dominant footprint — estimate ~2GB total across all sources. Trivial for our Postgres instance.
- **Backwards compatibility**: extending `trip_quality_history` with new columns is additive; existing queries unaffected.

### Constraints

- Single Cloud Run + Postgres + Cloud Run Jobs stack — no new infrastructure.
- All adapters need a `--from-date YYYY-MM-DD` flag (or a new `--backfill-years N` flag) to override their default lookback.
- iNat rate limit (1 req/s) is hard; cannot parallelize.
- NWS forecast data **cannot** be backfilled — they don't publish a forecast archive. Backcast uses NWS *observations* (the actuals that happened) rather than forecasts that would have been issued.

## Architecture Decisions

### AD-1: Backfill via a one-shot Cloud Run Job vs. extending the existing cron

- **Question**: Run the 5-year backfill once as a dedicated job, or update the existing weekly/monthly crons to extend their lookback?
- **Chosen**: **One-shot Cloud Run Job** (`riversignal-backfill-5y`) with explicit `--from-date 2021-05-14` per adapter.
- **Rationale**: Bounded operation. Crons should not surprise you with a 24h run. New job is intent-revealing (its name says "backfill"). Once complete, it never runs again — we can leave it in terraform with `min_instance_count: 0` or simply delete it.

### AD-2: Backcast forecast_source value

- **Question**: How do we distinguish backcast rows from real-time forecasts and future ML predictions in `trip_quality_history`?
- **Chosen**: New string value for `forecast_source` column: `'backcast'`. Existing values (likely `'rule_based'`, `'nws'`, etc.) stay; future ML values can be `'ml_v1'`, etc.
- **Rationale**: Single column already exists for this purpose. No schema change. Backcast rows are unambiguously identified for downstream queries (e.g., "exclude backcast when computing forecast accuracy").

### AD-3: Sub-score history — extend existing table vs. new metric_snapshots integration

- **Question**: Add columns to `trip_quality_history`, or fold this into the broader `metric_snapshots` table from the metric-history plan?
- **Alternatives**:
  - **A1: Add columns to `trip_quality_history`** — `catch_score`, `water_temp_score`, `flow_score`, `weather_score`, `hatch_score`, `access_score`, `horizon_days`, `forecast_source`. Existing rows nullable.
    - Pros: minimal change; reads stay efficient; tight cohesion with composite TQS.
    - Cons: doesn't generalize to other metrics (hatch confidence, etc.).
  - **A2: Use `metric_snapshots` from metric-history plan** — each sub-score is its own `metric_type`.
    - Pros: uniform model across all metrics; supports the broader trends/sparkline UI.
    - Cons: queries for "all 6 sub-scores at one date" become an aggregation; loses the per-reach decomposition cleanliness; depends on metric-history Phase 1 shipping.
- **Chosen**: **A1 for now** (extend `trip_quality_history`), and **also write to `metric_snapshots`** once that table exists. Belt-and-braces dual write for the next ~6 months; once `metric_snapshots` is the single source of truth, the additional columns on `trip_quality_history` can be deprecated.
- **Rationale**: Don't block this plan on the metric-history plan. Capture sub-score history *now* in the simplest way, and double-write later if/when `metric_snapshots` lands.

### AD-4: Forecast endpoint shape

- **OPEN FORK (OF-1).**
- **Question**: One endpoint returning all 14 days, or paginated/streamed?
- **Alternatives**:
  - **B1: One endpoint, all 14 days at once**. Frontend renders all cards lazily but data is already there.
  - **B2: Endpoint per day** (`?day=offset`). Cleaner caching per-day; more HTTP calls.
  - **B3: First 3 days eager, days 4–13 lazy** (separate request fired on swipe).
- **My recommendation**: **B1** — 14 day cards × maybe 1KB JSON each = ~14KB total. Cacheable, simple, fast.

### AD-5: Forecast modal — UI library or hand-rolled?

- **OPEN FORK (OF-2).**
- **Question**: For the swipeable carousel, do we add a touch-gesture library or hand-roll with CSS scroll-snap?
- **Alternatives**:
  - **C1: CSS `scroll-snap-type: x mandatory`** — native horizontal scroll with snap-to-card. No JS library. Mobile-native feel.
  - **C2: Add `embla-carousel` or similar** — robust gesture handling, pagination dots, programmatic API for arrow buttons.
  - **C3: Hand-rolled with framer-motion or react-swipeable** — between C1 and C2 in complexity.
- **My recommendation**: **C1 (CSS scroll-snap)** for MVP. Adds zero dependencies, behaves natively on mobile (momentum, fling), pagination-dot indicator is a CSS-tracked active state. If we hit ergonomic issues (e.g., user requests "jump to day 7" button), upgrade to C2.

### AD-6: Confidence visualization

- **OPEN FORK (OF-3).**
- **Question**: How to show forecast confidence on each day card?
- **Options**: Numeric "65% confidence", narrowing/widening visual band, simple icon (✓✓ for high, ✓ for medium, ~ for low), or omit on near-term days where confidence is trivially high.
- **My recommendation**: **Numeric band + visual chip** — "Confidence: High" / "Medium" / "Low" pulled from a simple bucketing of the existing `confidence` column.

### AD-7: Backfill failure handling

- The backfill job is long-running and any single source failure should not kill the whole run.
- Each adapter writes its own log line: `BACKFILL: <source> <watershed> <start_date>..<end_date> <records_inserted>` or `BACKFILL: <source> FAILED: <reason>`.
- After the job, a post-flight script summarizes coverage by source × watershed × year and writes a markdown report to GCS.
- Re-running the job is idempotent: each adapter checks for existing rows and only inserts gaps.

## Interface Contracts

### REST endpoint

```
GET /api/v1/sites/{watershed}/trip-quality/forecast?days=14
  Auth: none (same as other sites endpoints)
  Returns: {
    watershed: string,
    generated_at: iso8601,
    days: [
      {
        target_date: 'YYYY-MM-DD',
        offset_days: number,         // 0 = today
        tqs: number | null,
        confidence: 'high'|'medium'|'low'|null,
        confidence_pct: number | null,
        band: 'excellent'|'good'|'fair'|'poor'|null,
        primary_factor: string | null,
        sub_scores: {
          catch: number, water_temp: number, flow: number,
          weather: number, hatch: number, access: number
        } | null,
        weather: {
          temp_high_f: number | null,
          temp_low_f: number | null,
          precip_in: number | null,
          wind_mph: number | null,
          wind_direction: string | null,    // "WSW", etc.
          wind_against_flow: boolean | null,
          gust_mph: number | null,
          thunderstorm: boolean | null,
          conditions_summary: string | null
        } | null,
        forecast_source: 'realtime' | 'nws' | 'climatological' | 'backcast',
        is_climatological: boolean,
        is_actual: boolean          // true for today (== day-of)
      }, ...
    ]
  }
```

### Type contract (TS)

```ts
type ForecastDay = {
  target_date: string
  offset_days: number
  tqs: number | null
  confidence: 'high' | 'medium' | 'low' | null
  confidence_pct: number | null
  band: 'excellent' | 'good' | 'fair' | 'poor' | null
  primary_factor: string | null
  sub_scores: SubScores | null
  weather: WeatherSummary | null
  forecast_source: 'realtime' | 'nws' | 'climatological' | 'backcast'
  is_climatological: boolean
  is_actual: boolean
}

type SubScores = {
  catch: number; water_temp: number; flow: number
  weather: number; hatch: number; access: number
}

type WeatherSummary = {
  temp_high_f: number | null
  temp_low_f: number | null
  precip_in: number | null
  wind_mph: number | null
  wind_direction: string | null
  wind_against_flow: boolean | null
  gust_mph: number | null
  thunderstorm: boolean | null
  conditions_summary: string | null
}
```

### Component contract

```tsx
<TripQualityCard watershed={watershed} />
// Existing card. Adds a "View 14-day Forecast" button.

<TripQualityForecastModal
  watershed={watershed}
  open={boolean}
  onClose={() => void}
  initialOffset={0}    // default: today
/>
// New modal. Fetches via useSWR. Renders 14 day cards in a swipeable carousel.
```

## Data Model

### Schema changes

```sql
-- Extend trip_quality_history with sub-scores and forecast metadata.
ALTER TABLE gold.trip_quality_history
  ADD COLUMN IF NOT EXISTS catch_score      integer,
  ADD COLUMN IF NOT EXISTS water_temp_score integer,
  ADD COLUMN IF NOT EXISTS flow_score       integer,
  ADD COLUMN IF NOT EXISTS weather_score    integer,
  ADD COLUMN IF NOT EXISTS hatch_score      integer,
  ADD COLUMN IF NOT EXISTS access_score     integer,
  ADD COLUMN IF NOT EXISTS forecast_source  text,
  ADD COLUMN IF NOT EXISTS horizon_days     integer,
  ADD COLUMN IF NOT EXISTS primary_factor   text;
```

No new tables. All extensions are additive and nullable.

### Backfill / backcast write pattern

- Backfill writes to existing tables: `time_series`, `observations`, `interventions`, `wa_fish_stocking`. Idempotent on conflict.
- Backcast writes to `gold.trip_quality_daily` (UPSERT) and `gold.trip_quality_history` (UPSERT) with `forecast_source = 'backcast'`.

## Error Handling

| Class | Examples | Strategy |
|---|---|---|
| Adapter rate-limit (iNat 429) | Hit during backfill | Honour Retry-After; resume from last-successful page |
| Adapter timeout (USGS 5xx) | Long backfill request times out | Reduce date chunk size to 6 months; retry up to 3x |
| Backcast on missing inputs | iNat data sparse for early dates | Sub-score returns neutral default (50); record with low confidence |
| Forecast endpoint with no data | Watershed has no trip_quality_daily rows | Return `days: []` with 200; UI shows empty state |
| Modal swipe to day beyond forecast horizon | User swipes to day 13 but NWS only covers 7 days | Day card displays climatological estimate + "Approximate" badge; forecast_source = 'climatological' |
| Backcast logic differs from real-time scoring | Drift between today's `compute_for_date` and what was scored historically | Document explicitly; backcast is "what we'd say *now* about that day" — not historical truth |

## Security

- Backfill job runs with the existing pipeline service account; same DB write permissions as production crons.
- Forecast endpoint has no PII; cacheable publicly.
- Modal data doesn't expose any new sensitive info — same metrics already shown on the card.

## Test Strategy

### Unit
- `weather_score()` with various wind/temp/precip combinations — verify wind penalties trigger correctly.
- Backcast `compute_for_date()` with mocked inputs returns expected sub-scores.
- Forecast endpoint: given fixture `trip_quality_daily` rows, returns correct shape.

### Integration
- Backfill dry-run: run with `--limit 100` to verify shape, then real run.
- Idempotency: backfill twice → no duplicate rows.
- End-to-end: backfill → backcast → forecast endpoint returns 14 days → UI renders.

### Manual / E2E
- Open `/path/now/deschutes`, tap "View 14-day Forecast", verify modal opens, swipe through all 14 days, verify each shows valid data.
- Verify wind callout appears when conditions warrant.
- Verify "Approximate" badge appears on days 8–13.

## Implementation Plan

### Dependency graph

```
Phase 0 — Adapter backfill mode (1–2 days dev)
├── Add --from-date / --backfill-years CLI args to each adapter:
│   USGS, iNat, SNOTEL, PRISM, NWS observations, UDWR, WDFW, MTBS
├── Each adapter respects the flag, ignores its built-in lookback when set
└── Bulk-insert optimization where applicable (USGS especially)

Phase 1 — Backfill execution (~24h wall clock, unattended)
├── New Cloud Run Job: riversignal-backfill-5y
├── Args: runs each adapter with --from-date 2021-05-14 sequentially
├── Per-source logging + post-flight summary
└── Verification: spot-check row counts per source per year

Phase 2 — Schema extension (Alembic migration)
├── ALTER trip_quality_history (add sub-score columns)
├── Update existing trip_quality scoring writer to populate the new columns
└── Migration runs in standard deploy pipeline

Phase 3 — Backcast execution (~1h)
├── Cloud Run Job: riversignal-tqs-backcast
├── For each reach × each date in 2021-05-14..today:
│   call compute_for_date(reach, target_date) with forecast_source='backcast'
└── Idempotent on re-run

Phase 4 — Forecast endpoint
├── GET /api/v1/sites/{ws}/trip-quality/forecast?days=14
├── Reads from gold.trip_quality_daily where target_date >= today
├── Joins with NWS daily observations table for weather context
└── Computes confidence buckets, sub-score normalization

Phase 5 — Forecast modal UI
├── TripQualityForecastModal component (CSS scroll-snap carousel)
├── Day card sub-component
├── "View 14-day Forecast" button on TripQualityCard
├── useSWR fetch from the new endpoint
└── Pagination dots, "Why this score?" expandable

Phase 6 — Polish + observability
├── PostHog events (forecast_opened, forecast_swiped, forecast_day_viewed)
├── Loading skeletons, error states
├── Print stylesheet (export plan via "Save" / share)
└── Wind callout polish on day cards
```

### Suggested HELIX issues

1. **Adapter backfill flags**: add `--from-date` to USGS, iNat, SNOTEL, PRISM, NWS observations, UDWR, WDFW. AC: each adapter respects flag without regressing default behaviour; integration test for each.
2. **`riversignal-backfill-5y` Cloud Run Job**: terraform resource + script that invokes each adapter sequentially with `--from-date 2021-05-14`. AC: runs end-to-end on staging; post-flight coverage report.
3. **Schema migration**: extend `gold.trip_quality_history`. AC: alembic upgrade head succeeds; existing rows unchanged; scoring writer populates new columns.
4. **Backcast job**: `pipeline/scripts/tqs_backcast.py` + cloud-run-job. AC: 30 reaches × 1825 days completes < 1h; rows tagged `forecast_source='backcast'`.
5. **Forecast endpoint**: `GET /trip-quality/forecast`. AC: returns 14 days with correct shape; P95 < 250ms.
6. **Forecast modal component**: scroll-snap carousel + day card. AC: 14-day swipe works on iOS Safari + Android Chrome; pagination dots track active day.
7. **TripQualityCard button**: triggers modal. AC: button visible on card; modal opens on tap; closes on swipe-down or back-button.
8. **Wind callout**: weather chip surfaces wind when notable. AC: ≥10 mph or upstream direction triggers visible callout; not shown otherwise.
9. **"Why this score?" drawer**: sub-score bar chart + primary-factor explanation. AC: expandable section per day; shows all six sub-scores with values.
10. **PostHog instrumentation**: forecast_opened / forecast_swiped / forecast_day_viewed events. AC: events fire correctly; dashboards configured.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| iNat backfill takes longer than 24h | M | L | Run in background; tolerate multi-day completion; pin SLO at 72h |
| USGS adapter chokes on 5-year bbox query | M | M | Chunk by 6-month windows; retry on timeout |
| Sub-score backcast drift from real-time scoring as code evolves | M | M | Document explicitly that backcast is "as-of-current-logic"; if scoring changes materially, re-run backcast |
| Forecast UI feels sluggish with 14 day cards | L | L | Lazy-render off-screen cards; CSS contain-intrinsic-size |
| NWS forecast horizon (~7 days) shorter than 14-day target | H | M | Day cards 8–13 use climatological norm + "Approximate" badge; document the cliff |
| Storage growth from 5-year input data | L | L | Estimate ~2GB; trivial for current Postgres instance |
| Backcast logic introduces a bug that pollutes history | L | M | Backcast is identifiable via forecast_source='backcast'; delete-and-rerun is a single SQL statement |

## Observability

- **Backfill log lines** in Cloud Logging: source, watershed, start_date, end_date, records_inserted, duration, errors. Post-flight summary to GCS bucket as markdown.
- **Backcast log lines**: reach_id, target_date, sub_scores, duration. Aggregated count by year for spot-check.
- **PostHog**: forecast_opened (watershed, current_tqs), forecast_swiped (from_day, to_day), forecast_day_viewed (offset_days, tqs, band).
- **Cloud Monitoring**: alert on backfill job > 48h runtime.

## Open Forks

1. **OF-1 Forecast endpoint shape**: one endpoint (B1) vs. paginated (B2/B3). Lean: B1.
2. **OF-2 Carousel implementation**: CSS scroll-snap (C1) vs. embla-carousel (C2). Lean: C1.
3. **OF-3 Confidence visualization**: bucket labels, numeric percent, visual band, or omit on near-term. Lean: bucketed text.
4. **OF-4 Backfill start date**: exact "5 years ago from today" (2021-05-14) or rounded to nearest year start (2021-01-01)? Lean: rounded so seasonal cycles align cleanly.
5. **OF-5 What about reaches not present in current `sites` table?** Some historical USGS stations may belong to reaches we don't currently track. Drop them, or expand `sites`? Lean: drop for now; revisit if a new reach is requested.
6. **OF-6 ML model phase**: write a follow-up plan or scope into this one? Lean: separate plan after we have 6 months of operational sub-score history to combine with the 5-year backcast.

## Governing Artifacts

- **FEAT-007 Fishing Intelligence**: source feature for TQS.
- **FEAT-017 Predictive Intelligence**: predictions infrastructure context.
- **plan-2026-05-10-metric-history.md**: complementary plan; sub-score history could eventually integrate with `metric_snapshots`.
- **plan-2026-05-14-push-notifications.md**: depends on this plan's forecast values for "watched watershed crossing threshold" alerts.
- **`pipeline/predictions/trip_quality.py`**: contains current scoring logic; backcast and going-forward writes both call its `compute_for_date()` function.
- **`gold.trip_quality_daily`, `gold.trip_quality_history`**: the gold tables being extended.

## Refinement Log

- **Round 1** (initial draft): identified the four work tracks (backfill, schema extension, backcast, forecast UI), sketched modal, captured wind.
- **Round 2**: enumerated source-by-source backfill feasibility; identified NWS-forecast-archive gap; resolved backcast tagging (forecast_source='backcast'); proposed scroll-snap carousel.
- **Round 3**: tightened sequencing (Phase 0 → 1 → 2 → 3); added "Approximate" badge logic for days beyond NWS horizon; documented backcast-drift risk; added 10 issue breakdown.
