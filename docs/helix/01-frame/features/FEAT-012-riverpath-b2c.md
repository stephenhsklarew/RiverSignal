---
dun:
  id: FEAT-012
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-012 -- RiverPath B2C Product Experience

**Feature ID**: FEAT-012
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

RiverPath is the consumer-facing (B2C) mobile-first product for families, anglers, educators, and river enthusiasts exploring Oregon's living rivers. It transforms the same data platform that powers RiverSignal's professional dashboard into story-driven, location-aware river experiences. RiverPath is the primary growth product — its user base (10,000+ monthly families, 500+ daily guides) is an order of magnitude larger than RiverSignal's B2B audience, and it creates the engagement flywheel that drives cross-product adoption to DeepTrail.

## Problem Statement

- **Current situation**: Families visiting Oregon rivers have no way to understand what they're looking at. A parent at the McKenzie River can see clear water and tall trees but can't answer "Is this river healthy?", "What fish live here?", or "Why is the forest burned?" Fishing guides check 5+ websites daily for conditions. No mobile tool combines species data, water conditions, fire recovery stories, fishing intelligence, and stewardship opportunities for a specific river reach.
- **Pain points**: River visits feel shallow for families; kids lose interest after 10 minutes; guides waste 30+ minutes daily assembling a conditions picture; citizen science feels disconnected from outcomes; interpretive signs are static and generic; no seasonal trip planning tool exists for river ecology.
- **Desired outcome**: A family opens RiverPath at any Oregon river and instantly understands its living story — what species are here now, how the river is recovering from fire, when salmon will spawn, where to swim safely, and how to help. A guide opens the morning brief and has everything they need for the day.

## Requirements

### Functional Requirements

#### Home Experience (Story-Driven)
1. Landing page presents 7 watersheds (5 Oregon, 1 Washington, 1 Utah) as visual story blocks with hero photos, health scores, species counts, and narrative taglines, ordered alphabetically
2. Each watershed block includes an inline question input with consumer-oriented placeholder (e.g., "Is today a good day to fly fish the McKenzie?") that submits the question inline within RiverPath — chat response renders as markdown below the watershed block without leaving the /path context
3. Scroll-reveal animations create a narrative flow: each watershed "unfolds" as the user scrolls
4. Species discovery section shows random photo cards from the 18,500+ species with CC-licensed photos

#### River Now — Hero Screen (Wireframe Screen 1)
5. Hero card at top of River Now showing: river name, current flow trend (rising/falling/stable), water temperature, water clarity, and hatch confidence level (high/medium/low)
6. Swipeable horizontal condition cards below hero: Fish Activity (species active now, preferred temps), Insect Activity (current hatch species, confidence), Refuge Status (cold-water refuge classification)
7. Nearby access point cards below condition cards showing name, type, distance, and amenity icons — tappable to expand details (data from FEAT-015 recreation layer)
8. Map pins update dynamically as the user pans the mini map header
9. All content optimized for one-hand scrolling on mobile

#### Living River Story Mode (Wireframe Screen 2 / Feature 2)
10. For each watershed, display a narrative "river story" synthesizing: current conditions (water temp, flow, DO), fire recovery status, restoration progress, and seasonal highlights
11. At least one immersive ecological story card per reach, presented as image-first cards with ecological narratives — prioritize fish, aquatic insect, or restoration visuals
12. Reading mode toggle with three levels: Kids (5th-grade vocabulary, "imagine you're standing in..." framing), Adult (standard narrative), Science (technical with citations and data references)
13. River story timeline: chronological events (fires, restoration projects, species milestones, dam removals) visualized as a scrollable timeline
14. Before/after restoration display showing species counts pre- and post-intervention from `gold.restoration_outcomes` (photo slider descoped to parking lot — MVP uses numeric before/after cards)

#### Species & Observation
15. Species photo gallery with cards showing common name, scientific name, photo, last observed date, and taxonomic group — filterable and scrollable
16. Indicator species checklist showing detected/absent status for ecological health indicators
17. Observation map search: user types a species name (e.g., "mayfly", "salmon", "eagle") and sees every observation as a pin on the map with photo popups
18. "What's here now" — species observed in the current month at the selected watershed

#### Hatch + Aquatic Insect Intelligence (Wireframe Screen 3)
19. Hatch tab displays a seasonal hatch timeline showing insect activity by month for the selected watershed — time horizon is "this month / next month" (hourly forecasts descoped to parking lot)
20. Top 3 likely aquatic insects displayed as species cards ranked by confidence level (high/medium/low), derived from `gold.hatch_confidence` combining observation frequency, current water temperature, and seasonal patterns
21. Each insect card includes: species photo, common name, lifecycle stage indicator (nymph/emerger/adult), and suggested matching fly pattern with fly name and size
22. Matching fly cards section below insect cards showing recommended dry flies and nymphs with: pattern name, hook size, fly type, time of day, and water type suitability
23. Users can save favorite fly patterns to the Saved tab (FEAT-016)

