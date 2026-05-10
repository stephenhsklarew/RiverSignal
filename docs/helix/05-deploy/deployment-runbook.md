# Deployment Runbook — Liquid Marble

This document is the operational reference for deploying, monitoring, and rolling back the production system. Pair it with `02-design/architecture.md` for the system overview.

## Production environment

| Resource | Identifier | Region |
|----------|------------|--------|
| GCP project | `riversignal-prod` | global |
| Cloud Run service | `riversignal-api` | `us-west1` |
| Cloud SQL instance | `riversignal-db` | `us-west1` |
| Artifact Registry | `us-west1-docker.pkg.dev/riversignal-prod/riversignal/api` | `us-west1` |
| GCS bucket | `riversignal-assets-riversignal-prod` | US multi-region |
| Public URL | `https://riversignal-api-x6ka75yaxa-uw.a.run.app` | — |

## Standard deploy (push to main)

The default path. Used for any code change.

1. Open a PR against `main`. CI deploys on merge to `main`, not on PR alone.
2. Local pre-flight before merging:
   ```bash
   npx tsc -p frontend/tsconfig.app.json --noEmit
   pytest tests/
   ```
3. Merge the PR (or push directly to `main` for solo-engineer expedited changes).
4. GitHub Actions workflow `Build & Deploy to GCP` (`.github/workflows/deploy.yml`) starts automatically.
5. Watch the run:
   ```bash
   gh run watch $(gh run list --workflow=deploy.yml --limit=1 --json databaseId -q '.[0].databaseId') --exit-status
   ```
6. Workflow steps (typical 4–5 minutes):
   - Authenticate to GCP via Workload Identity Federation
   - Build Docker image (multi-stage: Python deps, frontend Vite build, runtime)
   - Push to Artifact Registry tagged `latest`
   - Run alembic migrations via `riversignal-migrate` Cloud Run Job
   - Deploy new revision to `riversignal-api` Cloud Run service
7. Verify production:
   ```bash
   gcloud run services describe riversignal-api --region us-west1 \
     --format="value(status.latestReadyRevisionName)"
   curl -s -o /dev/null -w "/health: %{http_code}\n" https://riversignal-api-x6ka75yaxa-uw.a.run.app/health
   ```

## Deploy without code changes (env var or secret rotation)

Use when only changing Cloud Run env vars or rotating secrets — no rebuild needed.

```bash
gcloud run services update riversignal-api --region us-west1 \
  --update-env-vars=KEY=VALUE
```

A new revision is created and traffic shifts to it; secrets at `version=latest` are re-fetched.

## Rollback

### Fast rollback (last-known-good revision)

```bash
# List recent revisions
gcloud run revisions list --service=riversignal-api --region us-west1 \
  --format="table(metadata.name,metadata.creationTimestamp,status.conditions[0].status)" --limit=10

# Roll back traffic to a specific revision
gcloud run services update-traffic riversignal-api --region us-west1 \
  --to-revisions=riversignal-api-00021-2rt=100
```

This is the fastest recovery. Revisions are immutable, so rolling back is safe.

### Code rollback (via git)

