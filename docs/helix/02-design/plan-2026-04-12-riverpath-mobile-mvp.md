# Design Plan: RiverPath Mobile Web MVP — Wireframe-Driven Rebuild

**Date**: 2026-04-12
**Status**: PROPOSED
**Refinement Rounds**: 1
**Scope**: FEAT-012 (RiverPath B2C), FEAT-014 (Mobile Navigation), FEAT-015 (Explore & Recreation), FEAT-016 (Saved & Favorites)
**Depends On**: plan-2026-04-11-b2c-products.md, riverpath-vision.md
**Source Documents**: `riverpath_mobile_web_mvp_features_v2.md`, `riverpath_wireframe_screen_map.md`

## 1. Problem Statement

The current RiverPath implementation reuses RiverSignal's desktop SitePanel with mobile CSS overrides. The wireframe screen map specifies a fundamentally different information architecture: a 5-tab bottom navigation (River Now / Explore / Hatch / Steward / Saved), swipeable card UX, GPS-first reach lookup, and screen-by-screen layouts purpose-built for one-handed mobile use.

The existing FEAT-012 spec covers data requirements well but does not prescribe the screen architecture, navigation model, or card-based UX patterns from the wireframe. This plan bridges that gap: restructure RiverPath from "RiverSignal with mobile CSS" into a purpose-built mobile web experience.

### Completed: RiverPath Product Separation (2026-04-12)

The RiverPath homepage (`HomePage.tsx`) was leaking users into the RiverSignal B2B product:
- **Ask button**: navigated to `/riversignal/:watershed` — now navigates to `/path/:watershed`
- **Nav links**: pointed to `/riversignal/:ws` — now point to `/path/:ws`
- **Watershed image/title clicks**: opened RiverSignal — now stay on `/path/:ws`
- **Placeholder text**: "Is the McKenzie healthy?" (B2B tone) — now "Is today a good day to fly fish the McKenzie?" (B2C consumer tone)
- **Inline chat**: Ask questions now resolve within the RiverPath homepage via the same `/sites/{ws}/chat` API, with the response rendered inline as markdown below the watershed block. Auto-scrolls to the target watershed when a question is pending.

### Current State vs. Wireframe Target

| Wireframe Screen | Current Implementation | Delta |
|-----------------|----------------------|-------|
| **River Now** (hero) | SitePanel Overview tab with temp/DO/species count | Need: GPS reach lookup, hero card, swipeable condition cards, access point cards |
| **Explore** | Observation text search on map | Need: recreation data ingestion, adventure cards, family/dog filters, map/list toggle |
| **Hatch** | FlyRecommendations + SeasonalPlanner (mini hatch chart) | Need: dedicated tab, insect species cards with confidence, matching fly cards, seasonal timeline |
| **Fish + Refuge** | Fishing tab with condition tables | Need: fish carousel, illustrated cards, cold-water refuge map overlay, holding water cards |
| **Steward** | 5-item timeline extract + static text | Need: restoration timeline cards, volunteer event display, before/after visuals |
| **Saved** | Not implemented | Need: favorites persistence, saved reaches, bookmarking UI |
| **Bottom nav** | Product-level picker (RiverSignal/RiverPath/DeepSignal/DeepTrail) | Need: 5-tab bottom nav replacing product picker on /path routes |

## 2. Descoping Decisions

The wireframe contains several elements that exceed data availability or MVP scope. These are descoped with rationale:

| Wireframe Element | Decision | Rationale |
|------------------|----------|-----------|
| Hatch timeline: "now / +4h / tomorrow" | **Descope to "this month / next month"** | Gold layer has monthly observation counts, not hourly phenology models. Seasonal intelligence is accurate; hourly forecasts are speculative. |
| Fish + Refuge as bottom nav tab | **Descope to drilldown from River Now** | Wireframe lists 6 screens but only 5 bottom nav tabs. Primary flows confirm Fish+Refuge is reached via River Now → Hatch → Refuge, not as a top-level tab. |
| Holding Water Cards (pool/riffle/run) | **Descope entirely** | No pool/riffle habitat classification data exists. Would require NHDPlus reach characterization or ODFW habitat survey ingestion — significant pipeline work for one UI element. |
| Saved: Trip Journal + Hatch Photos + Notes | **Descope to bookmarks only** | Wireframe Screen 6 implies user-generated content (photos, notes, timeline). This is a UGC platform feature requiring a backend user model. MVP Saved = bookmarked reaches/species/flies via localStorage. |
| Before/After restoration slider | **Descope to before/after species count cards** | `gold.restoration_outcomes` has numeric before/after data but no imagery. Photo slider needs curated image sourcing — defer to post-MVP content effort. |
| Adventure cards: difficulty, dog policy, kid suitability | **Partial — ingest what's available, curate the rest** | RIDB has pet/accessibility flags; Oregon State Parks has dog policies. Difficulty ratings require manual curation seed table. |

