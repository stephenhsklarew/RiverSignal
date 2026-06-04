"""seed stocking_locations for chattahoochee (map pins for ga_trout stockings)

Revision ID: ch10a1b2c3d4
Revises: ch09a1b2c3d4
Create Date: 2026-06-04 00:00:00.000000

The ga_trout stockings surface in gold.stocking_schedule (via ch09) but had
NULL lat/lon — the schedule LEFT JOINs stocking_locations on (watershed,
waterbody), and there were no Chattahoochee rows, so the Fish Stocking "View map"
showed no pins. Seed coords for the Chattahoochee-system stocking waters. The
`waterbody` strings MUST match exactly what ga_trout writes to
interventions.description ->> 'waterbody'. Coords approximate (needs_review).
Idempotent via NOT EXISTS on (watershed, waterbody).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ch10a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ch09a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (waterbody EXACT, lat, lon, notes)
LOCS = [
    ('Lanier Tailwater', 34.158, -84.073, 'Buford Dam tailwater (Forsyth/Gwinnett) — cold-release trout'),
    ('Chattahoochee River', 34.700, -83.730, 'Upper Chattahoochee near Helen (White Co)'),
    ('Chattahoochee River (WMA)', 34.742, -83.772, 'Chattahoochee WMA section above Helen (White Co)'),
    ('Soque River', 34.611, -83.522, 'Soque River, Clarkesville (Habersham Co) — Chattahoochee tributary'),
    ('Smith Creek', 34.720, -83.722, 'Smith Creek, Unicoi SP (White Co)'),
    ('Low Gap Creek', 34.732, -83.792, 'Low Gap Creek (White Co) — Chattahoochee headwaters'),
    ('Jasus Creek', 34.712, -83.762, 'Jasus Creek (White Co) — Chattahoochee headwaters'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for waterbody, lat, lon, notes in LOCS:
        conn.execute(
            text("""
                INSERT INTO stocking_locations (id, watershed, waterbody, latitude, longitude, notes)
                SELECT gen_random_uuid(), 'chattahoochee', CAST(:wb AS varchar),
                       CAST(:lat AS double precision), CAST(:lon AS double precision), CAST(:notes AS text)
                WHERE NOT EXISTS (
                    SELECT 1 FROM stocking_locations
                    WHERE watershed = 'chattahoochee' AND waterbody = :wb
                )
            """),
            {"wb": waterbody, "lat": lat, "lon": lon, "notes": notes},
        )


def downgrade() -> None:
    op.execute("DELETE FROM stocking_locations WHERE watershed = 'chattahoochee'")
