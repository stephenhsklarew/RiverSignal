"""seed ODNR special-regulation notes for the Mad River C&R trout section

Revision ID: mr12a1b2c3d4
Revises: mr11a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

P2 follow-on bead. ODNR designates a special-regulation brown-trout section
on the Mad River (Champaign/Clark Co.). There is no structured ODNR regs
feed (HTML/PDF, annual cadence), so the regulation summary is curated into
`silver.river_reaches.notes` for the trout-section reach — the same
mechanism the VA DWR regs path uses so the TQS access sub-score can reflect
gear/harvest restrictions on the reach. Flagged needs_review (confirm exact
boundaries + current-year regs with ODNR before treating as authoritative).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mr12a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr11a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_REG_NOTE = (
    " | REGULATION (needs_review 2026-05-30): ODNR special-regulation "
    "brown-trout section — artificial-lures / restricted-harvest stretch "
    "(confirm exact C&R boundaries, gear + daily-limit with current ODNR "
    "fishing regulations before relying on this for access scoring)."
)


def upgrade() -> None:
    # Append (idempotently) to the trout-section reach notes.
    op.execute(f"""
        UPDATE silver.river_reaches
           SET notes = COALESCE(notes, '') || '{_REG_NOTE}'
         WHERE id = 'mad_river_oh_trout_section'
           AND (notes IS NULL OR notes NOT LIKE '%REGULATION (needs_review%')
    """)


def downgrade() -> None:
    op.execute(f"""
        UPDATE silver.river_reaches
           SET notes = replace(notes, '{_REG_NOTE}', '')
         WHERE id = 'mad_river_oh_trout_section'
    """)
