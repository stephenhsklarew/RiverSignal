"""merge alembic heads ip07 (ipswich hatch) + ph03 (sms users.phone_hash)

Revision ID: mh01a2b3c4d5
Revises: ip07b1c2d3e4, ph03b1c2d3e4
Create Date: 2026-06-02 00:00:00.000000

Pure merge revision. The shared migration chain forked into two heads when the
Ipswich onboarding (ip01..ip07, with ip03 deliberately re-pointed off ph03) and
the parallel SMS work (ph03 users.phone_hash) both landed on main without
serializing — so `alembic upgrade head` became ambiguous and the prod migrate
step failed. This unifies the two heads into one; no schema change.
"""
from typing import Sequence, Union

revision: str = 'mh01a2b3c4d5'
down_revision: Union[str, Sequence[str], None] = ('ip07b1c2d3e4', 'ph03b1c2d3e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
