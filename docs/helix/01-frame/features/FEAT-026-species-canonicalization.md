---
dun:
  id: FEAT-026
  depends_on:
    - helix.prd
    - FEAT-007
    - FEAT-023
---
# Feature Specification: FEAT-026 -- Fish-Species Canonicalization

**Feature ID**: FEAT-026
**Status**: In Build (Phase 1)
**Priority**: P1
**Owner**: Core Engineering
**Date**: 2026-06-08

## Overview

Collapse near-duplicate fish names in "Fish Present" (`/path/now`) and the
`/admin/photos` fish list to one canonical entry per species, so users see a
clean list and admins curate a photo once per species instead of per name
variant. Design of record: `02-design/plan-2026-06-08-species-canonicalization.md`.

## Problem Statement

- **Current**: `gold.species_by_reach` is a UNION of ~6 sources with no name
  canonicalization, so the same fish appears as case/whitespace variants
  ("rainbow trout" vs "Rainbow Trout"), suffix noise ("Chinook" vs "Chinook
  Salmon"), subspecies ("Coastal/Redband Rainbow Trout"), and run-timing baked
  into the name ("Fall/Spring Chinook", "Summer/Winter Steelhead").
  `scientific_name` is unreliable (often a common-name string or NULL). Result:
  cluttered Fish Present lists and admins re-uploading the same photo per variant.
- **Desired**: one canonical entry per species (with run-timing shown as a badge,
  not a separate row); a single photo per species covers all its variants;
  zero per-watershed admin repetition.

## Requirements

### Functional Requirements

#### FR-01: Deterministic canonicalization
- A pure `canonicalize(common_name, scientific_name) -> {key, label, run}` maps
  raw names to a stable canonical key + display label, stripping run-timing
  prefixes (recorded as `run`), descriptor prefixes (coastal/redband/westslope),
  suffix noise, and normalizing case/spacing.
- Acceptance: `Chinook`, `Chinook Salmon`, `Fall Chinook`, `Spring Chinook` →
  one key `chinook salmon`; case/spacing variants collapse; `redbreast sunfish`
  → `Redbreast Sunfish`.

#### FR-02: Forms kept separate (product decision)
- Steelhead and Rainbow Trout remain **separate** canonical entries (anadromous
  vs resident *O. mykiss*); only within-form noise collapses (Summer/Winter
  Steelhead → Steelhead; Coastal/Redband/Rainbow → Rainbow Trout). Kokanee stays
  separate from Sockeye by the same logic.
- Acceptance: `steelhead` key ≠ `rainbow trout` key; each variant set collapses
  to its own single entry.

#### FR-03: Deduped lists with run badges + alias coverage
- `/sites/{ws}/fishing/species` (Fish Present, reused by the admin fish list)
  groups by canonical key, displays the canonical label, and returns `runs`
  (e.g. `["spring","fall"]`) and `aliases` (raw names covered).
- Acceptance: John Day returns one Chinook Salmon (runs spring+fall), one
  Steelhead (summer+winter), one Rainbow Trout — not 8 rows.

#### FR-04: One photo per canonical species
- The curated-photo key is the canonical key, so an admin sets a watershed's
  Chinook photo once; the admin row shows which raw names it covers (`aliases`).
- Acceptance: setting a photo on the canonical entry covers all its variants.

### Non-Functional Requirements

- **Global + automatic**: canonicalization is a shared library applied in the
  gold-serving layer; it applies to every watershed and every future onboarding
  with no per-watershed work.
- **Long-tail via override (Phase 2)**: names the deterministic normalizer can't
  merge (e.g. "Columbia River Redband Trout") are handled by a curated override
  table + an admin "merge?" suggestion — not by editing code.

## Phases

- **Phase 1 (this build)**: `app/lib/species_canonical.py` + dedup in
  `/fishing/species` (fixes Fish Present + admin list + canonical photo key).
- **Phase 2**: curated override table + admin merge UI; one-time re-key of
  existing `curated_species_photos`; apply the same canonicalization to
  catch-probability/species-spotter for cross-surface parity; run/form badges in the UI.

## Implementation Evidence

- `app/lib/species_canonical.py` (canonicalizer), `app/routers/fishing.py`
  (`fishing_species` grouping), `app/routers/admin.py` (`list_watershed_fish`
  reuses it). Tests: `tests/test_species_canonical.py`.

## Dependencies

- **Features**: FEAT-007 (Fishing Intelligence / Fish Present), FEAT-023 (admin photo curation)
- **Data**: `gold.species_by_reach`, `gold.curated_species_photos`

## Out of Scope

- Re-ingestion or changing source adapters (canonicalization is downstream)
- A full taxonomy backbone (GBIF taxon IDs) — the deterministic normalizer +
  override table is sufficient at this scale
- Insect/prey canonicalization (separate surface; future)

## Review Checklist

- [x] Overview connects to a PRD requirement (data quality / UX / curation cost)
- [x] Every functional requirement is testable
- [x] Non-functional requirements stated (global, automatic, long-tail path)
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes reasonable assumptions
