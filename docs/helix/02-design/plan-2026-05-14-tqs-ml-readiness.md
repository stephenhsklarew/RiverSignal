# Design Note: TQS ML Readiness Checklist

**Date**: 2026-05-14
**Status**: READINESS CHECKLIST (not an active design plan)
**Companion to**: `plan-2026-05-14-tqs-forecast-history.md`
**Scope**: Captures the prerequisites and decisions needed before we can responsibly start an ML-driven TQS forecasting model. Deliberately not a full design plan — that comes later, when the prerequisites are met.

## Purpose

The TQS forecast history plan (Phases 0–6) sets up the data foundation for ML but explicitly ends at rule-based forecasts. This document records *what we'll need before we can take the next step*, so future-us doesn't re-derive these decisions cold.

Goal of the eventual ML model: predict TQS values for the next 7–14 days at confidence levels that meaningfully beat the current rule-based scorer on held-out data, evaluated against either actual same-day TQS (computed from observed inputs) or user-reported trip outcomes via `TripFeedbackPrompt`.

## When to Revisit This Doc

Trigger one or more of:

- **Time-based**: 6 months of operational sub-score history have accumulated past the deploy of `plan-2026-05-14-tqs-forecast-history.md` Phase 2. Today is 2026-05-14, so trigger date is roughly 2026-11-14.
- **Data-volume-based**: ≥ 500 `TripFeedbackPrompt` responses captured with the score the user saw at decision time. (Need to instrument this — see Prerequisites below.)
- **Quality-based**: forecast accuracy tracking (already enabled by `trip_quality_history`) shows a structural bias in rule-based forecasts that ML could plausibly fix — e.g., 7-day forecasts systematically off by >10 TQS points, especially during shoulder seasons.

If none of these triggers fire within a year, revisit anyway and decide whether ML is still worth it. Sometimes the rule-based scorer is just good enough.

## Prerequisites

These must exist before training begins. Status as of 2026-05-14:

| Prerequisite | Status | Owner |
|---|---|---|
| 5-year backfill of raw inputs (USGS, iNat, SNOTEL, PRISM, NWS obs, state stocking) | Pending — Phase 1 of forecast plan | Engineering |
| Sub-score history columns on `trip_quality_history` populated going forward | Pending — Phase 2 | Engineering |
| Backcast TQS sub-scores for 2021-01-01 → backcast-run date, tagged `forecast_source='backcast'` | Pending — Phase 3 | Engineering |
| Forecast accuracy tracking — comparing `snapshot_date < target_date` forecasts to `snapshot_date = target_date` actuals — running for ≥ 6 months | Pending — emerges from Phase 3 | Engineering |
| `TripFeedbackPrompt` response capture, joined to the score the user saw at the time | **Partially implemented** — verify the join-to-score-at-decision-time is captured, not just feedback timestamp | Engineering |
| Persistence of NWS forecast values *at the time of scoring* (not just actuals) | **Scoped into forecast-history plan Phase 2** — the scorer writes a `forecast_inputs_payload` JSONB snapshot to `trip_quality_history` on every run, capturing the exact NWS forecast values consumed. Going-forward only; backcast rows will have null NWS payload | Engineering |
| Decision on minimum-feedback threshold to start training | This doc | Product |
| Decision on evaluation methodology | This doc | Product + Engineering |

## Decisions Needed (Captured Now, Refined Later)

### Decision 1: Evaluation methodology

The candidate splits for the labeled dataset:

- **Time-based**: train on 2021–2024, validate on 2025, test on 2026. Cleanest if seasonality matters; most representative of "deploy this and watch it perform on next year's conditions."
- **Reach-based**: hold out 2–3 reaches entirely as the test set. Tests generalization to new watersheds.
- **Random sample**: 80/20 random split. Maximally optimistic; not recommended for time-series forecasting (leaks future info into training).

**Provisional**: combine time-based and reach-based — train on 2021–2024 across most reaches, hold out (a) all of 2025 *and* (b) two random reaches across all years, evaluate against both holdout sets.

### Decision 2: Loss function

Candidates:
- **MAE** (mean absolute error) on TQS score: interpretable, robust to outliers.
- **RMSE**: penalizes large errors more; useful if "missed a high-score day" is worse than "off by a couple points on a mediocre day."
- **Quantile loss** at multiple quantiles: gives us prediction intervals naturally, supports confidence visualization.

**Provisional**: optimize MAE for the primary metric; track RMSE as secondary; consider quantile regression as a phase-2 model if confidence visualization needs improvement.

### Decision 3: Model family