#### Fish Activity + Cold-Water Refuge (Wireframe Screen 4)
24. Fish carousel displaying likely species as illustrated cards with: common name, photo, preferred temperature range, and current activity status
25. Trout cards show preferred temperature range and current water temperature comparison — color-coded green (in range), amber (marginal), red (stress)
26. Cold-water refuge overlay on MapLibre map shading thermal station classifications from `gold.cold_water_refuges`: blue=cold refuge, teal=cool, amber=warm, red=thermal stress
27. Refuge cards below the map explaining ecological importance: why cold-water refuges matter, which species depend on them, and current thermal status of this reach
28. Fish + Refuge is a drilldown from River Now (not a bottom nav tab), accessible via hero card or condition swipe cards

#### Fishing Intelligence
29. Fishing morning brief: water temp, flow, species active, recent stocking, harvest trends — all in one scrollable view
30. Species by river mile table showing what fish are present and where (from `gold.species_by_reach`)
31. Stocking schedule with recent and upcoming events
32. Seasonal trip planner: "When should I visit for salmon?" returns peak activity windows by species and river
33. Swim safety ratings with flow/temperature safety indicators

#### AI Chat
34. Natural-language chat for each watershed with consumer-friendly tone: "Is today a good day to fly fish?", "What bugs are hatching?", "Tell me about the Holiday Farm Fire"
35. Chat responses are grounded in gold-layer data with citations to observations, water quality, and interventions
36. Chat is contextual — knows which watershed the user is viewing
37. Inline chat on homepage: questions submitted from watershed blocks are answered inline with markdown rendering, auto-scrolling to the response

#### Stewardship (Wireframe Screen 5)
38. Restoration timeline cards showing project history: year, category, project name, and outcome summary — presented as a scrollable card timeline
39. Restoration outcome cards displaying before/after species counts from `gold.restoration_outcomes` with clear numeric comparison (e.g., "12 species before → 34 species after")
40. Volunteer and stewardship section showing: watershed council links, "How to help" actions tied to current restoration needs, and upcoming volunteer opportunities (manual curation initially, event feed post-MVP)
41. Action CTAs on stewardship cards: Save (bookmark via FEAT-016), Share (native share API or copy link), Join (link to watershed council or event page)

#### Weather + Live Conditions (Built 2026-04-13, not in original wireframe)
42. NWS 7-day weather forecast displayed as a 3x2 grid on River Now between condition cards and What's Here Now. Shows temperature, conditions, wind for 6 periods (3 days).
43. USGS real-time stream gauge readings (water temp °F, flow cfs) replace monthly averages on hero card when gauges respond. Red pulsing "LIVE" badge indicates real-time data. Station name and timestamp shown.
44. Snowpack card on River Now showing: average SWE (inches), % of normal (color-coded green/amber/red), stations with snow, 7-day trend (building/melting/stable), and a fishing-relevant insight generated from deterministic rules (e.g., "Drought conditions — target cold-water refuges and fish early morning").
45. Fish stocking section showing upcoming stocking events (green "UPCOMING" badge) and recent stocking events.

#### Species Map (Built 2026-04-13)
46. Full-screen MapLibre species map at `/path/map/:watershed` with Fish/Insect toggle. All observations shown as colored pins (blue=fish, amber=insects). Clicking a pin shows popup with photo, common name, scientific name, date. For insect pins, a "Match the hatch" fly recommendation is shown when a pattern match exists.
47. "View Map" button next to "What's Here Now" section on River Now navigates to species map.

