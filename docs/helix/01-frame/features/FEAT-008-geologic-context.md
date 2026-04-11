---
dun:
  id: FEAT-008
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-008 -- Geologic Context Layer

**Feature ID**: FEAT-008
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

The geologic context layer provides, for any location, the underlying geologic unit, rock type, formation age, lithology, and a narrative explanation of how geology drives the local ecology and hydrology. This feature implements PRD P1-6 and bridges the watershed ecology domain (RiverSignal/RiverPath) with the deep-time domain (DeepSignal/DeepTrail). It is the foundational data layer that all geology features build upon.

## Problem Statement

- **Current situation**: Geologic maps and watershed ecology data exist in completely separate systems. A geologist studying volcanic influences on fish habitat must manually overlay USGS geologic maps on water quality data in GIS. A family visiting Tamolitch Blue Pool has no way to understand that the pool exists because the river flows underground through a lava tube.
- **Pain points**: No tool connects rock type → water chemistry → species distribution in a queryable way; geologic context is invisible in ecological analysis; families can't access the "why" behind what they see at a river or landscape.
- **Desired outcome**: For any lat/lon, the system returns the geologic unit name, age (Ma), rock type, lithology, and an LLM-generated explanation of how this geology shapes the local water, soil, and species.

## Requirements

### Functional Requirements

1. Ingest USGS National Geologic Map Database (NGMDB) polygons for Oregon with unit name, age, rock type, lithology, and formation description
2. Ingest Oregon DOGAMI state geologic maps and hazard layers where they provide higher resolution than NGMDB
3. Ingest Macrostrat geologic columns linking surface units to stratigraphic time and lithologic properties
4. For any lat/lon point, return the intersecting geologic unit with standardized fields: unit_name, formation, rock_type (igneous/sedimentary/metamorphic), lithology (basalt/sandstone/etc), age_min_ma, age_max_ma, period (Miocene/Eocene/etc)
5. Pre-join geologic units to watershed sites so that each site's gold views include geologic context
6. LLM tool function `get_geologic_context(lat, lon)` returns structured geologic data plus narrative
7. Gold view `gold.geology_watershed_link` correlates geologic units with water chemistry, spring locations, and species distribution per watershed
8. Map layer toggle allows users to overlay geologic unit polygons on the existing basemap

### Non-Functional Requirements

- **Performance**: Geologic unit lookup for a point returns within 500ms
- **Coverage**: 95%+ of Oregon land area has geologic unit data
- **Accuracy**: Geologic ages and unit names match USGS published maps

## User Stories

- US-030 -- Researcher queries geologic controls on McKenzie River water temperature (to be created)
- US-031 -- Family at Tamolitch asks "Why is this water so blue?" and gets geologic explanation (to be created)
- US-032 -- Watershed manager correlates post-fire recovery speed with soil parent material (to be created)

## Edge Cases and Error Handling

- **Ocean or water body**: If the point is over water, return the nearest onshore geologic unit with a note
- **Unmapped areas**: Some remote areas may lack detailed geologic mapping; return regional-scale data with a confidence flag
- **Multiple overlapping units**: Where geologic maps overlap (e.g., surficial deposits over bedrock), return both with a priority indicator

## Success Metrics

- 100% of watershed sites have geologic context in their gold views
- LLM can answer "Why is the water cold/warm/impaired here?" using geologic reasoning
- DeepSignal users report geologic context improves their ecological analysis

## Dependencies

- **Other features**: FEAT-005 (Data Ingestion provides the pipeline pattern)
- **External services**: USGS NGMDB ArcGIS REST, Oregon DOGAMI, Macrostrat API
- **PRD requirements**: Implements P1-6 (Geologic context layer)

## Out of Scope

- Subsurface 3D geologic modeling
- Real-time seismic or volcanic monitoring (deferred to P2-6)
- Global geologic coverage (Oregon MVP only)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Problem statement describes what exists now and what is broken
- [x] Every functional requirement is testable
- [x] Non-functional requirements have specific numeric targets
- [x] Edge cases cover realistic failure scenarios
- [x] Success metrics are specific to this feature
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
