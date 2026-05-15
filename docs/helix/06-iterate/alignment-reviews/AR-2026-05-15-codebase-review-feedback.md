# Alignment Review Feedback: Codebase Review - 2026-05-15

## 1. Review Metadata

| Field | Value |
|-------|-------|
| Date | 2026-05-15 |
| Scope | Full codebase review, with emphasis on deployability, auth, schema management, and RiverPath alert surfaces |
| Reviewer | Codex code review |
| Trigger | User-requested codebase review |
| Status | Open findings captured for follow-up |

## 2. Summary

The review found that the local application database contains auth, user observation, settings, watchlist, and alert tables, but the repository does not appear to contain migrations that create several of those foundational tables from an empty database. This is a deployment and disaster-recovery risk: the current local database works, but a clean environment may not be reproducible from the checked-in Alembic chain alone.

The review also identified auth-flow and RiverPath alert issues that should be handled before broader production use.

## 3. Findings

| Severity | Area | Finding | Evidence | Recommended Follow-up |
|----------|------|---------|----------|-----------------------|
| High | Schema management | Clean database setup is not reproducible from Alembic. Migrations add columns or foreign keys to `users`, `user_observations`, and `user_settings`-dependent surfaces, but no checked-in migration was found creating `users`, `user_observations`, or `user_settings`. | `alembic/versions/h9c0d1e2f3a4_persona_self_selection.py`, `alembic/versions/c3d4e5f6a7b8_add_observation_visibility_scientific_name.py`, `alembic/versions/q8f9a0b1c2d3_tqs_user_watchlist.py` | Add an idempotent Alembic reconciliation migration for missing auth/user tables and columns, then validate `alembic upgrade head` against a fresh database. |
| High | Auth | Apple sign-in cannot complete because Apple posts to `/auth/apple/callback`, which always returns 501; the async implementation is mounted at `/auth/apple/callback-async`. | `app/routers/auth.py` | Point `APPLE_REDIRECT_URI` and the login URL to the implemented callback, or move the async implementation to `/auth/apple/callback`. Add an integration test for the callback route. |
| High | Auth/security | Production auth defaults are unsafe: fallback JWT secret, `secure=False` cookies, and wildcard credentialed CORS. | `app/routers/auth.py`, `app/main.py` | Fail startup in production without `AUTH_SECRET_KEY`; make secure cookies environment-aware with HTTPS default; restrict CORS origins by env. |
| Medium | Fishing alerts | Dissolved oxygen alert SQL can count anomalies from all watersheds because `AND`/`OR` precedence drops the watershed filter for `%do%`. | `app/routers/fishing.py` | Wrap the oxygen/DO anomaly predicates in parentheses and add a regression test with cross-watershed fixture data. |
| Medium | Watchlist | `trend_7d` is wrong for most watched reaches because the `week_ago` CTE selects one global history row, then joins it to each watch. | `app/routers/watchlist.py` | Use `DISTINCT ON (reach_id)` or a window partition so each reach gets its own week-ago row. |
| Medium | RiverPath alerts UI | The alerts watershed picker navigates to `/path/alerts/{watershed}`, but the router only defines `/path/alerts`. | `frontend/src/pages/AlertsPage.tsx`, `frontend/src/components/WatershedHeader.tsx`, `frontend/src/main.tsx` | Either add `/path/alerts/:watershed` or make the alerts header use a base route that does not append a watershed. |

## 4. Local Database Check

A read-only schema probe against the configured local database found:

| Object | Local DB Status |
|--------|-----------------|
| Alembic version | `w4f5a6b7c8d9` |
| `users` | Exists, including `provider`, `provider_id`, `username`, `anonymous_id`, and persona columns |
| `user_observations` | Exists, including `user_id`, `source_app`, `visibility`, and `scientific_name` |
| `user_settings` | Exists, including `user_id` and `settings` |
| `user_reach_watches` | Exists |
| `user_alert_deliveries` | Exists |

Interpretation: the local database has the expected runtime objects, but some of them appear to have been created outside the currently checked-in migration history or by migrations no longer present in the repository.

## 5. Verification Performed

| Command | Result |
|---------|--------|
| `npm run build` in `frontend/` | Passed; Vite reported large chunk warnings |
| `.venv/bin/python -m pytest tests/test_trip_quality.py -q` | Passed: 36 tests |
| `python3 -m compileall app pipeline tests` | Passed |
| `python3 -m pytest tests/test_trip_quality.py -q` using system Python | Failed because system Python lacked project dependencies (`fastapi`) |

## 6. Suggested Issue Breakdown

1. Create a schema reconciliation migration for auth/user tables.
2. Fix Apple OAuth callback routing and add callback coverage.
3. Harden auth production configuration.
4. Fix fishing alert SQL precedence and add coverage.
5. Fix watchlist `trend_7d` query semantics and add coverage.
6. Fix or route `/path/alerts/:watershed`.

The schema reconciliation item should be treated as the first follow-up because it affects every clean deployment, restore, and contractor handoff.
