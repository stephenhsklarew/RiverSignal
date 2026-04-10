---
dun:
  id: FEAT-007
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-007 -- Fishing Intelligence Layer

**Feature ID**: FEAT-007
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

The fishing intelligence layer provides species-by-reach distribution, sport catch harvest trends, stocking schedule alerts, and water condition correlation for angler and guide decision support. This feature implements PRD P1-5 and expands RiverSignal's user base from restoration professionals to the recreational fishing community -- a larger, higher-frequency user segment with willingness to pay for actionable river intelligence.

## Problem Statement

- **Current situation**: Fishing guides and serious anglers check 5+ websites daily -- ODFW stocking schedules, USGS flow gauges, myodfw.com recreation reports, iNaturalist for hatch activity, and word-of-mouth from other guides. No single source combines water conditions, species distribution, harvest trends, and stocking data for a specific reach.
- **Pain points**: "What's biting where?" requires synthesizing disconnected data sources; stocking schedules are HTML tables with abbreviated waterbody names; sport catch data is annual CSVs that most anglers never find; water temperature and flow data exists but isn't correlated with fishing success; guides waste 30+ minutes daily assembling a picture of current conditions across their operating rivers.
- **Desired outcome**: A guide opens RiverSignal before a trip, sees current water conditions (flow, temp, DO) for their reach, which species are present and active based on season and conditions, whether recent stocking occurred nearby, and how this year's harvest compares to prior years -- all in one view.

## Requirements

### Functional Requirements

1. Given a stream reach or site, display all sport fish species known to be present with distribution type (spawning, rearing, migration, resident), origin (native/stocked), and life history
2. Given a watershed, display monthly sport catch harvest data for salmon, steelhead, and sturgeon with year-over-year comparison (2019-2025 data from ODFW CSVs)
3. Given a watershed zone, display upcoming and recent trout stocking events with waterbody, date, and count by category (legals, trophy, brood, fingerling)
4. Correlate current water temperature and flow conditions with species activity windows (e.g., steelhead prefer 8-14°C water temperature, are most active at flows between 3,000-6,000 cfs on the Deschutes)
5. Display fish passage barrier status for reaches where barrier type, passage status, and any remediation history are available
6. Generate a "fishing brief" for a given river and date that synthesizes conditions, species activity, recent stocking, and harvest trends into a 2-3 paragraph natural-language summary
7. Allow users to set alerts for stocking events, flow thresholds, or temperature windows on their preferred rivers
8. Display seasonal fishing calendar showing peak activity windows by species and river based on historical harvest data patterns

### Non-Functional Requirements

- **Performance**: Fishing brief generation completes within 15 seconds
- **Freshness**: Water conditions (USGS flow/temp) update within 24 hours of gauge readings; stocking schedule updates weekly
- **Accuracy**: Species distribution data matches ODFW official records; harvest numbers match published sport catch statistics exactly

## User Stories

- US-020 -- Guide checks morning conditions before a Deschutes trip (to be created in `docs/helix/01-frame/user-stories/`)
- US-021 -- Angler looks up what species are in the Metolius (to be created)
- US-022 -- Guide compares this year's steelhead run to last year (to be created)
- US-023 -- Angler sets alert for stocking at a favorite lake (to be created)

## Edge Cases and Error Handling

- **No sport catch data for watershed**: Metolius and Klamath have no ODFW sport catch location codes; the system shows fish habitat distribution and stocking data but notes "no harvest tracking data available for this fishery"
- **Stocking schedule only shows upcoming weeks**: ODFW publishes 1-2 weeks ahead; the system caches historical stocking data and shows both upcoming and past stocking at the location
- **Wild fishery vs stocked fishery**: Metolius and upper Deschutes are wild fisheries; the system distinguishes between native/wild populations and stocked populations based on ODFW origin data
- **Catch-and-release regulations**: Some reaches are catch-and-release only; the system should note regulatory context from the impaired waters / regulation data when displaying harvest trends

## Success Metrics

- 100+ weekly active fishing guide users within 6 months of launch
- Guides rate fishing brief usefulness at 4+ out of 5
- 50%+ of fishing users check conditions at least 3x per week during season
- Stocking alert adoption rate > 30% among active users

## Constraints and Assumptions

- Sport catch data is only available for salmon, steelhead, and sturgeon -- not trout (which is the primary species for many anglers on these rivers)
- Stocking schedule data is forward-looking only (1-2 weeks); historical stocking requires accumulation over time through repeated scraping
- ODFW does not publish creel survey data publicly; actual catch rates must be inferred from harvest statistics and effort proxies
- Fishing regulations are not available as structured data; regulatory context must be manually configured or scraped from eRegulations HTML

## Dependencies

- **Other features**: FEAT-001 (Observation Interpretation provides species observation context), FEAT-005 (Data Ingestion provides USGS flow/temp data), FEAT-006 (Map Workspace for spatial display)
- **Data sources**: ODFW Sport Catch CSVs, ODFW Fish Habitat Distribution ArcGIS, ODFW Stocking Schedule (HTML scrape), USGS Water Services (flow/temp), ODFW Fish Passage Barriers
- **PRD requirements**: Implements P1-5 (Fishing intelligence layer)

## Out of Scope

- Real-time fish finder / sonar integration
- Fly pattern recommendations (too subjective, not data-driven)
- Guided trip booking or marketplace features
- Fishing license purchase integration
- Social features (catch photos, trip reports) -- these belong in a separate feature if pursued

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
