---
dun:
  id: TD-020
  depends_on:
    - US-photo-observations
    - ADR-004
---
# Technical Design: TD-020-photo-observations-with-visibility

**User Story**: User wants to share river/site observations publicly OR keep them private | **Feature**: [[FEAT-020]] | **Solution Design**: `02-design/plan-2026-04-12-riverpath-mobile-mvp.md`

## Scope

- One vertical slice: photo observation upload (RiverPath + DeepTrail), visibility filtering across all public surfaces.
- Inherits broader B2C app architecture from FEAT-012 / FEAT-013 plans.

## Acceptance Criteria

1. **Given** an authenticated user, **When** they submit a photo with `visibility=private`, **Then** the row is written to `user_observations` with `visibility='private'` AND it does not appear in any public list/map/search/AI surface for any other user.
2. **Given** an authenticated user, **When** they submit a photo with `visibility=public` (default), **Then** it appears in user lists, the map (geojson), search results, and is available to AI grounding contexts.
3. **Given** an anonymous user, **When** they attempt to upload, **Then** they are prompted to sign in (auth required for write).
4. **Given** any user, **When** they view their own observations list, **Then** they see all of their observations regardless of visibility.
5. **Given** an iOS Safari client uploading a HEIC photo, **When** the file is uploaded, **Then** it is accepted and converted/stored as JPEG.

## Technical Approach

**Strategy**: Add `visibility` and `scientific_name` columns to `user_observations`. Apply visibility filter at every public read surface in addition to the silver-view layer. Privacy is enforced server-side with redundant filters (defense-in-depth, see ADR-004).

**Key Decisions**:
- Default `visibility = 'public'` on insert: anonymous-first ethos respected; users explicitly choose to hide.
- Store private obs in the same `user_observations` table (not a separate table): simpler joins, fewer tables to audit.
- Filter applied at: `app/routers/user_observations.py` (list endpoint), the geojson endpoint, observation search, reasoning grounding context, ai_features (predictions), time-machine, and `gold.watershed_scorecard` source counts.

**Trade-offs**:
- Gain: One column to manage; one filter pattern to enforce; tests can be written per surface.
- Lose: Every new endpoint touching `user_observations` must remember the filter — humans are fallible. Mitigated by the regression test suite.

## Component Changes

### Modified: `user_observations` table
- **Current State**: `id, user_id, site_id, taxon_name, observed_at, latitude, longitude, photo_url, data_payload, ingested_at`
- **Changes**: Add `visibility VARCHAR(20) NOT NULL DEFAULT 'public'`; add `scientific_name VARCHAR(255)`; index on `(user_id, visibility)` for fast user list queries.

### Modified: `app/routers/user_observations.py`
- Add `visibility` parameter to `POST /api/v1/observations` request body (Pydantic optional, default `public`).
- Filter `visibility = 'public'` on all public-listing endpoints; user-self-listing endpoints retain access to private items.

### Modified: `app/routers/reasoning.py`, `app/routers/ai_features.py`, `app/routers/sites.py`
- Apply `visibility = 'public'` filter when retrieving observation context for AI grounding or aggregate counts.

### New: `tests/test_observation_features.py`
- 13 tests covering visibility filtering at each public surface; auth requirement; default-public on insert; user-self-list bypass.

## API/Interface Design

```yaml
endpoint: /api/v1/observations
method: POST
auth: required (bearer JWT cookie)
request:
  type: object
  required: [latitude, longitude, taxon_name, observed_at]
  properties:
    latitude: number
    longitude: number
    taxon_name: string
    scientific_name: string
    observed_at: string  # ISO 8601
    photo_base64: string  # optional
    visibility: string  # enum: "public" | "private"; default "public"
    data_payload: object  # optional; observer notes, common_name, etc.
response:
  type: object
  properties:
    id: string  # UUID
    visibility: string
    photo_url: string  # GCS URL if photo provided
    created_at: string
```

```yaml
endpoint: /api/v1/observations/list
method: GET
auth: optional
response:
  type: array
  items:
    type: object
    properties:
      id: string
      taxon_name: string
      latitude: number
      longitude: number
      observed_at: string
      photo_url: string
      visibility: string  # always "public" for non-self queries
```

## Data Model Changes

