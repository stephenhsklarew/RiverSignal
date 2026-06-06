# Design note: Watershed-first admin photo workflow (insect curation, River Story, Splash Card)

| | |
|---|---|
| **Date** | 2026-06-05 |
| **Status** | **In Build** — implemented on `claude/river-path-photo-workflow-qNOzI` (PR #43); not yet merged/deployed. |
| **Origin** | The `/admin/photos` console was species-first (a flat list), but content is curated *per watershed*. Several RiverPath content surfaces (insect/prey photos, the River Story, the `/path` splash cards) had no admin editing path. |
| **Related** | FEAT-020 (Photo Observations), `02-design/technical-design-photo-observations.md`, `plan-2026-05-18-insect-photo-curation.md`, FEAT-010 (Deep Time / River Story), FEAT-012 (RiverPath). |

## Problem
- `/admin/photos` was organized by species, not watershed, so curating a watershed's content meant hunting across species.
- **Insect/prey photos** ("What Fish Are Eating Now" / `species_spotter`) resolved live from `gold.species_gallery` by genus-prefix only — no editorial override, no per-watershed specialization (fish already had `gold.curated_species_photos`).
- The **`/path` splash cards** (image + tagline + narrative per watershed) were hardcoded in `HomePage.tsx` constants — not admin-editable.
- The **River Story** had a viewer but no watershed-scoped entry in the admin nav.

## What ships
1. **Watershed-first `/admin/photos`** — pick a watershed, then manage its content. `AdminPhotosPage.tsx` reworked (~+820 lines); tabs for photos / insects / River Story / Splash Card.
2. **Insect photo curation** — new `gold.curated_insect_photos` (+ `audit.curated_insect_photos_log`), admin CRUD at `/admin/curated-insect-photos*`. Kept **separate** from the fish table so fish lookups are untouched and an insect can share a common name with a fish without colliding. `species_spotter` lookup precedence: `species_gallery` genus match  <  global default `'*'`  <  watershed-specific override. Empty table = exact prior behavior.
3. **Splash Card editor** — new `gold.watershed_splash` (+ `audit.watershed_splash_log`); admin sets per-watershed `image_url` / `tagline` / `narrative`. `GET /sites/{watershed}` returns the overrides; `HomePage.tsx` falls back to built-in `SPLASH_PHOTOS` / `SPLASH_META` (`frontend/src/lib/watershedSplash.ts`) when no row exists. Image upload uses multipart form data (new dep `python-multipart`).
4. **River Story tab** in the watershed-first admin nav (edits the existing `river_stories` narrative + audio regen path).

## Schema (linear chain `… sv01 → ci40 → ws50`)
- `alembic/versions/ci40a1b2c3d4_curated_insect_photos.py` — additive `gold.curated_insect_photos` + audit log.
- `alembic/versions/ws50a1b2c3d4_watershed_splash.py` — additive `gold.watershed_splash` + audit log.
Both additive `CREATE TABLE` — non-destructive; empty tables preserve current behavior.

## Key files
`app/routers/admin.py` (+617; curated-insect + splash CRUD, audit logging), `app/routers/ai_features.py` (`species_spotter` precedence), `app/routers/sites.py` (splash read), `app/audio_cache.py`, `frontend/src/pages/AdminPhotosPage.tsx`, `frontend/src/lib/watershedSplash.ts`, `frontend/src/pages/HomePage.tsx`, `pyproject.toml` (`python-multipart`).

## Verification
- `alembic upgrade head` clean, single head; `gold.curated_insect_photos` + `gold.watershed_splash` created.
- TypeScript build clean; backend imports clean (requires `python-multipart`).
- Existing RiverPath suites green after merging `main` (pytest 12/12, Playwright 8/8).
- Manual: admin sets an insect override → appears in "What Fish Are Eating Now"; admin edits a splash card → `/path` reflects it; empty tables → unchanged behavior.

## Deploy
Merging to `main` runs the migrate job (`ci40`, `ws50`) + frontend/API deploy; the Docker build picks up `python-multipart`. Admin routes are gated by `AdminRoute`.
