---
dun:
  id: ADR-005
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-005: Managed cloud platform only; no self-hosted services

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-04-10 | Accepted | Founder | FEAT-018 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | A solo engineer cannot also be a 24/7 SRE. Any service that requires patching, OS-level monitoring, or capacity planning is a tax we cannot afford. |
| Current State | New project; we get to choose the runtime model. |
| Requirements | Production must be operationally boring. Founder absences of up to 30 days should not produce outages from neglected maintenance. |

## Decision

Every component of production runs on a managed cloud service. No EC2, no GKE, no Kubernetes, no self-hosted Postgres, no Redis-on-VM. Specifically:

- Compute: Cloud Run (services + jobs) — no instances to patch
- Database: Cloud SQL (Postgres 17) — managed backups + failover
- Storage: GCS — no disk management
- Secrets: Secret Manager — managed rotation
- DNS: Cloud DNS or domain provider — no BIND
- Monitoring: Cloud Logging + Cloud Monitoring — no Prometheus to operate
- Scheduler: Cloud Scheduler — no cron-on-VM

**Key Points**: We accept vendor lock-in to GCP as a known cost | We pay a small premium over self-hosted in exchange for ~10× operational time savings | Terraform manages everything so reconstruction is reproducible.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Kubernetes (GKE Autopilot or self-managed) | Industry standard; portable across clouds | Requires cluster ops knowledge; YAML sprawl; costs more for our scale | Rejected: complexity not justified |
| EC2 / GCE VMs with Docker | Full control; cheapest sticker | OS patching, monitoring, scaling are now our problem | Rejected: doesn't fit solo-engineer profile |
| Serverless framework (Lambda / Cloud Functions) | Even more managed | FastAPI doesn't fit serverless function model cleanly; cold-start unpredictability for AI endpoints | Rejected: Cloud Run is the better serverless container fit |
| **Managed services: Cloud Run + Cloud SQL + GCS + Secret Manager + Scheduler** | Operational simplicity; reproducible via Terraform; full IaC | Vendor lock-in; price > self-hosted at scale | **Selected: net-positive at our team size** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | Founder absences of weeks don't produce outages; production self-stable; Terraform reconstructs everything |
| Negative | Vendor lock-in to GCP — pricing changes or policy changes are existential events; per-unit costs higher than self-hosted at scale |
| Neutral | Cost ceiling visible in monthly billing; we'd cross break-even on self-hosting around 100k MAU — well past current state |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| GCP price increase | L | M | Monthly cost monitoring; Terraform makes migration to AWS feasible (~2 weeks effort) if needed |
| Cloud Run cold-start latency on AI endpoints | M | L | min_instance_count = 1 keeps a warm instance; AI narrative pre-cached |
| Cloud SQL maintenance window causes brief downtime | M | L | Scheduled in low-traffic windows; status page communicates |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| Founder average ops hours per week ≤ 4 | Quarterly |
| Production uptime ≥ 99.5% per month | Monthly |
| Monthly GCP bill stays predictable (< 1.2× rolling 6-month avg) | Monthly |

## Concern Impact

- **Concern selection**: Selects `managed-cloud-platform-only` (infra) — see `01-frame/concerns.md`.

## References

- `terraform/` directory (entire IaC)
- `02-design/architecture.md` (deployment diagram)
