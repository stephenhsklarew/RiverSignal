#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# RiverSignal — Restore Production Database from Migration Export
#
# Run AFTER Terraform has created the Cloud SQL instance.
# Can be run from Cloud Shell, a local machine with Cloud SQL Proxy,
# or as a Cloud Run Job.
#
# Prerequisites:
#   - DATABASE_URL env var pointing to Cloud SQL
#     (e.g. via Cloud SQL Proxy: postgresql+psycopg://user:pass@localhost:5432/riversignal)
#   - gsutil access to the backups bucket
#   - Python venv with project dependencies
#
# Usage:
#   export DATABASE_URL="postgresql+psycopg://riversignal_app:PASSWORD@localhost:5432/riversignal"
#   ./scripts/restore-production.sh <backups-bucket>
#
# Example:
#   ./scripts/restore-production.sh riversignal-backups-myproject
# ═══════════════════════════════════════════════════════════════

BACKUPS_BUCKET="${1:?Usage: $0 <backups-bucket>}"
DATABASE_URL="${DATABASE_URL:?ERROR: DATABASE_URL environment variable is required}"

# Parse DATABASE_URL for pg_restore (needs host/port/user/db separately)
# Format: postgresql+psycopg://user:pass@host:port/dbname or with ?host=/cloudsql/...
if [[ "$DATABASE_URL" =~ ://([^:]+):([^@]+)@([^:/]+):?([0-9]*)/([^?]+) ]]; then
  PG_USER="${BASH_REMATCH[1]}"
  PG_PASS="${BASH_REMATCH[2]}"
  PG_HOST="${BASH_REMATCH[3]}"
  PG_PORT="${BASH_REMATCH[4]:-5432}"
  PG_DB="${BASH_REMATCH[5]}"
else
  echo "ERROR: Could not parse DATABASE_URL. Expected format: postgresql+psycopg://user:pass@host:port/dbname"
  exit 1
fi

export PGPASSWORD="$PG_PASS"
WORK_DIR="/tmp/riversignal-restore"
mkdir -p "$WORK_DIR"

echo "═══════════════════════════════════════════"
echo "  RiverSignal — Production Restore"
echo "  Database: $PG_DB @ $PG_HOST:$PG_PORT"
echo "  Bucket: gs://$BACKUPS_BUCKET"
echo "═══════════════════════════════════════════"

# ── Step 1: Download migration files from GCS ──
echo ""
echo "Step 1/6: Downloading migration files..."

# Find the latest dump file
DUMP_FILE=$(gsutil ls "gs://$BACKUPS_BUCKET/migration/riversignal-*.dump" 2>/dev/null | sort | tail -1)
if [ -z "$DUMP_FILE" ]; then
  echo "ERROR: No dump file found in gs://$BACKUPS_BUCKET/migration/"
  exit 1
fi

gsutil cp "$DUMP_FILE" "$WORK_DIR/riversignal.dump"
gsutil cp "gs://$BACKUPS_BUCKET/migration/medallion_views.sql" "$WORK_DIR/"
echo "  Downloaded: $(basename $DUMP_FILE)"

# ── Step 2: Enable PostGIS ──
echo ""
echo "Step 2/6: Enabling PostGIS extensions..."
psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>/dev/null || true
psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;" 2>/dev/null || true
echo "  PostGIS enabled"

# ── Step 3: Run Alembic migrations (create schema) ──
echo ""
echo "Step 3/6: Running Alembic migrations..."
alembic upgrade head
echo "  Schema created"

# ── Step 4: Restore data ──
echo ""
echo "Step 4/6: Restoring data (this may take several minutes)..."
pg_restore \
  -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" \
  --no-owner --no-privileges \
  --data-only \
  --jobs=4 \
  --disable-triggers \
  "$WORK_DIR/riversignal.dump" 2>&1 || true
# pg_restore returns non-zero on warnings (e.g. missing tables), so we allow failure

echo "  Data restored"

# ── Step 5: Create materialized views ──
echo ""
echo "Step 5/6: Creating materialized views..."

# Create schemas first
psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "CREATE SCHEMA IF NOT EXISTS silver;"
psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "CREATE SCHEMA IF NOT EXISTS gold;"

psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -f "$WORK_DIR/medallion_views.sql"
echo "  Materialized views created"

# ── Step 6: Refresh views ──
echo ""
echo "Step 6/6: Refreshing materialized views..."
python -m pipeline.cli refresh
echo "  Views refreshed"

# ── Verify ──
echo ""
echo "═══════════════════════════════════════════"
echo "  Verification"
echo "═══════════════════════════════════════════"

OBS_COUNT=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -t -c "SELECT count(*) FROM observations;")
TS_COUNT=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -t -c "SELECT count(*) FROM time_series;")
MV_COUNT=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -t -c "SELECT count(*) FROM pg_matviews WHERE schemaname IN ('silver','gold');")
WS_COUNT=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -t -c "SELECT count(*) FROM sites;")

echo "  Observations:       $(echo $OBS_COUNT | xargs)"
echo "  Time series:        $(echo $TS_COUNT | xargs)"
echo "  Materialized views: $(echo $MV_COUNT | xargs)"
echo "  Watersheds:         $(echo $WS_COUNT | xargs)"
echo ""
echo "  Restore complete!"
echo "═══════════════════════════════════════════"

# Cleanup
rm -rf "$WORK_DIR"
