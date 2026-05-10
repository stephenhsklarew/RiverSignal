# Metric Definitions

This document indexes the KPIs we track to evaluate the platform against the goals in `01-frame/prd.md` and `00-discover/opportunity-canvas.md`. Each metric has a YAML file under `metrics/` with the canonical command, output pattern, and tolerance.

## North Star

| Metric | File | Direction | Source |
|--------|------|-----------|--------|
| Sessions where a user saved a finding | `metrics/save-conversion-rate.yaml` | higher | App analytics + DB |

## Product KPIs

| Metric | File | Direction | Source |
|--------|------|-----------|--------|
| Monthly Active Users (MAU) | `metrics/mau.yaml` | higher | DB sessions table (TODO) |
| Sign-up conversion (anonymous → authed) | `metrics/signup-conversion.yaml` | higher | DB users + anonymous_id mapping |
| Retention — week-4 returning user | `metrics/wau-retention-w4.yaml` | higher | DB sessions table |
| Sessions per MAU per month | `metrics/sessions-per-mau.yaml` | higher | DB sessions table |
| Time-to-first-value (landing → first useful answer) | `metrics/time-to-first-value.yaml` | lower | Frontend telemetry (TODO) |

## Operational KPIs

| Metric | File | Direction | Source |
|--------|------|-----------|--------|
| API p99 latency | `metrics/api-p99-latency.yaml` | lower | Cloud Run metrics |
| API error rate | `metrics/api-error-rate.yaml` | lower | Cloud Run metrics |
| AI cost per MAU | `metrics/ai-cost-per-mau.yaml` | lower | Anthropic + OpenAI billing / DB MAU |
| Gold-view refresh duration | `metrics/refresh-duration.yaml` | lower | Cloud Run job logs |
| Ingestion job success rate | `metrics/ingestion-success.yaml` | higher | Cloud Run job execution status |

## Business KPIs

| Metric | File | Direction | Source |
|--------|------|-----------|--------|
| B2B accounts paying | `metrics/b2b-accounts.yaml` | higher | Manual / CRM |
| B2C subscription revenue | `metrics/b2c-subscription.yaml` | higher | Subscription system (when launched) |
| Cost per acquired user | `metrics/cac.yaml` | lower | Manual ledger |

## Quality KPIs

| Metric | File | Direction | Source |
|--------|------|-----------|--------|
| Zero private-obs leak incidents | `metrics/private-obs-leaks.yaml` | lower (target 0) | Bug tracker |
| AI narrative accuracy (expert review) | `metrics/ai-narrative-accuracy.yaml` | higher | Quarterly expert panel |
| Ingestion data freshness (hours since last sync) | `metrics/ingestion-freshness.yaml` | lower | DB pipelines table |
| Backend test coverage | `metrics/backend-coverage.yaml` | higher | pytest --cov |

## Review cadence

- **Weekly**: operational KPIs (latency, error rate, cost, refresh duration)
- **Monthly**: product + business KPIs in alignment review
- **Quarterly**: quality KPIs + research-plan findings
- **Annual**: revisit metric definitions; deprecate anything not driving decisions

See `06-iterate/alignment-reviews/` for periodic review records.
