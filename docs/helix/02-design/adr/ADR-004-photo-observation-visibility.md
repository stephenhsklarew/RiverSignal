---
dun:
  id: ADR-004
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-004: Photo observation visibility flag enforced at view + endpoint layers

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-05-09 | Accepted | Founder | FEAT-020 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | Users want to share some observations publicly (community contribution) but keep others private (favorite fishing spot, personal record). A leak via any public surface (search, map, list, AI Q&A) erodes trust irreparably. |
| Current State | Pre-FEAT-020: every observation was public by default with no visibility flag. |
| Requirements | The privacy boundary must be enforced server-side at every layer that exposes obs data, not by client filters. New endpoints touching obs must be gated by review. |

## Decision

We added a `visibility` column to `user_observations` (values: `public` | `private`, default `public`). Private observations are filtered server-side from every public surface:

1. The user-list endpoint (`GET /api/v1/observations/list`)
2. The geojson endpoint (used by maps)
3. The observation search endpoint
4. The AI reasoning + Q&A grounding context
5. The AI features (predictions trained or served per observation)
6. The time-machine view
7. Site observation counts (`gold.watershed_scorecard` etc.)

Private observations remain in the bronze table (with `visibility` flag in `data_payload`) for the user's own retrieval and for future "share with friends" features. We treat visibility as a defense-in-depth requirement: each new endpoint that joins to user_observations must add the filter, plus a regression test.

**Key Points**: Default public preserves anonymous-first ethos | View-layer + endpoint-layer redundant filters | Tests in `tests/test_observation_features.py` cover all 7 surfaces.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Don't store private obs at all (delete client-side) | Zero leak risk | Loses user data; can't show user their own private obs | Rejected: user wants to *see* their private obs; just doesn't want others to |
| Client-side filtering | Simpler backend | Trivially bypassable; not a real privacy guarantee | Rejected: not a privacy boundary |
| Separate `private_observations` table | Hard separation | Two tables to query; doubles join complexity | Rejected: column-level filter is simpler and easier to audit |
| **Visibility column + view + endpoint filters** | Defense in depth; one column to manage; works in joins | New endpoints must remember to filter — humans are fallible | **Selected: with regression-test gating to compensate for the human risk** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | Real privacy guarantee; user can store sensitive observations without trade-off; supports future "share with specific friends" extension |
| Negative | Every new endpoint that joins user_observations requires extra filter + test; cognitive load on contributors |
| Neutral | EXIF stripping is a separate concern (TM-I-002); visibility doesn't replace it |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| New endpoint forgets the filter | M | C | Mandatory test added to test suite per surface; PR review checklist; consider a SQL view that already filters and is the only thing endpoints can join against |
| Visibility flag misset client-side (default sticks public when user wanted private) | L | H | UI defaults to public with explicit toggle; show visibility status in confirmation; user can edit post-upload |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| Zero private-obs leaks reported | Continuous (any leak is critical) |
| 100% test coverage on filter at all 7 surfaces | Pre-merge gate |

## Concern Impact

- **Concern selection**: Selects `visibility-aware-photo-observations` (privacy) — see `01-frame/concerns.md`.

## References

- `alembic/versions/<rev>_add_observation_visibility_scientific_name.py`
- `app/routers/user_observations.py` (filter implementation)
- `tests/test_observation_features.py` (regression suite)
- `01-frame/threat-model.md` (TM-I-001)
