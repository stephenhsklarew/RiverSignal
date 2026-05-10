# Threat Model

**Project**: Liquid Marble
**Date**: 2026-05-10

## Executive Summary

**System Overview**: A FastAPI backend on Google Cloud Run, Cloud SQL Postgres warehouse (medallion bronze/silver/gold), React + Vite frontend served from the same Cloud Run service. Three apps share one backend. OAuth via Google and Apple. User-generated photo observations with public/private visibility.

**Key Assets**: User identity tokens (JWTs); private photo observations; the curated medallion warehouse; OAuth client secrets; Cloud SQL credentials.

**Primary Threats**: (1) Photo observation abuse (malicious uploads, doxxing, copyright); (2) OAuth callback or JWT compromise leading to account takeover; (3) Private observation leaking through a query path that didn't get the visibility filter; (4) Cost-based denial via expensive AI endpoints; (5) Data exfiltration of bulk warehouse via API enumeration.

**Risk Level**: Medium

## System Description

### Boundaries and Components

**In Scope**:
- Cloud Run service (`riversignal-api`) hosting FastAPI + static frontend bundle
- Cloud SQL Postgres (`riversignal-db`) on private VPC IP
- GCS bucket `riversignal-assets-riversignal-prod` for user uploads + audio cache
- Secret Manager for OAuth secrets, AUTH_SECRET_KEY, DB password
- Cloud Run scheduled jobs (ingestion, refresh-views)
- GitHub Actions deploy pipeline (Workload Identity Federation)
- React SPA (`/`, `/path/*`, `/trail/*`, `/riversignal/*`, `/status`, `/auth/*`)

**Out of Scope**:
- Upstream public-data providers (USGS, iNaturalist, etc.) — we treat their APIs as untrusted external
- User devices (browser/iOS/Android) beyond standard browser security model
- Cloud Run platform internals (managed by GCP)
- Anthropic / OpenAI API platforms

**Trust Boundaries**:
- Public internet ↔ Cloud Run (TLS termination)
- Cloud Run ↔ Cloud SQL (private VPC; password auth; encrypted in transit via socket)
- Cloud Run ↔ Secret Manager (IAM-scoped)
- Cloud Run ↔ external APIs (Anthropic, OpenAI, OAuth providers, public data) — outbound only, secrets in headers
- GitHub Actions ↔ GCP (WIF; no static service-account key)
- User browser ↔ Cloud Run (cookie-bound JWT)

### Components

| Component | Description | Trust Level |
|-----------|-------------|-------------|
| FastAPI server | Public HTTP entry; routes auth, ingestion read APIs, photo upload | Trusted (we own) |
| Cloud SQL Postgres | All bronze/silver/gold tables and user data | Trusted (we own) |
| GCS bucket | User photo storage; audio cache | Trusted (we own) |
| Cloud Run scheduled jobs | Ingestion + view refresh; service-account auth | Trusted (we own) |
| Anthropic API | LLM for narrative + Q&A | External (TLS; signed requests) |
| OpenAI API | TTS audio generation | External |
| Google OAuth | Sign-in for `provider=google` | External (trusted by spec) |
| Apple OAuth | Sign-in for `provider=apple` | External (trusted by spec) |
| Public data sources | USGS, iNaturalist, NOAA, etc. | Semi-trusted (verified TLS, treated as potentially untrusted content) |
| Frontend (React SPA) | UI; runs on user device | Untrusted (treats input as adversarial) |

### Data Flows

- **External Sources**: 30+ public data adapters fetch into bronze on cron; OAuth callbacks deliver user identity; photo observation uploads from authenticated browser.
- **Internal Processing**: Bronze → silver (clean/normalize) → gold (aggregate) via materialized views refreshed nightly. AI calls hit warehouse for grounding context.
- **External Destinations**: HTTP responses to browsers; outbound API calls to LLM/TTS providers; logs to Cloud Logging.

## Assets

### Data Assets

