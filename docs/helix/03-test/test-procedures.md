# Test Procedures

## Pre-Test Setup

- [x] Test framework configured (pytest + Playwright; Vitest TODO)
- [x] Local Postgres 17 available via Docker (`docker compose up`)
- [x] Test data and mocks prepared (`tests/conftest.py`, `tests/fixtures/`)
- [ ] CI pipeline runs tests on PR — currently CI runs build + deploy only; test workflow TODO

## Writing Procedures

### Contract Tests (FastAPI endpoints)
1. Read the route handler in `app/routers/*.py`.
2. Add or extend a test in `tests/test_api.py` (or a per-router file for larger surfaces).
3. Cover: success path; validation failures (Pydantic 422); auth requirements (401 for write endpoints); not-found / conflict behavior.
4. Use the FastAPI `TestClient` from `fastapi.testclient`.
5. For privileged endpoints, build a JWT using `app.routers.auth.create_token` against the test secret in `conftest.py`.
6. Verify the test fails before any new behavior is implemented (TDD-style; not strictly required for retroactive tests).

### Integration Tests
1. Identify the components and the data flow.
2. Use the smallest realistic mix: real Postgres (via `docker compose`), mocked external APIs (`httpx_mock`).
3. Cover: happy path, downstream failure (e.g., Anthropic 500), partial-data edge cases (e.g., observation without photo URL).
4. Set up DB state via fixtures or factories; tear down via `conftest.py` rollback.

### Unit Tests
1. Identify a pure function or class with no external dependencies.
2. Write one test per behavior, named `test_<module>_<behavior>` or `test_<class>_<method>_<scenario>`.
3. No I/O, no DB, no HTTP — if you need any of those, it's an integration test.

### E2E Tests (Playwright)
1. Choose a real user journey (the "golden path" for an app).
2. Run against a deployed environment OR a locally-running dev server (`npm run dev`).
3. Use `page.goto`, `page.click`, `page.locator` with stable selectors (`data-testid` preferred over text).
4. Take screenshots at key states for visual diff (kept in `frontend/tests/screenshots/`, gitignored except baselines).
5. Mobile viewport for B2C apps: `viewport: { width: 390, height: 844 }` (iPhone 14).

### Visibility-Filter Regression (mandatory for FEAT-020)
1. For any new public endpoint that joins `user_observations`, add a test in `tests/test_observation_features.py`.
2. Test pattern: insert a public obs and a private obs from different users, hit the endpoint as each user (and as anonymous), assert that private obs only appear for their owner.
3. Test must fail with a clear message if the filter is missing.

## Execution

### Local

```bash
# Backend
docker compose up -d postgres
pytest tests/                                      # all backend tests
pytest tests/test_observation_features.py -v      # visibility regression only
pytest --cov=app --cov-report=term-missing         # coverage report

# Frontend type check
cd frontend && npx tsc -p tsconfig.app.json --noEmit

# Playwright E2E
npx playwright install                              # one-time
npx playwright test                                 # all suites
npx playwright test --project=chromium-mobile       # mobile only
```

### CI

GitHub Actions runs build + deploy on push to `main` (`.github/workflows/deploy.yml`). A separate test workflow (TODO) should run pytest + tsc + selected Playwright suites on every PR before deploy is considered.

Block deploys on test failure. Block merges on test failure when the CI test workflow ships.

## Quality Checklist

- [ ] Test names describe behavior (`test_private_obs_excluded_from_geojson`, not `test_geojson_2`)
- [ ] Tests are independent (no shared state between tests)
- [ ] Tests are deterministic (no time-of-day dependence; no random without seed)
- [ ] Assertions are specific (assert exact JSON shape or row count, not just status code)
- [ ] Use factories from `conftest.py`, not duplicate setup
- [ ] No commented-out tests; if a test is broken, fix or delete it

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| Test passes locally but fails in CI | Timezone, DB state, env var difference | Use UTC explicitly; ensure fixtures truncate; load .env.test |
| Flaky Playwright test | Async race; element not yet rendered | `await page.waitFor*` instead of fixed sleep |
| `pytest` can't find DB | Docker compose down or wrong DATABASE_URL | `docker compose up -d`; verify `DATABASE_URL` env |
| OAuth callback test fails with signature error | Mock OAuth response missing `id_token` | Add a static valid id_token fixture in `tests/fixtures/oauth/` |
| Visibility test passes too easily | Filter being applied client-side instead of server-side | Make request as a *different* user, not the owner |
| `pytest --cov` shows 0% for a router | Module imported lazily; not included in --cov path | Add `--cov=app.routers.<name>` explicitly |

## Handoff

- [x] Visibility regression suite is comprehensive and runs in <30s
- [ ] CI test workflow runs on PR (TODO)
- [ ] Auth flow integration tests written
- [ ] Frontend unit tests adopted (Vitest)
- [ ] Coverage report visible in PR comment
