---
dun:
  id: FEAT-009
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-009 -- Fossil Discovery Layer

**Feature ID**: FEAT-009
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

The fossil discovery layer provides fossil occurrence data from the Paleobiology Database, iDigBio, and GBIF, enabling users to discover what ancient organisms lived at any location and when. Combined with land ownership data, it answers the critical question "Can I legally collect here?" This feature implements PRD P1-7 and P1-8, and is the core attraction of DeepTrail.

## Problem Statement

- **Current situation**: Fossil occurrence data exists in academic databases (PBDB, iDigBio) that are inaccessible to general users. Families visiting the John Day Fossil Beds don't know what they might find or where. Rockhounds can't easily determine if a site is on BLM land (collecting often permitted) or NPS land (collecting prohibited).
- **Pain points**: Legal collecting rules vary by land agency and are buried in regulations; fossil databases use academic interfaces designed for researchers; no mobile-friendly tool combines fossil locations + legal status + access information; families feel uncertain about what's allowed.
- **Desired outcome**: A user opens DeepTrail at any location and sees: what fossils have been found nearby, what geologic period they're from, whether collecting is legal at this exact spot, and what museums have specimens from this area.

## Requirements

### Functional Requirements

1. Ingest Paleobiology Database (PBDB) fossil occurrences for Oregon via REST API (paleobiodb.org/data1.2) with taxon name, age, coordinates, collector, and reference
2. Ingest BLM Surface Management Agency land ownership polygons for Oregon with agency, designation, and management status
3. For any lat/lon, return fossil occurrences within configurable radius (default 25km) with taxon, age, and geologic period
4. For any lat/lon, return land ownership (BLM, USFS, NPS, state, private) and legal collecting status based on agency rules
5. Legal collecting status uses these rules: BLM = "permitted for personal use (reasonable amounts)"; USFS = "permitted for personal use with restrictions"; NPS = "prohibited"; State parks = "varies, check locally"; Private = "prohibited without permission"
6. Gold view `gold.fossils_nearby` returns fossil occurrences with taxa, ages, and museum/collection information
7. Gold view `gold.legal_collecting_sites` returns public lands where collecting is permitted with access information
8. LLM tool function `get_fossils_near_me(lat, lon, radius_km)` returns fossil data with legal status
9. LLM tool function `is_collecting_legal(lat, lon)` returns definitive land ownership and collecting rules

### Non-Functional Requirements

- **Performance**: Fossil lookup within 2 seconds for 25km radius
- **Legal accuracy**: Land ownership boundaries match BLM/USFS published data within current fiscal year
- **Coverage**: All known PBDB fossil occurrences in Oregon loaded (estimated 5K+)

## User Stories

- US-033 -- Family at Painted Hills asks "What fossils can we find here?" (to be created)
- US-034 -- Rockhound plans a legal collecting trip to BLM land near Fossil, Oregon (to be created)
- US-035 -- Teacher plans a field trip to John Day Fossil Beds with species list by period (to be created)

## Edge Cases and Error Handling

- **Private land**: Clearly state "Private land — collecting requires landowner permission" with no ambiguity
- **Mixed ownership boundary**: If a point is within 100m of a land ownership boundary, show both parcels and recommend verifying on-site
- **No fossils in radius**: Return "No documented fossil occurrences within Xkm" with suggestion to expand radius or visit nearby known sites
- **Sensitive fossil sites**: Some localities may be protected even on public land; flag known sensitive sites

## Success Metrics

- 90% of DeepTrail users report feeling confident about collecting legality
- Fossil occurrence data covers all major Oregon fossil regions
- LLM correctly identifies land ownership for 99%+ of Oregon locations

## Dependencies

- **Other features**: FEAT-008 (Geologic Context provides age/formation context for fossils)
- **External services**: Paleobiology Database API, BLM SMA ArcGIS service
- **PRD requirements**: Implements P1-7 (Fossil discovery) and P1-8 (Land access and legality)

## Out of Scope

- Fossil identification from photos (image recognition)
- Real-time fossil marketplace or trading
- Permit application processing
- International fossil regulations
