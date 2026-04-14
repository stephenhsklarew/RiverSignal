---
dun:
  id: FEAT-015
  depends_on:
    - helix.prd
    - FEAT-012
    - FEAT-014
---
# Feature Specification: FEAT-015 — Explore & Recreation Discovery

**Feature ID**: FEAT-015
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

RiverPath's Explore tab helps families, anglers, and outdoor travelers find nearby river experiences — campgrounds, trailheads, boat ramps, day-use areas, and fishing access points — presented as adventure cards with filters for family suitability, dog policy, fishing access, and difficulty. This feature requires ingesting recreation data from public sources (USFS RIDB, Oregon State Parks) that do not currently exist in the platform, creating new medallion views, and building a map/list discovery UI.

This addresses PRD persona Sarah (river-visiting family): "I want nearby river experiences so I can build a memorable outing" and wireframe Screen 2 (Explore).

## Problem Statement

- **Current situation**: RiverPath has no recreation access data. The platform ingests ecological, hydrological, and geologic data but nothing about where to park, launch a boat, camp, or access the river. The only spatial discovery is observation text search on the RiverSignal map.
- **Pain points**: Families cannot find access points, trailheads, or campgrounds within RiverPath. They must leave the app and search Google Maps, Recreation.gov, or Oregon State Parks separately. There is no way to filter experiences by family-friendliness, dog policy, or difficulty.
- **Desired outcome**: A family at the Metolius taps "Explore" and sees nearby campgrounds, trailheads, and boat ramps as cards with distance, amenity badges (pets, restrooms, water), and family/difficulty ratings. They toggle between map and list views and filter by what matters to them.

## Requirements

### Functional Requirements

#### Data Ingestion
1. Multi-source `RecreationAdapter` ingests from 6 public sources in priority order:
   - **Tier 1 (no key, ArcGIS)**: OSMB Boating Access (1,815 OR sites — boat ramps, launches), USFS Recreation Opportunities (2,164 sites — campgrounds, trailheads, picnic areas), BLM Recreation Sites (129 sites — campgrounds, day-use), SARP Waterfall Database (5,407 sites — waterfalls with height/fish ladder status), Oregon HABs Advisories (245 sites — harmful algal bloom swim warnings)
   - **Tier 2 (free key)**: RIDB / Recreation.gov (500+ federal campgrounds with reservability, fees, photos)
2. Store all recreation sites in a unified `recreation_sites` bronze table with: name, type (campground/trailhead/boat_ramp/day_use/fishing_access/waterfall/swim_advisory), coordinates, amenities (JSONB), source_type (osmb/usfs_rec/blm_rec/sarp/habs/ridb), source metadata
3. Parse source-specific amenity fields into normalized flags: pets_allowed, accessible, water, restrooms, fee, reservable, parking, height_ft (waterfalls), advisory_status (HABs)
4. Create `silver.recreation_access` materialized view standardizing sites across all data sources with normalized types and amenity fields
5. Create `gold.adventures_nearby` materialized view enriching recreation sites with current water conditions (temp, flow from `gold.water_quality_monthly`), species counts, and safety ratings (from `gold.swim_safety`) for the nearest watershed

#### API
6. Serve recreation data via `GET /api/v1/sites/{watershed}/recreation` returning adventure cards with: name, type, distance from watershed centroid, coordinates, amenities, family_suitable, difficulty, photo_url (if available), and enrichment data (water temp, species count)
7. Support query parameters for filtering: `type` (campground, trailhead, etc.), `family` (boolean), `pets` (boolean), `difficulty` (easy/moderate/difficult)

#### Frontend — Explore Page
8. Explore page accessible via bottom nav "Explore" tab at `/path/explore`
9. Search bar at top for text search across recreation site names and descriptions
10. Filter chips below search: Family, Fishing, Dogs, Easy Walk — each toggleable
11. Map/list toggle: map view shows pins on full-width MapLibre map; list view shows vertically scrollable adventure cards
12. Map pins are colored by type (campground=green, trailhead=brown, boat_ramp=blue, fishing_access=orange, day_use=purple)
13. Tapping a map pin shows a popup card with name, type, distance, and amenity icons
14. Adventure cards display: name, type badge, distance, amenity icons (pets, restrooms, water, accessible), family/difficulty badges, and a thumbnail photo if available
15. Cards are sorted by distance from the user's GPS location (if available) or from the selected watershed centroid
16. Empty state when no results match filters: "No results — try removing a filter" with a reset button

