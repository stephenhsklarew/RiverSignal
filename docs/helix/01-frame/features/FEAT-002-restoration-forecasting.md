---
dun:
  id: FEAT-002
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-002 -- Restoration Forecasting

**Feature ID**: FEAT-002
**Status**: Draft
**Priority**: P0
**Owner**: Core Engineering

## Overview

Restoration forecasting predicts which ecological indicators (species, habitat conditions, water quality thresholds) should appear at a restoration site in the next monitoring period, given the site's intervention history and current baseline. This feature implements PRD P0-2 and converts monitoring from reactive observation into proactive expectation management and adaptive planning.

## Problem Statement

- **Current situation**: Restoration ecologists set informal mental expectations for what should return at a site based on personal experience. These expectations are rarely documented, never quantified, and leave with the ecologist when they move on. Funder conversations about "is this working?" rely on anecdotal comparisons rather than structured predictions.
- **Pain points**: Without documented forecasts, teams cannot distinguish between "on track" and "falling behind" until outcomes are obviously bad; junior staff have no framework for what to expect; funders have no basis for early confidence or concern; adaptive management decisions (should we change the intervention?) are made too late because there is no prediction to deviate from.
- **Desired outcome**: An ecologist requests a restoration forecast for any site with intervention history and receives a structured prediction of expected species returns, habitat condition changes, and risk factors -- each with confidence scores -- that can be tracked against actual outcomes in the next monitoring cycle.

## Requirements

### Functional Requirements

1. Given a site with at least one logged intervention and a current observation baseline, the engine produces a forecast for the next monitoring period (configurable: 3, 6, or 12 months)
2. Forecasts include expected species returns: named taxa likely to appear or increase, based on restoration type, biome, and intervention history
3. Forecasts include expected habitat condition changes: native plant cover, canopy closure, riparian connectivity, or other relevant metrics based on intervention type
4. Forecasts include risk factors: specific threats that could derail expected recovery (e.g., invasive recolonization, drought stress, upstream contamination)
5. Each prediction element includes a confidence score (high/medium/low) with a natural-language explanation of what drives the confidence level
6. Forecasts cite the ecological reasoning basis: which intervention types, comparable site outcomes, seasonal patterns, or known succession models informed the prediction
7. When the next monitoring cycle's data becomes available, the system automatically scores the forecast accuracy (prediction confirmed, partially confirmed, not confirmed) per element
8. Forecast accuracy scores are stored and surfaced to users alongside the original predictions
9. The system presents a "forecast vs. actuals" comparison view for completed monitoring periods
10. Forecasts are exportable as a standalone section for inclusion in funder reports

### Non-Functional Requirements

- **Performance**: Forecast generation completes within 90 seconds for sites with up to 3 years of intervention history
- **Accuracy**: 70%+ of high-confidence predictions confirmed by next monitoring cycle (measured by automated scoring in requirement 7)
- **Interpretability**: Every prediction element must include a human-readable reasoning chain; no "black box" confidence scores

## User Stories

- US-004 -- Ecologist generates restoration forecast for spring season (to be created in `docs/helix/01-frame/user-stories/`)
- US-005 -- Manager reviews forecast vs. actuals after monitoring cycle (to be created)
- US-006 -- Ecologist adjusts intervention plan based on forecast risk factors (to be created)

## Edge Cases and Error Handling

- **New intervention with no comparable history**: If the site's intervention type has no prior outcome data in the system, the forecast is labeled "exploratory -- based on ecological succession models only, no site-specific outcome history" and confidence is capped at "low"
- **Multiple concurrent interventions**: If a site has overlapping interventions (e.g., invasive removal + native planting + large wood installation), the forecast attributes expected outcomes to each intervention where possible and flags interactions that increase uncertainty
- **Drought or disturbance override**: If recent climate data (temperature extremes, drought indices) suggests conditions that override normal succession expectations, the forecast includes an explicit environmental override flag explaining why predictions diverge from typical patterns
- **Insufficient baseline data**: If the current observation baseline has fewer than 20 taxa recorded, the forecast warns that species-return predictions are less reliable and recommends a comprehensive baseline survey before relying on forecasts

## Success Metrics

- 70%+ of high-confidence predictions confirmed by next monitoring cycle
- Ecologists rate forecast usefulness at 4+ out of 5 in pilot feedback
- At least 2 of 3 pilot sites use forecasts in funder conversations during the pilot period
- Forecast vs. actuals comparison is reviewed by site managers at least once per monitoring cycle

## Constraints and Assumptions

- Assumes intervention history is logged with sufficient detail (intervention type, date, location, scope) to support reasoning; the system cannot forecast for undocumented interventions
- Assumes ecological succession models for PNW biomes (riparian, wetland, mixed conifer) are well enough established in scientific literature for LLM reasoning to produce meaningful predictions
- Forecast accuracy depends on observation density in the confirmation period; sparse monitoring may result in "unconfirmed" rather than "not confirmed"

## Dependencies

- **Other features**: FEAT-001 (Observation Interpretation) provides the baseline ecological summary that forecasts build on; FEAT-005 (Data Ingestion) provides intervention history and observation data
- **External services**: Anthropic Claude API for ecological reasoning
- **PRD requirements**: Implements P0-2 (Restoration forecast)

## Out of Scope

- Climate modeling or downscaled climate projections (forecasts use observed recent conditions, not modeled future climate)
- Quantitative population models (forecasts are qualitative species-return predictions, not population dynamics simulations)
- Automatic intervention recommendations based on forecast deviations (covered by FEAT-003)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Problem statement describes what exists now and what is broken -- not just what is wanted
- [x] Every functional requirement is testable -- you can write an assertion for it
- [x] Non-functional requirements have specific numeric targets, not "must be fast"
- [x] Edge cases cover realistic failure scenarios, not just happy paths
- [x] Success metrics are specific to this feature, not product-level metrics
- [x] Dependencies reference real artifact IDs (FEAT-XXX, external APIs)
- [x] Out of scope excludes things someone might reasonably assume are in scope
- [x] No implementation details ("use X library", "create Y table") -- specify WHAT not HOW
- [x] Feature is consistent with governing PRD requirements
- [x] No [NEEDS CLARIFICATION] markers remain unresolved for P0 features
