# Security Requirements

**Project**: Liquid Marble
**Date**: 2026-05-10
**Security Champion**: Stephen Sklarew

## Overview

The platform is a public-facing web app with mostly read-only public data, optional user accounts, and user-generated photo observations. The security profile is "anonymous-first, defense-in-depth": every read endpoint must work safely without auth, and every write endpoint must authenticate and authorize. The primary protection goals are integrity of public data, confidentiality of private user observations, and availability against amateur DoS.

## Required Controls

### Authentication
- OAuth-only login via Google and Apple (no password storage on our side)
- JWT cookie (`rs_token`) — `httpOnly`, `samesite=lax`, 30-day expiry
- JWT signing with HS256 + 32-char secret rotated annually (or on suspected compromise)
- Apple client secret JWT (ES256) regenerated server-side, valid 6 months
- Anonymous browsers identified by client-generated `rs_anonymous_id` (not a security boundary; UX only)

### Authorization
- Read endpoints: open to anonymous (default) or authed; never require auth except where explicitly stated
- Write endpoints: require authenticated user via `get_current_user` dependency
- Photo observations: write requires auth; private observations are filtered server-side from all public surfaces (user list, geojson, search, reasoning, ai_features, time-machine, site obs counts)
- Migrations: scoped to `riversignal-migrate` Cloud Run job; service account has `cloudsql.client` only

### Data Protection
- Data at rest: Cloud SQL Postgres with default Google-managed encryption
- Data in transit: TLS only (Cloud Run enforces HTTPS; private VPC traffic to Cloud SQL via socket)
- Photo observations: stored in GCS bucket `riversignal-assets-riversignal-prod` with signed URLs for private items
- Secrets: Google Secret Manager (no .env files in repo); Cloud Run service account has `secretmanager.secretAccessor` scoped to specific secrets
- DB password: random 32+ char, stored as Terraform `random_password` resource and Secret Manager
- No PII in logs (CSPM lint check on log strings — TODO)

### Privacy
- Anonymous-first architecture; all reads work without identity
- `is_new` flag prompts username setup post-OAuth without leaking the underlying email
- Photo observations: `visibility` column gates exposure across all surfaces; default public, opt-in private
- EXIF stripping: server-side removal of GPS metadata before serving public photo observations (TODO — currently relies on client)
- iNaturalist photos served as-is from upstream URLs (no proxy / re-host); license badges visible

### Input Validation
- All API inputs use Pydantic models (FastAPI default) — type-checked, length-limited
- File uploads (photo observations): MIME-type whitelist (image/jpeg, image/png, image/heic), max 10 MB, virus scan via Cloud Run service or relying on GCS-side controls (TODO)
- SQL: only parameterized queries (`text("...")` with bind params); no string concatenation
- HTML escaping: React's default escape is relied upon; never use `dangerouslySetInnerHTML` except for inline `<style>` blocks
- Watershed parameter: validated against allow-list before query

### Logging and Audit
- Cloud Run request logs: 90-day retention via Cloud Logging
- Auth events (sign-in, sign-out, username set, account migration): logged with user_id (no email)
- DB queries via SQLAlchemy: not logged at app level (Cloud SQL audit logs available if needed)
- AI API calls (Anthropic, OpenAI): cost-tracked, not logged with user prompts
- No silent failures in auth code: every JWTError logs and returns 401, no swallowed exceptions

## Compliance Requirements

**Applicable Regulations**: GDPR, CCPA, COPPA (see `compliance-requirements.md`)
**Applicable Standards**: OWASP Top 10, OWASP API Security Top 10
- Auth uses industry-standard OAuth 2.0 flow (no roll-your-own)
- Passwords: not collected (federated auth only)
- Crypto: standard libraries (Python `jose`, `httpx` TLS); no roll-your-own crypto

## Security Risks

### High-Risk Areas

1. **Photo observation upload**: User-controlled file upload with public visibility option. Risks: malware, CSAM, doxxing via EXIF. Mitigation: file-size + MIME limits, server-side EXIF strip, abuse-report flow (TODO).

2. **OAuth callback handling**: `code` parameter from Google/Apple is trusted. Mitigation: redirect URI strictly registered with provider; state parameter (TODO — currently no anti-CSRF state on OAuth flow).

3. **JWT secret leak**: All sessions invalidated on rotation. Mitigation: secret in Secret Manager, never in code/env files; rotate annually.

4. **API endpoint enumeration**: FastAPI auto-generates OpenAPI docs at `/docs` exposing every route. Mitigation: leave docs visible for transparency (data is public anyway); ensure no admin-only endpoints leak via the schema.

5. **CORS misconfiguration**: Currently `CORS_ORIGIN = "*"` — any origin can call API. Acceptable for public data but means rich-text-app developers can use our API. No write endpoint is reachable without auth, so worst case is read load.

6. **Cloud SQL public IP**: Currently `ipv4_enabled = false` — DB has private IP only, accessed via VPC connector. Mitigation: keep this configuration.

## Security Architecture Requirements

- [x] Network segmentation (Cloud Run + Cloud SQL via VPC connector)
- [x] Application security testing (Playwright, pytest, type checks in CI)
- [ ] Dependency vulnerability scanning (Dependabot or Snyk — TODO)
- [x] Server hardening (managed Cloud Run; minimal Dockerfile)
- [x] Patch management (managed runtime by GCP; pip-tools lock TODO)
- [x] Backup and recovery tested (Cloud SQL automated backups; restore procedure documented in `05-deploy/`)

## Security Testing Requirements

- [ ] Penetration testing (annual external pen test once B2B paying customers exist)
- [ ] Vulnerability assessments (quarterly automated scan)
- [ ] Security code review (each PR — currently solo, so checklist-driven)
- [ ] Automated security scanning (GitHub CodeQL — TODO; Dependabot — TODO)
- [x] Auth integration tests (`tests/test_observation_features.py` covers visibility filtering across surfaces; auth flow has manual E2E)

## Assumptions and Dependencies

- GCP IAM is configured correctly (service accounts, Workload Identity Federation for GitHub Actions deploy)
- Apple/Google OAuth providers are themselves secure
- Anthropic / OpenAI APIs are themselves secure (we don't store user prompts in logs)
- `httpOnly` cookie + `samesite=lax` is enforced by browsers (assumed; no fallback for older browsers needed for PWA)
- Cloud SQL backups are restorable (verify quarterly)
- The CC BY-NC images we render are hosted on iNaturalist's CDN (we don't proxy or re-host)
