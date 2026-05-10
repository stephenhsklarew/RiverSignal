# Project Concerns

## Active Concerns

<!-- Concerns track the cross-cutting properties this project explicitly cares about,
     each with a governing ADR. -->

- anonymous-first-access (privacy) — ADR-001: Read endpoints work without auth; sign-in adds sync only
- medallion-data-warehouse (data) — ADR-002: Bronze ingest, silver clean, gold pre-aggregate
- secret-management-via-secret-manager (security) — ADR-003: All secrets in Google Secret Manager, never in env files or repo
- visibility-aware-photo-observations (privacy) — ADR-004: Public/private flag enforced at view layer + every public endpoint
- managed-cloud-platform-only (infra) — ADR-005: Cloud Run + Cloud SQL only; no self-hosted services
- federated-auth-only (security) — ADR-006: Google + Apple OAuth; never store passwords
- ai-grounded-narrative (quality) — ADR-007: All AI narrative retrieval-grounded in our warehouse, never raw LLM
- license-tagged-source-data (compliance) — ADR-008: Every ingestion adapter tags rows with license + commercial flag

## Project Overrides

<!-- Override specific library or framework defaults. Cite the governing ADR. -->

- Cloud Run min instances = 1 (overrides cost-optimal 0): keeps cold starts off the user path (see ADR-005)
- Cloud SQL deletion_protection_enabled = false (overrides production-default true): solo-dev convenience for early iteration; revisit at first paying B2B customer (see RISK-004)
- React StrictMode enabled (default kept): catches double-render side effects in development
- TypeScript noUnusedLocals + noUnusedParameters = true: stricter than default to catch dead code in solo-engineer setting

## Area Labels

This project uses the following area labels for concern scoping:

- `area:ui` — React app, components, pages
- `area:api` — FastAPI routers, dependency-injection layer
- `area:data` — Postgres warehouse, medallion views, ingestion adapters
- `area:infra` — Terraform, Cloud Run, Cloud SQL, secrets, scheduled jobs
- `area:auth` — OAuth, JWT, user accounts, sessions
- `area:ai` — Anthropic / OpenAI API integration, narrative caching, TTS
- `area:ci` — GitHub Actions, deploy pipeline, container build
