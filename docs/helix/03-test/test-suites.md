# Test Suite Structure

**Project**: Liquid Marble
**Coverage Target**: 80% backend line; 100% critical paths; 100% visibility-filter regressions
**Test Framework**: pytest (backend), Playwright (E2E), Vitest (frontend unit, TODO)

## Test Organization

```
tests/                         # Backend test root
├── conftest.py                # Shared fixtures, DB setup, factories
├── test_api.py                # Contract tests across all routers (light)
├── test_data.py               # Bronze data sanity tests; ingestion smoke
├── test_observation_features.py # FEAT-020 visibility regression suite
├── (TODO) test_auth_flow.py   # OAuth callback + JWT round-trip
├── (TODO) test_predictions.py # FEAT-017 model output schema
├── (TODO) test_medallion.py   # View existence + freshness
└── *.spec.ts                  # Playwright tests at repo root (legacy location)

frontend/tests/                # Frontend Playwright suites
├── deeptrail-tabs.spec.ts     # DeepTrail 5-tab navigation
├── rocks-fossil-map.spec.ts   # DeepTrail map interaction
└── screenshots/               # Baseline screenshots (gitignored)
```

## Contract Tests

| Endpoint | Method | Test File | Status |
|----------|--------|-----------|--------|
| /api/v1/sites/{ws} | GET | tests/test_api.py | Green |
| /api/v1/sites/{ws}/snowpack | GET | tests/test_api.py | Green |
| /api/v1/observations | POST | tests/test_observation_features.py | Green |
| /api/v1/observations/list | GET | tests/test_observation_features.py | Green |
| /api/v1/observations/geojson | GET | tests/test_observation_features.py | Green |
| /api/v1/auth/me | GET | (TODO) tests/test_auth_flow.py | Red |
| /api/v1/auth/google/login | GET | (TODO) | Red |
| /api/v1/auth/google/callback | GET | (TODO) | Red |
| /api/v1/auth/apple/callback-async | POST | (TODO) | Red |
| /api/v1/data-status | GET | tests/test_api.py | Green |
| /api/v1/deep-time/story | POST | (TODO) tests/test_ai_grounding.py | Red |
| /api/v1/ai-features/* | GET | (TODO) tests/test_predictions.py | Red |

Coverage: success path, validation, auth (where required), and not-found/conflict behavior.

## Integration Tests

| Component A | Component B | Test File | Status |
|------------|-------------|-----------|--------|
| user_observations writer | gold.watershed_scorecard view | tests/test_observation_features.py | Green |
| user_observations | reasoning grounding context | tests/test_observation_features.py | Green |
| user_observations | ai_features predictions | tests/test_observation_features.py | Green |
| user_observations | observation search | tests/test_observation_features.py | Green |
| OAuth callback | JWT issuance + user upsert | (TODO) | Red |
| Ingestion adapter | bronze table write | tests/test_data.py | Green |
| Anthropic API mock | gold.deep_time_story cache | (TODO) | Red |
| Cloud Scheduler trigger | Cloud Run Job execution | Manual / monitored in production | n/a |

Coverage: component coordination, persistence, and downstream failure handling.

## Unit Tests

| Module | Function | Test File | Status |
|--------|----------|-----------|--------|
| app/routers/auth.py | `create_token`, `get_current_user` | (TODO) | Red |
| app/routers/user_observations.py | visibility filter helper | tests/test_observation_features.py | Green |
| pipeline/ingest/snotel.py | parameter mapping | (TODO) tests/test_ingest.py | Red |
| pipeline/medallion.py | `_has_unique_index`, refresh-CONCURRENTLY logic | (TODO) | Red |
| pipeline/predictions/* | each model's output shape | (TODO) | Red |

Coverage: happy path, edge/error cases, and business rules.

## E2E Tests (Playwright)

| Journey | Steps | Critical | Test File | Status |
|---------|-------|----------|-----------|--------|
| RiverPath tab navigation (now → explore → hatch → steward → saved) | 5 | Yes | tests/riverpath-mvp.spec.ts | Green |
| Species map: select species, see pins | 4 | Yes | tests/species-map.spec.ts | Green |
| Species rocks: select rock site, see detail | 4 | Yes | tests/species-rocks-select.spec.ts | Green |
| DeepTrail tab navigation (story → explore → collect → learn → saved) | 5 | Yes | frontend/tests/deeptrail-tabs.spec.ts | Green |
| Rocks/fossil map click → detail panel | 3 | Yes | frontend/tests/rocks-fossil-map.spec.ts | Green |
| AI features panel renders predictions | 3 | No | tests/ui-ai-features.spec.ts | Green |
| Full UI audit (visual regression) | n/a | No | tests/ui-full-audit.spec.ts | Green |
| Anonymous → Google sign-in → username setup | 6 | Yes | (TODO) | Red |
| Photo observation upload + visibility toggle | 5 | Yes | (TODO) | Red |
| RiverPath header + watershed picker on mobile viewport | 3 | Yes | (TODO) | Red |
| `/status` page TOC pill jumps with sticky header | 3 | No | (TODO) | Red |

## Test Data

| Asset | Purpose |
|-------|---------|
| Fixtures (tests/fixtures/*) | Canonical bronze rows per source (one iNat obs, one SNOTEL reading, one Macrostrat unit, etc.) |
| Factories (`tests/conftest.py:make_user`, `make_observation`, `make_site`) | Generated test objects with sensible defaults; override per-test |
| Mocks | `httpx_mock` for outbound public-data calls; static OAuth response fixtures; mock Anthropic responses with deterministic narratives |

## Coverage Targets

| Metric | Target |
|--------|--------|
| Overall backend line coverage | 80% |
| Contract test coverage (endpoint count) | 100% |
| Critical path coverage | 100% |
| Visibility-filter regression coverage (per surface) | 100% |
| Error handling coverage | 90% |

## Readiness

- [x] Suite boundaries are defined
- [x] Shared test data assets exist (`conftest.py`)
- [x] Visibility regression suite is comprehensive
- [ ] Auth flow test suite (highest-priority gap)
- [ ] AI grounding test suite
- [ ] Predictions test suite
- [ ] Frontend unit tests (Vitest)