| Asset | Classification | Confidentiality | Integrity | Availability |
|-------|---------------|-----------------|-----------|--------------|
| OAuth client secrets (Google, Apple) | Secret | Critical | Critical | Medium |
| AUTH_SECRET_KEY (JWT signing) | Secret | Critical | Critical | High |
| Cloud SQL password | Secret | Critical | Critical | Critical |
| User email + provider_id | PII | High | High | Medium |
| User photo observations (private) | UGC + PII | High | High | High |
| User photo observations (public) | UGC | Low | Medium | High |
| User saved items | UGC | Medium | Medium | Medium |
| Bronze warehouse (8.4M time-series + 1.3M obs etc.) | Public + curated | Low | High | High |
| AI narrative cache | Derived | Low | Medium | Medium |
| Audit logs | Operational | Medium | Critical | High |

### System Assets

| Asset | Criticality | Dependencies |
|-------|-------------|--------------|
| Cloud Run revision | Critical | GCP Cloud Run, Artifact Registry |
| Cloud SQL instance | Critical | GCP Cloud SQL |
| GCS bucket | High | GCP Storage |
| GitHub repo | Critical | GitHub |
| Domain / DNS | High | Custom domain not yet — Cloud Run URL only |

## STRIDE Threat Analysis

| ID | Threat | Impact | Likelihood | Risk | Mitigation |
|----|--------|--------|------------|------|------------|
| **TM-S-001** | OAuth provider spoofing — attacker tricks user into authenticating against a fake provider | High | Low | Med | Rely on browser's TLS; only register exact production redirect URIs in Google/Apple consoles |
| **TM-S-002** | Anonymous user spoofs another anonymous user's saved items by guessing their `rs_anonymous_id` | Low | Medium | Low | Anonymous IDs are random + base36 + ~22 chars (~131 bits entropy); local to browser; not a security boundary |
| **TM-S-003** | Forged JWT cookie | Critical | Low | High | HS256 + Secret-Manager-stored key; reject on signature failure; rotate annually |
| **TM-T-001** | SQL injection via watershed parameter | High | Low | Med | All queries use SQLAlchemy `text()` with bind params; watershed validated against allow-list; pytest covers parameter tampering |
| **TM-T-002** | XSS via user-submitted photo observation caption | Medium | Medium | Med | React auto-escapes; never `dangerouslySetInnerHTML` user data; CSP TODO |
| **TM-T-003** | Tampering with cached AI narratives | Low | Low | Low | Narratives cached in `gold.deep_time_story` table; only writable by service account; cache key includes data freshness signal |
| **TM-T-004** | Bronze-table corruption via malicious upstream API response | Medium | Low | Low | Pydantic schema validation in adapters; sanity-bound checks (e.g., `value > -999998`) |
| **TM-R-001** | User repudiates having uploaded an offensive photo observation | High | Medium | Med | Auth required for all uploads; user_id stored on observation row; immutable bronze table preserves original |
| **TM-R-002** | Repudiation of B2B contract usage | Medium | Low | Low | API access logged with user_id and timestamp |
| **TM-I-001** | Private photo observations leak through public surface (search/map/list) | Critical | Medium | High | Visibility filter applied at silver/gold view level + every public endpoint; integration tests in `tests/test_observation_features.py` |
| **TM-I-002** | EXIF GPS leak in public photo observation | High | High | High | Server-side EXIF strip before public display (TODO — currently client-side) |
| **TM-I-003** | OAuth code interception | High | Low | Med | TLS only; redirect URIs registered exactly in provider consoles; OAuth state parameter (TODO — anti-CSRF) |
| **TM-I-004** | DB credentials leak via GitHub Actions log | Critical | Low | Med | Secrets never echoed; GitHub Actions runs use WIF (no static creds); `gcloud sql ...` doesn't print password |
| **TM-I-005** | API enumeration of bulk warehouse (data scraping for resale) | Medium | High | Med | Rate limit per IP (TODO); CC BY-NC license tag in responses; ToS prohibits scraping |
| **TM-D-001** | DoS via expensive AI narrative endpoint | Medium | High | High | Per-IP rate limit (TODO); circuit breaker on daily LLM cost; speech-synthesis fallback if TTS fails |
| **TM-D-002** | DoS via large photo upload | Medium | Medium | Med | Cloud Run request size limit (32 MiB default); app-level 10 MB limit; reject non-image MIME |
| **TM-D-003** | Cloud SQL exhaustion via heavy query | Medium | Low | Low | Connection pooling; gold views pre-aggregate; query timeouts via `statement_timeout` (TODO) |
| **TM-D-004** | GCP billing overrun via runaway loop | High | Low | Med | Daily budget alert at $50; alarms for AI spend |
| **TM-E-001** | Privilege escalation: anonymous user obtains another user's session | Critical | Low | High | JWT signed with secret in Secret Manager; httpOnly + samesite=lax cookie; no JWT in localStorage |
| **TM-E-002** | Service account scope creep | High | Low | Med | Each Cloud Run service has its own SA with minimal IAM (cloudsql.client + storage.objectAdmin on bucket + secretAccessor) |
| **TM-E-003** | GitHub Actions WIF bound to wrong repo | Critical | Low | Med | WIF binding scoped to `attribute.repository/${var.github_repo}` in `cloud_build.tf` |

