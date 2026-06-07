---
dun:
  id: FEAT-024
  depends_on:
    - helix.prd
    - FEAT-012
    - FEAT-023
---
# Feature Specification: FEAT-024 -- Splash Card Editor

**Feature ID**: FEAT-024
**Status**: Implemented (spec retroactive)
**Priority**: P2
**Owner**: Core Engineering
**Date**: 2026-06-05

## Overview

An admin can edit the per-watershed `/path` splash card — image, tagline, and
narrative — through the watershed-first admin console (FEAT-023). Overrides are
stored in `gold.watershed_splash` (migration `ws50a1b2c3d4`); `GET /sites/{ws}`
returns them and `HomePage` falls back to built-in defaults
(`frontend/src/lib/watershedSplash.ts`) when no override exists.

## Problem Statement

- **Current situation**: The `/path` splash cards (image + tagline + narrative per
  watershed) were hardcoded in the frontend with no admin editing path.
- **Desired outcome**: Admins set per-watershed splash content without a code change.

## Requirements

### Functional Requirements

#### FR-01: Splash override storage + read
- `gold.watershed_splash` (+ `audit.watershed_splash_log`); `PUT
  /admin/watershed-splash/{ws}` upserts image/tagline/narrative; `GET /sites/{ws}`
  returns `splash_image_url`/`splash_tagline`/`splash_narrative`; HomePage falls back
  to `SPLASH_PHOTOS`/`SPLASH_META` when null.
- Acceptance criteria: a saved override shows on `/path`; with no override, the
  built-in default shows.

#### FR-02: Image upload that persists immediately
- `POST /admin/watershed-splash/{ws}/image` accepts a multipart image (≤8MB,
  image/* only), stores it (GCS in prod via public bucket; `frontend/public/images/
  uploads/` in dev), returns the URL. Choosing a file **auto-saves** (no separate
  Save click needed); text edits use Save.
- Acceptance criteria: choosing a `.png` persists the override with no extra click;
  the image is servable.

#### FR-03: Picker + /path parity
- The admin watershed picker (FEAT-023) and `/path` both show the saved override
  image (via `GET /admin/watershed-splash` list), not just the default.
- Acceptance criteria: after upload, the override image shows on both the admin
  picker and `/path`.

### Non-Functional Requirements

- **Auth**: admin-only (`get_current_admin`); audit-logged.
- **Bytes**: ≤8MB; `image/*` content-type enforced.

## Implementation Evidence

- `app/routers/admin.py` (watershed-splash CRUD + list + image upload),
  `app/routers/sites.py` (splash read), `app/audio_cache.py` (`put_image_bytes`),
  `alembic/versions/ws50a1b2c3d4_watershed_splash.py`
- `frontend/src/pages/AdminPhotosPage.tsx`, `frontend/src/lib/watershedSplash.ts`,
  `frontend/src/pages/HomePage.tsx`
- Tests: `tests/admin-splash.spec.ts` (upload auto-saves; picker reflects override)

## Dependencies

- **Features**: FEAT-012 (RiverPath splash surface), FEAT-023 (admin console + nav)
- **Data**: `gold.watershed_splash`
- **Infra**: GCS public assets bucket (prod); `python-multipart` (form upload)

## Out of Scope

- Multiple images / carousel per watershed
- Image cropping/editing in-app
- Scheduled / seasonal splash rotation

## Review Checklist

- [x] Overview connects to a PRD requirement (B2C presentation / curation)
- [x] Every functional requirement is testable
- [x] Non-functional requirements have numeric targets (8MB)
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes reasonable assumptions
