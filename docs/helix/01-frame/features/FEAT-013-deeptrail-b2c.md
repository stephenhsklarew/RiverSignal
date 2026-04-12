---
dun:
  id: FEAT-013
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-013 -- DeepTrail B2C Product Experience

**Feature ID**: FEAT-013
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

DeepTrail is the consumer-facing (B2C) mobile-first product for families, rockhounds, and educators exploring Oregon's deep time geology and fossil heritage. It transforms abstract geologic data into vivid, adventure-focused experiences — answering "What ancient world am I standing in?", "Can I legally collect here?", and "What fossils have been found nearby?" DeepTrail is the signature product of the geology domain, making Oregon's world-class fossil sites accessible to non-specialists for the first time.

## Problem Statement

- **Current situation**: Oregon has some of the richest fossil sites in North America (John Day Fossil Beds, Clarno, Painted Hills) but no mobile tool helps visitors understand what they're looking at. Geologic time is abstract and hard to grasp. Fossil databases (PBDB, iDigBio) are designed for researchers, not families. Legal collecting rules vary by land agency and are buried in regulations. Rockhounds use paper BLM maps and word-of-mouth from clubs. Museum exhibits are static and location-generic.
- **Pain points**: A family at the Painted Hills has no way to visualize what this place looked like 33 million years ago without reading academic papers; a rockhound can't easily determine if a site is on BLM land (collecting often permitted) or NPS land (collecting prohibited); families feel uncertain about what's allowed and miss sites they'd love; no tool combines fossil locations + legal status + deep time stories + kid-friendly content.
- **Desired outcome**: A family opens DeepTrail at any Oregon location and sees: what ancient ecosystem existed here (with vivid narrative), what fossils have been found nearby, whether collecting is legal at this exact spot, what minerals others have found, and which museums are worth visiting. A rockhound plans a legal collecting trip with confidence about land ownership and access.

## Requirements

### Functional Requirements

#### Deep Time Storytelling
1. For any lat/lon, generate an AI narrative describing the ancient ecosystem: climate, vegetation, key animal species (with common-name equivalents), geologic setting, and what physical evidence remains today
2. Three reading levels: expert (scientific terminology, full citations), general adult (DeepTrail default), and kid-friendly (5th-grade reading level, "imagine you're standing in..." framing)
3. If fossil data exists for the location, cite specific fossil taxa as evidence with PBDB references
4. If no local fossil data exists, use regional formation-level data with "based on regional geology, not local fossil evidence" qualifier
5. Deep time timeline: chronological visualization of geologic events at a location, oldest at top, with geologic units and fossil occurrences interleaved

#### Fossil Discovery
6. For any lat/lon, display fossil occurrences within configurable radius (default 25km, max 100km) with taxon name, phylum, class, period, age, and distance
7. Fossil cards showing key information in a scannable grid layout
8. Filter fossils by geologic period (Eocene, Miocene, etc.) or phylum (Mollusca, Chordata, etc.)
9. Link to source records (PBDB, iDigBio) for researchers wanting full citation data

#### Legal Collecting Status
10. For any lat/lon, display land ownership (BLM, USFS, NPS, state, private) with collecting legality shown as prominent color-coded badges: green (permitted), yellow (restricted), red (prohibited)
11. Collecting rules text displayed per agency: BLM = "casual collecting of common fossils for personal use"; NPS = "all collecting prohibited"; USFS = "limited, with restrictions"
12. Boundary proximity warning: if point is within 100m of a land ownership boundary, show both parcels and recommend verifying on-site
13. Persistent disclaimer on all legal status responses: "Always verify on-site with posted signs and local regulations"

#### Mineral and Rockhounding Sites
14. Display MRDS mineral deposit locations within radius with commodity names (gold, agate, thunderegg, obsidian, etc.), development status, and coordinates
15. Filter mineral sites by commodity type
16. Where available, show collecting access information and directions

#### Geologic Context
17. For any lat/lon, display the underlying geologic unit: formation name, rock type (igneous/sedimentary/metamorphic), lithology, age range (Ma), and period
18. Color-coded rock type badges for quick visual scanning
19. DOGAMI high-resolution data (16,936 Oregon polygons) supplemented by Macrostrat continental data

#### Location Selector
20. Curated list of Oregon deep time locations: Painted Hills, Clarno, John Day Fossil Beds, Smith Rock, Newberry Volcanic Monument — each with story tagline and coordinates
21. Custom location support: user can enter any lat/lon or use GPS
22. Cross-product navigation: link from geologic features to RiverPath watershed stories where geology drives ecology

