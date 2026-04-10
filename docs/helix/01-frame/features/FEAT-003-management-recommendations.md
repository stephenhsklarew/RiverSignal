---
dun:
  id: FEAT-003
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-003 -- Management Recommendations

**Feature ID**: FEAT-003
**Status**: Draft
**Priority**: P0
**Owner**: Core Engineering

## Overview

The management recommendation engine produces a prioritized list of field actions for a given site and time window, grounded in current observations, seasonal context, restoration goals, and intervention history. This feature implements PRD P0-3 and is the primary "what should we do next?" capability that distinguishes RiverSignal from passive monitoring dashboards.

## Problem Statement

- **Current situation**: Watershed managers decide weekly field priorities through informal team meetings, relying on whoever remembers what was seen last visit. Decisions are driven by recency bias (last site visited gets attention) rather than ecological priority. There is no systematic way to weigh competing needs across sites.
- **Pain points**: Invasive treatment windows are missed because the optimal timing isn't connected to detection data; survey effort is allocated evenly across sites rather than directed toward sites with the most actionable signals; seasonal windows for specific monitoring types (e.g., amphibian breeding audio, spawning surveys) are missed because they aren't triggered by relevant observation patterns.
- **Desired outcome**: A manager requests field priorities for the week and receives a ranked list of 3-5 recommended actions across their managed sites, each with reasoning that connects the recommendation to specific observations, seasonal timing, and restoration objectives.

## Requirements

### Functional Requirements

1. Given one or more managed sites and a target time window (default: current week), the engine produces a ranked list of 3-5 recommended field actions
2. Each recommendation includes: action description, target site and location within site, priority rank, time sensitivity (e.g., "within 10 days" or "this month"), and 2-3 sentence reasoning
3. Recommendations are grounded in at least one of: current observation anomalies, seasonal monitoring windows, restoration plan milestones, or invasive detection follow-up needs
4. The engine considers seasonal ecological calendars (breeding seasons, migration windows, growth periods, treatment windows) appropriate to the site's biome and latitude
5. The engine considers the site's restoration goals and intervention history when ranking actions (e.g., a site focused on riparian restoration prioritizes canopy monitoring over open-meadow surveys)
6. Recommendations do not duplicate actions already logged as completed in the current period
7. Users can mark a recommendation as "accepted" (assigned to field crew), "deferred" (acknowledged but postponed), or "dismissed" (not relevant) with optional notes
8. Dismissed recommendations with user notes feed back into the reasoning engine to improve future relevance
9. Recommendations refresh automatically when new observation data is ingested for a managed site
10. The engine explains trade-offs when recommendations compete (e.g., "invasive sweep at Site A is more time-sensitive than the photo-point survey at Site B because the treatment window closes in 8 days")

### Non-Functional Requirements

- **Performance**: Recommendation generation completes within 60 seconds for a portfolio of up to 10 managed sites
- **Relevance**: Fewer than 25% of recommendations dismissed as "not relevant" by pilot users (measured via dismiss tracking in requirement 7)
- **Freshness**: Recommendations update within 4 hours of new data ingestion

## User Stories

- US-007 -- Manager reviews weekly field priorities Monday morning (to be created in `docs/helix/01-frame/user-stories/`)
- US-008 -- Manager assigns recommended action to field crew (to be created)
- US-009 -- Manager dismisses irrelevant recommendation with feedback (to be created)

## Edge Cases and Error Handling

- **No actionable signals**: If all managed sites are in stable condition with no anomalies, active treatment windows, or upcoming milestones, the engine returns "No priority actions this period" with a summary of overall site health status rather than inventing low-value busywork
- **Too many competing priorities**: If more than 5 actions are genuinely time-sensitive across the portfolio, the engine returns a ranked list of 5 with an overflow section noting additional actions and their deadlines
- **Conflicting recommendations**: If two recommendations compete for the same field crew time (e.g., invasive sweep at Site A and spawning survey at Site B, both time-sensitive), the engine explicitly presents the trade-off and explains its ranking rationale
- **Stale data**: If a site's most recent observation data is older than 30 days, recommendations for that site include a warning: "Data older than 30 days -- consider a general status survey before acting on these recommendations"

## Success Metrics

- Fewer than 25% of recommendations dismissed as "not relevant" during pilot
- Managers report recommendations saved them at least 2 hours/week of planning time (pilot survey)
- At least 60% of generated recommendations are acted on (accepted) within their time-sensitivity window
- Zero instances of a recommendation causing ecological harm (e.g., recommending activity during sensitive nesting period) during pilot -- validated by domain advisor review

## Constraints and Assumptions

- Assumes site restoration goals are documented in the site registry with enough specificity to inform action ranking (e.g., "riparian native cover restoration" vs. just "restoration")
- Assumes field crew capacity is not modeled in MVP -- recommendations are prioritized by ecological urgency, not staff availability
- Seasonal ecological calendars for PNW biomes are pre-configured by domain advisor during setup

## Dependencies

- **Other features**: FEAT-001 (Observation Interpretation) provides the current ecological summary that triggers recommendations; FEAT-002 (Restoration Forecasting) informs expected-vs-actual comparisons; FEAT-005 (Data Ingestion) provides current observation data and intervention logs
- **External services**: Anthropic Claude API for reasoning
- **PRD requirements**: Implements P0-3 (Management recommendation generation)

## Out of Scope

- Field crew scheduling and dispatch (recommendations are advisory; assignment workflows are basic accept/defer/dismiss only)
- Cost estimation for recommended actions
- Equipment or supply requirements per action
- Automated triggering of field crew notifications (MVP: managers review and assign manually)

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
