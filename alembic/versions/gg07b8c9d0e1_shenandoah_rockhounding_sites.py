"""seed shenandoah rockhounding_sites — v0 intentionally empty

Revision ID: gg07b8c9d0e1
Revises: ff06a7b8c9d0
Create Date: 2026-05-15 11:25:00.000000

NO ROWS INSERTED.

Rockhounding sites carry liability risk on bad entries (illegal trespass,
collecting violations on federal land). Per runbook §2.4 step 8, the
agent must verify per-row:
  - Land ownership (BLM SMA / USFS / state DNR / verified private)
  - Collecting rules from the specific managing district
  - Provenance citation (published rockhound guide or state mineral
    society field-trip log)

Most Shenandoah-area land of rockhound interest falls under one of:
  - Shenandoah National Park (NPS — collecting prohibited)
  - George Washington & Jefferson National Forest (USFS — casual
    collecting allowed in some districts but not in wilderness)
  - Private land (collecting requires landowner permission)

Known rockhound interest but unverified for v0:
  - Tye River area quartz crystals (private — needs landowner permission)
  - Roses Mill unakite (Amherst Co — partially private)
  - Crabtree Falls area (Blue Ridge — within George Washington NF;
    casual collecting allowed in some sections)
  - WV side garnet schist localities along Cacapon

None inserted until a curator with the published-guide references
(Falcon's *Rockhounding Virginia*) verifies each entry's current
land-owner and collecting rules. Follow-on bead: P3 — curate
Shenandoah rockhounding_sites with verified provenance.

This migration is a sequence marker only.
"""
from typing import Sequence, Union


revision: str = 'gg07b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'ff06a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
