#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# RiverSignal — Migrate Local Data to GCP Production
#
# Exports the local PostgreSQL database and filesystem assets,
# then uploads everything to GCS for production restore.
#
# Prerequisites:
#   - gcloud CLI authenticated (gcloud auth login)
#   - gsutil available
#   - pg_dump for PostgreSQL 17
#
# Usage:
#   ./scripts/migrate-to-production.sh <assets-bucket> <backups-bucket>
#
# Example:
#   ./scripts/migrate-to-production.sh \
#     riversignal-assets-myproject \
#     riversignal-backups-myproject
# ═══════════════════════════════════════════════════════════════

ASSETS_BUCKET="${1:?Usage: $0 <assets-bucket> <backups-bucket>}"
BACKUPS_BUCKET="${2:?Usage: $0 <assets-bucket> <backups-bucket>}"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXPORT_DIR="$PROJECT_DIR/migration-export"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# PostgreSQL connection (local)
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5433}"
PG_DB="${PG_DB:-riversignal}"
PG_DUMP="/opt/homebrew/opt/postgresql@17/bin/pg_dump"

echo "═══════════════════════════════════════════"
echo "  RiverSignal — Migration Export"
echo "  Database: $PG_DB @ $PG_HOST:$PG_PORT"
echo "  Assets bucket: gs://$ASSETS_BUCKET"
echo "  Backups bucket: gs://$BACKUPS_BUCKET"
echo "═══════════════════════════════════════════"

# ── Validate prerequisites ──
command -v gsutil >/dev/null 2>&1 || { echo "ERROR: gsutil not found. Install gcloud SDK."; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "ERROR: psql not found."; exit 1; }

if [ ! -f "$PG_DUMP" ]; then
  PG_DUMP="$(which pg_dump)"
fi
[ -x "$PG_DUMP" ] || { echo "ERROR: pg_dump not found."; exit 1; }

gsutil ls "gs://$ASSETS_BUCKET" >/dev/null 2>&1 || { echo "ERROR: Bucket gs://$ASSETS_BUCKET not accessible."; exit 1; }
gsutil ls "gs://$BACKUPS_BUCKET" >/dev/null 2>&1 || { echo "ERROR: Bucket gs://$BACKUPS_BUCKET not accessible."; exit 1; }

# ── Create export directory ──
mkdir -p "$EXPORT_DIR"

# ── Step 1: Database dump (custom format for parallel restore) ──
echo ""
echo "Step 1/5: Exporting database..."
DUMP_FILE="$EXPORT_DIR/riversignal-$TIMESTAMP.dump"
"$PG_DUMP" -h "$PG_HOST" -p "$PG_PORT" -d "$PG_DB" \
  --format=custom \
  --no-owner \
  --no-privileges \
  --compress=6 \
  -f "$DUMP_FILE"

DUMP_SIZE=$(du -sh "$DUMP_FILE" | cut -f1)
echo "  Database dump: $DUMP_SIZE → $DUMP_FILE"

# ── Step 2: Copy medallion views SQL ──
echo ""
echo "Step 2/5: Copying medallion views..."
cp "$PROJECT_DIR/medallion_views.sql" "$EXPORT_DIR/"
echo "  medallion_views.sql copied"

# ── Step 3: Upload database dump to GCS ──
echo ""
echo "Step 3/5: Uploading database dump to GCS..."
gsutil cp "$DUMP_FILE" "gs://$BACKUPS_BUCKET/migration/"
gsutil cp "$EXPORT_DIR/medallion_views.sql" "gs://$BACKUPS_BUCKET/migration/"
echo "  Uploaded to gs://$BACKUPS_BUCKET/migration/"

# ── Step 4: Sync image cache to assets bucket ──
echo ""
echo "Step 4/5: Syncing image cache to assets bucket (this may take a while)..."

if [ -d "$PROJECT_DIR/frontend/public/images/cache" ]; then
  gsutil -m rsync -r "$PROJECT_DIR/frontend/public/images/cache/" \
    "gs://$ASSETS_BUCKET/images/cache/"
  echo "  Image cache synced"
else
  echo "  No image cache found, skipping"
fi

# ── Step 5: Sync audio files to assets bucket ──
echo ""
echo "Step 5/5: Syncing audio files..."

if [ -d "$PROJECT_DIR/.river_story_audio" ]; then
  gsutil -m rsync -r "$PROJECT_DIR/.river_story_audio/" \
    "gs://$ASSETS_BUCKET/audio/river_stories/"
  echo "  River Path audio synced"
fi

if [ -d "$PROJECT_DIR/.deep_time_audio" ]; then
  gsutil -m rsync -r "$PROJECT_DIR/.deep_time_audio/" \
    "gs://$ASSETS_BUCKET/audio/deep_time/"
  echo "  Deep Trail audio synced"
fi

if [ -d "$PROJECT_DIR/.campfire_cache" ]; then
  gsutil -m rsync -r "$PROJECT_DIR/.campfire_cache/" \
    "gs://$ASSETS_BUCKET/audio/campfire/"
  echo "  Campfire audio synced"
fi

if [ -d "$PROJECT_DIR/.user_photos" ]; then
  gsutil -m rsync -r "$PROJECT_DIR/.user_photos/" \
    "gs://$ASSETS_BUCKET/user_photos/"
  echo "  User photos synced"
fi

# ── Summary ──
echo ""
echo "═══════════════════════════════════════════"
echo "  Migration export complete!"
echo ""
echo "  Database dump: gs://$BACKUPS_BUCKET/migration/$(basename $DUMP_FILE)"
echo "  Views SQL:     gs://$BACKUPS_BUCKET/migration/medallion_views.sql"
echo "  Images:        gs://$ASSETS_BUCKET/images/cache/"
echo "  Audio:         gs://$ASSETS_BUCKET/audio/"
echo ""
echo "  Next: run restore-production.sh on the production side"
echo "═══════════════════════════════════════════"
