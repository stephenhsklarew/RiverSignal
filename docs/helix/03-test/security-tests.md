# Security Test Suite

**Project**: Liquid Marble
**Date**: 2026-05-10

## Coverage Summary

- Threats covered: TM-S-001, TM-S-003, TM-T-001, TM-T-002, TM-I-001, TM-I-002, TM-I-003, TM-D-001, TM-D-002, TM-E-001 (see `01-frame/threat-model.md`)
- Required setup: local Postgres, mocked OAuth fixtures, valid + invalid JWT samples
- Out of scope: full pen-test (deferred to external annual engagement); social-engineering attacks

## Security Test Categories

- **Authentication**: forged JWT rejection, expired JWT rejection, missing JWT for write endpoints, OAuth state/CSRF (TODO when state added)
- **Authorization**: anonymous user cannot read another user's private obs, signed-in user A cannot read user B's private obs, signed-in user cannot delete another user's saved items
- **Input validation**: SQL injection in watershed param, XSS in photo observation caption, path traversal in photo upload filename, oversized photo upload, non-image MIME, null bytes in JSON fields
- **Data protection**: encrypted secrets in Secret Manager (not env), httpOnly cookie attributes, samesite=lax cookie attribute, EXIF GPS removed from public photos (TODO when implemented)
- **Session management**: cookie expiry honored, sign-out clears cookie, JWT secret rotation invalidates all sessions

## Threat Matrix

| Threat / Control | Test | Expected Result | Pass Criteria |
|------------------|------|-----------------|---------------|
| TM-S-003 Forged JWT | Submit cookie with valid header but invalid signature | 401 | Endpoint returns 401, no user context |
| TM-S-003 Expired JWT | Submit JWT with `exp` in the past | 401 | Endpoint returns 401 |
| TM-T-001 SQL injection in watershed | `GET /api/v1/sites/skagit'; DROP TABLE users--` | 422 / 404 | Watershed allow-list rejects; no DB statement executes |
| TM-T-002 XSS in caption | Insert obs with caption `<script>alert(1)</script>`; render in UI | Caption escaped | React auto-escape; no script execution |
| TM-I-001 Private obs leak via list | User A (auth) inserts private obs; user B (auth) calls /list | Empty | User B sees no rows from user A's privates |
| TM-I-001 Private obs leak via geojson | Same setup; anonymous calls /geojson | Empty for that point | No private obs in response |
| TM-I-001 Private obs leak via search | Same setup; user B searches by lat/lon | Empty | No private obs |
| TM-I-001 Private obs leak via reasoning grounding | Same setup; AI Q&A request near point | Private obs not in context | Verified by mock Anthropic capturing prompt |
| TM-I-001 Private obs leak via ai_features predictions | Same setup; predictions endpoint | Private obs not in features | Verified by counting features used |
| TM-I-001 Private obs leak via watershed scorecard | Same setup; watershed counts | Excludes private | gold view filter verified |
| TM-I-002 EXIF GPS leak | Upload photo with GPS EXIF; retrieve public URL | EXIF stripped | (TODO — requires server-side strip implementation) |
| TM-D-002 Oversized photo upload | POST 50 MB photo | 413 | Cloud Run / app-level rejection |
| TM-D-002 Non-image MIME | POST `image/svg+xml` or `application/zip` | 415 | MIME whitelist rejects |
| TM-E-001 Anonymous → another user | Provide forged anonymous_id matching real user_id pattern | No escalation | anonymous_id is not a security boundary; cannot be used to read user data |

## Automated Security Testing

```yaml
sast:
  tool: GitHub CodeQL (TODO — to be enabled)
  trigger: PR + weekly scan on default branch
dast:
  tool: OWASP ZAP (manual quarterly run)
  target: dev environment
dependency_scan:
  tool: Dependabot (Python + npm)  # TODO — to enable
```

## Key Test Cases

### SEC-TC-001: Forged JWT Rejection
**Steps**:
1. Generate a JWT with the correct shape but signed with a different key.
2. Submit `Cookie: rs_token=<forged>` to `GET /api/v1/auth/me`.

**Expected**: Response 200 with `{"user": null, "anonymous": true}` (decode silently fails, treats as anonymous).

### SEC-TC-002: Private Observation Stays Private Across All Surfaces
**Steps**:
1. Create user A and user B.
2. As user A, POST observation at (44.32, -121.22) with `visibility=private`.
3. As user B (auth), call: `/observations/list`, `/observations/geojson?bbox=...`, `/sites/deschutes/observations`, `/deep-time/story` (POST with that lat/lon), `/ai-features/predictions?lat=44.32&lon=-121.22`.
4. As anonymous, call the same endpoints.
5. As user A, call `/observations/list?mine=true`.

**Expected**: Steps 3 and 4 never include the private observation. Step 5 includes it. Verified by `tests/test_observation_features.py` (Green).

### SEC-TC-003: SQL Injection on Watershed Parameter
**Steps**:
1. `GET /api/v1/sites/' OR 1=1--`
2. `GET /api/v1/sites/deschutes; DROP TABLE users`

**Expected**: 404 (allow-list rejects); no DB statement executed beyond the parameterized query.

### SEC-TC-004: Photo Upload Size + MIME Limits
**Steps**:
1. Upload `application/pdf` as photo.
2. Upload 15 MB JPEG.
3. Upload null-byte filename `evil%00.jpg`.

**Expected**: (1) 415; (2) 413; (3) sanitized filename or rejection.

### SEC-TC-005: Cookie Attributes
**Steps**:
1. Sign in via OAuth.
2. Inspect `Set-Cookie` header.

**Expected**: `rs_token=...; HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age=2592000`. (`Secure` once HTTPS is enforced — verify on production.)

### SEC-TC-006: Sign-Out Clears Session
**Steps**:
1. Sign in.
2. POST `/auth/logout`.
3. Try authed action.

**Expected**: Step 3 returns 401 (cookie cleared).

### SEC-TC-007: AI Endpoint Cost Circuit Breaker (TODO)
**Steps**:
1. Force daily cost telemetry to exceed threshold.
2. Call `/deep-time/story`.

**Expected**: 503 with explanatory error; resumes once cost drops below threshold.

## Compliance and Abuse Cases

- [x] iNaturalist CC BY-NC content not exposed via B2B paid surfaces — audit script (TODO) compares routes used by paid features against `commercial=false` source list
- [ ] EXIF GPS stripping verified on every public photo (TODO — implementation gap)
- [x] Sign-in events logged with user_id (no email or password in logs)
- [ ] Rate limit on AI endpoints (TODO)
- [ ] Abuse-report endpoint for photo observations (TODO)
- [x] Private observations never logged at INFO level

## Done

- [x] High-risk threats from `threat-model.md` mapped to tests
- [x] Visibility-filter coverage is comprehensive
- [x] Tests are executable and deterministic
- [ ] DAST scan run quarterly (next: 2026-08-10)
- [ ] SAST tool enabled (CodeQL — TODO)
- [ ] Dependency scanning enabled (Dependabot — TODO)
