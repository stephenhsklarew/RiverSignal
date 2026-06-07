---
dun:
  id: FEAT-022
  depends_on:
    - helix.prd
    - FEAT-016
    - FEAT-019
    - FEAT-020
    - FEAT-021
---
# Feature Specification: FEAT-022 -- Saved Account Sync

**Feature ID**: FEAT-022
**Status**: Implemented (spec retroactive)
**Priority**: P1
**Owner**: Core Engineering
**Date**: 2026-06-05

## Overview

Saved items persist to the signed-in user's account so they follow the user
across devices, backed by a `saved_items` table (migration `sv01a1b2c3d4`). A
kept shared observation (FEAT-021) is stored as a bookmark snapshot that
preserves the **original photographer + source + observed date + visibility** —
it is never written to `user_observations` for the recipient, so the original
attribution and privacy are never overwritten.

## Problem Statement

- **Current situation**: Saved items (FEAT-016) were localStorage-only, so "sign
  in to keep" only meant *this browser*, and kept shared observations lost the
  original photographer + privacy.
- **Desired outcome**: Saved items sync to the account cross-device; shared
  observations retain correct attribution and visibility.

## Requirements

### Functional Requirements

#### FR-01: Saved-items persistence API
- `GET /saved/items` (auth) returns the user's items; `POST /saved/items` bulk
  upserts (`ON CONFLICT (user_id,item_type,item_id) DO UPDATE`); `DELETE
  /saved/items/{item_type}/{item_id}` removes one. 401 when unauthenticated.
- Acceptance criteria: unauth → 401; authed upsert→list→delete round-trips.

#### FR-02: Write-through + login merge
- When signed in, `save()`/`keepShared()` also POST and `unsave()` also DELETEs.
- On login: push local items up, then GET the account's items and merge by
  `type+id` (dropping expiry → permanent). Network failures fail silently;
  localStorage stays the local source of truth.
- Acceptance criteria: an item saved on device A appears on device B after sign-in;
  a delete on B propagates to A.

#### FR-03: Observation attribution + visibility preserved
- Shared observations carry `observer` (original photographer), `source`,
  `observedAt`, `visibility`, `originObservationId` through share → keep.
- The observation detail screen shows a Visibility row (🔒 Private / 🌐 Public).
- Acceptance criteria: a kept shared **private** observation shows the original
  photographer and "Private" on the detail screen; `observer`/`visibility`
  survive the upsert→list round-trip.

### Non-Functional Requirements

- **Bookmark, not ownership**: a saved observation never creates a
  `user_observations` row for the saver; it is not re-shareable.
- **Cap**: ≤1000 saved items per user.

## Implementation Evidence

- `app/routers/saved_items.py`, `alembic/versions/sv01a1b2c3d4_saved_items.py`
- `frontend/src/components/SavedContext.tsx` (write-through + login merge),
  `frontend/src/pages/SavedPage.tsx`, `frontend/src/pages/PhotoDetailPage.tsx`,
  `frontend/src/components/TappablePhoto.tsx` (PhotoMeta.visibility)
- Tests: `tests/test_riverpath_fixes.py` (saved-items 401 + authed round-trip +
  attribution), `tests/riverpath-fixes.spec.ts` (#6d)
- Cross-device sync verified on prod (two-client same-user round-trip).

## Dependencies

- **Features**: FEAT-016, FEAT-019 (account), FEAT-020 (observation attribution),
  FEAT-021 (shared items that get kept)
- **Data**: `saved_items` table
- **ADR**: ADR-001 (anonymous-first — sync adds persistence, never gates access)

## Out of Scope

- Conflict-resolution UI (last-write-wins by type+id)
- Clearing local Saved on logout (items remain on the device)
- Syncing observation *ownership* (only bookmarks sync; owned observations sync
  via `user_observations` + `/auth/migrate`)

## Review Checklist

- [x] Overview connects to a PRD requirement (cross-device, trust-the-user)
- [x] Every functional requirement is testable
- [x] Non-functional requirements have numeric targets (1000 cap)
- [x] Dependencies reference real artifact IDs + ADR-001
- [x] Out of scope excludes reasonable assumptions
