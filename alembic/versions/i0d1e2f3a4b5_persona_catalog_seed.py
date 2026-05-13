"""seed the six personas into user_personas_catalog

Revision ID: i0d1e2f3a4b5
Revises: h9c0d1e2f3a4
Create Date: 2026-05-13 00:00:01.000000

Phase A2 of persona self-selection. Idempotent insert of the v1 persona
catalog (the six user-facing options from
docs/helix/02-design/plan-2026-05-13-persona-self-selection.md §3 seed block).

Re-running this migration is safe — ON CONFLICT (key) DO NOTHING. Future
catalog evolution happens through additional migrations: new personas
get their own INSERT migration; rename/deactivate goes through UPDATE
migrations. The stable `key` column is the contract.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'i0d1e2f3a4b5'
down_revision: Union[str, Sequence[str], None] = 'h9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERSONAS = [
    (
        'angler_self_guided',
        'I fish — for myself',
        'Personal trips, no clients. Watchlist your home rivers and get pinged when conditions are good.',
        '🎣',
        10,
    ),
    (
        'guide_professional',
        'I guide for clients',
        "Run paid trips. Get a client-ready morning briefing, multi-reach planning, and late-cancellation alerts.",
        '🪝',
        20,
    ),
    (
        'family_outdoor',
        'I visit rivers with family',
        'Make every river stop feel alive. Stories, kid-friendly mode, swim safety, species photos.',
        '👨‍👩‍👧',
        30,
    ),
    (
        'rockhound',
        'I look for rocks and fossils',
        'Find legal collecting sites and learn what others have found nearby.',
        '🪨',
        40,
    ),
    (
        'outdoor_general',
        'I hike, camp, or explore generally',
        'Access points, trailheads, scenic stops, and what to look for at each river.',
        '🌲',
        50,
    ),
    (
        'watershed_pro',
        'I teach, study, or steward watersheds',
        'Restoration data, citizen-science contribution, watershed-council links, professional analytics.',
        '🔬',
        60,
    ),
]


def upgrade() -> None:
    for key, display_label, description, icon, sort_order in PERSONAS:
        op.execute(
            f"""
            INSERT INTO user_personas_catalog (key, display_label, description, icon, sort_order, is_active)
            VALUES ({_quote(key)}, {_quote(display_label)}, {_quote(description)}, {_quote(icon)}, {sort_order}, true)
            ON CONFLICT (key) DO NOTHING
            """
        )


def downgrade() -> None:
    keys = ', '.join(_quote(p[0]) for p in PERSONAS)
    op.execute(f"DELETE FROM user_personas_catalog WHERE key IN ({keys})")


def _quote(value: str) -> str:
    """Safely quote a SQL string literal (doubles single quotes)."""
    return "'" + value.replace("'", "''") + "'"
