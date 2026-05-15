"""seed shenandoah mineral_shops — v0 intentionally empty

Revision ID: ff06a7b8c9d0
Revises: ee05f6a7b8c9
Create Date: 2026-05-15 11:20:00.000000

NO ROWS INSERTED.

Per runbook §2.4 step 7 + ADR-008 + the runbook's "don't invent sites
from forum posts" rule, the agent declined to fabricate placeholder
mineral-shop listings for the Shenandoah Valley. Curator research is
needed to identify real retail rock/mineral shops in the region
(Charlottesville / Front Royal / Harrisonburg / Winchester / Luray).

Targets for the follow-on curator work:
  - AFMS-affiliated lapidary/mineral clubs in the region (club rolls)
  - Google Maps "rock shop" + "gem & mineral" near each Valley town
  - VA Tech Geology Museum gift shop + UVA mineral collection contacts

This migration exists as a sequence marker so the alembic chain stays
linear and the §3.6 verification grid clearly shows mineral_shops=0
with the gap-report cross-reference rather than missing the table check
entirely.
"""
from typing import Sequence, Union


revision: str = 'ff06a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'ee05f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
