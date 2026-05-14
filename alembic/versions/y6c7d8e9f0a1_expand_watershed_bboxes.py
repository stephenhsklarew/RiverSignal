"""expand watershed bboxes to cover full drainage + curated stocking lakes

Revision ID: y6c7d8e9f0a1
Revises: x5b6c7d8e9f0
Create Date: 2026-05-14 14:00:00.000000

Updates `sites.bbox` for each watershed to match the audited values in
pipeline/config/watersheds.py.

The config dict only seeds new sites — existing sites.bbox values were
populated at first-ingest time and stayed at the original (tight)
bboxes. This migration writes the new values directly so adapters pick
up the expanded geography on their next run.

Idempotent. Old/new bboxes are captured so downgrade restores the prior
state exactly.
"""
from typing import Sequence, Union

from alembic import op
import json


revision: str = 'y6c7d8e9f0a1'
down_revision: Union[str, Sequence[str], None] = 'x5b6c7d8e9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (watershed, new_bbox, old_bbox) — explicit so downgrade can restore.
BBOX_UPDATES = [
    (
        "klamath",
        {"north": 43.20, "south": 42.10, "east": -120.70, "west": -122.30},
        {"north": 43.10, "south": 42.20, "east": -121.00, "west": -122.10},
    ),
    (
        "mckenzie",
        {"north": 44.45, "south": 43.85, "east": -121.70, "west": -123.10},
        {"north": 44.30, "south": 43.85, "east": -121.70, "west": -122.90},
    ),
    (
        "deschutes",
        {"north": 45.70, "south": 43.55, "east": -120.30, "west": -121.95},
        {"north": 44.80, "south": 43.85, "east": -120.60, "west": -121.85},
    ),
    (
        "metolius",
        {"north": 44.85, "south": 44.30, "east": -121.30, "west": -121.90},
        {"north": 44.65, "south": 44.35, "east": -121.35, "west": -121.80},
    ),
    (
        "johnday",
        {"north": 45.80, "south": 44.10, "east": -118.30, "west": -120.80},
        {"north": 45.05, "south": 44.15, "east": -118.40, "west": -119.90},
    ),
    (
        "skagit",
        {"north": 48.95, "south": 47.75, "east": -120.95, "west": -122.65},
        {"north": 48.90, "south": 48.20, "east": -121.00, "west": -122.60},
    ),
    (
        "green_river",
        {"north": 43.50, "south": 38.10, "east": -108.75, "west": -111.50},
        {"north": 43.50, "south": 38.10, "east": -109.00, "west": -111.50},
    ),
]


def upgrade() -> None:
    for ws, new_bbox, _ in BBOX_UPDATES:
        op.execute(
            f"UPDATE sites SET bbox = '{json.dumps(new_bbox)}'::jsonb "
            f"WHERE watershed = '{ws}'"
        )


def downgrade() -> None:
    for ws, _, old_bbox in BBOX_UPDATES:
        op.execute(
            f"UPDATE sites SET bbox = '{json.dumps(old_bbox)}'::jsonb "
            f"WHERE watershed = '{ws}'"
        )