#### Deep Time Cross-Sell (Built 2026-04-12)
48. Dark-themed Deep Time card in condition card carousel showing: oldest rock formation age, rock type narrative, nearby fossil count, and "Explore in DeepTrail" link (opens in new tab with lat/lon context). Uses DeepTrail brown theme (#2a2318) with DeepTrail favicon mark.

#### Temperature Display
49. All temperatures displayed in Fahrenheit across all RiverPath pages (hero card, hatch, fish carousel, thermal refuges, trend rates). Conversion utility in `utils/temp.ts`.

#### Watershed State Persistence
50. Selected watershed persists across all tabs (River Now, Explore, Hatch, Steward) via `sessionStorage` and `useWatershed` hook. Changing river on any page updates all pages. "View all rivers" clears selection.
51. Shared `WatershedHeader` component (pin icon + river name + Change modal) used on all tab pages and drilldowns.

#### Explore Map (Built 2026-04-13)
52. Full-screen MapLibre recreation map at `/path/explore-map/:watershed` with type filter chips (All, Camping, Trails, Boats, Fishing, Day Use). Color-coded pins by type. Click pin shows popup with name, type, amenity badges. "← Explore List" back button.

#### Predictive Intelligence + UX Enhancements (Built 2026-05-08)
53. Info tooltips on all prediction sections (hatch forecast, catch probability, health anomaly) explaining the model, confidence level, and data sources in layman's terms. Visible (i) icon expands to plain-language tooltip.
54. Sticky headers on all RiverPath screens (River Now, Explore, Hatch, Steward, Saved) for consistent navigation context while scrolling.
55. Alphabetical watershed ordering on the homepage and in watershed picker modals.
56. Green River (Utah) and Skagit (Washington) watersheds added to the watershed list alongside the 5 Oregon watersheds, expanding coverage to 7 watersheds across 3 states.

### Non-Functional Requirements

- **Mobile performance**: Lighthouse score > 80 on mobile (tested at 4G throttle)
- **Responsive**: Tested at 320px, 375px, 414px, 768px, 1024px, 1440px breakpoints
- **Touch targets**: All interactive elements minimum 48px
- **Offline**: Previously viewed watershed data accessible without internet via service worker cache
- **Load time**: Initial page render < 3 seconds on 4G; subsequent navigation < 1 second
- **Accessibility**: WCAG 2.1 AA on all non-map elements
- **Content tone**: Storytelling, wonder-first, family-friendly; no jargon without explanation

## User Stories

### Existing
- US-040 -- Family at McKenzie opens RiverPath and sees the fire recovery story with before/after species richness
- US-041 -- Angler searches "steelhead" on Deschutes and sees every observation pinned on the map
- US-042 -- Guide opens morning brief before a Deschutes trip and gets conditions + species + stocking in one view
- US-043 -- Parent plans September trip to see salmon spawning on the McKenzie
- US-044 -- Teacher uses RiverPath to prep a field trip itinerary with species checklist for students
- US-045 -- Family discovers volunteer tree-planting event at their favorite swimming hole

### New (Wireframe-Driven)
- US-046 -- Family opens River Now via GPS and sees hero card with current conditions
- US-047 -- Angler checks hatch confidence and sees top 3 insects with matching flies
- US-048 -- Angler views cold-water refuge map overlay to find holding water
- US-049 -- Parent switches story to Kids reading mode for a 7-year-old
- US-056 -- Steward taps Share on a restoration outcome card to send to a friend
- US-057 -- Guide swipes through Fish/Bugs/Refuge condition cards on River Now
- US-058 -- Family asks inline question on homepage and reads the answer without leaving RiverPath

## Edge Cases and Error Handling

- **No observations for species search**: Return "No observations of [species] found in [watershed]" with suggestion to try a broader term or different watershed
- **Offline mode**: Show cached data with "Last updated X ago" banner; disable chat and observation search with clear explanation; species gallery and river story still work from cache
- **Small screen (< 375px)**: Collapse species gallery to single column; hide KPI chips that don't fit; full-width story blocks
- **Slow connection**: Progressive loading — text and stats render first, photos lazy-load with blur-up placeholders
- **No fishing data for watershed**: Metolius has limited sport catch data; show fish habitat distribution and note "harvest tracking data not available for this wild fishery"
- **Chat returns long response**: Auto-scroll chat to latest message; render markdown tables and formatting correctly

## Success Metrics

- B2C mobile Lighthouse performance score > 80
- Families complete primary task (check conditions, read story, identify species) within 30 seconds of opening
- 50%+ of fishing users check conditions 3x+ per week during season (May-Oct)
- Observation search returns results for 95%+ of common species name queries
- PWA install rate > 10% among returning mobile users
- 30% of RiverPath users also access DeepTrail (cross-product)

## Dependencies

- **Other features**: FEAT-001 (ecological summaries), FEAT-005 (data ingestion), FEAT-006 (map workspace), FEAT-007 (fishing intelligence), FEAT-011 (four-product UI architecture), FEAT-014 (mobile navigation — bottom nav shell), FEAT-015 (explore — recreation data for access point cards), FEAT-016 (saved — persistence for save CTAs and fly pattern bookmarks)
- **Data**: 534K+ geolocated observations, 18,500+ species with photos, 31+ gold views (including hatch_chart, cold_water_refuges, restoration_outcomes, whats_alive_now, hatch_confidence), 5 watersheds
- **New gold view**: `gold.hatch_confidence` — combines hatch_chart + water_quality_monthly + seasonal_observation_patterns to produce confidence tier per insect per month
- **External services**: MapLibre basemap tiles, Claude API for chat, Browser Geolocation API

## Out of Scope

- Native iOS/Android apps (PWA first)
- Social features (trip reports, catch photos, community posts)
- Push notifications for conditions alerts
- Citizen science write-back (submitting observations to iNaturalist)
- E-commerce (fishing permits, guided trip booking)
- Hourly hatch forecasts — "now / +4h / tomorrow" (descoped to monthly; see parking lot)
- Before/after restoration photo slider (descoped to numeric comparison; see parking lot)
- Holding water cards with pool/riffle/run classification (no habitat data; see parking lot)
- Trip journals with user-generated photos and notes (UGC feature; see parking lot)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Problem statement describes what exists now and what is broken
- [x] Every functional requirement is testable
- [x] Non-functional requirements have specific numeric targets
- [x] Edge cases cover realistic failure scenarios
- [x] Success metrics are specific to this feature
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
