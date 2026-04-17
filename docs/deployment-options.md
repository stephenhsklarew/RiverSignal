# Deployment Options — RiverSignal / RiverPath / DeepTrail

## What Needs Hosting

| Component | Size | Requirements |
|-----------|------|-------------|
| Frontend | ~3MB build (4 apps, one SPA) | Static file serving, CDN |
| Backend | FastAPI + 9 routers | Python 3.12, ~256MB RAM |
| Database | PostgreSQL 17 + PostGIS, 3.2GB | Port 5433, spatial extensions |
| Image cache | 22,302 files, 3.0GB | Static serving, no compute |
| Nightly pipeline | 22 adapters, 30-60 min run | Cron + Python + network access |
| Backups | ~288MB compressed per full backup | Storage + scheduled job |

---

## GCP Option A — Minimal VM + Managed DB (~$23/mo)

A traditional server setup with a managed database.

```
┌─────────────────────────────┐
│  Compute Engine (e2-small)  │
│  ├── FastAPI (uvicorn)      │
│  ├── Nginx (reverse proxy)  │
│  ├── Cron (nightly pipeline)│
│  └── Image cache (3GB disk) │
└──────────┬──────────────────┘
           │ private IP
┌──────────▼──────────────────┐
│  Cloud SQL (PostgreSQL 17)  │
│  ├── PostGIS extension      │
│  ├── 10GB SSD               │
│  ├── Automated daily backups│
│  └── Point-in-time recovery │
└─────────────────────────────┘

Cloud Storage: DB backup exports + frontend SPA
Cloud CDN: serves frontend globally
```

| Service | Spec | Cost |
|---------|------|------|
| Compute Engine e2-small | 2 vCPU, 2GB RAM | ~$13/mo |
| Cloud SQL PostgreSQL 17 | db-f1-micro, 10GB SSD, PostGIS | ~$9/mo |
| Cloud Storage | Image cache + backups | ~$0.10/mo |
| Cloud CDN | Frontend static files | ~$1/mo |
| Cloud Scheduler | Nightly cron triggers | Free (3 jobs) |
| **Total** | | **~$23/mo** |

**You manage:** the VM (OS updates, uvicorn restarts, cron).
**GCP manages:** the database (backups, patching, failover).

Best for: wanting a managed database without managing Postgres yourself, but comfortable running a Linux box.

---

## GCP Option B — Serverless + Managed DB (~$17-27/mo) ⭐ PREFERRED

No VMs at all — everything runs as containers that scale to zero.

```
┌────────────────────────────────┐
│  Cloud Run (FastAPI container)  │
│  ├── Scales to zero when idle  │
│  ├── Scales up on traffic      │
│  └── HTTPS + custom domain     │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│  Cloud SQL (PostgreSQL 17)     │
│  ├── PostGIS                   │
│  └── Automated backups         │
└────────────────────────────────┘

Cloud Run Jobs: nightly pipeline (runs 30 min, then stops)
Cloud Scheduler: triggers pipeline job at 2am
Cloud Storage: image cache bucket + frontend SPA
Firebase Hosting: frontend CDN (free)
```

| Service | Spec | Cost |
|---------|------|------|
| Cloud Run | FastAPI container, scales to zero | ~$5-15/mo (usage) |
| Cloud SQL PostgreSQL 17 | db-f1-micro, 10GB SSD, PostGIS | ~$9/mo |
| Cloud Storage | Image cache + backups | ~$0.50/mo |
| Cloud Run Jobs | Nightly pipeline (30 min/day) | ~$2/mo |
| Cloud Scheduler | Triggers pipeline + backup | Free |
| Firebase Hosting | Frontend CDN | Free |
| **Total** | | **~$17-27/mo** |

**You manage:** Docker images, deployment config.
**GCP manages:** everything else — scaling, SSL, runtime, database, scheduling.

Best for: zero server management, pay only for what you use. FastAPI container sleeps when nobody's using it (nights/weekends = $0 compute). Pipeline job runs once per night.

### Implementation Notes

**Dockerfile for Cloud Run:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Cloud Run Job for pipeline:**
```bash
gcloud run jobs create pipeline-daily \
  --image gcr.io/PROJECT/riversignal-pipeline \
  --command "python,-m,pipeline.cli,ingest,all" \
  --task-timeout 3600 \
  --memory 2Gi
```

**Cloud Scheduler trigger:**
```bash
gcloud scheduler jobs create http pipeline-nightly \
  --schedule "0 2 * * *" \
  --uri "https://REGION-run.googleapis.com/apis/run.googleapis.com/v1/..." \
  --http-method POST
```

**Cloud SQL connection:**
Cloud Run connects to Cloud SQL via Unix socket (no public IP needed):
```
DATABASE_URL=postgresql+psycopg://user:pass@/riversignal?host=/cloudsql/PROJECT:REGION:INSTANCE
```

**Image cache on Cloud Storage:**
```bash
gsutil -m rsync -r frontend/public/images/cache/ gs://riversignal-images/cache/
```
Serve via Cloud CDN or Firebase Hosting rewrite.

