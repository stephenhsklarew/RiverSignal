# Alignment Review: RiverPath Mobile Web MVP

**Review Date**: 2026-04-13
**Scope**: RiverPath Mobile Web MVP (FEAT-012, FEAT-014, FEAT-015, FEAT-016)
**Status**: complete
**Review Bead**: RiverSignal-2084d07e
**Primary Governing Artifact**: docs/helix/02-design/plan-2026-04-12-riverpath-mobile-mvp.md

## Scope and Governing Artifacts

### Scope

- RiverPath bottom navigation and mobile architecture (FEAT-014)
- RiverPath 6-screen wireframe implementation (FEAT-012)
- Explore and recreation discovery (FEAT-015)
- Saved and favorites (FEAT-016)
- All user stories US-040 through US-058
- Data sources added during build phase

### Governing Artifacts

- `docs/helix/00-discover/product-vision.md`
- `docs/helix/00-discover/riverpath-vision.md`
- `docs/helix/01-frame/prd.md`
- `docs/helix/01-frame/features/FEAT-012-riverpath-b2c.md`
- `docs/helix/01-frame/features/FEAT-014-mobile-navigation.md`
- `docs/helix/01-frame/features/FEAT-015-explore-recreation.md`
- `docs/helix/01-frame/features/FEAT-016-saved-favorites.md`
- `docs/helix/01-frame/user-stories/riverpath-stories.md`
- `docs/helix/02-design/plan-2026-04-12-riverpath-mobile-mvp.md`

## Intent Summary

- **Vision**: RiverPath is the B2C mobile-first river field companion for families, anglers, and stewards
- **Requirements**: 41 functional requirements across 8 areas (hero, story, species, hatch, fish/refuge, fishing, chat, stewardship)
- **Features**: 4 feature specs (FEAT-012 core, FEAT-014 nav, FEAT-015 explore, FEAT-016 saved)
- **User Stories**: 19 stories (US-040 through US-058)
- **Design Plan**: Phased build with dependency graph, 11 tracker beads

## Planning Stack Findings

| Finding | Type | Evidence | Impact |
|---------|------|----------|--------|
| NWS weather not in any spec | missing-link | Built in `app/routers/weather.py`, not in FEAT-012 or design plan | Medium — feature exists, no governing spec |
| USGS real-time gauges not specced | missing-link | Built in `weather.py`, hero card uses it | Medium — replaces static data with live |
| Snowpack card not in any spec | missing-link | Built with gold view + API + UI, not in any FEAT | Medium — significant new feature |
| Species map page not specced | missing-link | `SpeciesMapPage.tsx` at `/path/map/:watershed` | Medium — full MapLibre map page |
| Explore map page not specced | missing-link | `ExploreMapPage.tsx` at `/path/explore-map/:watershed` | Low — UI detail |
| Deep Time card on River Now not specced | missing-link | Cross-product card linking to DeepTrail | Low — enhancement |
| Living River card on DeepTrail not specced | missing-link | Cross-product card linking to RiverPath | Low — enhancement |
| GBIF fossil ingestion not specced | missing-link | `pipeline/ingest/gbif.py`, 965 records | Medium — new data source |
| WQP bugs ingestion not specced | missing-link | `pipeline/ingest/wqp_bugs.py`, 14,876 records | Medium — new data source |
| OSMB boat ramp fix not documented | stale | Design plan references wrong URL | Low — URL updated in code |
| Curated hatch chart not specced | missing-link | `pipeline/seed_hatch_chart.py`, 50 entries | Medium — expert data |
| FEAT-012 FR-12 reading mode toggle | underspecified | Backend param added, no frontend toggle | Medium — incomplete |
| FEAT-012 FR-8 "map pins update as map moves" | underspecified | No dynamic map on River Now | Low — sticky map not built |
| PRD P2-7 Mobile PWA elevated to P1 | stale | PRD still lists it as P2-7 in some places | Low |

## Implementation Map

- **Frontend**: React 19 + TypeScript + Vite at `frontend/src/`
  - Pages: HomePage, RiverNowPage, ExplorePage, ExploreMapPage, HatchPage, FishRefugePage, StewardPage, SavedPage, SpeciesMapPage
  - Shared: BottomNav, WatershedHeader, SavedContext, SaveButton, useWatershed hook
  - Utils: temp.ts (C→F conversion)
- **Backend**: FastAPI at `app/`
  - Routers: sites, fishing, weather (new), geology, reasoning, reports, health, data_status
  - New endpoints: /weather, /conditions/live, /snowpack, /sites/nearest, /cold-water-refuges, /recreation, /stewardship, /fishing/hatch-confidence
- **Pipeline**: 22 ingestion adapters at `pipeline/ingest/`
  - New: gbif.py, wqp_bugs.py, recreation.py (OSMB + USFS)
  - New: seed_hatch_chart.py (curated data)
- **Gold views**: 34 materialized views (was 31 at spec time)
  - New: aquatic_hatch_chart, snowpack_current, (silver.fossil_records rebuilt with image_url)