```sql
-- alembic/versions/<rev>_add_observation_visibility_scientific_name.py
ALTER TABLE user_observations ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'public';
ALTER TABLE user_observations ADD COLUMN scientific_name VARCHAR(255);
CREATE INDEX IF NOT EXISTS idx_user_observations_user_visibility
    ON user_observations(user_id, visibility);
CREATE INDEX IF NOT EXISTS idx_user_observations_visibility_observed_at
    ON user_observations(visibility, observed_at DESC) WHERE visibility = 'public';
```

## Integration Points

| From | To | Method | Data |
|------|-----|--------|------|
| RiverPath frontend (PhotoObservation.tsx) | `POST /api/v1/observations` | REST + multipart | image, lat/lon, visibility, taxon |
| DeepTrail frontend | `POST /api/v1/observations` | REST + multipart | same |
| `app/routers/user_observations.py` | GCS bucket | Cloud Storage SDK | image upload, signed URL |
| `app/routers/reasoning.py` (AI grounding) | user_observations table | SQL with `visibility='public'` | observations near (lat, lon) |
| `silver.species_observations` materialized view | user_observations | view definition `WHERE visibility='public'` | filtered observations |

### External Dependencies
- **Google Cloud Storage**: photo upload + signed URL retrieval. Fallback: if GCS fails on upload, return 503 — don't store the row without the photo.
- **Anthropic API (for reasoning grounding)**: out of scope for this TD; the change is the filter applied to context that flows in.

## Security

- **Authentication**: required for write (upload). Read of own private obs requires auth.
- **Authorization**: A user can only see their own private obs. Public obs are visible to all.
- **Data Protection**: photos stored in GCS with default encryption-at-rest. Private obs photos served via signed URLs with 1-hour expiry; public obs photos served via permanent public URLs.
- **Threats**: TM-I-001 (private obs leak via missing filter); TM-I-002 (EXIF GPS leak — separate; this TD does not yet implement server-side strip); TM-D-002 (large photo upload DoS — addressed via 10 MB limit + MIME whitelist).

## Performance

- **Expected Load**: <100 photo uploads/day initially; up to 10k/day at 10k MAU.
- **Response Target**: < 2s p95 for upload (incl. GCS write); < 200ms p95 for observation list query.
- **Optimizations**: Index on `(user_id, visibility)` for fast self-list; partial index on public obs ordered by `observed_at` for the geojson endpoint; client-side image resize before upload (TODO).

## Testing

- [x] **Unit**: visibility default; Pydantic schema validation
- [x] **Integration**: insert public + private; verify each public surface filters private out
- [x] **API**: end-to-end POST + list; auth-required check; visibility round-trip
- [x] **Security**: another user cannot list user A's private obs; anonymous user cannot list any private obs
- [ ] **Mobile E2E** (Playwright): camera capture flow on iOS Safari + Android Chrome (TODO)

## Migration & Rollback

- **Backward Compatibility**: New columns have defaults; existing rows get `visibility='public'`. No client breaking changes.
- **Data Migration**: Alembic migration is idempotent; run via `riversignal-migrate` Cloud Run job on next deploy.
- **Feature Toggle**: None — visibility is part of the core data model.
- **Rollback**: Revert the migration (`alembic downgrade -1`) drops the columns and indexes; existing functionality unaffected (no code paths require the columns to exist on read).

## Implementation Sequence

1. **DB migration** — Files: `alembic/versions/<rev>_add_observation_visibility_scientific_name.py` — Tests: schema check
2. **Backend write path** — Files: `app/routers/user_observations.py` (POST handler) — Tests: `tests/test_observation_features.py::test_insert_*`
3. **Backend read filters** — Files: `app/routers/user_observations.py`, `reasoning.py`, `sites.py`, `ai_features.py` — Tests: `tests/test_observation_features.py::test_visibility_filter_*`
4. **Silver view filter** — Files: `medallion_views.sql` (`silver.species_observations` adds `WHERE visibility='public'` for user_observations join) — Tests: integration query
5. **Frontend toggle** — Files: `frontend/src/components/PhotoObservation.tsx` — Tests: Playwright (TODO)

**Prerequisites**: FEAT-019 (auth) deployed; GCS bucket exists; users table has user records.

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| New endpoint forgets the filter | M | C | Regression test per surface; PR review checklist; consider migrating to a `silver.public_user_observations` view that's the only thing endpoints can join |
| EXIF GPS leak on public obs (out of scope here) | H | H | Tracked separately as TM-I-002; server-side strip in next release |
| GCS upload failure leaves orphaned DB row | L | M | Wrap upload + insert in a transaction; rollback DB on GCS failure |
