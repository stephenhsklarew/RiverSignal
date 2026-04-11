---
dun:
  id: FEAT-010
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-010 -- Deep Time Storytelling

**Feature ID**: FEAT-010
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

Deep time storytelling generates AI-powered narratives that describe what ancient ecosystem existed at any location during each geologic period, grounded in fossil evidence and geologic data. This is the signature experience of DeepTrail — transforming abstract geologic data into vivid, family-friendly stories. It also serves DeepSignal by providing scientifically grounded paleoenvironmental reconstructions. Implements PRD P1-9.

## Problem Statement

- **Current situation**: Understanding what the world looked like 33 million years ago at the Painted Hills requires reading academic papers or hoping a museum exhibit covers it. Families standing at a fossil site have no way to visualize the ancient world without specialized knowledge.
- **Pain points**: Geologic time is abstract and difficult to grasp; museum exhibits are static and location-generic; no mobile tool generates location-specific ancient world narratives; the "wow factor" of deep time is lost in data tables.
- **Desired outcome**: A family at the Painted Hills asks "What was this place like 33 million years ago?" and gets: "You're standing in a subtropical forest with towering redwoods and palms. The climate was warm and wet — like modern-day Costa Rica. Rhinoceros-like brontotheres browsed nearby, and early horses the size of dogs ran through the underbrush. The colorful clay layers you see formed from volcanic ash that blanketed the forest floor."

## Requirements

### Functional Requirements

1. For any lat/lon and optional time period, generate a narrative describing the ancient ecosystem using fossil evidence from FEAT-009 and geologic context from FEAT-008
2. Narratives include: climate reconstruction, dominant vegetation, key animal species (with common-name equivalents for non-scientists), geologic setting, and what physical evidence remains today
3. If fossil data exists for the location, cite specific fossil taxa as evidence
4. If no local fossil data exists, use regional formation-level data to construct the narrative
5. Gold view `gold.deep_time_story` provides a chronological timeline of geologic events and paleoenvironments per location
6. Gold view `gold.formation_species_history` links geologic formations to fossil taxa found within them
7. LLM tool function `get_deep_time_story(lat, lon)` returns the full narrative with cited evidence
8. Narratives are generated at three reading levels: expert (DeepSignal), general adult (DeepTrail default), and kid-friendly (DeepTrail family mode)

### Non-Functional Requirements

- **Performance**: Narrative generation within 15 seconds (LLM call)
- **Scientific accuracy**: All factual claims must trace to PBDB, NGMDB, or Macrostrat data; no speculative paleontology without flagging
- **Readability**: Kid-friendly narratives target 5th-grade reading level

## User Stories

- US-036 -- Family at Clarno asks "What lived here?" and gets illustrated narrative (to be created)
- US-037 -- Geologist compares modern McKenzie ecology to Eocene-era ecosystem at same site (to be created)

## Edge Cases and Error Handling

- **No fossil data**: Use geologic unit age and regional paleogeography to construct a general narrative, clearly labeled "based on regional geology, not local fossil evidence"
- **Very recent geology**: For Holocene/Pleistocene locations, focus on glacial history, volcanic events, and early human presence
- **Active volcanic areas**: Include modern volcanic hazard context alongside geologic history

## Success Metrics

- Families rate deep time stories as "engaging" at 4+ out of 5
- Narratives cite specific fossil evidence in 80%+ of Oregon locations with PBDB data
- Cross-product engagement: 30% of RiverPath users also access deep time stories

## Dependencies

- **Other features**: FEAT-008 (geologic units), FEAT-009 (fossil occurrences)
- **External services**: Anthropic Claude API for narrative generation
- **PRD requirements**: Implements P1-9 (Deep time storytelling)

## Out of Scope

- AI-generated paleo-art or 3D reconstructions (text narratives only for MVP)
- Audio narration / podcast-style tours (text only)
- VR/AR overlays
