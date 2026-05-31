"""seed Mad River brown-trout STREAM stocking (ODNR) + stocking_locations

Revision ID: mr10a1b2c3d4
Revises: mr09a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

P1 follow-on bead from the mad_river_oh verification report. The signature
Mad River fishery — ~11,500 brown-trout yearlings stocked every mid-October
in the Champaign/Clark C&R section (~500/mile) — is NOT in any structured
ODNR feed (the ohio_stocking adapter parses the statewide put-and-take
rainbow schedule, which has no Mad-River rows). ODNR publishes this program
as narrative content, so it is curated here as `interventions` rows
(type='fish_stocking', source='ohio_dnr', needs_review=true), matching the
shape the `gold.stocking_schedule` ohio_dnr branch reads (see mr11).

A `stocking_locations` row gives the C&R section coords so the Fish Stocking
"View map" surface renders a pin.

Idempotent: interventions dedup by (date, waterbody) via NOT EXISTS;
stocking_locations via ON CONFLICT.
"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'mr10a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr09a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


WATERBODY = "Mad River (C&R Section)"

# (stocking_date, quantity, species) — ODNR's annual fall brown-trout program.
# Mid-October yearling stocking, ~11,500 fish (~500/mile). Two most-recent
# years seeded for a small history; needs_review for exact dates/counts.
EVENTS = [
    ("2024-10-16", 11500, "Brown Trout"),
    ("2025-10-15", 11500, "Brown Trout"),
]


def upgrade() -> None:
    conn = op.get_bind()
    sid = conn.execute(
        text("SELECT id FROM sites WHERE watershed = 'mad_river_oh' LIMIT 1")
    ).fetchone()
    if not sid:
        return
    site_id = sid[0]

    for date_iso, qty, species in EVENTS:
        conn.execute(
            text("""
                INSERT INTO interventions (id, site_id, type, description, started_at, created_at)
                SELECT gen_random_uuid(), :sid, 'fish_stocking',
                       :desc, :sa, now()
                WHERE NOT EXISTS (
                    SELECT 1 FROM interventions
                    WHERE site_id = :sid AND type = 'fish_stocking'
                      AND description::jsonb ->> 'source' = 'ohio_dnr'
                      AND description::jsonb ->> 'stocking_date' = :date_iso
                      AND description::jsonb ->> 'waterbody' = :wb
                )
            """),
            {
                "sid": site_id,
                "sa": datetime.fromisoformat(f"{date_iso}T12:00:00").replace(tzinfo=timezone.utc),
                "date_iso": date_iso,
                "wb": WATERBODY,
                "desc": (
                    '{"source":"ohio_dnr","waterbody":"%s","county":"Champaign/Clark",'
                    '"species":"%s","stocking_date":"%s","quantity":"%d",'
                    '"program":"brown-trout C&R (annual fall yearling stocking)",'
                    '"needs_review":true}' % (WATERBODY, species, date_iso, qty)
                ),
            },
        )

    # Pin for the Fish Stocking map (C&R section near the Eagle City gauge).
    conn.execute(
        text("""
            INSERT INTO stocking_locations (watershed, waterbody, latitude, longitude, notes)
            VALUES ('mad_river_oh', :wb, 40.00, -83.85,
                    'Mad River C&R brown-trout section, Champaign/Clark Co. (near USGS 03267900). needs_review')
            ON CONFLICT (watershed, waterbody) DO NOTHING
        """),
        {"wb": WATERBODY},
    )


def downgrade() -> None:
    op.execute("""
        DELETE FROM interventions
         WHERE type = 'fish_stocking'
           AND description::jsonb ->> 'source' = 'ohio_dnr'
           AND description::jsonb ->> 'waterbody' = 'Mad River (C&R Section)'
    """)
    op.execute("DELETE FROM stocking_locations WHERE watershed = 'mad_river_oh'")
