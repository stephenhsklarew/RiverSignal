---
dun:
  id: FEAT-005
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-005 -- Data Ingestion Pipeline

**Feature ID**: FEAT-005
**Status**: Draft
**Priority**: P0
**Owner**: Core Engineering

## Overview

The data ingestion pipeline retrieves, normalizes, and stores ecological data from external APIs (iNaturalist, USGS, Oregon Water Data Portal) and manual uploads (CSV, PDF, GeoJSON) into a canonical schema indexed by site, timestamp, and source. This feature implements PRD P0-6 and is the foundational data layer that every other feature depends on.

## Problem Statement

- **Current situation**: Watershed data lives in 5+ disconnected systems -- iNaturalist for species observations, USGS for stream gauges, state portals for water quality, local spreadsheets for intervention logs, and PDFs for field notes. Each system has a different format, access method, and update cadence. No unified view exists.
- **Pain points**: Ecologists spend 2-4 hours per site manually pulling data from each source before they can begin interpretation; data gaps are discovered mid-analysis when a source turns out to be missing for the period; field notes and intervention logs exist only on individual laptops or in email threads; there is no consistent way to associate all data types with a specific restoration site.
- **Desired outcome**: All configured data sources for a watershed sync automatically on a daily schedule, land in a unified schema queryable by site and time range, and are available to the reasoning engine within 15 minutes of sync completion. Manual uploads are normalized into the same schema immediately.

## Requirements

### Functional Requirements

1. System ingests iNaturalist observations via API, filtered by HUC12 watershed boundaries, on a configurable schedule (default: daily at 02:00 Pacific)
2. System ingests USGS stream gauge data (discharge, temperature, dissolved oxygen, specific conductance) via USGS Water Services REST API for configured station IDs, on a daily schedule
3. System ingests water quality data (phosphorus, chlorophyll-a, cyanotoxins, turbidity) from Oregon Water Data Portal for configured monitoring stations, on a daily schedule
4. System accepts manual upload of CSV files with a defined column mapping interface for species lists, water quality readings, or custom monitoring data
5. System accepts manual upload of PDF files (field notes, grant reports) and extracts text content for use in ecological reasoning context
6. System accepts manual upload of GeoJSON files for site boundaries, restoration polygons, and intervention zones
7. All ingested data is normalized to a canonical schema with fields: site_id, timestamp, source_type, source_id, data_category (observation, hydrology, water_quality, intervention, narrative), and payload (structured per category)
8. System maintains a site registry where each site has: name, HUC12 boundary polygon, list of configured data source endpoints, intervention history log, restoration goals, and indicator species list
9. Ingestion jobs log success/failure, record count, and duration; failed jobs retry once after 15 minutes and alert the admin if the retry also fails
10. System deduplicates observations: if the same iNaturalist observation ID is ingested twice, it updates the existing record rather than creating a duplicate
11. Data availability dashboard shows last sync time, record count, and status (healthy/warning/error) per data source per site

### Non-Functional Requirements

- **Performance**: Daily sync for a single watershed (up to 5 HUC12 boundaries, 3 USGS stations, 2 water quality stations) completes within 30 minutes
- **Reliability**: 99% of scheduled syncs complete successfully over any 30-day period
- **Latency**: Manually uploaded files are normalized and queryable within 2 minutes of upload completion
- **Storage**: System handles up to 100,000 observations and 5 years of daily hydrology/water quality data per watershed without performance degradation

## User Stories

- US-013 -- Admin configures a new watershed with data sources (to be created in `docs/helix/01-frame/user-stories/`)
- US-014 -- Ecologist uploads field notes PDF for a site visit (to be created)
- US-015 -- Admin reviews data ingestion health dashboard (to be created)

## Edge Cases and Error Handling

- **API rate limiting**: If iNaturalist API rate limit (100 req/min) is hit during sync, the job backs off exponentially and resumes; the sync may take longer but completes without data loss
- **API downtime**: If an external API is unreachable, the sync job logs a warning, retries after 15 minutes, and if still unreachable, marks the source as "degraded" on the health dashboard without blocking other sources
- **Malformed CSV upload**: If a CSV file has unrecognized columns or data types, the system rejects the upload with a specific error message listing the problematic columns and expected format
- **Duplicate site boundaries**: If a new site's HUC12 boundary overlaps with an existing site by >50%, the system warns the admin and requires confirmation before creating the site
- **Large PDF upload**: If a PDF exceeds 50 pages, the system processes only the first 50 pages and notifies the user of the truncation

## Success Metrics

- 99% of scheduled daily syncs complete successfully over the pilot period
- Data from all configured sources for the pilot watershed is queryable within 15 minutes of sync completion
- Manual CSV/PDF uploads are processed without error in 95%+ of uploads during pilot
- Zero data loss incidents during the pilot period

## Constraints and Assumptions

- Assumes iNaturalist API v1 remains stable and available; API deprecation would require adapter updates
- Assumes USGS Water Services API response format is consistent across all Pacific Northwest stations
- Assumes manual uploads are infrequent (fewer than 20 per week per organization) -- not designed for high-throughput batch loading
- PDF text extraction quality depends on document quality; handwritten field notes may extract poorly

## Dependencies

- **Other features**: None (FEAT-005 is the foundation; all other features depend on it)
- **External services**: iNaturalist API v1, USGS Water Services REST API, Oregon Water Data Portal API
- **PRD requirements**: Implements P0-6 (Data ingestion pipeline)

## Out of Scope

- Real-time streaming ingestion (IoT sensors, live telemetry) -- MVP uses scheduled batch polling
- Satellite or drone imagery ingestion -- deferred to Phase 2
- eBird data ingestion -- deferred to P2-4
- Automated data quality scoring beyond deduplication (e.g., outlier detection in water quality readings) -- deferred to Phase 2

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