### Non-Functional Requirements

- **Performance**: Recreation API response < 500ms for any watershed (expect < 200 sites per watershed)
- **Responsive**: Map/list toggle works at all breakpoints; list is default on mobile (< 768px), map is default on desktop
- **Touch targets**: Filter chips and cards minimum 48px tap targets
- **Offline**: Previously loaded recreation data available from service worker API cache

## User Stories

- [US-050 — Family finds campground near Metolius](../user-stories/riverpath-stories.md)
- [US-051 — Angler finds boat ramp on Deschutes](../user-stories/riverpath-stories.md)
- [US-052 — Parent filters for dog-friendly access](../user-stories/riverpath-stories.md)

## Current Data Status (2026-04-13)

566 recreation sites loaded across 5 watersheds:
- **By source**: USFS Recreation 406, OSMB Boating Access 160
- **By type**: Boat ramps 183, Trailheads 169, Campgrounds 142, Day use 68, Swim areas 3, Fishing access 1
- **OSMB URL**: `Boating_Access_Sites_OA` FeatureServer from boatoregon-geo.hub.arcgis.com (1,815 statewide)

### Explore Map (Built 2026-04-13)

Full-screen MapLibre recreation map at `/path/explore-map/:watershed`:
- Type filter chips (All, Camping, Trails, Boats, Fishing, Day Use) filter pins in real time
- Color-coded pins: campground=green, trailhead=brown, boat ramp=blue, fishing=orange, day use=purple
- Click pin → popup with name, type, amenity badges
- "← Explore List" back button returns to card view
- "View Map" button on Explore list page navigates to map

## Edge Cases and Error Handling

- **No recreation sites in watershed**: Show message: "No recreation sites found for [watershed]. Check back soon."
- **Sparse data for remote watersheds**: OSMB provides statewide boat access; USFS covers federal lands. Accept sparse coverage with count display.
- **GPS unavailable for distance sorting**: Fall back to alphabetical sort; show "Enable location for distance sorting" hint
- **Filter combination returns zero results**: Show empty state with reset button — don't silently fail

## Success Metrics

- Recreation data loaded for all 5 MVP watersheds with > 10 sites each
- Explore page renders adventure cards within 2 seconds on 4G
- 30%+ of RiverPath sessions include an Explore tab visit
- Filter usage tracked: which filters are most used informs future data curation priorities

## Constraints and Assumptions

- Tier 1 sources (OSMB, USFS, BLM, SARP, HABs) require no API key and use the same ArcGIS query pattern already used by 6 other adapters in the pipeline
- RIDB API key registration is free but may take 1-2 business days — RIDB is additive to Tier 1, not required for launch
- Family suitability and difficulty ratings are not available from any source — require a curated seed table or manual curation for initial launch
- Photo URLs are available for some RIDB sites but coverage is inconsistent; Tier 1 sources have no photos
- ArcGIS feature servers occasionally return partial results or timeout — adapter retries 3 times per source
- Waterfall and HABs data are bonus layers that enhance the Explore experience but are not core recreation access

## Dependencies

- **Other features**: FEAT-014 (bottom nav — Explore tab lives here), FEAT-016 (save an adventure to favorites)
- **External services**: USFS RIDB API (api.recreation.gov), MapLibre for map view
- **Data pipeline**: New `RecreationAdapter` + `recreation_sites` table + 2 new medallion views
- **PRD requirements**: Addresses features v2 Feature 5 (Best river adventures nearby)

## Out of Scope

- Campground reservation or booking functionality
- Real-time availability or occupancy data
- User reviews or ratings of recreation sites
- USFS Trails geometry (5,949 segments — Phase 2 layer)
- Oregon State Parks park boundary polygons (useful but not point-of-access data)
- NWS weather forecasts (valuable but separate feature, not recreation access)
- OSM Overpass queries (variable quality in rural OR; use as Phase 2 gap-fill)
- Trail route geometry or hiking directions
- Fee payment or permit purchasing