---

## GCP Option D — Production-Ready (~$63/mo)

Everything managed + security + reliability for real users.

```
┌─────────────────────────────────────┐
│  Cloud Load Balancer + Cloud Armor  │
│  ├── DDoS protection               │
│  ├── SSL termination                │
│  ├── Rate limiting                  │
│  └── WAF rules                      │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│  Cloud Run (FastAPI, min 1 instance)│
│  ├── Always warm (no cold starts)   │
│  ├── 2GB RAM for LLM calls         │
│  └── Auto-scales to 10 instances   │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│  Cloud SQL (db-g1-small)            │
│  ├── 20GB SSD + auto-grow          │
│  ├── Daily backups (7 day retain)  │
│  ├── High availability (optional)  │
│  └── Private VPC connection         │
└──────────────────────────────────────┘

Cloud Run Jobs: nightly pipeline + backup export
Cloud Scheduler: triggers at 2am
Cloud Storage:
  ├── images bucket (3GB, CDN-fronted)
  ├── backups bucket (lifecycle: delete after 30 days)
  └── frontend bucket (SPA)
Firebase Hosting: frontend CDN with preview channels
Cloud Monitoring: alerts on errors, latency, DB size
Secret Manager: API keys (Anthropic, RIDB)
```

| Service | Spec | Cost |
|---------|------|------|
| Cloud Run | FastAPI, min 1 instance, 2GB RAM | ~$15/mo |
| Cloud SQL PostgreSQL 17 | db-g1-small, 20GB SSD, daily backups | ~$26/mo |
| Cloud Storage | Images + backups + frontend | ~$0.50/mo |
| Cloud Run Jobs | Nightly pipeline | ~$3/mo |
| Cloud Armor + Load Balancer | DDoS, WAF, SSL | ~$18/mo |
| Firebase Hosting | Frontend CDN | Free |
| Cloud Monitoring | Alerts | Free (basic) |
| Secret Manager | API keys | Free (<10K accesses) |
| **Total** | | **~$63/mo** |

**You manage:** code deploys (git push → Cloud Build → Cloud Run).
**GCP manages:** literally everything else.

Best for: real users depending on the app, where downtime and security matter.

---

## Other Provider Comparison

| Provider | Cheapest | Best Value | Production |
|----------|----------|-----------|------------|
| **Hetzner + Cloudflare** | $5/mo | $8/mo | $15/mo |
| **GCP** | Free (yr 1) → $10 | $23/mo | $63/mo |
| **Railway** | $10/mo | $20/mo | $40/mo |
| **AWS** | $10/mo | $30/mo | $60/mo |
| **DigitalOcean** | $12/mo | $32/mo | $50/mo |
| **Fly.io + Neon** | $5/mo | $25/mo | $45/mo |

### Hetzner CX22 + Cloudflare (~$5/mo)

```
Hetzner CX22 ($4.50/mo) — 4GB RAM, 40GB SSD, 20TB traffic
├── PostgreSQL 17 + PostGIS (3.2GB database)
├── FastAPI (uvicorn with systemd)
├── Cron (nightly pipeline + backups)
├── Image cache (3GB on local disk)
└── Nginx (reverse proxy + static files)

Cloudflare (free)
├── Pages: frontend SPA (global CDN)
├── R2: backup storage (free under 10GB)
└── DNS + SSL
```

Cheapest option. You manage everything on the VPS.

### Railway (~$10-20/mo)

Git-push deploy, managed Postgres with PostGIS, built-in cron. One platform for everything. Usage-based billing.

### Fly.io + Neon (~$25/mo)

Fly.io for backend (scales to zero, ~$5-15). Neon for serverless Postgres with PostGIS ($19/mo for 10GB). Cloudflare R2 for images (free). Vercel for frontend (free).

---

## Current Local Development Setup

```
Frontend: Vite dev server (port 5174)
Backend: FastAPI uvicorn --reload (port 8001)
Database: PostgreSQL 17 + PostGIS 3.6.2 (port 5433)
Image cache: frontend/public/images/cache/ (3GB local)
Pipeline: python -m pipeline.cli (manual or cron)
Backups: ./scripts/backup-db.sh → backups/ directory
```

## Deployment Checklist (Any Provider)

- [ ] PostgreSQL 17 with PostGIS extension enabled
- [ ] Environment variables: DATABASE_URL, ANTHROPIC_API_KEY
- [ ] Run database migration: `alembic upgrade head`
- [ ] Seed data: `python -m pipeline.seed_hatch_chart && python -m pipeline.seed_fly_tying_videos`
- [ ] Run initial ingestion: `./scripts/deploy-pipeline.sh all`
- [ ] Refresh materialized views: `python -m pipeline.cli refresh`
- [ ] Cache images: `python -m pipeline.cache_images`
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] Configure nightly cron (pipeline/crontab or Cloud Scheduler)
- [ ] Configure backup schedule (scripts/backup-db.sh or Cloud SQL automated)
- [ ] Set up DNS + SSL
- [ ] Verify all 4 product routes work: /, /riversignal, /path/now, /trail
