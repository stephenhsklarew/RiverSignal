# Feature Registry

**Status**: Active
**Last Updated**: 2026-05-10

## Active Features

| ID | Name | Description | Status | Priority | Owner | Updated |
|----|------|-------------|--------|----------|-------|---------|
| FEAT-001 | Observation Interpretation | Interpret species observations with conservation/quality context | Deployed | P0 | sklarew | 2026-05-08 |
| FEAT-002 | Restoration Forecasting | Predict species recovery from restoration interventions | Deployed | P1 | sklarew | 2026-05-08 |
| FEAT-003 | Management Recommendations | Suggest restoration actions based on watershed health | In Build | P1 | sklarew | 2026-05-08 |
| FEAT-004 | Funder Report Generation | Generate restoration funder reports from outcomes data | Specified | P2 | sklarew | 2026-05-08 |
| FEAT-005 | Data Ingestion Pipeline | Daily/weekly/monthly Cloud Run jobs ingesting 30+ sources | Deployed | P0 | sklarew | 2026-05-09 |
| FEAT-006 | Map Workspace | RiverSignal desktop map view with layered observations | Deployed | P0 | sklarew | 2026-05-08 |
| FEAT-007 | Fishing Intelligence | Hatch charts, stocking, catch probability for anglers | Deployed | P0 | sklarew | 2026-05-09 |
| FEAT-008 | Geologic Context | Macrostrat-backed rock unit/age data | Deployed | P0 | sklarew | 2026-05-08 |
| FEAT-009 | Fossil Discovery | PBDB + iDigBio + GBIF specimen lookup near location | Deployed | P0 | sklarew | 2026-05-08 |
| FEAT-010 | Deep Time Storytelling | AI narrative + audio TTS at adult/kid/expert reading levels | Deployed | P0 | sklarew | 2026-05-08 |
| FEAT-011 | Three-Product UI | Single React app routing to 3 product surfaces (was 4 — DeepSignal consolidated into RiverSignal on 2026-05-08) | Deployed | P0 | sklarew | 2026-05-10 |
| FEAT-012 | RiverPath B2C | Mobile-first angler/family app | Deployed | P0 | sklarew | 2026-05-10 |
| FEAT-013 | DeepTrail B2C | Mobile-first rockhound/family adventure app | Deployed | P0 | sklarew | 2026-05-10 |
| FEAT-014 | Mobile Navigation | Bottom-nav tab pattern for /path and /trail | Deployed | P0 | sklarew | 2026-05-10 |
| FEAT-015 | Explore Recreation | Camping, boat ramps, trailheads near a watershed | Deployed | P1 | sklarew | 2026-05-10 |
| FEAT-016 | Saved Favorites | Cross-app saved-items store (reach/species/fly/site/fossil/etc.) | Deployed | P1 | sklarew | 2026-05-10 |
| FEAT-017 | Predictive Intelligence | 5 predictive models (catch, hatch, health, species, restoration) | Deployed | P0 | sklarew | 2026-05-09 |
| FEAT-018 | Production Infrastructure | Terraform/Cloud Run/Cloud SQL/CI on GCP | Deployed | P0 | sklarew | 2026-05-09 |
| FEAT-019 | Authentication | Google + Apple OAuth, JWT cookie, anonymous-first | Deployed | P0 | sklarew | 2026-05-08 |
| FEAT-020 | Photo Observations | Camera/EXIF/GCS/private-vs-public toggle | Deployed | P0 | sklarew | 2026-05-09 |

## Status Definitions

- **Draft**: Requirements being gathered
- **Specified**: Feature spec complete (Frame done)
- **Designed**: Technical design complete (Design done)
- **In Test**: Tests being written
- **In Build**: Implementation in progress
- **Deployed**: Released to production
- **Deprecated**: Scheduled for removal

## Dependencies

| Feature | Depends On | Type | Notes |
|---------|------------|------|-------|
| FEAT-002 | FEAT-005 | Required | Forecasting needs ingested restoration outcomes |
| FEAT-003 | FEAT-002, FEAT-006 | Required | Recommendations layer on forecasts + map UI |
| FEAT-004 | FEAT-002 | Required | Funder reports use forecast outputs |
| FEAT-007 | FEAT-005, FEAT-017 | Required | Hatch/catch use ingestion + predictive models |
| FEAT-009 | FEAT-005 | Required | Fossil specimens come through ingestion |
| FEAT-010 | FEAT-008, FEAT-009 | Required | Story uses geology + fossils |
| FEAT-012 | FEAT-007, FEAT-014, FEAT-016 | Required | RiverPath assembles fishing + nav + saved |
| FEAT-013 | FEAT-008, FEAT-009, FEAT-014, FEAT-016 | Required | DeepTrail assembles geology + fossils + nav + saved |
| FEAT-015 | FEAT-005 | Required | Recreation sites come through ingestion |
| FEAT-016 | FEAT-019 | Optional | Cross-device sync needs auth; works anonymously locally |
| FEAT-017 | FEAT-005 | Required | Models train on ingested data |
| FEAT-019 | FEAT-018 | Required | OAuth needs Cloud Run + Secret Manager |
| FEAT-020 | FEAT-019, FEAT-018 | Required | Photo obs need user identity + GCS |

## Feature Categories

### Platform infrastructure
- FEAT-005: Data Ingestion Pipeline
- FEAT-018: Production Infrastructure
- FEAT-019: Authentication

### B2B (RiverSignal)
- FEAT-001: Observation Interpretation
- FEAT-002: Restoration Forecasting
- FEAT-003: Management Recommendations
- FEAT-004: Funder Report Generation
- FEAT-006: Map Workspace

### B2C (RiverPath)
- FEAT-007: Fishing Intelligence
- FEAT-012: RiverPath B2C
- FEAT-014: Mobile Navigation
- FEAT-015: Explore Recreation
- FEAT-016: Saved Favorites
- FEAT-020: Photo Observations

### B2C (DeepTrail)
- FEAT-008: Geologic Context
- FEAT-009: Fossil Discovery
- FEAT-010: Deep Time Storytelling
- FEAT-013: DeepTrail B2C

### Cross-cutting
- FEAT-011: Three-Product UI
- FEAT-017: Predictive Intelligence

## ID Rules

1. Sequential numbering: FEAT-XXX (zero-padded 3 digits)
2. Never reuse IDs, even for cancelled features
3. Reserve FEAT-021+ for next features

## Deprecated/Cancelled

| ID | Name | Status | Reason | Date |
|----|------|--------|--------|------|
| (none) | DeepSignal product card | Deprecated | Removed from landing 2026-05-08; consolidated under DeepTrail | 2026-05-08 |