#### AI Chat
23. Natural-language questions about geology: "What was this place like 33 million years ago?", "Can I collect fossils here?", "What minerals can I find near Madras?"
24. Chat responses grounded in geologic_units, fossil_occurrences, mineral_deposits, and land_ownership data
25. Kid-friendly mode for family conversations

### Non-Functional Requirements

- **Mobile performance**: Lighthouse score > 80 on mobile
- **Dark theme**: Adventure-focused dark UI with warm accent colors (amber/gold on dark brown)
- **Responsive**: Tested at 320px, 375px, 414px, 768px, 1024px breakpoints
- **Touch targets**: All interactive elements minimum 48px; location cards and fossil cards touch-friendly
- **Offline**: Previously viewed location data accessible via service worker; deep time stories cached per geologic unit
- **Narrative generation**: Deep time story within 15 seconds (LLM call); cached stories < 200ms
- **Legal accuracy**: Land ownership boundaries match BLM/USFS published data; updated quarterly minimum
- **Scientific accuracy**: All fossil claims traceable to PBDB or iDigBio records; no speculative paleontology without flagging
- **Kid readability**: Kid-friendly narratives target 5th-grade reading level (Flesch-Kincaid grade 5)

## User Stories

- US-046 -- Family at Painted Hills asks "What was this place like 33 million years ago?" and gets an illustrated narrative
- US-047 -- Rockhound checks if the BLM land near Fossil, OR allows collecting and plans a weekend trip
- US-048 -- Parent activates kid-friendly mode and reads deep time stories with their 8-year-old
- US-049 -- Teacher prepares a geology field trip to John Day Fossil Beds with species list by period
- US-050 -- Family at Clarno discovers that 44 million years ago, tropical palms and crocodiles lived here
- US-051 -- Rockhound searches for thunderegg collecting sites near Madras using mineral deposit data
- US-052 -- Geologist uses DeepTrail timeline to visualize the volcanic history of Newberry Crater
- US-053 -- Family navigates from DeepTrail to RiverPath to understand why the Metolius is spring-fed (volcanic aquifer)

## Edge Cases and Error Handling

- **No fossil data within radius**: Return "No documented fossil occurrences within Xkm" with suggestion to expand radius or visit nearby known sites (John Day Fossil Beds)
- **Private land**: Clearly state "Private land — collecting requires landowner permission" with red badge; never ambiguous
- **Mixed ownership boundary**: If within 100m of boundary transition, show both parcels and recommend on-site verification with posted signs
- **Ocean or water body location**: Return nearest onshore geologic unit with a note
- **Very recent geology (Holocene)**: Focus on volcanic events, glacial history, and early human presence rather than fossils
- **Active volcanic area**: Include modern volcanic hazard context alongside geologic history
- **No geologic data**: Some remote areas may lack detailed mapping; return regional-scale data with "low resolution — based on regional geology" confidence flag
- **Offline mode**: Show cached deep time stories and fossil data with "Last updated X ago" banner; disable chat and new story generation with explanation
- **Sensitive fossil locality**: Flag known sensitive sites but do not suppress publicly available PBDB data; add "contact land manager before visiting" note

## Success Metrics

- 5,000 monthly active families during season (May-Oct) within 18 months
- 90% of users report feeling confident about collecting legality (in-app survey)
- Deep time narratives cite specific fossil evidence in 80%+ of queries within 50km of PBDB records
- 30% of active users also engage with RiverPath (cross-product)
- Average session duration > 3 minutes (indicating story engagement, not just a quick lookup)
- Kid-friendly mode activated in 20%+ of family sessions
- PWA install rate > 10% among returning mobile users

## Dependencies

- **Other features**: FEAT-008 (geologic context layer), FEAT-009 (fossil discovery layer), FEAT-010 (deep time storytelling), FEAT-011 (four-product UI architecture)
- **Data**: 17,288 geologic units (DOGAMI + Macrostrat), 1,959 fossil occurrences (PBDB + iDigBio), 1,980 mineral deposits (MRDS), 40 land ownership records (BLM SMA), 38 materialized views
- **External services**: MapLibre basemap tiles, Claude API for narrative generation, BLM SMA real-time point query for legal status

## Out of Scope

- Native iOS/Android apps (PWA first)
- AI-generated paleo-art or 3D reconstructions (text narratives only for MVP)
- Audio narration / podcast-style tours
- VR/AR overlays of ancient landscapes
- Fossil identification from photos (image recognition)
- Real-time fossil marketplace or trading
- Permit application processing
- International fossil regulations
- User-submitted fossil locality data (crowdsourcing)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Problem statement describes what exists now and what is broken
- [x] Every functional requirement is testable
- [x] Non-functional requirements have specific numeric targets
- [x] Edge cases cover realistic failure scenarios
- [x] Success metrics are specific to this feature
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
