---
dun:
  id: helix.test-plan
  depends_on:
    - helix.architecture
---
# Test Plan

## Testing Strategy

**Goals**: Catch regressions before they reach production users; protect privacy boundaries (especially photo observation visibility); validate ingestion correctness on schema-changing upstreams.

**Out of Scope**: Full unit-level coverage of UI components; cross-browser visual regression beyond manual review; load testing (premature at current scale).

### Test Levels

| Level | Coverage Target | Priority |
|-------|-----------------|----------|
| Contract | All public API endpoints | P0 |
| Integration | Auth flow; visibility filtering across all 7 surfaces; ingestion adapter ↔ DB | P0 |
| Unit | Business logic in routers (e.g., predictions calc, fishing rules, narrative grounding context build) | P1 |
| E2E | Each app's golden path on at least one mobile viewport | P0 |

### Frameworks

| Type | Framework | Reason |
|------|-----------|--------|
| Backend (contract / integration / unit) | pytest + FastAPI TestClient | Native, fast, async-friendly |
| Frontend (component) | Vitest (TODO) | Vite-native; not yet adopted |
| Frontend (E2E) | Playwright | Real-browser, mobile profiles, visual screenshots; already in use |
| Linting / type checks | TypeScript `tsc --noEmit`, Python `ruff` (TODO) | Cheap pre-flight gate |

## Test Data

| Type | Strategy |
|------|----------|
| Fixtures | `tests/fixtures/` JSON files for canonical bronze rows per source; `conftest.py` loads on demand |
| Factories | Factory functions in `tests/conftest.py` for creating users, observations, sites with sensible defaults |
| Mocks | `httpx_mock` for upstream public-data API calls; static `responses` fixtures for OAuth flows |

## Coverage Requirements

| Metric | Target | Minimum | Enforcement |
|--------|--------|---------|-------------|
| Backend line coverage | 80% | 70% | CI report (no block yet — TODO) |
| Critical paths | 100% | 100% | Required (PR review) |
| Visibility-filter regressions | 100% | 100% | Mandatory test in `tests/test_observation_features.py` per public surface |
| Auth flow | 100% | 100% | Manual E2E + automated where feasible |

### Critical Paths (P0)

1. **Auth flow**: anonymous → Google OAuth → `/auth/me` returns user → JWT cookie set → username setup → migrate anonymous data
2. **Photo observation upload**: signed-in user POSTs photo with `visibility=private` → row written → does not leak via any of 7 surfaces
3. **Ingestion → gold view → API**: bronze write → silver/gold refresh → API endpoint returns expected shape (e.g., snowpack endpoint returns `station_count`)
4. **AI narrative grounding**: warehouse context bundle → Anthropic call → cached in `gold.deep_time_story` → served on subsequent requests
5. **Anonymous flow**: any read endpoint works without cookie

### Secondary Paths (P1–P2)

- P1: Saved items round-trip (anonymous → authed migration); watershed picker; settings panels
- P2: Edge cases (missing photo URL; observation with no taxon; cold-start AI cache miss; iOS Safari quirks)

## Implementation Order

1. **Contract tests for every public API endpoint** — must exist before any new endpoint ships.
2. **Visibility regression suite** (`tests/test_observation_features.py`) — already in place; expand on every new public surface.
3. **Integration tests for auth flow** — round-trip through Google OAuth callback simulation.
4. **Ingestion adapter tests against canned upstream JSON** — protects against silent schema drift.
5. **Playwright E2E for each app's golden path** — RiverPath tab navigation, DeepTrail tab navigation, RiverSignal map load.
6. **Predictive-model serving tests** — output schema; null handling.

## Infrastructure

| Requirement | Specification |
|-------------|---------------|
| CI Tool | GitHub Actions (`.github/workflows/deploy.yml` runs build + deploy; separate test workflow TODO) |
| Test DB | Local Postgres 17 in Docker; ephemeral per test run via `pytest` fixtures |
| Services | Mocked: Anthropic, OpenAI, OAuth providers, public-data APIs. Real: local Postgres. |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flaky tests due to async timing in FastAPI | Med | Use TestClient (synchronous wrapper); avoid sleep-based waits |
| Slow execution as suites grow | Med | Parallelize with pytest-xdist (TODO); separate slow integration suite |
| Drift between test schema and production schema | High | Tests run alembic upgrade head; fixtures match production model definitions |
| Visibility-filter regression slips through | Critical | Defensive: every new endpoint touching user_observations needs an entry in the regression test file; PR review checklist includes this |

**Known Gaps**:
- No automated frontend unit tests yet (TODO — Vitest)
- No load tests (premature at current MAU)
- iOS Safari camera flow not yet covered by Playwright (manual QA per release)

## Build Handoff

**Commands**:
- `pytest tests/` (backend, all)
- `pytest tests/test_observation_features.py` (visibility regression suite)
- `cd frontend && npx tsc -p tsconfig.app.json --noEmit` (frontend type check)
- `cd frontend && npx playwright test` (E2E)

**Priority**: Backend tests must pass before deploy; type check is a pre-flight; Playwright runs nightly on the deployed dev environment.
