# Proof of Concept: Predictive Intelligence (5 models)

**PoC ID**: POC-017 | **Lead**: Founder | **Time Budget**: 3 weeks | **Status**: Completed (deployed as FEAT-017)

## Objective

**Primary Question**: Can our medallion warehouse ground 5 distinct predictive models (catch probability, hatch timing, river health, species presence, restoration outcome) at sufficient accuracy and acceptable cost to ship as B2C/B2B features?

**Success Criteria**:
- **Functional**: Each model produces interpretable predictions for any (lat, lon) in our 7 watersheds.
- **Performance**: p95 inference latency < 500ms for warehouse-grounded prediction; refresh in daily light view job.
- **Integration**: Predictions accessible via FastAPI endpoints; surface in RiverPath (`/path/now`) and RiverSignal (`/riversignal`).

**In Scope**: Build, train, and ship the five models against current warehouse. Verify reasonable behavior on holdout watersheds.

**Out of Scope**: Hyperparameter tuning past first-pass; cross-validation infrastructure; A/B testing.

## Approach

**Architecture Pattern**: Retrieval + simple model. We pre-aggregate features in gold views, run lightweight Python models on a daily cadence (`refresh-views` job), and store outputs in a `gold.predictions` table for low-latency serving.

**Key Technologies**:
- **Primary**: Python 3.12, scikit-learn for tabular models; SQL for feature engineering.
- **Integration**: Postgres (warehouse + serving), FastAPI (`/api/v1/ai-features/*`).

## Implementation

### Architecture Overview

```
[bronze + silver tables]
        │
        ▼
[gold feature views]  (per watershed, per period)
        │
        ▼
[Python model train/score in refresh-views job]
        │
        ▼
[gold.predictions table]   ← daily refresh
        │
        ▼
[/api/v1/ai-features/*]    ← read-only serving
        │
        ▼
[RiverPath / RiverSignal UI cards]
```

### Core Components

#### `pipeline/predictions/`
- **Purpose**: Train + score models against warehouse; write back to `gold.predictions`.
- **Implementation**: One module per model (catch, hatch, health, species, restoration). Shared utilities for feature loading via SQL.

#### `app/routers/ai_features.py`
- **Purpose**: Serve precomputed predictions to UI.
- **Implementation**: SQL read from `gold.predictions` indexed by (watershed, model, location_grid).

#### `gold.predictions` table
- **Purpose**: Serving layer for all five models.
- **Implementation**: `(model_id, watershed, lat_grid, lon_grid, prediction, confidence, computed_at)` schema.

### Integration Points

| Integration | Type | Status | Notes |
|-------------|------|--------|--------|
| Warehouse → feature views | SQL | Working | Per-model gold view; refreshed in light cycle |
| Feature views → models | Python pandas + sklearn | Working | Models loaded once per refresh; outputs to predictions table |
| Predictions → API | FastAPI + SQLAlchemy | Working | Standard read pattern |
| Predictions → UI | React fetch | Working | Cards on RiverNowPage and RiverSignal map |

## Results

### Test Scenarios

| Scenario | Result | Status |
|----------|--------|--------|
| Catch probability for 7 watersheds × 5 species | Reasonable distributions; passes hand-check vs ODFW data | Pass |
| Hatch timing for current month | Matches expert curated chart within 2 weeks | Pass |
| River health score correlates with EPA 303(d) listings | r ≈ 0.7 across listed reaches | Pass |
| Species presence reproduces iNat baseline within 10% | True | Pass |
| Restoration outcome forecast handles low-data sites | Returns "low confidence" rather than fabricating | Pass |
| End-to-end latency: API call → response | p95 ~ 80ms (read from gold.predictions) | Pass |
| Daily refresh time | ~ 7 minutes | Pass (well within 2h budget) |

### Findings

- **FINDING 1**: Pre-aggregating features in gold views, then training simple sklearn models, is sufficient for our domain. Deep learning offered no advantage given data volume and feature heterogeneity.
- **Evidence**: Holdout-watershed errors comparable to expert benchmarks; latency well under target.
- **Implications**: We can keep adding models on this pattern without infrastructure rewrite.

- **FINDING 2**: Model staleness is the main risk, not accuracy.
- **Evidence**: When upstream data source goes stale (e.g., USGS hydrology gap), predictions drift before alerts fire.
- **Implications**: Must tie model freshness to upstream freshness signals; show "as of" dates in UI.

- **FINDING 3**: Restoration outcome forecasts have wide confidence bands by nature.
- **Evidence**: Many restoration projects have small sample sizes.
- **Implications**: Always show confidence in UI; never display point estimates as definitive.

### Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Model accuracy regression on warehouse refresh | M | M | Holdout evaluation per refresh; alert on > 10% delta from prior run |
| User over-trusts predictions ("the app said I'd catch fish") | H | M | Confidence bands shown; "based on X observations" copy |
| New data source schema break propagates to models | M | M | Per-source schema test in adapter; predictions skip on bad input |

## Analysis

**Overall Assessment**: VIABLE

**Rationale**: All five models meet functional + latency targets. The pattern (gold views → Python models → predictions table → API) is reusable. Confidence bands are built into the surfacing pattern from the start, mitigating user-trust risk. Production deployed as FEAT-017 on 2026-05-08; running cleanly.

## Recommendations

1. Promote the POC pattern to standard practice — every future predictive feature uses this architecture. — Rationale: it works, it's cheap, and it's reproducible. — Timeline: applied immediately.
2. Add model-staleness monitoring tied to upstream data freshness in `gold.predictions` table. — Rationale: addresses Finding 2. — Timeline: next release.
3. Add a confidence-band UI primitive shared across all model surfaces. — Rationale: addresses user-trust risk uniformly. — Timeline: with next predictive surface.

### Follow-up

- [x] Promote to FEAT-017 spec (done; lives in `01-frame/features/FEAT-017-predictive-intelligence.md`)
- [ ] Document the per-model serving pattern as a tech-spike-style standard (TODO; this PoC + ADR-007 cover most of it)
- [ ] Add model staleness column to `gold.predictions`
