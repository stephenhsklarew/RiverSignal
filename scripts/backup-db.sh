#!/usr/bin/env bash
#
# RiverSignal Database Backup
#
# Usage:
#   ./scripts/backup-db.sh                    # Full backup (schema + data)
#   ./scripts/backup-db.sh --schema-only      # Schema only (fast, small)
#   ./scripts/backup-db.sh --data-only        # Data only
#   ./scripts/backup-db.sh --tables           # List tables with sizes
#   ./scripts/backup-db.sh --restore <file>   # Restore from backup
#
set -euo pipefail

DB_NAME="riversignal"
DB_PORT="5433"
DB_HOST="localhost"
PG_DUMP="/opt/homebrew/opt/postgresql@17/bin/"$PG_DUMP""
PSQL="/opt/homebrew/opt/postgresql@17/bin/"$PSQL""
BACKUP_DIR="$(cd "$(dirname "$0")/.." && pwd)/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

case "${1:-full}" in
  --schema-only)
    FILE="$BACKUP_DIR/schema-${TIMESTAMP}.sql"
    echo "Backing up schema only to $FILE..."
    "$PG_DUMP" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" \
      --schema-only --no-owner --no-privileges \
      > "$FILE"
    echo "Done: $(du -h "$FILE" | cut -f1)"
    ;;

  --data-only)
    FILE="$BACKUP_DIR/data-${TIMESTAMP}.sql.gz"
    echo "Backing up data only to $FILE..."
    "$PG_DUMP" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" \
      --data-only --no-owner \
      | gzip > "$FILE"
    echo "Done: $(du -h "$FILE" | cut -f1)"
    ;;

  --tables)
    echo "Table sizes in $DB_NAME:"
    "$PSQL" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "
      SELECT schemaname || '.' || tablename AS table,
             pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size
      FROM pg_tables
      WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
      ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;
    "
    echo ""
    "$PSQL" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "
      SELECT schemaname || '.' || matviewname AS view,
             pg_size_pretty(pg_total_relation_size(schemaname || '.' || matviewname)) AS size
      FROM pg_matviews
      WHERE schemaname IN ('silver', 'gold')
      ORDER BY pg_total_relation_size(schemaname || '.' || matviewname) DESC
      LIMIT 15;
    "
    echo ""
    "$PSQL" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "
      SELECT pg_size_pretty(pg_database_size('$DB_NAME')) AS total_database_size;
    "
    ;;

  --restore)
    FILE="${2:?Usage: backup-db.sh --restore <file>}"
    if [[ ! -f "$FILE" ]]; then
      echo "Error: $FILE not found"
      exit 1
    fi
    echo "⚠  This will overwrite the $DB_NAME database. Continue? (y/N)"
    read -r CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
      echo "Cancelled."
      exit 0
    fi
    echo "Restoring from $FILE..."
    if [[ "$FILE" == *.gz ]]; then
      gunzip -c "$FILE" | "$PSQL" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME"
    else
      "$PSQL" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" < "$FILE"
    fi
    echo "Done."
    ;;

  full|*)
    FILE="$BACKUP_DIR/full-${TIMESTAMP}.sql.gz"
    echo "Full backup to $FILE..."
    echo "This may take a few minutes for a 2.5M+ record database."
    "$PG_DUMP" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" \
      --no-owner --no-privileges \
      --format=plain \
      | gzip > "$FILE"
    SIZE=$(du -h "$FILE" | cut -f1)
    echo ""
    echo "═══════════════════════════════════════"
    echo "  Backup complete: $FILE"
    echo "  Size: $SIZE"
    echo "  Restore: ./scripts/backup-db.sh --restore $FILE"
    echo "═══════════════════════════════════════"
    ;;
esac

# Cleanup: keep last 5 backups, remove older
cd "$BACKUP_DIR"
ls -t full-*.sql.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
ls -t schema-*.sql 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
ls -t data-*.sql.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
