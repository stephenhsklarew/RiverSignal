---
dun:
  id: ADR-003
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-003: All secrets in Google Secret Manager; never in env files or repo

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-04-12 | Accepted | Founder | FEAT-018, FEAT-019 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | OAuth client secrets, JWT signing key, DB password, Anthropic and OpenAI API keys, USGS API key, etc. all need to be available to the running Cloud Run service but must not appear in the repo, in build logs, in `.env` files committed by accident, or in container layers. |
| Current State | We use OAuth (Google, Apple), JWT auth, AI providers, and a managed Cloud SQL instance — meaning ~10 distinct secrets. |
| Requirements | Rotation must be operationally feasible. Secrets must be auditable (who accessed them, when). Local dev must work without copying production secrets to a laptop. |

## Decision

All production secrets live exclusively in Google Secret Manager. The Cloud Run service references them by name with `version = "latest"` so secret rotation propagates on next revision rollout. No secret value appears in Terraform state cleartext (we use `random_password` resources which Terraform handles, but the source of truth is Secret Manager once written).

**Key Points**: Dynamic env binding via `dynamic "env"` block in `cloud_run.tf` | IAM-scoped: each Cloud Run service account gets `secretmanager.secretAccessor` only on the secrets it actually needs | Local dev uses non-production secrets in a gitignored `.env.local` (file pattern only; values are dev-only).

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| `.env` file checked into private repo | Simple; visible in code | Anyone with repo access has prod secrets; rotation requires PR; bad git hygiene leaks history | Rejected: industry-standard anti-pattern |
| Hashicorp Vault | Best-in-class; cross-cloud | Operational overhead; we're single-cloud; overkill for our scale | Rejected: complexity not justified |
| GitHub Actions encrypted secrets | OK for CI variables | Hard to share between Cloud Run and CI; no built-in rotation | Rejected: secrets need to live in the runtime, not the build |
| **Google Secret Manager** | Native to GCP; IAM integrated; audit logs; rotation-friendly | Vendor lock-in (we're already locked) | **Selected: matches our managed-platform posture** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | Secrets are auditable; rotation only requires `gcloud secrets versions add` then `gcloud run services update`; no .env to manage |
| Negative | Cloud Run cold-starts read secrets at boot — first request slightly slower (negligible in practice); requires GCP service-account configuration for local dev |
| Neutral | All Cloud Run jobs that need DB access also pull secrets from Secret Manager via the same pattern |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Service account leak | L | C | WIF for GitHub Actions (no static keys); Cloud Run SA scoped only to needed secrets |
| Forgotten rotation of long-lived OAuth client secrets | M | M | Annual reminder in calendar; secret-list audit command in `05-deploy/` runbook |
| Local dev contaminated with prod secrets | L | H | Documented `.env.local` pattern with dev-only values; `.gitignore` enforces |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| Zero secrets in git history (audit) | Pre-commit hook; quarterly audit |
| Secret access logs reviewed quarterly for anomalies | Quarterly |

## Concern Impact

- **Concern selection**: Selects `secret-management-via-secret-manager` (security) — see `01-frame/concerns.md`.

## References

- `terraform/cloud_run.tf:64–87` (dynamic env block)
- `terraform/secrets.tf` (secret resources)
- `05-deploy/secret-rotation-runbook.md` (TODO)
