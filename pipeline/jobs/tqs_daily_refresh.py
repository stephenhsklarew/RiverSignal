"""Daily TQS refresh job.

Runs once per day. Recomputes gold.trip_quality_daily for today..today+90,
then appends today's snapshot rows into gold.trip_quality_history for
the alert engine's slope queries.

Both operations are idempotent — safe to re-run within the same day.

Cloud Run Job entry point: `python -m pipeline.jobs.tqs_daily_refresh`.
"""

from __future__ import annotations

import json
import sys
from datetime import date

from pipeline.predictions.trip_quality import (
    refresh_trip_quality_daily,
    snapshot_history,
)


def main() -> int:
    today = date.today()
    refreshed = refresh_trip_quality_daily()
    snapshotted = snapshot_history(today)
    summary = {
        "date": today.isoformat(),
        "refreshed_rows": refreshed,
        "snapshot_rows_appended": snapshotted,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