Descoped items added to `docs/helix/parking-lot.md`.

## 3. Architecture Decisions

### AD-18: RiverPath Navigation — Bottom Tab Bar

- **Question**: How should the 5-tab bottom navigation coexist with the existing product-level navigation?
- **Chosen**: On `/path/*` routes, replace the top-level product picker with a fixed bottom tab bar. The product picker moves to a hamburger menu or settings screen. On `/signal/*`, `/deep/*`, and `/trail/*` routes, navigation remains unchanged.
- **Rationale**: The wireframe specifies a bottom nav as the primary navigation for RiverPath. Keeping the product picker as the top-level nav on /path routes forces an extra tap to reach any RiverPath screen. The product picker is an app-level concern; the bottom tabs are the RiverPath experience.

### AD-19: Screen Architecture — Route-Based vs. Tab State

- **Question**: Are the 5 bottom tabs separate routes or state within a single route?
- **Chosen**: Separate routes under `/path/`:
  - `/path` or `/path/now` → River Now
  - `/path/explore` → Explore
  - `/path/hatch` → Hatch
  - `/path/steward` → Steward
  - `/path/saved` → Saved
  - `/path/fish/:watershed` → Fish + Refuge (drilldown, no bottom tab highlight)
- **Rationale**: Route-based tabs support deep linking, browser back/forward, and URL sharing ("check out this river's hatch chart"). React Router already handles code splitting by route.

### AD-20: GPS → Reach Resolution

- **Question**: How does the hero screen resolve GPS coordinates to a named river reach?
- **Chosen**: Client-side geolocation → `GET /api/v1/sites/nearest?lat=X&lon=Y` (new endpoint) → returns nearest watershed + reach info from `gold.river_miles` using PostGIS `ST_Distance`. Falls back to watershed selector if GPS is denied or unavailable.
- **Rationale**: The wireframe specifies "GPS reach lookup in under 3 seconds." PostGIS spatial queries against 15K stream segments are sub-second. The new endpoint is trivial (single PostGIS query) and reusable across products.

### AD-21: Recreation Data Ingestion Strategy

- **Question**: Which recreation data sources to ingest for Explore?
- **Chosen**: Phase 1 — USFS RIDB (REST API, free key) for campgrounds, trailheads, boat ramps, and day-use areas. Phase 2 — Oregon State Parks ArcGIS FeatureServer for state park access. Both follow the existing `IngestionAdapter` pattern.
- **Rationale**: RIDB has the broadest coverage across federal lands where the 5 target watersheds are located. Oregon State Parks adds state-managed access points. Together they cover the primary recreation access for all 5 MVP watersheds. Family/dog/difficulty metadata is partially available in RIDB amenity flags; gaps filled by a curated seed table.

### AD-22: Saved/Favorites — Client-Side Persistence

- **Question**: How to persist saved items without a user auth system?
- **Chosen**: localStorage with a React context provider (`SavedContext`). Saved items are `{ type: 'reach'|'species'|'fly'|'event', id: string, watershed: string, label: string, thumbnail?: string, savedAt: string }`. The context provides `save()`, `unsave()`, `isSaved()`, and `listSaved()`. A heart/bookmark icon on any saveable card toggles state.
- **Rationale**: Zero backend changes. localStorage survives browser sessions and has ample capacity for bookmark-scale data (IDs + labels, not payloads). Service worker already caches API responses, so saved items render offline from the API cache. Migration path to backend: on future auth implementation, sync localStorage to a `user_favorites` table on first login.

## 4. Data Requirements

### New Data Sources

Multi-source `RecreationAdapter` ingests from 6 public sources into a unified `recreation_sites` table:

| # | Source | Data | Records (OR) | Access | Key? |
|---|--------|------|-------------|--------|------|
| 1 | OSMB Boating Access | Boat ramps, hand launches, fees, hours | 1,815 | ArcGIS FeatureServer | No |
| 2 | USFS Recreation Opportunities | Campgrounds, trailheads, picnic areas | 2,164 | ArcGIS REST | No |
| 3 | BLM Recreation Sites | Campgrounds, day-use, stay limits | 129 | ArcGIS REST | No |
| 4 | SARP Waterfalls | Waterfalls with height, fish ladder status | 5,407 | ArcGIS FeatureServer | No |
| 5 | Oregon HABs Advisories | Harmful algal bloom swim warnings | 245 | ArcGIS FeatureServer | No |
| 6 | RIDB / Recreation.gov | Federal campgrounds, reservability, fees | 500+ | REST JSON | Free key |

Tier 1 (#1-5) uses the same ArcGIS query pattern as 6 existing adapters. No API key needed. Tier 2 (#6) adds enrichment when RIDB_API_KEY is set.

### New Bronze Table

```
recreation_sites (
  id SERIAL PRIMARY KEY,
  site_id INTEGER REFERENCES sites(id),
  source_type VARCHAR NOT NULL,  -- 'ridb', 'state_parks'
  source_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  rec_type VARCHAR,              -- 'campground', 'trailhead', 'boat_ramp', 'day_use', 'fishing_access'
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  geom GEOMETRY(Point, 4326),
  amenities JSONB,               -- {pets_allowed, accessible, water, restrooms, fee}
  family_suitable BOOLEAN,
  difficulty VARCHAR,             -- 'easy', 'moderate', 'difficult' (curated)
  description TEXT,
  url VARCHAR,
  data_payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(source_type, source_id)
)
```

### New Medallion Views

| View | Layer | Supports | Query Pattern |
|------|-------|----------|---------------|
| `silver.recreation_access` | Silver | Explore | Standardized recreation sites across RIDB + State Parks, with normalized amenities |
| `gold.adventures_nearby` | Gold | Explore | Recreation sites enriched with current water conditions + species counts + safety ratings from existing gold views |
| `gold.hatch_confidence` | Gold | Hatch | Combines `hatch_chart` observation counts + `water_quality_monthly` current temp + `seasonal_observation_patterns` to produce a confidence tier (high/medium/low) per insect species per month |

### New API Endpoints

| Endpoint | Method | Purpose | Data Source |
|----------|--------|---------|-------------|
| `/api/v1/sites/nearest` | GET | GPS → nearest watershed + reach | `gold.river_miles` via PostGIS |
| `/api/v1/sites/{ws}/recreation` | GET | Recreation sites for Explore | `gold.adventures_nearby` |
| `/api/v1/sites/{ws}/fishing/hatch-confidence` | GET | Hatch confidence scores | `gold.hatch_confidence` |

### Existing Endpoints Reused (No Changes)

| Screen | Endpoints |
|--------|-----------|
| River Now | `/sites/{ws}`, `/sites/{ws}/story`, `/sites/{ws}/species`, `/sites/{ws}/fishing/conditions` |
| Hatch | `/sites/{ws}/fishing/hatch`, `/sites/{ws}/fishing/fly-recommendations`, `/sites/{ws}/seasonal` |
| Fish + Refuge | `/sites/{ws}/fishing/brief`, `/sites/{ws}/fishing/barriers`, `/sites/{ws}/species` |
| Steward | `/sites/{ws}/story`, `/sites/{ws}/recommendations` |

## 5. Frontend Component Architecture

### New Components

| Component | Screen | Description |
|-----------|--------|-------------|
| `BottomNav.tsx` | Global (/path) | Fixed bottom tab bar: River Now, Explore, Hatch, Steward, Saved. Active tab highlighted. Hidden on non-/path routes. |
| `RiverNowPage.tsx` | River Now | GPS header + mini map + hero condition card + swipeable cards + access point list |
| `HeroCard.tsx` | River Now | River name, flow trend, temperature, hatch confidence badge |
| `ConditionSwipeCards.tsx` | River Now | Horizontal swipeable cards: Fish Activity, Insect Activity, Refuge Status |
| `ExplorePage.tsx` | Explore | Search bar + filter chips + full map + adventure card list with map/list toggle |
| `AdventureCard.tsx` | Explore | Photo, name, distance, type, family/dog/difficulty badges |
| `HatchPage.tsx` | Hatch | Seasonal hatch timeline + insect species cards + matching fly cards |
| `InsectCard.tsx` | Hatch | Insect photo, common name, confidence badge, lifecycle stage, suggested fly |
| `FishRefugePage.tsx` | Fish + Refuge | Fish carousel + trout cards + refuge overlay map |
| `RefugeMap.tsx` | Fish + Refuge | MapLibre with cold-water refuge station shading (blue→red gradient by thermal class) |
| `StewardPage.tsx` | Steward | Restoration timeline + restoration outcome cards + volunteer section |
| `RestorationCard.tsx` | Steward | Project name, year, category, before/after species counts |
| `SavedPage.tsx` | Saved | Grouped list of bookmarked reaches, species, flies |
| `SaveButton.tsx` | Shared | Heart/bookmark toggle icon, wired to SavedContext |
| `SavedContext.tsx` | Shared | React context for localStorage-backed favorites |
| `GPSLocator.tsx` | Shared | GPS locate FAB button, calls geolocation API → `/sites/nearest` |

### Modified Components

| Component | Change |
|-----------|--------|
| `App.tsx` | Add `/path/*` routes; conditionally render BottomNav on /path routes |
| `MapView.tsx` | Add cold-water refuge layer (colored circles by thermal class from `gold.cold_water_refuges`); add recreation site markers |

## 6. Implementation Plan

### Phase 1A: Foundation (enables all other work)

```
F1: BottomNav component + /path/* route structure         -- no dependency
F2: SavedContext (localStorage provider)                   -- no dependency
F3: GPSLocator FAB + /sites/nearest API endpoint           -- no dependency
F4: Recreation ingestion adapter (RIDB)                    -- no dependency
```

All four are independent. F1-F3 are frontend; F4 is pipeline.

### Phase 1B: River Now (hero screen)

```
R1: RiverNowPage shell + GPS header                       -- depends on F1, F3
R2: HeroCard (river name, temp, flow, hatch confidence)    -- depends on R1
R3: ConditionSwipeCards (fish, bugs, refuge)                -- depends on R1
R4: Access point cards (from recreation data)               -- depends on F4
```

R1 is the shell; R2-R4 are independent sections within it.

### Phase 1C: Explore

```
E1: silver.recreation_access + gold.adventures_nearby views -- depends on F4
E2: /sites/{ws}/recreation API endpoint                     -- depends on E1
E3: ExplorePage + AdventureCard components                   -- depends on F1
E4: Map/list toggle + filter chips (family, fishing, dogs)   -- depends on E3
E5: Wire adventure cards to API                              -- depends on E2, E3
```

### Phase 1D: Hatch

```
H1: gold.hatch_confidence materialized view                 -- no dependency
H2: /sites/{ws}/fishing/hatch-confidence endpoint           -- depends on H1
H3: HatchPage shell with seasonal timeline                   -- depends on F1
H4: InsectCard with confidence badge                         -- depends on H2, H3
H5: Matching fly card section (reuse FlyRecommendations)     -- depends on H3
```

### Phase 1E: Fish + Refuge (drilldown)

```
FR1: FishRefugePage shell + fish carousel                    -- depends on F1
FR2: Trout card with temp range + illustration placeholder   -- depends on FR1
FR3: RefugeMap — cold-water refuge overlay on MapLibre       -- depends on FR1
FR4: Wire SaveButton to fish/species cards                   -- depends on F2
```

### Phase 2A: Steward

```
S1: StewardPage shell + restoration timeline                 -- depends on F1
S2: RestorationCard with before/after species counts         -- depends on S1
S3: Volunteer/stewardship section with CTA links             -- depends on S1
```

### Phase 2B: Saved

```
V1: SavedPage shell grouped by type                          -- depends on F1, F2
V2: SaveButton on all card types (reach, species, fly, event) -- depends on F2
V3: Saved count badge on bottom nav tab                       -- depends on F2, F1
```

### Phase 2C: Polish

```
P1: Responsive audit at 320/375/414/768/1024px               -- depends on all
P2: Lighthouse mobile audit (target > 80)                     -- depends on all
P3: Offline/PWA test — cached data renders, save works offline -- depends on V1
P4: End-to-end walkthrough of 3 primary flows                 -- depends on all
```

### Dependency Graph (Critical Path)

```
F4 (RIDB ingestion) → E1 (medallion views) → E2 (API) → E5 (wired UI)
     ↑ longest lead time — API key registration + adapter + initial load

F1 (bottom nav) → all page shells (R1, E3, H3, FR1, S1, V1)

F3 (GPS) → R1 (River Now needs reach lookup)
```

**Critical path**: F4 → E1 → E2 → E5. Recreation data ingestion no longer requires an API key — Tier 1 sources (OSMB, USFS, BLM, SARP, HABs) are all open ArcGIS endpoints. Running `python -m pipeline.cli ingest recreation` will populate data immediately for all 5 watersheds.

**Parallel tracks**: Phase 1B (River Now), 1D (Hatch), and 1E (Fish+Refuge) can proceed concurrently once F1 is done — they use existing API endpoints. Explore (1C) gates on F4.

### Issue Breakdown

| ID | Title | Phase | Depends On | AC Summary |
|----|-------|-------|------------|------------|
| W-069 | RiverPath bottom nav + route structure | F1 | -- | 5-tab bottom bar on /path routes; active tab highlighted; hidden on other routes |
| W-070 | SavedContext localStorage provider | F2 | -- | save/unsave/isSaved/listSaved; persists across sessions; type-safe |
| W-071 | GPS reach locator + /sites/nearest | F3 | -- | Geolocation → PostGIS nearest reach; < 3s; fallback to watershed picker |
| W-072 | RIDB recreation ingestion adapter | F4 | -- | Ingest campgrounds/trailheads/boat ramps for 5 watersheds; amenity flags parsed |
| W-073 | River Now page shell + hero card | R1-R2 | W-069, W-071 | GPS header, river name, temp/flow/hatch confidence |
| W-074 | Condition swipe cards | R3 | W-073 | Horizontal swipeable Fish/Bugs/Refuge cards |
| W-075 | Recreation medallion views | E1 | W-072 | silver.recreation_access + gold.adventures_nearby |
| W-076 | Explore page + adventure cards | E3-E5 | W-069, W-075 | Map/list toggle, filter chips, adventure cards with distance/type |
| W-077 | Hatch confidence view + endpoint | H1-H2 | -- | gold.hatch_confidence; high/medium/low per insect per month |
| W-078 | Hatch page + insect cards | H3-H5 | W-069, W-077 | Seasonal timeline, insect cards with confidence, fly card reuse |
| W-079 | Fish + Refuge drilldown | FR1-FR3 | W-069 | Fish carousel, trout cards, cold-water refuge map overlay |
| W-080 | Steward page | S1-S3 | W-069 | Restoration timeline, outcome cards, volunteer CTAs |
| W-081 | Saved page + bookmark UI | V1-V3 | W-069, W-070 | Grouped saved items, heart icon on cards, badge count on tab |
| W-082 | Mobile responsive + Lighthouse audit | P1-P2 | all | All /path screens pass 320px-1024px; Lighthouse > 80 |

## 7. Acceptance Criteria (Primary User Flows)

### Flow 1: Family — River Now → Explore → Save Trip

1. Family opens `/path` at Metolius River
2. GPS resolves to Metolius, hero card shows: "Metolius River — 8.2°C, 1,450 cfs, Hatch: High"
3. Swipe cards show: Bull Trout active, PMD mayflies emerging, cold-water refuge status
4. Tap "Explore" tab → see nearby campgrounds, trailheads, boat ramps as cards
5. Filter by "family" → subset with family-suitable badges
6. Tap heart on "Camp Sherman Campground" → saved
7. Tap "Saved" tab → see bookmarked campground

### Flow 2: Angler — River Now → Hatch → Fish + Refuge → Save Spot

1. Guide opens `/path` at Deschutes
2. Hero card shows conditions; taps "Hatch" tab
3. Sees seasonal hatch timeline: "October — Blue-Winged Olive (High), October Caddis (Medium)"
4. Taps BWO card → sees lifecycle info + matching flies (Parachute Adams #18, RS2 #20)
5. Taps "Fish" link in hero card → drills into Fish + Refuge
6. Fish carousel shows Steelhead, Rainbow, Brown Trout with temp preferences
7. Refuge map shows thermal classification of stations (blue = cold refuge, red = thermal stress)
8. Saves "Lower Deschutes — Steelhead reach" to favorites

### Flow 3: Steward — River Now → Steward → Join Event

1. Family at McKenzie taps "Steward" tab
2. Sees restoration timeline: Holiday Farm Fire (2020) → Riparian planting (2021-2024) → Species return
3. Restoration outcome card: "McKenzie riparian restoration — 12 species before, 34 species after"
4. Volunteer section shows watershed council link + "How to help" actions
5. Saves restoration project for later reference

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| RIDB API key registration delayed | Low | Low (no longer blocks Explore) | Tier 1 sources (OSMB, USFS, BLM, SARP, HABs) require no key and provide 9,700+ OR sites. RIDB is additive enrichment, not a blocker. |
| Recreation data sparse for remote watersheds (Metolius, Upper Klamath) | Medium | Medium | USFS Recreation Opportunities has good coverage on federal lands; OSMB has boat access statewide; SARP waterfalls fill scenic gaps |
| Bottom nav conflicts with existing product picker UX | Low | Medium | Bottom nav only renders on /path routes; product picker remains on /signal, /deep, /trail |
| Cold-water refuge map overlay slow with 120 station points | Low | Low | 120 points is trivial for MapLibre; use simple circle markers with color gradient |
| localStorage favorites lost on browser data clear | Medium | Low | Acceptable for MVP; warn user in settings; migration to backend on auth implementation |

## 9. Feature Spec Requirements

This plan requires three new feature specs beyond the existing FEAT-012:

| Spec | Scope | Rationale |
|------|-------|-----------|
| **FEAT-014**: RiverPath Mobile Navigation Architecture | Bottom nav, route structure, GPS FAB, responsive layout | FEAT-012 doesn't prescribe navigation model or screen architecture |
| **FEAT-015**: Explore & Recreation Discovery | Recreation data ingestion, adventure cards, filters, map/list toggle | Entirely new capability not in FEAT-012; requires new data source |
| **FEAT-016**: Saved & Favorites | localStorage persistence, SavedContext, bookmark UI, saved page | Explicitly out of scope in FEAT-012; now in wireframe scope |

The remaining wireframe screens (River Now hero, Hatch, Fish+Refuge, Steward) are enhancements to existing FEAT-012 requirements and should be addressed by updating FEAT-012 rather than creating new specs.

## 10. Parking Lot Additions

Items descoped from the wireframe that should be added to `docs/helix/parking-lot.md`:

| Item | Source | Rationale |
|------|--------|-----------|
| Hourly hatch forecasts (now/+4h/tomorrow) | Wireframe Screen 3 | Requires phenology model; monthly data is what exists |
| Holding water cards (pool/riffle/run) | Wireframe Screen 4 | No habitat classification data; needs NHDPlus or ODFW survey ingestion |
| Before/after restoration photo slider | Wireframe Screen 5 | No curated imagery; need content sourcing effort |
| Trip journal with photos and notes | Wireframe Screen 6 | UGC feature requiring backend user model |
| Oregon State Parks adapter | AD-21 Phase 2 | RIDB covers federal lands first; state parks are incremental |

## Governing Artifacts

| Artifact | Path | Role |
|----------|------|------|
| Product Vision | `docs/helix/00-discover/product-vision.md` | Platform strategy |
| RiverPath Vision | `docs/helix/00-discover/riverpath-vision.md` | B2C watershed product definition |
| PRD | `docs/helix/01-frame/prd.md` | Requirements authority |
| FEAT-012 | `docs/helix/01-frame/features/FEAT-012-riverpath-b2c.md` | RiverPath requirements (to be updated) |
| FEAT-014 | `docs/helix/01-frame/features/FEAT-014-mobile-navigation.md` | Mobile nav architecture (new) |
| FEAT-015 | `docs/helix/01-frame/features/FEAT-015-explore-recreation.md` | Explore + recreation data (new) |
| FEAT-016 | `docs/helix/01-frame/features/FEAT-016-saved-favorites.md` | Saved/favorites (new) |
| Source: Features v2 | `~/Downloads/riverpath_mobile_web_mvp_features_v2.md` | Product requirements input |
| Source: Wireframe | `~/Downloads/riverpath_wireframe_screen_map.md` | Screen architecture input |
| B2C Design Plan | `docs/helix/02-design/plan-2026-04-11-b2c-products.md` | Prior B2C design decisions |