Candidates (in order of complexity):
- **Linear regression** with hand-engineered features: lowest complexity baseline.
- **Gradient-boosted trees** (LightGBM / XGBoost): well-suited to tabular features, handles non-linear interactions, fast to train.
- **Time-series-specific** (Prophet, ARIMA variants): captures seasonality but assumes the inputs themselves are not the focus.
- **Neural network**: overkill for this dataset size and adds operational complexity.

**Provisional**: start with linear baseline (to measure "is ML actually helping vs. the rule-based scorer?"), then LightGBM as the working model. Defer neural nets unless we see compelling reason.

### Decision 4: Feature set

Available features (per (reach, target_date) prediction row):
- Lag features: TQS / sub-scores at t-1, t-3, t-7 days for the same reach
- Climate context: water_temp, flow, DO at t-1, t-3, t-7
- Forecast inputs: NWS 7-day forecast values at scoring time (requires Prerequisite gap above to be filled)
- Calendar: day_of_year, month, day_of_week
- Reach metadata: latitude, elevation, watershed
- Stocking proximity: days since last stocking event in this reach
- Phenology: cumulative degree-days since Jan 1

**Provisional**: start with the lag features + climate + calendar (about 20 features). Add NWS forecast features once the input-snapshotting gap is closed. Add phenology and stocking as iteration 2.

### Decision 5: Retraining cadence

Two viable cadences:
- **Annual retrain** with a full year of new data. Stable, predictable, low ops.
- **Monthly retrain** rolling-window. Captures regime change faster; higher ops cost.

**Provisional**: annual full retrain + monthly fine-tune (frozen features, just refit model weights on a recent window). Re-evaluate after 12 months in production.

### Decision 6: Deployment

Two viable shapes:
- **Batch inference**: model runs nightly, writes predictions to `gold.trip_quality_daily` with `forecast_source='ml_v1'`, serves identically to the rule-based scorer.
- **Online inference**: REST endpoint queried at request time.

**Provisional**: batch inference. The forecast endpoint already serves from `gold.trip_quality_daily`; adding an ML-source row alongside the rule-based row is the cleanest path. Lets us A/B which `forecast_source` we display by simply changing a query filter.

## Open Questions (Need Data to Answer)

These are explicitly *not* answered in this document. They require real operational data:

1. **What's the actual forecast horizon useful range?** Is 14 days plausible or does accuracy degrade so steeply past day 5 that there's no point?
2. **Which sub-scores carry the most predictive signal?** Domain intuition says `weather_score` and `water_temp_score` lead the composite, but we don't know.
3. **How noisy is `TripFeedbackPrompt`?** Are user ratings dominated by trip-mood-confound (caught fish vs. didn't) rather than actual conditions?
4. **Are there reach-level heterogeneities that demand per-reach models?** Maybe the Deschutes follows different dynamics than the Klamath in ways the model can't capture from features alone.
5. **What's the right confidence calibration?** The rule-based scorer reports confidence values that may not reflect real predictive uncertainty. ML lets us measure calibration empirically.

## Out of Scope for This Doc

- Specific model implementation details (architecture, hyperparameters, training loop).
- Production deployment architecture (Vertex AI vs. local? Cloud Run Job vs. Cloud Function?).
- Cost projections beyond an upper bound estimate.
- Comparison to rule-based scorer (that's the *outcome* of the work, not a prerequisite).

## Anti-Pattern to Avoid

The trap this doc is designed to prevent: **building the ML system before having data to validate it works.** A model trained on backcast-only data (no real `TripFeedbackPrompt` ground truth, no real forecast-vs-actual error tracking) is just a curve-fitter against the rule-based scorer's own output. It will look great in offline evaluation and tell you nothing about whether it actually predicts trip quality. Wait for the labeled data.

## Governing Artifacts

- **`plan-2026-05-14-tqs-forecast-history.md`** — the upstream plan that creates the data this work depends on.
- **`plan-2026-05-10-metric-history.md`** — companion metric-snapshot infrastructure; eventual ML predictions can write to `metric_snapshots` alongside the rule-based scores.
- **`plan-2026-05-14-push-notifications.md`** — downstream consumer; ML-improved forecasts would feed the threshold-crossing detection there.
- **FEAT-007 Fishing Intelligence** — feature owner.
- **FEAT-017 Predictive Intelligence** — existing predictions infrastructure context.

## Calendar

- **2026-05-14**: this doc written.
- **2026-11-14 (estimated)**: revisit. Check prerequisites. Decide whether to write the full ML plan.

If the revisit produces "yes, time to build," that work becomes its own design plan (`plan-2026-11-XX-tqs-ml-forecasting.md` or similar) and references this doc as background.
