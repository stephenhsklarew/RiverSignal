"""Verify the persona-self-selection migration (h9c0d1e2f3a4) applied cleanly.

Skipped when no DATABASE_URL is configured. When running against a DB that has
`alembic upgrade head` applied, asserts the new schema is in place.
"""

import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set; skipping live schema check",
)


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = :t AND column_name = :c
                """
            ),
            {"t": table, "c": column},
        ).scalar()
    )


def _table_exists(conn, table: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_name = :t
                """
            ),
            {"t": table},
        ).scalar()
    )


def _index_exists(conn, index_name: str) -> bool:
    return bool(
        conn.execute(
            text("SELECT 1 FROM pg_indexes WHERE indexname = :i"),
            {"i": index_name},
        ).scalar()
    )


@pytest.fixture(scope="module")
def conn():
    from pipeline.db import engine

    with engine.connect() as c:
        yield c


def test_user_personas_catalog_exists(conn):
    assert _table_exists(conn, "user_personas_catalog"), (
        "user_personas_catalog table missing — did alembic upgrade head run?"
    )
    for col in (
        "key",
        "display_label",
        "description",
        "icon",
        "sort_order",
        "is_active",
        "created_at",
        "updated_at",
    ):
        assert _column_exists(conn, "user_personas_catalog", col), (
            f"user_personas_catalog.{col} missing"
        )


def test_users_persona_columns_exist(conn):
    for col in ("personas", "personas_set_at", "personas_version"):
        assert _column_exists(conn, "users", col), (
            f"users.{col} missing — did alembic upgrade head run?"
        )


def test_users_personas_default_empty_array(conn):
    row = conn.execute(
        text(
            """
            SELECT column_default
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'personas'
            """
        )
    ).scalar()
    assert row is not None and "'{}'" in row, (
        f"users.personas default should be empty array, got: {row!r}"
    )


def test_personas_gin_index_exists(conn):
    assert _index_exists(conn, "idx_users_personas"), (
        "GIN index idx_users_personas missing — array gating queries will be slow"
    )


EXPECTED_SEED = {
    "angler_self_guided": 10,
    "guide_professional": 20,
    "family_outdoor": 30,
    "rockhound": 40,
    "outdoor_general": 50,
    "watershed_pro": 60,
}


def test_persona_catalog_seeded_with_six_rows(conn):
    """After migration i0d1e2f3a4b5, the catalog has the v1 six personas."""
    rows = conn.execute(
        text("SELECT key, sort_order FROM user_personas_catalog ORDER BY sort_order")
    ).fetchall()
    actual = {key: order for key, order in rows}
    for expected_key, expected_order in EXPECTED_SEED.items():
        assert expected_key in actual, f"persona '{expected_key}' missing from catalog"
        assert actual[expected_key] == expected_order, (
            f"persona '{expected_key}' has sort_order {actual[expected_key]}, "
            f"expected {expected_order}"
        )


def test_persona_seed_idempotent_metadata(conn):
    """Every seeded persona has a non-empty display_label and is_active=true."""
    rows = conn.execute(
        text(
            """
            SELECT key, display_label, is_active
            FROM user_personas_catalog
            WHERE key = ANY(:keys)
            """
        ),
        {"keys": list(EXPECTED_SEED.keys())},
    ).fetchall()
    for key, label, active in rows:
        assert label and label.strip(), f"persona '{key}' has empty display_label"
        assert active is True, f"persona '{key}' should be is_active=true after seed"
