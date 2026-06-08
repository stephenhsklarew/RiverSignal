"""Re-key gold.curated_species_photos species_key to canonical (FEAT-026 P2)

Revision ID: sk20a1b2c3d4
Revises: ne15a1b2c3d4
Create Date: 2026-06-08 00:00:00.000000

Phase 1 made Fish Present + the admin list group by a canonical species key
(app/lib/species_canonical.py): "Fall Chinook"/"Spring Chinook"/"Chinook" → one
"Chinook Salmon"; Summer/Winter Steelhead → "Steelhead" (kept separate from
Rainbow Trout). But existing curated photos were keyed by the RAW name
("summer steelhead", "redband trout", …), so after Phase 1 the admin "curated"
badge no longer matched the deduped row and a single canonical photo didn't
formally own all variants.

This migration re-keys each curated row's species_key to its canonical key.
Collisions (several raw rows in one watershed mapping to the same canonical key)
are resolved by keeping ONE row — the one already at the canonical key if
present, else the most-recently-updated — and deleting the rest (one photo per
canonical species is the intended end state; the audit log retains history).

A FROZEN copy of the canonicalization maps is inlined so this migration's result
never changes if app/lib/species_canonical.py evolves later.

Downgrade is a no-op: merged/deleted rows cannot be reconstructed.
"""
from collections import defaultdict
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'sk20a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'ne15a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Frozen copy of the canonicalization (mirror of app/lib/species_canonical) ──
_RUN_PREFIXES = ("spring", "fall", "summer", "winter", "autumn")
_DESCRIPTOR_PREFIXES = ("coastal", "interior", "westslope", "inland")
_CANONICAL = {
    "chinook": "Chinook Salmon", "chinook salmon": "Chinook Salmon", "king salmon": "Chinook Salmon",
    "coho": "Coho Salmon", "coho salmon": "Coho Salmon", "silver salmon": "Coho Salmon",
    "sockeye": "Sockeye Salmon", "sockeye salmon": "Sockeye Salmon",
    "chum": "Chum Salmon", "chum salmon": "Chum Salmon", "pink salmon": "Pink Salmon",
    "kokanee": "Kokanee", "kokanee salmon": "Kokanee",
    "steelhead": "Steelhead",
    "rainbow": "Rainbow Trout", "rainbow trout": "Rainbow Trout",
    "redband": "Rainbow Trout", "redband trout": "Rainbow Trout",
    "cutthroat": "Cutthroat Trout", "cutthroat trout": "Cutthroat Trout",
    "musky": "Muskellunge", "muskellunge": "Muskellunge",
    "walleye": "Walleye", "walleyed pike": "Walleye",
}


def _canonical_key(raw: str | None) -> str:
    base = " ".join((raw or "").split()).lower()
    for p in _RUN_PREFIXES:
        if base.startswith(p + " "):
            base = base[len(p) + 1:]
            break
    for p in _DESCRIPTOR_PREFIXES:
        if base.startswith(p + " "):
            base = base[len(p) + 1:]
            break
    base = base.replace("small mouth", "smallmouth").replace("large mouth", "largemouth")
    label = _CANONICAL.get(base, base.title() if base else "")
    return label.lower()


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT species_key, watershed, updated_at FROM gold.curated_species_photos"
    )).fetchall()

    _MIN = datetime.min.replace(tzinfo=timezone.utc)
    groups: dict[tuple, list] = defaultdict(list)
    for species_key, watershed, updated_at in rows:
        groups[(watershed, _canonical_key(species_key))].append((species_key, updated_at))

    for (watershed, ck), members in groups.items():
        if not ck:
            continue
        keeper = next((m for m in members if m[0] == ck), None)
        if keeper is None:
            keeper = max(members, key=lambda m: m[1] or _MIN)
        keeper_key = keeper[0]
        # Delete losers FIRST so re-keying the keeper can't hit the (species_key,
        # watershed) PK of a soon-to-be-removed row.
        for lk, _ in members:
            if lk != keeper_key:
                bind.execute(sa.text(
                    "DELETE FROM gold.curated_species_photos WHERE watershed = :w AND species_key = :k"
                ), {"w": watershed, "k": lk})
        if keeper_key != ck:
            bind.execute(sa.text(
                "UPDATE gold.curated_species_photos SET species_key = :ck WHERE watershed = :w AND species_key = :k"
            ), {"ck": ck, "w": watershed, "k": keeper_key})


def downgrade() -> None:
    # No-op: merged/deleted curated rows cannot be reconstructed.
    pass
