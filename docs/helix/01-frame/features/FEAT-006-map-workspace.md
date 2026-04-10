---
dun:
  id: FEAT-006
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-006 -- Map-First Workspace

**Feature ID**: FEAT-006
**Status**: Draft
**Priority**: P0
**Owner**: Core Engineering

## Overview

The map-first workspace is the primary user interface for RiverSignal. It displays managed watersheds on an interactive map with site boundaries, observation overlays, alert indicators, and linked detail panels including ecological summaries and a natural-language chat interface. This feature implements PRD P0-5 and reflects the seed strategy's insight that ecological reasoning is inherently spatial -- the map is not a visualization add-on but the core interaction surface.

## Problem Statement

- **Current situation**: Watershed managers use a combination of ArcGIS/QGIS for spatial views, spreadsheets for data, email for alerts, and Word documents for reports. Switching between these tools takes significant time, and no single view connects spatial context with ecological intelligence.
- **Pain points**: Managers cannot see the ecological status of all their sites at a glance; alerts (invasive detections, anomalies) are not spatially contextualized; asking a question about a specific site requires opening multiple applications; field staff need to know "what's happening at this location" and have no single entry point.
- **Desired outcome**: A manager opens RiverSignal and immediately sees all managed sites on a map with color-coded health indicators. Clicking any site opens a detail panel with the current ecological summary, recent observations, alerts, and a chat pane for natural-language queries. The entire daily check-in takes under 15 minutes.

## Requirements

### Functional Requirements

1. Interactive map displays all managed sites as polygon overlays on a satellite/terrain basemap with zoom, pan, and layer controls
2. Each site polygon displays a color-coded status indicator: green (healthy/on-track), amber (attention needed -- anomaly or alert), red (critical -- intervention required)
3. Status indicators update automatically when new ecological summaries are generated from ingested data
4. Observation markers are overlaid on the map showing individual iNaturalist observations, color-coded by category (native species, invasive species, indicator species, other)
5. Clicking a site polygon opens a side detail panel containing: site name, current ecological summary (from FEAT-001), active alerts, most recent observations (last 10), restoration forecast status (from FEAT-002), and recommended actions (from FEAT-003)
6. The detail panel includes a chat interface where users can ask natural-language questions about the site (e.g., "What changed here since last spring?" or "Why is dissolved oxygen dropping?") and receive responses grounded in site data
7. Map supports filtering by: date range, data source type, species group (birds, fish, plants, amphibians, invertebrates), and alert status
8. Map supports toggling overlay layers: watershed boundaries, observation points, water quality stations, stream gauge stations, intervention zones, burn severity
9. Users can define the spatial extent of a new site by drawing a polygon on the map or uploading a boundary file
10. The workspace persists user preferences (default map extent, active layers, panel state) across sessions

### Non-Functional Requirements

- **Performance**: Map renders initial view with up to 20 site polygons and 2,000 observation markers within 3 seconds on a standard broadband connection (25 Mbps)
- **Responsiveness**: Pan and zoom interactions respond within 100ms; detail panel opens within 500ms of click
- **Browser support**: Chrome, Firefox, and Safari (latest 2 versions); desktop-primary with usable tablet layout
- **Accessibility**: Map controls and detail panel meet WCAG 2.1 AA for keyboard navigation and screen reader compatibility on non-map elements

## User Stories

- US-016 -- Manager checks all-sites status on Monday morning (to be created in `docs/helix/01-frame/user-stories/`)
- US-017 -- Manager investigates an amber alert on the map (to be created)
- US-018 -- Ecologist asks a natural-language question about a site (to be created)
- US-019 -- Admin defines a new site boundary on the map (to be created)

## Edge Cases and Error Handling

- **Large observation volumes**: If a site has >2,000 observations in the visible date range, the map clusters observations at higher zoom levels and expands them on zoom-in, displaying a count badge on clusters
- **Offline data sources**: If a data source is in degraded state (from FEAT-005 health monitoring), the affected site's status indicator includes a small warning badge and the detail panel notes which data sources are stale
- **No observations**: If a newly configured site has no observations yet, the map shows the boundary polygon in gray with a "No data yet -- awaiting first sync" label
- **Chat query out of scope**: If a user asks the chat a question unrelated to the site's ecological data (e.g., "What's the weather tomorrow?"), the system responds that it can only answer questions about the site's ecological monitoring data

## Success Metrics

- Managers complete their daily site check-in in under 15 minutes (measured by session duration analytics)
- 80%+ of user sessions start from the map view (not from reports or settings)
- Chat queries receive relevant, data-grounded responses in 90%+ of cases (measured by user thumbs-up/down feedback)
- Pilot users rate the map workspace usability at 4+ out of 5

## Constraints and Assumptions

- Assumes users have modern browsers and broadband internet; offline/field use is not supported in MVP
- Assumes satellite/terrain basemap tiles are available from a free or low-cost tile provider (e.g., MapTiler free tier, Stamen)
- Map polygon rendering assumes HUC12 boundaries are available as GeoJSON; boundaries are pre-loaded from USGS WBD
- Chat interface uses the same Claude API reasoning engine as FEAT-001 through FEAT-003, scoped to the selected site's data

## Dependencies

- **Other features**: FEAT-001 (Observation Interpretation) provides ecological summaries displayed in detail panels; FEAT-002 (Restoration Forecasting) provides forecast status; FEAT-003 (Management Recommendations) provides recommended actions; FEAT-005 (Data Ingestion) provides observation and site data
- **External services**: Map tile provider for basemap; Anthropic Claude API for chat reasoning
- **PRD requirements**: Implements P0-5 (Map-first workspace)

## Out of Scope

- Mobile-native application (responsive web only in MVP)
- Offline map caching for field use without internet
- Custom basemap styling or organization-branded map themes
- GIS data export (Shapefile, GDB) from the map interface
- Integration with desktop GIS tools (ArcGIS, QGIS plugins) -- deferred to Phase 2

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
