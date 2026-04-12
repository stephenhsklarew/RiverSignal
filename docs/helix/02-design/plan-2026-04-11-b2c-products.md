# Design Plan: RiverPath + DeepTrail B2C Product Experiences

**Date**: 2026-04-11
**Status**: CONVERGED
**Refinement Rounds**: 5
**Scope**: FEAT-012 (RiverPath B2C), FEAT-013 (DeepTrail B2C)
**Depends On**: plan-2026-04-10.md (MVP), plan-2026-04-10-four-product-platform.md (geology expansion)

## 1. Problem Statement and User Impact

RiverPath and DeepTrail are the B2C consumer products that turn the platform's professional-grade data into accessible, story-driven mobile experiences. The B2B products (RiverSignal, DeepSignal) exist and function. The B2C products have initial page shells but lack the depth, polish, and feature completeness specified in FEAT-012 and FEAT-013.

**Current implementation gaps**:

| Capability | FEAT Spec | Current State | Gap |
|------------|-----------|---------------|-----|
| RiverPath story home | FEAT-012 FR-1-4 | HomePage.tsx exists with watershed blocks, scroll animations, inline ask | Mostly complete; needs species discovery section, seasonal highlights |
| River detail narrative | FEAT-012 FR-5-9 | SitePanel has Overview/Species/Fishing/Story/Ask tabs | Story tab exists but narrative is data-dump, not story-driven; no timeline visualization; indicator checklist is basic |
| Observation map search | FEAT-012 FR-10 | API endpoint + MapView overlay built | Working but needs UX polish, empty state, fuzzy matching |
| "What's here now" | FEAT-012 FR-11 | gold.whats_alive_now view exists (39 rows) | No frontend display; needs seasonal context |
| Seasonal trip planner | FEAT-012 FR-12 | gold.hatch_chart + gold.seasonal_observation_patterns exist | No frontend; need to present as "when to visit" guide |
| DeepTrail story | FEAT-013 FR-1-5 | DeepTrailPage.tsx has timeline, fossil cards, legal badge | Story card is static text, not LLM-generated; needs reading level toggle; no fossil evidence citations |
| Fossil gallery filtering | FEAT-013 FR-6-9 | Fossils display but no period/phylum filters | Need filter controls |
| Legal collecting detail | FEAT-013 FR-10-13 | Green/yellow/red badges work; BLM API real-time query | Boundary proximity warning not implemented |
| Mineral sites | FEAT-013 FR-14-16 | gold.mineral_sites_nearby exists (1,980 rows) | No frontend display at all |
| Geologic map layer | FEAT-013 FR-17-19 | API endpoint exists; no map integration in DeepTrail | DeepTrail has no MapLibre map component |
| Kid-friendly mode | FEAT-013 FR-2 | API supports reading_level param | No UI toggle |
| Cross-product nav | FEAT-012/013 | Links exist in headers | Context not preserved on navigation |
| PWA offline | FEAT-012/013 | Service worker + manifest in place | Needs testing; no staleness UI |
| Stewardship | FEAT-012 FR-16-17 | gold.stewardship_opportunities exists (94 rows) | No frontend display |

**Who benefits**: Sarah (river family), Rachel (road trip family), Mike (rockhound), Alex (fishing guide) — the four B2C personas from the PRD.

## 2. Requirements Analysis

### Functional Requirements Summary

**RiverPath** (FEAT-012): 17 requirements across 5 areas — story home (4), river detail (5), location-aware (3), AI chat (3), stewardship (2). Of these, ~60% are partially built.

**DeepTrail** (FEAT-013): 25 requirements across 7 areas — deep time (5), fossils (4), legal (4), minerals (3), geologic context (3), locations (3), chat (3). Of these, ~40% are partially built.

### Non-Functional Requirements

| Requirement | Target | Current | Status |
|-------------|--------|---------|--------|
| Lighthouse mobile score | > 80 | Not measured | UNTESTED |
| Responsive breakpoints | 320-1440px | CSS exists for 480px and 900px | PARTIAL — needs 320px, 375px, 768px |
| Touch targets | 48px minimum | Partially applied | PARTIAL |
| Offline (PWA) | Cached data accessible | SW registered, cache rules written | UNTESTED |
| Deep time generation | < 15s | LLM call not integrated in DeepTrail UI | NOT BUILT |
| Legal accuracy | Quarterly BLM update | Real-time API query works | OK |

### Constraints

- **No new backend tables or API endpoints needed** — all data and endpoints exist. This is purely a frontend + UX design effort.
- **Single React SPA** — all four products share one codebase with route-based code splitting (already working).
- **No auth** — B2C products are public, no login required for MVP.
- **Budget-conscious LLM usage** — deep time narrative generation caches by geologic unit; don't re-generate for repeat visits.