For longer-term issues (regressions you don't want to roll forward through):

```bash
git revert <bad-sha>
git push origin main
# Triggers a fresh deploy with the revert
```

### Schema rollback

Alembic migrations should be written to support `downgrade()`. To roll back:

```bash
gcloud run jobs execute riversignal-migrate --region us-west1 \
  --args="alembic downgrade -1" --wait
```

Caution: not all migrations are reversible (e.g., column drops with data). Check the migration file before running.

## Failed deploy diagnostics

```bash
# Most recent run
gh run list --workflow=deploy.yml --limit=3
# Failed step logs
gh run view <run-id> --log-failed | tail -50
```

Common failures:

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Build fails at `npm run build` with TS error | TypeScript regression from a merged change | `cd frontend && npx tsc -p tsconfig.app.json --noEmit` locally; fix |
| Migrate job fails | Alembic migration depends on a column that doesn't exist in current schema | Check `alembic history`; resolve in a new migration |
| Deploy succeeds but `/health` returns 5xx | Env var or secret missing on revision | `gcloud run services describe` to inspect env; fix and redeploy |
| Deploy succeeds but app loads then errors | Frontend bundle calls a removed API endpoint | Check browser console; trace to changed route; fix |

## Manual operations

### Run an ad-hoc data fix in production

The production DB has private VPC IP only — `cloud-sql-proxy` from a laptop can't reach it without a VPN tunnel. Use a Cloud Run Job override to run SQL/Python from within the VPC:

```bash
# Encode a Python snippet
B64=$(cat << 'EOF' | base64 | tr -d '\n'
from sqlalchemy import text
from pipeline.db import engine
with engine.connect() as conn:
    print(conn.execute(text("SELECT count(*) FROM gold.snowpack_current")).scalar())
EOF
)

gcloud run jobs execute riversignal-pipeline-daily --region us-west1 \
  --args="echo $B64 | base64 -d | python -" --wait
```

This was used to apply the `gold.snowpack_current` view DDL on 2026-05-09 (see `02-design/tech-spike-snowpack-current-view.md`).

### Rotate a secret

```bash
echo -n "<new-value>" | gcloud secrets versions add <secret-name> --data-file=-
# Force a new revision so Cloud Run re-reads
gcloud run services update riversignal-api --region us-west1
```

Secrets used in production: `google-client-id`, `google-client-secret`, `apple-client-id`, `apple-team-id`, `apple-key-id`, `apple-private-key`, `auth-secret-key`, `anthropic-api-key`, `openai-api-key`, `usgs-api-key`. DB password is auto-managed by Terraform.

### Force a gold view refresh

```bash
gcloud run jobs execute riversignal-refresh-views --region us-west1 --wait      # light views
gcloud run jobs execute riversignal-refresh-heavy --region us-west1 --wait      # heavy views (~30min)
```

### View Cloud Scheduler status

```bash
gcloud scheduler jobs list --location=us-west1 \
  --format="table(name.basename(),schedule,timeZone,state,lastAttemptTime)"
```

Currently configured: `riversignal-daily-pipeline` (02:00 PT), `riversignal-weekly-pipeline` (Mon 04:00 PT), `riversignal-monthly-pipeline` (1st @ 05:00 PT), `riversignal-refresh-views` (10:00 PT daily), `riversignal-refresh-heavy` (Sun 03:00 PT — declared in Terraform; verify deployed).

## Database backup & restore

Cloud SQL automated backups run nightly with 14-day retention.

### Restore to a new instance

```bash
gcloud sql backups list --instance=riversignal-db
gcloud sql backups restore <backup-id> \
  --restore-instance=riversignal-db-restore --instance=riversignal-db
```

After restore, point a new Cloud Run revision at the restored instance via Terraform or `--update-env-vars=DATABASE_URL=...`.

### Point-in-time recovery

```bash
gcloud sql instances clone riversignal-db riversignal-db-pit \
  --point-in-time=<RFC3339-timestamp>
```

## Incident response

1. **Detect**: alert from Cloud Logging error rate, user report, or `/health` failure.
2. **Triage**: check `gcloud run services describe`, recent deploy log (`gh run list`), Cloud SQL status, recent secret rotations.
3. **Stabilize**: rollback to last-known-good revision (see "Fast rollback" above) or scale up if it's a load issue (`gcloud run services update --max-instances=20`).
4. **Communicate**: update `/status` page if the incident is user-visible (TODO: status page banner mechanism).
5. **Fix**: write a fix on a branch; deploy with the standard flow.
6. **Postmortem**: write up in `docs/helix/06-iterate/alignment-reviews/AR-YYYY-MM-DD-incident.md` and link from this runbook.

## Compliance: data subject deletion / export

Until self-service endpoints ship (in `04-build/implementation-plan.md` backlog item 14):

```bash
# Delete user manually (irreversible)
gcloud run jobs execute riversignal-pipeline-daily --region us-west1 \
  --args="echo <base64-script> | base64 -d | python -" --wait
```

Where the script reads the user_id and removes from `users`, `user_observations`, `user_settings`, and saved-items tables. Document each deletion in an append-only log file (TODO: build the log).

## Cost monitoring

```bash
# Recent month's bill
gcloud billing accounts list
gcloud beta billing accounts get-iam-policy <account-id>
# Or use the GCP console → Billing → Reports
```

Budget alerts configured at $50/day and $500/month. Review monthly.

## See also

- `02-design/architecture.md` — system layout
- `02-design/tech-spike-snowpack-current-view.md` — example of in-VPC DB hot-fix
- `01-frame/risk-register.md` — risks this runbook addresses
- `01-frame/threat-model.md` — incident response context
- `terraform/` directory — IaC for everything above
