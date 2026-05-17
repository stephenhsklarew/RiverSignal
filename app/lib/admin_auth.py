"""Admin auth dependency.

Wraps the existing `get_current_user` from auth.py with an `is_admin`
check. Returns 403 when the user is signed in but not admin, 401 when
anonymous. All `/api/v1/admin/*` routes use this dependency.
"""
from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy import text

from app.routers.auth import get_current_user
from pipeline.db import engine


def get_current_admin(request: Request) -> dict:
    """Resolve current user, assert is_admin. Returns the user dict."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    # The JWT doesn't store is_admin (it's a server-side check on every
    # request so revocation is immediate). Look up live.
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT is_admin FROM users WHERE id = :uid"),
            {"uid": user["id"]},
        ).fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