- **Tests**: 48 Playwright tests in tests/riverpath-mvp.spec.ts + 4 in species-map.spec.ts

## Acceptance Criteria Status

| Story / Feature | Criterion | Status | Evidence |
|-----------------|-----------|--------|----------|
| US-040 Family sees fire recovery | McKenzie fire story visible | SATISFIED | HomePage.tsx watershed blocks + Playwright test |
| US-041 Steelhead search on map | Observation search with map pins | SATISFIED | MapView overlay + SpeciesMapPage |
| US-042 Guide morning brief | Fishing tab with conditions | SATISFIED | FishRefugePage + fishing endpoints |
| US-043 Parent plans salmon trip | Seasonal planner shows peak months | SATISFIED | HatchPage seasonal timeline |
| US-044 Teacher species checklist | Species gallery filterable | SATISFIED | Species gallery with taxonomic filters |
| US-045 Volunteer event | Stewardship section visible | SATISFIED | StewardPage with council links |
| US-046 GPS hero card | GPS → nearest watershed → hero | SATISFIED | RiverNowPage GPS + /sites/nearest |
| US-047 Hatch confidence + flies | Top insects with confidence + flies | SATISFIED | HatchPage with curated + observed data |
| US-048 Cold-water refuge map | Thermal station overlay | SATISFIED | FishRefugePage thermal grid (no MapLibre overlay) |
| US-049 Kids reading mode | Reading level toggle | UNTESTED | Backend param exists, no frontend toggle |
| US-050 Campground near Metolius | Explore adventure cards | SATISFIED | ExplorePage with 566 recreation sites |
| US-051 Boat ramp on Deschutes | Fishing filter in Explore | SATISFIED | ExplorePage filter + 183 boat ramps |
| US-052 Dog-friendly filter | Dogs filter chip | SATISFIED | ExplorePage filter chips |
| US-053 Save campground | Heart icon on adventure cards | SATISFIED | SaveButton + SavedContext |
| US-054 Save fly pattern | Heart icon on fly cards | SATISFIED | SaveButton on HatchPage fly cards |
| US-055 Save restoration project | Save on outcome cards | SATISFIED | SaveButton on StewardPage |
| US-056 Share restoration outcome | Share CTA button | SATISFIED | Web Share API on StewardPage |
| US-057 Swipe condition cards | 3 horizontal swipeable cards | SATISFIED | RiverNowPage condition cards |
| US-058 Inline homepage question | Ask stays in /path context | SATISFIED | HomePage inline chat + Playwright test |

## Gap Register

| Area | Classification | Planning Evidence | Implementation Evidence | Resolution Direction |
|------|----------------|-------------------|------------------------|----------------------|
| Bottom nav (FEAT-014) | ALIGNED | FEAT-014 FR 1-12 | BottomNav.tsx, 5 tabs, route-based | — |
| River Now hero (FEAT-012 FR 5-9) | DIVERGENT | Spec says temp/flow/clarity/hatch confidence | Built: temp/flow/DO/hatch + LIVE badge + weather + snowpack (no clarity metric) | plan-to-code |
| Living River Story (FEAT-012 FR 10-14) | INCOMPLETE | FR-12 reading mode toggle | Backend param exists, no UI toggle | code-to-plan |
| Hatch Intelligence (FEAT-012 FR 19-23) | DIVERGENT | Spec says from gold.hatch_chart | Built: curated_hatch_chart + aquatic filter + GBIF. Much richer than spec. | plan-to-code |
| Fish + Refuge (FEAT-012 FR 24-28) | INCOMPLETE | FR-26 cold-water refuge overlay MAP | Built thermal station grid, no MapLibre map overlay | code-to-plan |
| Stewardship (FEAT-012 FR 38-41) | ALIGNED | Timeline + outcomes + CTAs | StewardPage with Save/Share/Join | — |
| Explore (FEAT-015) | DIVERGENT | Spec says RIDB primary | Built: USFS + OSMB primary, RIDB optional. 566 sites. | plan-to-code |
| Saved (FEAT-016) | DIVERGENT | Spec says grouped by type | Built: grouped by watershed (user requested change) | plan-to-code |
| NWS Weather | UNDERSPECIFIED | Not in any spec | weather.py + River Now weather grid | plan-to-code |
| USGS Real-Time | UNDERSPECIFIED | Not in any spec | weather.py + LIVE badge on hero | plan-to-code |
| Snowpack | UNDERSPECIFIED | Not in any spec | gold.snowpack_current + API + fishing insights | plan-to-code |
| Species Map | UNDERSPECIFIED | Not in any spec | SpeciesMapPage with Fish/Insect toggle + fly matching | plan-to-code |
| Explore Map | UNDERSPECIFIED | Not in any spec | ExploreMapPage with type filters | plan-to-code |
| DeepTrail cross-sell | UNDERSPECIFIED | Not in any spec | Deep Time card + Living River card | plan-to-code |
| GBIF ingestion | UNDERSPECIFIED | Not in any spec | GBIFFossilAdapter, 965 records, image backfill | plan-to-code |
| WQP bugs ingestion | UNDERSPECIFIED | Not in any spec | WQPBugsAdapter, 14,876 records | plan-to-code |
| Curated hatch chart | UNDERSPECIFIED | Not in any spec | seed_hatch_chart.py, 50 entries | plan-to-code |
| Fahrenheit conversion | UNDERSPECIFIED | Not in any spec | utils/temp.ts, all pages converted | plan-to-code |
| Watershed header persistence | UNDERSPECIFIED | Not in any spec | useWatershed hook + sessionStorage | plan-to-code |

