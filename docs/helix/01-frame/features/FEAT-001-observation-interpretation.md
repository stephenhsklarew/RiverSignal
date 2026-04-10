---
dun:
  id: FEAT-001
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-001 -- Observation Interpretation Engine

**Feature ID**: FEAT-001
**Status**: Draft
**Priority**: P0
**Owner**: Core Engineering

## Overview

The observation interpretation engine is the core reasoning capability of RiverSignal. It synthesizes iNaturalist observations, water quality readings, and hydrology data for a defined watershed site and time range into a structured ecological summary. This feature implements PRD P0-1 and provides the foundation that FEAT-002 (forecasting), FEAT-003 (recommendations), and FEAT-004 (reporting) build upon.

## Problem Statement

- **Current situation**: Watershed managers manually export iNaturalist observations into spreadsheets, cross-reference them against water quality CSVs and stream gauge readings, and write narrative interpretations by hand. A single site-season interpretation takes 4-6 hours of skilled ecologist time.
- **Pain points**: Junior staff cannot perform this synthesis without senior review; the process is repeated from scratch each cycle with no institutional memory; observations from different data sources are never jointly analyzed; anomalies (invasive emergence, indicator absence) are discovered weeks late because no one connects the dots across sources.
- **Desired outcome**: A watershed manager requests an ecological summary for any configured site and date range and receives a structured interpretation within 2 minutes, including species richness changes, invasive flags, indicator status, water quality trends, and anomaly explanations -- all cited to specific source data.

## Requirements

### Functional Requirements

1. Given a site boundary (HUC12 polygon) and date range, the engine retrieves all ingested iNaturalist observations, water quality readings, and hydrology data for that spatiotemporal window
2. The engine computes species richness delta compared to the same period in the prior year (or prior available period)
3. The engine identifies new species detections (taxa observed for the first time at this site)
4. The engine flags invasive species detections against a configurable invasive species watchlist per watershed
5. The engine evaluates indicator species presence/absence against a site-specific expected-indicator list derived from restoration goals
6. The engine summarizes water quality trends (dissolved oxygen, temperature, phosphorus, chlorophyll) as improving/stable/declining with magnitude
7. The engine produces anomaly flags for statistically unusual patterns (e.g., expected indicator absent, unexpected species present, water quality exceedance) with natural-language explanations
8. All summary elements include citations to specific observation IDs, station readings, or data records that informed the conclusion
9. The engine returns results as structured JSON (for UI rendering) and natural-language narrative (for reports and chat)
10. Summary generation completes within 120 seconds for sites with up to 500 observations in the queried period

### Non-Functional Requirements

- **Performance**: 95th percentile response time under 120 seconds for sites with up to 500 observations per query period
- **Accuracy**: Fewer than 10% of ecological summaries require substantive correction by domain expert during pilot (measured via weekly review sessions)
- **Scalability**: Engine supports up to 50 concurrent site-summary requests across all tenants
- **Availability**: 99.5% uptime during business hours (6am-8pm Pacific)

## User Stories

- US-001 -- Manager requests site ecological summary (to be created in `docs/helix/01-frame/user-stories/`)
- US-002 -- Ecologist drills into anomaly explanation (to be created)
- US-003 -- Manager compares current summary to prior period (to be created)

## Edge Cases and Error Handling

- **Sparse data**: If a site has fewer than 10 observations in the queried period, the engine returns a partial summary with a "low confidence -- insufficient observations" warning and lists which data sources had no data
- **Missing baseline**: If no prior-period data exists for comparison (new site), species richness delta is omitted and the summary is labeled "baseline period -- no comparison available"
- **Conflicting signals**: If water quality is improving but biodiversity indicators are declining, the engine explicitly flags the discrepancy and suggests possible explanations (e.g., lag effects, upstream contamination, seasonal variation)
- **Invasive watchlist mismatch**: If an observation matches a species on the invasive watchlist but the iNaturalist research-grade confidence is below 80%, the engine flags it as "possible invasive -- confirm in field" rather than a definitive detection

## Success Metrics

- Fewer than 10% of ecological summaries require substantive correction by domain advisor during pilot
- 95th percentile generation time under 120 seconds
- Managers rate summary usefulness at 4+ out of 5 in weekly pilot feedback surveys
- At least 80% of summary citations correctly trace to verifiable source observations

## Constraints and Assumptions

- Assumes iNaturalist observations include research-grade species identifications; the engine does not perform its own species ID from photos
- Assumes USGS and Oregon Water Data Portal APIs provide data with no more than 24-hour lag
- Invasive species watchlists must be pre-configured per watershed by a domain advisor before the engine can flag invasives
- Indicator species lists per site must be defined during site setup, informed by restoration goals

## Dependencies

- **Other features**: FEAT-005 (Data Ingestion Pipeline) must be operational to provide normalized data
- **External services**: iNaturalist API v1, USGS Water Services API, Oregon Water Data Portal API, Anthropic Claude API
- **PRD requirements**: Implements P0-1 (Observation interpretation engine)

## Out of Scope

- Species identification from raw photos (iNaturalist handles this upstream)
- Real-time streaming observation processing (MVP uses daily batch ingestion)
- Macroinvertebrate index scoring (deferred to Phase 2 pending public dataset availability assessment)
- Cross-watershed comparative analysis (covered by P1-3, multi-site comparison dashboard)

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
