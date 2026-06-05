# Design note: Saved-items account sync + shared-observation attribution

| | |
|---|---|
| **Date** | 2026-06-05 |
| **Status** | **In Build → Deploying.** Backend + frontend implemented and tested locally; ships behind the standard CI deploy. |
| **Origin** | Follow-up to the Saved "share with a friend" feature (`plan-2026-05-10-trip-share.md`, shipped as shared collections — see `06-iterate/riverpath-ux-2026-06.md`). The shared-items banner said "sign in to keep them permanently," but saved items were localStorage-only, so "permanent" meant *this browser*, not the account. |
| **Related** | FEAT-016 (Saved Favorites), FEAT-019 (Authentication), FEAT-020 (Photo Observations). |

## Problem
RiverPath "Saved" items (species, flies, recreation, geology, observation bookmarks) lived only in
`localStorage` (`frontend/src/components/SavedContext.tsx`, key `riverpath-saved`). The login
`migrate` call accepted a `saved_items` field but ignored it — there was no server persistence. So
saved items never followed a user across devices, and a kept *shared observation* carried only
label/photo/coords — losing the original photographer and the original privacy setting.

## Goals
1. **Cross-device sync** — saved items persist to the user's account and load on any device after sign-in.
2. **Attribution preserved** — a shared observation keeps the *original photographer* (never re-attributed to the recipient).
3. **Visibility preserved & visible** — a `private` observation stays `private`; visibility shows on the observation detail screen alongside Photographer / Source / Observed.

## Core principle
A saved item is a **bookmark/snapshot, not ownership**. A kept shared observation is stored in the
new `saved_items` table owned by the *recipient*, with a payload snapshot — it is **never** written
to `user_observations` for the recipient. The original observation (and its owner + privacy) is
untouched. Re-sharing of others' observations is naturally prevented: `handleShare` only shares the
user's *own* API observations + non-observation saves, never bookmarked observations.

## Backend
- **Migration** `alembic/versions/sv01a1b2c3d4_saved_items.py` (down_revision `sc01a1b2c3d4`):
  additive `CREATE TABLE saved_items (id uuid pk, user_id uuid, item_type, item_id, watershed,
  payload jsonb, saved_at, UNIQUE(user_id,item_type,item_id))` + `ix_saved_items_user`.
- **Router** `app/routers/saved_items.py` (registered in `app/main.py`, prefix `/api/v1`), all auth-required (401 otherwise):
  - `GET /saved/items` — the user's items (payload fields spread at top level).
  - `POST /saved/items` — bulk upsert `ON CONFLICT (user_id,item_type,item_id) DO UPDATE`. Used for write-through and the login merge.
  - `DELETE /saved/items/{item_type}/{item_id}`.
  - `payload` carries: `label, sublabel, thumbnail, latitude, longitude` + (observations) `observer, source, observedAt, visibility, originObservationId`.

## Frontend
- **`SavedContext.tsx`**: `SavedItem` gains `observer/source/observedAt/visibility/originObservationId`.
  Write-through when logged in (`save`/`keepShared` → POST, `unsave` → DELETE); on login, push local
  items up then GET + merge by `type+id` (drop expiry → permanent). Server calls fail silently —
  localStorage stays the local source of truth (mirrors `AuthContext.syncSettings`).
- **`SavedPage.tsx`** `handleShare`: enriches each observation with `observer` (the signed-in
  sharer's `name || username`), `source: 'RiverPath'`, `observedAt`, `visibility`, `originObservationId`.
  Shared-observation rows are tappable and open the detail with the original attribution.
- **`SharedCollectionPage.tsx`**: maps the new fields into `addShared`.
- **Detail screen**: `PhotoMeta` gains `visibility`; `PhotoDetailPage.tsx` renders a **Visibility**
  row (🔒 Private / 🌐 Public).

## Verification
- pytest (`tests/test_riverpath_fixes.py`): `/saved/items` 401 unauth; authed round-trip (forged dev
  JWT) upsert→list→delete preserves `observer`/`visibility`; share payload round-trip carries them.
- Playwright (`tests/riverpath-fixes.spec.ts` #6d): recipient opens a shared **private** observation
  → detail screen shows `📷 Original Photographer` + `Visibility: Private`.
- The logged-in cross-device merge (OAuth session) verified manually on staging after deploy.

## Known limitations / follow-ups
- Logout does not clear local saved items (existing behavior).
- Cross-device sync covers `saved_items`; the owner's *own* observations already sync via
  `user_observations` + `/auth/migrate`.