## 3. Architecture Decisions

### AD-14: RiverPath River Detail — Tabs vs. Scroll

- **Question**: Should the RiverPath river detail be a tabbed panel (like RiverSignal's SitePanel) or a single scrolling page?
- **Alternatives**:
  - (A) Reuse SitePanel's tabbed layout with mobile-friendly styling
  - (B) Build a new scrolling page where each section (story, species, fishing, timeline, chat) flows vertically
  - (C) Hybrid: scrolling sections with sticky section tabs for quick jump
- **Chosen**: (A) Reuse SitePanel with enhanced mobile styling
- **Rationale**: SitePanel already has all 5 tabs (Overview, Species, Fishing, Story, Ask) with full data integration. Building a separate scrolling page would duplicate 90% of the code. Instead, when accessed from /path routes, SitePanel gets mobile-optimized CSS: full-width layout instead of 400px sidebar, larger touch targets, story-driven text in Overview tab. The tab bar becomes a horizontal scrollable strip.

### AD-15: DeepTrail Map Integration

- **Question**: Should DeepTrail include a MapLibre map like RiverSignal, or stay map-free?
- **Alternatives**:
  - (A) No map — keep the current card-based scroll layout
  - (B) Full map like RiverSignal with geology overlay
  - (C) Compact map embedded in the location selector area — not the primary interface, but available for spatial context
- **Chosen**: (C) Compact embedded map
- **Rationale**: DeepTrail's primary UX is narrative, not spatial. A full-screen map would make it look like a GIS tool. But users need spatial context: "Where are the nearest fossils?", "What land agency is this?" A compact map (200-300px height) at the top of the page shows the selected location, nearby fossil markers, and land ownership boundaries. Tapping a fossil marker scrolls to its card below.

### AD-16: Deep Time Narrative Generation — Real-time vs. Pre-cached

- **Question**: Should the DeepTrail story card call the LLM in real-time, or serve pre-cached narratives?
- **Chosen**: Hybrid (from AD-12 in the platform design). Check deep_time_stories cache first; if miss, show geologic context data immediately with a "Generating story..." indicator, then stream the LLM response.
- **Rationale**: The deep_time_stories table caches by (geologic_unit_id, reading_level). For the 5 curated Oregon locations, narratives should be pre-generated. For arbitrary lat/lon, real-time generation with a loading state is acceptable at < 15s. This avoids pre-generating 17K stories (one per geologic unit).

### AD-17: Cross-Product Context Transfer

- **Question**: When navigating RiverPath → DeepTrail (or vice versa), how is context preserved?
- **Chosen**: URL query parameters. Navigating from RiverPath to DeepTrail passes `?lat=X&lon=Y&from=path` in the URL. DeepTrail reads these on mount and auto-selects the nearest location. Similarly, DeepTrail → RiverPath passes `?watershed=X&from=trail`.
- **Rationale**: URL params are stateless, bookmarkable, and don't require shared state management. The `from` param enables a "Back to RiverPath" link.

## 4. Interface Contracts

### New API Endpoints Needed

None. All required data is served by existing endpoints:

| RiverPath Need | Existing Endpoint |
|----------------|-------------------|
| Watershed story | GET /sites/{ws}/story |
| Species gallery | GET /sites/{ws}/species |
| Fishing brief | GET /sites/{ws}/fishing/brief |
| Observation search | GET /sites/{ws}/observations/search?q= |
| What's alive now | GET /sites/{ws}/species (filter by recent) |
| Hatch chart | GET /sites/{ws}/fishing/hatch |
| Swim safety | GET /sites/{ws}/swim-safety |
| Chat | POST /sites/{ws}/chat |

| DeepTrail Need | Existing Endpoint |
|----------------|-------------------|
| Deep time story | POST /deep-time/story |
| Timeline | GET /deep-time/timeline/{lat}/{lon} |
| Fossils nearby | GET /fossils/near/{lat}/{lon} |
| Legal status | GET /land/at/{lat}/{lon} |
| Geologic context | GET /geology/at/{lat}/{lon} |
| Mineral sites | (NEW) GET /minerals/near/{lat}/{lon} |
| Geologic units GeoJSON | GET /geology/units?west=&south=&east=&north= |

**One new endpoint needed**: `/minerals/near/{lat}/{lon}` — mineral deposits within radius. Currently `gold.mineral_sites_nearby` exists but has no REST endpoint.

### Frontend Component Changes

| Component | Change |
|-----------|--------|
| **MapView.tsx** | Add optional compact mode (reduced height, no KPI chips, no watershed tabs) for DeepTrail embed |
| **SitePanel.tsx** | Add `mobile` prop that switches to full-width layout; add "What's Here Now" and "Stewardship" sub-sections to Overview tab |
| **HomePage.tsx** | Add species discovery scroll section; add seasonal highlights to watershed blocks |
| **DeepTrailPage.tsx** | Add compact map, mineral sites section, reading level toggle, LLM story generation with loading state, fossil period/phylum filters |
| **NEW: MineralSection.tsx** | Display mineral deposit cards with commodity, status, distance |

## 5. Data Model

No new tables or views needed. All data exists:

| Data Need | Source |
|-----------|--------|
| Species photos (18.5K) | gold.species_gallery |
| What's alive now | gold.whats_alive_now |
| Stewardship opportunities | gold.stewardship_opportunities |
| Hatch chart / seasonality | gold.hatch_chart, gold.seasonal_observation_patterns |
| Mineral sites (1,980) | gold.mineral_sites_nearby |
| Deep time stories (cached) | deep_time_stories table |
| All fossil data | gold.fossils_nearby (1,951 rows) |
| Legal status | Real-time BLM SMA API + land_ownership table |

## 6. Error Handling Strategy

| Scenario | RiverPath | DeepTrail |
|----------|-----------|-----------|
| API timeout | Show cached data with staleness banner | Show geologic context data without LLM narrative |
| No results for search | "No observations of [X] found. Try a broader term." | "No fossils within Xkm. Try expanding the radius." |
| LLM narrative fails | Show structured data (conditions, species counts) without prose | Show geologic unit data without story narrative; retry button |
| Offline | Cached watershed data renders; chat disabled with message | Cached location data renders; story generation disabled |
| No data for watershed | "Data coming soon for this river" placeholder | "No geologic data at this location" with regional fallback |

## 7. Security Considerations

No new attack surfaces beyond what the platform design already addresses. B2C products are read-only (no user-generated content, no auth). The only write operation is the deep_time_stories cache, which is server-side only.

The legal collecting status carries liability risk. Mitigation: persistent disclaimer on every response, quarterly data refresh, boundary proximity warnings, "verify on-site" language. Never state collecting is "definitely legal."

## 8. Test Strategy

### Frontend Tests (New)

| Test | What to Verify |
|------|---------------|
| RiverPath home renders all 5 watersheds | HomePage loads, 5 watershed blocks visible, health scores populated |
| Species discovery section | Random species cards render with photos |
| Observation search shows map pins | Search "salmon" on deschutes → orange markers appear on map |
| DeepTrail location selector | 5 curated locations render; clicking switches content |
| Fossil period filter | Filter by "Eocene" reduces fossil card count |
| Legal badge colors | BLM → green, NPS → red, USFS → yellow |
| Reading level toggle | Toggle to kid-friendly, verify text changes |
| Cross-product navigation | Click DeepTrail link from RiverPath → lands on DeepTrail with lat/lon |
| Offline banner | Service worker active, API blocked → staleness banner appears |
| Mobile responsive | At 375px width, no horizontal overflow, touch targets ≥ 48px |

### Backend Tests (Existing — verify no regression)

The 61 existing tests cover all API endpoints used by both products. No new backend tests needed unless the minerals endpoint is added.

## 9. Implementation Plan with Dependency Ordering

```
Phase A: RiverPath Enhancements (3-5 days)
├── A1: Add species discovery section to HomePage ──no dependency
├── A2: Add "What's Here Now" to SitePanel Overview tab ──no dependency
├── A3: Add stewardship opportunities to SitePanel ──no dependency
├── A4: Add seasonal highlights to watershed blocks ──no dependency
├── A5: Mobile-optimize SitePanel for /path routes ──depends on A2, A3
├── A6: Polish observation search UX (empty state, suggestions) ──no dependency
└── A7: Test responsive breakpoints at 320/375/414/768px ──depends on A5

Phase B: DeepTrail Enhancements (3-5 days)
├── B1: Add mineral sites section + API endpoint ──no dependency
├── B2: Add compact MapLibre map with fossil markers ──no dependency
├── B3: Integrate LLM deep time story generation with loading state ──no dependency
├── B4: Add reading level toggle (adult/kid-friendly/expert) ──depends on B3
├── B5: Add fossil period and phylum filter controls ──no dependency
├── B6: Add cross-product navigation with context transfer ──depends on A5
└── B7: Test responsive + offline + Lighthouse audit ──depends on all

Phase C: Polish (1-2 days)
├── C1: Pre-generate deep time narratives for 5 curated locations ──depends on B3
├── C2: Lighthouse performance audit + fix any score < 80 issues ──depends on A7, B7
└── C3: End-to-end test all user stories from FEAT-012 + FEAT-013 ──depends on all
```

### Parallel Tracks

Phases A and B can proceed concurrently — RiverPath and DeepTrail have no code dependencies on each other (they share components but don't modify them simultaneously). Phase C is integration.

### Issue Breakdown

| ID | Title | Phase | Acceptance Criteria |
|----|-------|-------|---------------------|
| W-058 | RiverPath species discovery section | A1 | HomePage shows scrollable species photo cards from gold.species_gallery |
| W-059 | RiverPath "What's Here Now" display | A2 | SitePanel Overview tab shows species observed this month from gold.whats_alive_now |
| W-060 | RiverPath stewardship section | A3 | SitePanel shows nearby volunteer events from gold.stewardship_opportunities |
| W-061 | RiverPath mobile SitePanel layout | A5 | At /path/:watershed, SitePanel renders full-width with 48px touch targets |
| W-062 | DeepTrail mineral sites section + endpoint | B1 | /minerals/near/{lat}/{lon} API; mineral cards in DeepTrail UI |
| W-063 | DeepTrail compact map with fossil markers | B2 | Embedded map shows fossil occurrence points; click marker scrolls to card |
| W-064 | DeepTrail LLM story generation | B3 | Story card calls /deep-time/story; shows loading state; caches result |
| W-065 | DeepTrail reading level toggle | B4 | Toggle switches narrative between adult/kid-friendly; re-fetches if needed |
| W-066 | DeepTrail fossil filtering | B5 | Period dropdown and phylum dropdown filter fossil card grid |
| W-067 | Cross-product context transfer | B6 | RiverPath → DeepTrail preserves lat/lon; DeepTrail → RiverPath preserves watershed |
| W-068 | B2C Lighthouse + responsive audit | C2 | Both /path and /trail score > 80 on mobile Lighthouse; no overflow at 320px |

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Deep time LLM generation > 15s on first visit | Medium | Medium | Show geologic unit data immediately while LLM generates; cache aggressively; pre-generate for curated locations |
| Mobile Lighthouse score < 80 due to MapLibre bundle (1MB) | High | Medium | MapLibre only loads for routes that use the map; DeepTrail compact map is lazy-loaded; consider lighter basemap style |
| Species discovery section slow to render 18K photo cards | Low | Low | Virtualized scroll (render only visible cards); randomize server-side and return 50 |
| Fossil period filter removes all results for some locations | Medium | Low | Show "No fossils from [period] near this location. Showing all periods." fallback |
| BLM SMA real-time API unavailable | Low | Medium | Fall back to cached land_ownership table data; show "based on cached data" note |

## 11. Observability

### New Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `riverpath_page_views_total` | Counter | `page` (home/detail), `watershed` |
| `deeptrail_page_views_total` | Counter | `page` (home/detail), `location` |
| `deep_time_story_generated` | Counter | `reading_level`, `cache_hit` (true/false) |
| `observation_search_total` | Counter | `watershed`, `result_count_bucket` (0/1-10/11-100/100+) |
| `cross_product_nav_total` | Counter | `from` (path/trail), `to` (trail/path) |
| `reading_level_toggle_total` | Counter | `level` (adult/kid_friendly/expert) |
| `fossil_filter_used_total` | Counter | `filter_type` (period/phylum) |

## Governing Artifacts

| Artifact | Path | Role |
|----------|------|------|
| Product Vision | `docs/helix/00-discover/product-vision.md` | Platform strategy |
| RiverPath Vision | `docs/helix/00-discover/riverpath-vision.md` | B2C watershed product definition |
| DeepTrail Vision | `docs/helix/00-discover/deeptrail-vision.md` | B2C geology product definition |
| PRD | `docs/helix/01-frame/prd.md` | Authority for requirements + personas |
| FEAT-012 | `docs/helix/01-frame/features/FEAT-012-riverpath-b2c.md` | RiverPath requirements |
| FEAT-013 | `docs/helix/01-frame/features/FEAT-013-deeptrail-b2c.md` | DeepTrail requirements |
| FEAT-011 | `docs/helix/01-frame/features/FEAT-011-four-product-ui.md` | Four-product UI architecture |
| Platform Design | `docs/helix/02-design/plan-2026-04-10-four-product-platform.md` | Geology data + UI architecture decisions |
| MVP Design | `docs/helix/02-design/plan-2026-04-10.md` | Core architecture decisions |
