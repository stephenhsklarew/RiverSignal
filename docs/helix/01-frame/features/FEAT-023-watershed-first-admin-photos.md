---
dun:
  id: FEAT-023
  depends_on:
    - helix.prd
    - FEAT-019
    - FEAT-020
---
# Feature Specification: FEAT-023 -- Watershed-First Admin Photos

**Feature ID**: FEAT-023
**Status**: Implemented (spec retroactive)
**Priority**: P2
**Owner**: Core Engineering
**Date**: 2026-06-05

## Overview

The `/admin/photos` console is reorganized to be **watershed-first**: an admin
picks a watershed, then manages its content across tabs — Fish Present photos,
"What Fish Are Eating Now" insect/prey photos, the River Story narrative, and the
Splash Card (FEAT-024). Adds per-watershed insect photo curation backed by
`gold.curated_insect_photos` (migration `ci40a1b2c3d4`), mirroring the existing
fish curation path. Admin-gated (`get_current_admin`).

## Problem Statement

- **Current situation**: `/admin/photos` was species-first (a flat list), but
  content is curated per watershed; insect/prey photos had no editorial override.
- **Desired outcome**: Curate a watershed's content from one watershed-scoped
  surface, including per-watershed insect photo overrides.

## Requirements

### Functional Requirements

#### FR-01: Watershed-first picker
- `/admin/photos` lists watersheds (alphabetical); each opens a watershed-scoped
  console with tabs (fish / insects / river story / splash). The picker thumbnail
  shows the watershed's splash image (override if set, else default — FEAT-024).
- Acceptance criteria: watersheds listed alphabetically; picking one opens its tabs.

#### FR-02: Insect photo curation
- `gold.curated_insect_photos` (+ `audit.curated_insect_photos_log`) with admin CRUD
  at `/admin/curated-insect-photos*`. Kept separate from the fish table so fish
  lookups are untouched and an insect can share a common name with a fish.
- `species_spotter` lookup precedence: gallery genus match < global default `'*'` <
  watershed-specific override. Empty table = prior behavior.
- Acceptance criteria: an admin override appears in "What Fish Are Eating Now";
  with the table empty, behavior is unchanged.

#### FR-03: River Story tab
- A River Story tab in the watershed-first nav edits the `river_stories` narrative
  (+ audio regeneration path).
- Acceptance criteria: the River Story tab is reachable per watershed.

### Non-Functional Requirements

- **Auth**: all `/admin/*` endpoints require `is_admin` (live DB check), else 401/403.
- **Audit**: every curation write is logged to an `audit.*` table.

## Implementation Evidence

- `app/routers/admin.py` (curated-insect CRUD + audit), `app/routers/ai_features.py`
  (`species_spotter` precedence), `alembic/versions/ci40a1b2c3d4_curated_insect_photos.py`
- `frontend/src/pages/AdminPhotosPage.tsx`
- Tests: `tests/admin-splash.spec.ts` (alphabetical picker, admin-gated UI)

## Dependencies

- **Features**: FEAT-019 (admin auth), FEAT-020 (photo/curation foundation), FEAT-024 (splash tab)
- **Data**: `gold.curated_insect_photos`, `gold.curated_species_photos`, `river_stories`

## Out of Scope

- Bulk photo import / CSV upload
- Non-admin curation (community moderation)
- Versioned rollback UI (audit log is append-only record only)

## Review Checklist

- [x] Overview connects to a PRD requirement (content quality / curation)
- [x] Every functional requirement is testable
- [x] Non-functional requirements stated (auth, audit)
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes reasonable assumptions
