# GCP Production Deployment: Terraform + Data Migration

## Configuration
- **Tier**: Option B — Production (~$75/mo)
- **Region**: us-west1 (Oregon)
- **Domain**: Cloud Run auto-generated URL (no custom domain initially)

## Architecture

```
                    ┌─────────────────┐
                    │  Firebase Hosting │  (frontend SPA)
                    │   *.web.app      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Cloud Run       │  (FastAPI, min 1 instance)
                    │   2 vCPU, 2GB     │  *.run.app
                    └────────┬─────────┘
                             │ VPC Connector
                    ┌────────▼─────────┐
                    │  Cloud SQL        │  (PostgreSQL 17 + PostGIS)
                    │  db-g1-small      │  private IP only
                    │  20GB SSD         │
                    └──────────────────┘

    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │ Cloud Storage │    │ Cloud Run    │    │ Cloud        │
    │ (assets CDN)  │    │ Jobs         │    │ Scheduler    │
    │ images/audio  │    │ pipeline     │    │ cron         │
    └──────────────┘    └──────────────┘    └──────────────┘
```

## Cost Breakdown (Monthly)

| Service | Spec | Cost |
|---|---|---|
| Cloud Run (API) | 2 vCPU, 2GB RAM, min 1 instance, max 10 | ~$18 |
| Cloud SQL PostgreSQL 17 | db-g1-small (1.7GB RAM), 20GB SSD, daily backups (14-day retention), private IP | ~$26 |
| Cloud Storage + CDN | assets bucket (3GB images, audio), backups bucket (30-day lifecycle) | ~$2 |
| Cloud Run Jobs | 4 jobs: daily/weekly/monthly pipeline + view refresh | ~$3 |
| Secret Manager | 11 secrets (API keys, DB password, auth keys) | Free |
| Serverless VPC Connector | e2-micro, Cloud Run → Cloud SQL private link | ~$7 |
| Artifact Registry | Docker image repo | ~$0.50 |
| Firebase Hosting | Frontend SPA with CDN | Free |
| Cloud Scheduler | 4 cron jobs | Free |
| **Total** | | **~$57/mo** |

Note: No load balancer or Cloud Armor since using Cloud Run URL directly. Add ~$18/mo when a custom domain is needed.

## Deliverables

### 1. Migration Scripts

**`scripts/migrate-to-production.sh`**
- `pg_dump --format=custom` the full database (~300MB compressed)
- `gsutil rsync` image cache to assets bucket (3GB)
- `gsutil rsync` audio files to assets bucket
- Upload medallion_views.sql

**`scripts/restore-production.sh`**
- Enable PostGIS extension on Cloud SQL
- Run Alembic migrations (creates schema)
- `pg_restore --data-only --jobs=4` (loads data)
- Execute medallion_views.sql (creates materialized views)
- Refresh all views

### 2. Terraform Structure

```
terraform/
  main.tf              — provider, required GCP APIs
  variables.tf         — configurable inputs (tier, region, scaling)
  cloud_sql.tf         — PostgreSQL 17 instance + database + user
  cloud_run.tf         — FastAPI service with VPC access + secrets
  cloud_run_jobs.tf    — 4 pipeline job definitions
  cloud_storage.tf     — assets bucket (CDN), backups bucket
  cloud_scheduler.tf   — cron triggers for pipeline jobs
  secrets.tf           — Secret Manager for 11 keys
  networking.tf        — VPC, subnet, serverless connector, private services
  iam.tf               — 3 service accounts + IAM bindings
  artifact_registry.tf — Docker image repository
  outputs.tf           — Cloud Run URL, Cloud SQL connection, bucket names
```

### 3. Dockerfile

Single image for API + pipeline:
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y libpq-dev libgdal-dev libgeos-dev libproj-dev gcc
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY app/ app/
COPY pipeline/ pipeline/
COPY alembic/ alembic/
COPY scripts/ scripts/
COPY alembic.ini medallion_views.sql .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
```

### 4. Required Code Changes

| File | Change |
|---|---|
| 15+ frontend components | Replace `http://localhost:8001/api/v1` → `import.meta.env.VITE_API_BASE \|\| '/api/v1'` |
| `app/main.py` | CORS: read from `CORS_ORIGIN` env var |
| `app/image_cache.py` | Support GCS URLs via `STORAGE_BACKEND=gcs` env var |
| Audio/photo file serving | Cloud Storage URLs instead of local filesystem |

### 5. Secrets to Populate

```
anthropic-api-key     — Claude API
openai-api-key        — OpenAI audio model
google-client-id      — Google OAuth
google-client-secret  — Google OAuth
apple-client-id       — Apple OAuth
apple-team-id         — Apple OAuth
apple-key-id          — Apple OAuth
apple-private-key     — Apple OAuth (.p8 contents)
auth-secret-key       — JWT signing (32+ chars)
usgs-api-key          — USGS water data
db-password           — Cloud SQL user password
```

## Implementation Phases

1. **Migration scripts** — create migrate + restore scripts
2. **Dockerfile** — build and test locally
3. **Terraform** — all 11 .tf files targeting Option B in us-west1
4. **Code changes** — API base URL, CORS, storage abstraction

## Deployment Sequence

1. Bootstrap: create GCP project, enable billing, create Terraform state bucket
2. `terraform apply` — creates all infrastructure
3. Populate secrets via `gcloud secrets versions add`
4. Build + push Docker image to Artifact Registry
5. Run `scripts/migrate-to-production.sh` — export local data to GCS
6. Run `scripts/restore-production.sh` — restore into Cloud SQL
7. Build frontend: `VITE_API_BASE=https://api-xxx.run.app/api/v1 npm run build`
8. Deploy frontend: `firebase deploy`
9. Verify: hit /health, check data counts, test OAuth
