---
dun:
  id: FEAT-017
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-017 -- Predictive Intelligence

**Feature ID**: FEAT-017
**Status**: Implemented (spec retroactive)
**Priority**: P0
**Owner**: Core Engineering
**Date**: 2026-05-08

## Overview

Predictive Intelligence replaces hardcoded scoring rules with five trained prediction models that provide forward-looking ecological and fishing intelligence across all 7 watersheds. Models are trained on historical data from the RiverSignal data platform and served via dedicated API endpoints. Predictions refresh on the daily pipeline run; heavy model retraining runs weekly.

## Problem Statement

- **Current situation**: RiverPath's hatch confidence and catch scoring used static month lookups and fixed formulas. River health was assessed with 3-line if/else rules. No species distribution shift tracking or restoration impact prediction existed.
- **Pain points**: Static rules do not adapt to changing conditions, cannot incorporate multi-factor inputs (weather, flow, stocking), and provide no confidence intervals.
- **Desired outcome**: Data-driven predictions that adapt to each watershed's conditions, with transparent confidence levels and info tooltips explaining methodology in layman's terms.

## Requirements

### Functional Requirements

#### FR-01: Hatch Emergence Prediction (Degree-Day Model)
- Logistic regression model using accumulated degree-days (water temperature) to predict aquatic insect emergence timing
- Output: predicted emergence date, confidence score (0-1), degree-day accumulation progress
- Endpoint: `GET /sites/{ws}/hatch-forecast`
- Acceptance criteria: Predictions for all insect species in the curated hatch chart; confidence scores correlate with observed emergence within +/- 7 days at rate > 65%

#### FR-02: Catch Probability Scoring (Multi-Factor Model)
- Multi-factor model combining: water temperature, flow rate, recent stocking events, hatch activity, weather conditions, and time of year
- Output: catch probability score (0-100) per species, contributing factor breakdown, recommended fishing window
- Endpoint: `GET /sites/{ws}/catch-forecast`
- Acceptance criteria: Catch probability scores correlate with reported catch rates at r > 0.5; factor breakdown shows top 3 contributing factors

#### FR-03: River Health Anomaly Detection (Z-Score + Trend Analysis)
- Z-score anomaly detection against historical baselines for water quality, species diversity, and observation patterns
- Output: anomaly flags (normal/watch/alert/critical), z-score values, trend direction (improving/stable/declining), baseline comparison
- Endpoint: `GET /sites/{ws}/health-anomaly`
- Acceptance criteria: Anomalies flagged when z-score exceeds 2.0; false positive rate < 20% when compared to expert assessment

#### FR-04: Species Distribution Shift Tracking (Range Analysis)
- Centroid tracking of species observation distributions over time; new arrival detection; range contraction/expansion estimation
- Output: species with significant range shifts, direction of shift, new arrivals in watershed, species at risk of local extirpation
- Endpoint: `GET /sites/{ws}/species-shifts`
- Acceptance criteria: Detects known range shifts (e.g., warm-water species moving upstream) with lag < 1 season; new arrival detection within 30 days of first observation cluster

#### FR-05: Restoration Impact Prediction (Regression)
- Regression model predicting species gain by intervention type, trained on 1,391 historical OWRI intervention records with outcomes
- Output: predicted species gain, confidence interval, comparable historical projects, estimated time to measurable impact
- Endpoint: `GET /sites/{ws}/restoration-forecast`
- Acceptance criteria: Predicted species gain within +/- 30% of actual for intervention types with > 10 historical examples

#### FR-06: Info Tooltips Explaining Predictions
- All prediction sections in RiverPath and RiverSignal include info tooltips explaining: what the model predicts, what data it uses, confidence level meaning, and limitations
- Tooltips written in layman's terms (no statistical jargon)
- Acceptance criteria: Every prediction card/section has a visible (i) icon that expands to a tooltip with plain-language explanation

#### FR-07: Prediction Refresh on Daily Pipeline
- Light prediction refresh runs daily via Cloud Scheduler (updates scores with latest data)
- Heavy model retraining runs weekly (rebuilds model weights from full historical dataset)
- Monthly full prediction recalculation across all watersheds
- Acceptance criteria: Daily refresh completes within 15 minutes; weekly retraining completes within 1 hour

### Non-Functional Requirements

- Model inference latency < 2 seconds per endpoint call
- Prediction tables persist in gold layer (`gold_hatch_emergence_forecast`, `gold_catch_forecast`, `gold_health_anomaly`, `gold_species_distribution_shifts`, `gold_restoration_forecast`)
- All models log training metrics (accuracy, precision, recall where applicable)
- Graceful degradation: if a model has insufficient data for a watershed, return empty results with explanation rather than error

## Implementation Evidence

- `pipeline/predictions/hatch_forecast.py` — degree-day logistic regression
- `pipeline/predictions/catch_forecast.py` — multi-factor catch probability model
- `pipeline/predictions/health_anomaly.py` — z-score anomaly detection
- `pipeline/predictions/species_distribution.py` — centroid tracking + range analysis
- `pipeline/predictions/restoration_impact.py` — regression model
- `app/routers/intelligence.py` — read endpoints for prediction results
- `app/routers/predictions.py` — full prediction lifecycle (generate/list/score/resolve)

## Dependencies

- **Other features**: FEAT-005 (data ingestion pipeline provides training data), FEAT-007 (fishing data for catch model), FEAT-012/013 (UI display of predictions)
- **Data**: Historical observations, time series (water quality, flow, temperature), intervention records with outcomes, hatch chart, stocking schedules
- **Infrastructure**: FEAT-018 (Cloud Scheduler for automated refresh, Cloud Run for compute)

## Out of Scope

- Real-time prediction updates (batch refresh only)
- User feedback loop on prediction accuracy (manual scoring via predictions API exists but no automated user feedback)
- Ensemble models or deep learning approaches
- Prediction confidence intervals on the UI (backend supports it; UI shows simplified confidence levels)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Problem statement describes what exists now and what is broken
- [x] Every functional requirement is testable
- [x] Non-functional requirements have specific numeric targets
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