## Risk Assessment

### Top Risks

| Risk ID | Threat | Impact | Likelihood | Score | Priority |
|---------|--------|--------|------------|-------|----------|
| TM-I-001 | Private obs leaks via missing visibility filter | 5 | 3 | 15 | High |
| TM-I-002 | EXIF GPS leak in public photo | 4 | 4 | 16 | High |
| TM-D-001 | DoS via AI endpoint | 3 | 4 | 12 | Medium-High |
| TM-S-003 | Forged JWT cookie | 5 | 2 | 10 | Medium |
| TM-E-001 | Anonymous escalation to another user | 5 | 2 | 10 | Medium |
| TM-R-001 | User repudiates offensive upload | 4 | 3 | 12 | Medium-High |

## Mitigation Strategies

### TM-I-001 — Private observation leakage
- **Controls**: View-layer filter (silver.species_observations etc. exclude `visibility != 'public'`); explicit filter in every public route; integration tests covering each surface.
- **Timeline**: Done as of a78892c (2026-05-09); ongoing — every new endpoint that touches user obs must add the filter.
- **Owner**: Founder (gating PR review).

### TM-I-002 — EXIF GPS leak
- **Controls**: Server-side EXIF strip on upload before storing the public version; preserve original in private storage if user opted private.
- **Timeline**: TODO — should ship within next release.
- **Owner**: Founder.

### TM-D-001 — AI endpoint DoS
- **Controls**: Per-IP rate limit; daily LLM cost circuit breaker; pre-cached narratives in `gold.deep_time_story` so most requests don't hit Anthropic.
- **Timeline**: Pre-cache in place; rate limit + circuit breaker TODO.
- **Owner**: Founder.

### TM-R-001 — Photo observation abuse
- **Controls**: Auth required; user-id on every row; in-app abuse-report button; manual takedown procedure; auto-moderation candidate for next release.
- **Timeline**: Manual procedure documented; auto-mod TODO.
- **Owner**: Founder.

## Security Controls Summary

- **Preventive**: OAuth federation (no password storage); JWT signing with Secret Manager keys; Pydantic input validation; React HTML escaping; CC BY-NC source flag; Cloud Run private VPC to Cloud SQL; allow-list for watershed param.
- **Detective**: Cloud Logging request logs; Cloud SQL audit logs; daily ingestion failure alerts; AI cost tracking; Playwright + pytest in CI.
- **Corrective**: Documented rollback runbook (`05-deploy/`); JWT secret rotation procedure; manual takedown for UGC; backup restore procedure.

## Assumptions and Dependencies

- TLS to/from all external endpoints
- Cloud Run platform isolates revisions correctly
- Apple and Google OAuth identity providers themselves are secure
- Browser cookie + samesite-lax behavior works as specified
- Anthropic and OpenAI API keys are not embedded in client bundles (verified — they're server-side only)
- GitHub Actions WIF cannot be impersonated by another GitHub repo
