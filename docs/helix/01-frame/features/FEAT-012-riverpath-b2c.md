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
1. Landing page presents 5 Oregon watersheds as visual story blocks with hero photos, health scores, species counts, and narrative taglines
2. Each watershed block includes an inline question input: "Ask about this river..." that navigates to the dashboard with the question pre-loaded
3. Scroll-reveal animations create a narrative flow: each watershed "unfolds" as the user scrolls
4. Species discovery section shows random photo cards from the 18,500+ species with CC-licensed photos

#### River Detail Experience
5. For each watershed, display a narrative "river story" synthesizing: current conditions (water temp, flow, DO), fire recovery status, restoration progress, and seasonal highlights
6. Species photo gallery with cards showing common name, scientific name, photo, last observed date, and taxonomic group — filterable and scrollable
7. Fishing intelligence section: morning brief, species by river mile, harvest trends, stocking schedule, hatch chart, swim safety ratings
8. River story timeline: chronological events (fires, restoration projects, species milestones, dam removals) visualized as a scrollable timeline
9. Indicator species checklist showing detected/absent status for ecological health indicators

#### Location-Aware Features
10. Observation map search: user types a species name (e.g., "mayfly", "salmon", "eagle") and sees every observation as a pin on the map with photo popups
11. "What's here now" — species observed in the current month at the selected watershed
12. Seasonal trip planner: "When should I visit for salmon?" returns peak activity windows by species and river

#### AI Chat
13. Natural-language chat for each watershed: "Is this river healthy?", "What fish are spawning?", "Tell me about the Holiday Farm Fire"
14. Chat responses are grounded in gold-layer data with citations to observations, water quality, and interventions
15. Chat is contextual — knows which watershed the user is viewing

#### Stewardship
16. Nearby volunteer events and watershed council links (manual curation initially)
17. "How to help" actions tied to current restoration needs at each watershed

### Non-Functional Requirements

- **Mobile performance**: Lighthouse score > 80 on mobile (tested at 4G throttle)
- **Responsive**: Tested at 320px, 375px, 414px, 768px, 1024px, 1440px breakpoints
- **Touch targets**: All interactive elements minimum 48px
- **Offline**: Previously viewed watershed data accessible without internet via service worker cache
- **Load time**: Initial page render < 3 seconds on 4G; subsequent navigation < 1 second
- **Accessibility**: WCAG 2.1 AA on all non-map elements
- **Content tone**: Storytelling, wonder-first, family-friendly; no jargon without explanation

## User Stories

- US-040 -- Family at McKenzie opens RiverPath and sees the fire recovery story with before/after species richness
- US-041 -- Angler searches "steelhead" on Deschutes and sees every observation pinned on the map
- US-042 -- Guide opens morning brief before a Deschutes trip and gets conditions + species + stocking in one view
- US-043 -- Parent plans September trip to see salmon spawning on the McKenzie
- US-044 -- Teacher uses RiverPath to prep a field trip itinerary with species checklist for students
- US-045 -- Family discovers volunteer tree-planting event at their favorite swimming hole

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

- **Other features**: FEAT-001 (ecological summaries), FEAT-005 (data ingestion), FEAT-006 (map workspace), FEAT-007 (fishing intelligence), FEAT-011 (four-product UI architecture)
- **Data**: 534K+ geolocated observations, 18,500+ species with photos, 21+ ecological gold views, 5 watersheds
- **External services**: MapLibre basemap tiles, Claude API for chat

## Out of Scope

- Native iOS/Android apps (PWA first)
- User accounts and saved favorites (deferred to auth implementation)
- Social features (trip reports, catch photos, community posts)
- Push notifications for conditions alerts
- Citizen science write-back (submitting observations to iNaturalist)
- E-commerce (fishing permits, guided trip booking)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Problem statement describes what exists now and what is broken
- [x] Every functional requirement is testable
- [x] Non-functional requirements have specific numeric targets
- [x] Edge cases cover realistic failure scenarios
- [x] Success metrics are specific to this feature
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
