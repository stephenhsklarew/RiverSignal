"""One-off backfill: populate users.phone_hash for users verified before the
phone_hash column existed (migration ph03b1c2d3e4).

phone_hash is a deterministic, key-bound hash the inbound STOP webhook uses to
find the sender. Users who verified earlier have an encrypted phone but a NULL
hash, so their STOP wouldn't match until they re-verify. This decrypts each
such phone (app-side — the AES key only lives in the app, not the DB) and
writes the hash.

Idempotent: only touches rows where phone_hash IS NULL, and the UPDATE re-checks
that predicate, so concurrent runs / re-runs are safe no-ops.

Requires SMS_ENCRYPTION_KEY in the environment (same secret the dispatcher uses).

Run:
    python -m pipeline.sms.backfill_phone_hash            # apply
    python -m pipeline.sms.backfill_phone_hash --dry-run  # report only
"""
from __future__ import annotations

import argparse
import logging
from typing import Any

from sqlalchemy import text

from app.lib.phone_crypto import decrypt_phone, hash_phone_for_lookup
from pipeline.db import engine


log = logging.getLogger(__name__)


def run(dry_run: bool = False) -> dict[str, Any]:
    """Backfill phone_hash for verified users missing it. Returns a summary."""
    # Read the candidate set first and close the read txn before writing, so we
    # don't nest transactions on one connection.
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, phone_number_e164_encrypted
                FROM users
                WHERE phone_number_e164_encrypted IS NOT NULL
                  AND phone_hash IS NULL
            """)
        ).fetchall()

    log.info("Found %d user(s) needing phone_hash backfill", len(rows))

    to_update: list[tuple[Any, bytes]] = []
    failed = 0
    for uid, enc in rows:
        try:
            phone = decrypt_phone(bytes(enc))
        except Exception as exc:  # undecryptable (e.g. key rotation) — skip, don't abort
            log.error("Failed to decrypt phone for user %s: %s", uid, exc)
            failed += 1
            continue
        to_update.append((uid, hash_phone_for_lookup(phone)))

    updated = 0
    if to_update and not dry_run:
        with engine.begin() as conn:
            for uid, phash in to_update:
                conn.execute(
                    text(
                        "UPDATE users SET phone_hash = :h "
                        "WHERE id = :id AND phone_hash IS NULL"
                    ),
                    {"h": phash, "id": uid},
                )
                updated += 1

    result = {
        "status": "dry_run" if dry_run else "ok",
        "candidates": len(rows),
        "updated": 0 if dry_run else updated,
        "would_update": len(to_update) if dry_run else 0,
        "failed": failed,
    }
    log.info("Backfill complete: %s", result)
    return result


if __name__ == "__main__":
    import json

    parser = argparse.ArgumentParser(description="Backfill users.phone_hash")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report how many rows would be updated without writing.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(run(dry_run=args.dry_run), indent=2))
