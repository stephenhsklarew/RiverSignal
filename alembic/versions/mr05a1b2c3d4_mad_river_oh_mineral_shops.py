"""seed mad_river_oh mineral_shops — v0 intentionally empty

Revision ID: mr05a1b2c3d4
Revises: mr04a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

NO ROWS INSERTED.

Per runbook §2.4 step 7 + ADR-008 + the "don't invent sites" rule, the
agent declined to fabricate placeholder rock/mineral-shop listings for the
Columbus / Dayton / Springfield area. Curator research is needed to identify
real retail shops.

Targets for the follow-on curator work:
  - AFMS-affiliated lapidary/mineral clubs near Columbus / Dayton (club rolls)
  - Google Maps "rock shop" / "gem & mineral" near Springfield + Dayton
  - Ohio Geological Survey / Orton Geological Museum (OSU) gift-shop contacts

This migration exists as a sequence marker so the alembic chain stays linear
and the §3.6 verification grid shows mineral_shops=0 with its gap-report
cross-reference rather than missing the table check entirely.
"""
from typing import Sequence, Union


revision: str = 'mr05a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr04a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
