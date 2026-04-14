#!/usr/bin/env bash
#
# RiverSignal Data Pipeline — Deployment & Refresh Script
#
# Usage:
#   ./scripts/deploy-pipeline.sh              # Full daily refresh
#   ./scripts/deploy-pipeline.sh daily        # Daily sources only
#   ./scripts/deploy-pipeline.sh weekly       # Weekly sources only
#   ./scripts/deploy-pipeline.sh monthly      # Monthly sources only
#   ./scripts/deploy-pipeline.sh quarterly    # Quarterly sources only
#   ./scripts/deploy-pipeline.sh annual       # Annual sources only
#   ./scripts/deploy-pipeline.sh all          # Everything including annual
#   ./scripts/deploy-pipeline.sh refresh      # Just refresh materialized views
#   ./scripts/deploy-pipeline.sh install-cron # Install the crontab
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
LOG="$LOG_DIR/pipeline-$(date +%Y%m%d-%H%M%S).log"

mkdir -p "$LOG_DIR"

run() {
  echo "[$(date +%H:%M:%S)] Running: $*" | tee -a "$LOG"
  "$PYTHON" -m pipeline.cli "$@" --watershed all >> "$LOG" 2>&1 || echo "  ⚠ Failed: $*" | tee -a "$LOG"
}

echo "═══════════════════════════════════════════" | tee -a "$LOG"
echo "  RiverSignal Pipeline — $(date)" | tee -a "$LOG"
echo "  Mode: ${1:-daily}" | tee -a "$LOG"
echo "═══════════════════════════════════════════" | tee -a "$LOG"

MODE="${1:-daily}"

# ── Daily sources ──
if [[ "$MODE" == "daily" || "$MODE" == "all" ]]; then
  echo "" | tee -a "$LOG"
  echo "── Daily Sources ──" | tee -a "$LOG"
  run ingest inaturalist
  run ingest snotel
  run ingest usgs
fi

# ── Weekly sources ──
if [[ "$MODE" == "weekly" || "$MODE" == "all" ]]; then
  echo "" | tee -a "$LOG"
  echo "── Weekly Sources ──" | tee -a "$LOG"
  run ingest fishing
  run ingest wqp
fi

# ── Monthly sources ──
if [[ "$MODE" == "monthly" || "$MODE" == "all" ]]; then
  echo "" | tee -a "$LOG"
  echo "── Monthly Sources ──" | tee -a "$LOG"
  run ingest biodata
  run ingest wqp_bugs
  run ingest gbif
  run ingest recreation
  run ingest pbdb
  run ingest restoration
  run ingest prism
  run ingest streamnet
  run ingest idigbio
fi

# ── Quarterly sources ──
if [[ "$MODE" == "quarterly" || "$MODE" == "all" ]]; then
  echo "" | tee -a "$LOG"
  echo "── Quarterly Sources ──" | tee -a "$LOG"
  run ingest mtbs
  run ingest fish_passage
  run ingest impaired
  run ingest blm_sma
fi

# ── Annual sources ──
if [[ "$MODE" == "annual" || "$MODE" == "all" ]]; then
  echo "" | tee -a "$LOG"
  echo "── Annual Sources ──" | tee -a "$LOG"
  run ingest nhdplus
  run ingest wetlands
  run ingest wbd
  run ingest macrostrat
  run ingest mrds
  run ingest dogami
fi

# ── Refresh materialized views ──
if [[ "$MODE" != "install-cron" ]]; then
  echo "" | tee -a "$LOG"
  echo "── Refreshing Materialized Views ──" | tee -a "$LOG"
  run refresh
fi

# ── Install crontab ──
if [[ "$MODE" == "install-cron" ]]; then
  echo "Installing crontab from pipeline/crontab..."
  # Update PROJECT path in crontab
  sed "s|PROJECT=.*|PROJECT=$PROJECT_DIR|g; s|PYTHON=.*|PYTHON=$PYTHON|g" \
    "$PROJECT_DIR/pipeline/crontab" | crontab -
  echo "Crontab installed. Current schedule:"
  crontab -l | grep -v "^#" | grep -v "^$" | head -20
  exit 0
fi

echo "" | tee -a "$LOG"
echo "═══════════════════════════════════════════" | tee -a "$LOG"
echo "  Complete: $(date)" | tee -a "$LOG"
echo "  Log: $LOG" | tee -a "$LOG"
echo "═══════════════════════════════════════════" | tee -a "$LOG"