## Traceability Matrix

| Vision | Requirement | Feature/Story | Design | Code Status | Classification |
|--------|-------------|---------------|--------|-------------|----------------|
| River wonder first | P1-10 Mobile nav | FEAT-014 | AD-18,19 | BottomNav + routes | ALIGNED |
| River wonder first | P0-5 Map workspace | FEAT-012 FR 5-9 | plan-2026-04-12 R1-R4 | RiverNowPage | DIVERGENT (richer) |
| Stewardship by design | P1-16 CTAs | FEAT-012 FR 38-41 | plan S1-S3 | StewardPage | ALIGNED |
| Fishing intelligence | P1-13 Hatch confidence | FEAT-012 FR 19-23 | plan H1-H5 | HatchPage + curated | DIVERGENT (richer) |
| Fishing intelligence | P1-14 Refuge mapping | FEAT-012 FR 24-28 | plan FR1-FR4 | FishRefugePage | INCOMPLETE (no map) |
| Family ritual creation | P1-15 Reading modes | FEAT-012 FR-12 | — | Backend only | INCOMPLETE |
| River wonder first | P1-11 Recreation | FEAT-015 | plan E1-E5 | ExplorePage + map | DIVERGENT (richer) |
| Family ritual creation | P1-12 Saved | FEAT-016 | plan V1-V3 | SavedPage | DIVERGENT (by watershed) |
| — (not specced) | — | — | — | NWS weather | UNDERSPECIFIED |
| — (not specced) | — | — | — | USGS real-time | UNDERSPECIFIED |
| — (not specced) | — | — | — | Snowpack + insights | UNDERSPECIFIED |
| — (not specced) | — | — | — | Species map page | UNDERSPECIFIED |
| — (not specced) | — | — | — | Cross-product cards | UNDERSPECIFIED |
| — (not specced) | — | — | — | GBIF + WQP bugs + curated hatch | UNDERSPECIFIED |

## Execution Issues Generated

Issues needed to close all non-ALIGNED gaps:

| # | Title | Type | Resolution |
|---|-------|------|------------|
| 1 | Update FEAT-012 with weather, live gauges, snowpack, species map, cross-product cards | chore | plan-to-code |
| 2 | Update FEAT-015 with OSMB source, explore map page, actual data sources used | chore | plan-to-code |
| 3 | Update FEAT-016 to reflect grouped-by-watershed design | chore | plan-to-code |
| 4 | Update design plan with all new endpoints, views, and components | chore | plan-to-code |
| 5 | Build reading mode toggle UI for river stories (FEAT-012 FR-12) | task | code-to-plan |
| 6 | Add cold-water refuge MapLibre overlay to Fish+Refuge page (FEAT-012 FR-26) | task | code-to-plan |
| 7 | Create feature spec for new data sources (GBIF, WQP bugs, curated hatch, SNOTEL gold) | chore | plan-to-code |
| 8 | Update data-sources-roadmap.md with implemented sources | chore | plan-to-code |

## Issue Coverage Verification

| Gap | Covering Issue | Status |
|-----|----------------|--------|
| NWS/USGS/Snowpack not specced | #1 | covered |
| Species map not specced | #1 | covered |
| Cross-product cards not specced | #1 | covered |
| FEAT-015 data source divergence | #2 | covered |
| FEAT-016 grouping divergence | #3 | covered |
| Design plan stale | #4 | covered |
| Reading mode toggle incomplete | #5 | covered |
| Refuge map overlay incomplete | #6 | covered |
| New data sources not specced | #7 | covered |
| Data roadmap stale | #8 | covered |

## Execution Order

1. **Doc updates first** (#1, #2, #3, #4, #7, #8) — all parallelizable, no code changes
2. **Then code** (#5 reading mode, #6 refuge map) — independent of each other

**Critical path**: None — all doc updates are independent. Code tasks #5 and #6 can proceed after or in parallel with doc updates.

## Open Decisions

| Decision | Why Open | Governing Artifacts | Recommended Owner |
|----------|----------|---------------------|-------------------|
| Should PRISM/impaired waters/wetlands be surfaced in UI? | Large bronze datasets with no gold views | data-sources-roadmap.md | Product |
| Should Fahrenheit be a user preference or hard-coded? | Currently hard-coded for US audience | FEAT-012 | Product |
