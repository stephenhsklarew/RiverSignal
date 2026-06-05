"""Shareable Saved collections — create a 24h link, resolve it for a recipient.

POST /saved/share         → snapshot the chosen Saved items into a token (24h TTL),
                            return a shareable URL.
GET  /saved/shared/{token} → return the snapshot if the token is valid + unexpired
                            (public; the recipient app drops the items into their
                            own Saved client-side for 24h until they sign in to keep).
"""
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.routers.auth import get_current_user
from pipeline.db import engine

router = APIRouter(tags=["saved-share"])

SHARE_TTL_HOURS = 24
MAX_ITEMS = 500


class SharedItem(BaseModel):
    type: str
    id: str
    # free-form display fields the Saved UI needs to render the item
    data: dict = Field(default_factory=dict)


class ShareRequest(BaseModel):
    watershed: str | None = None
    sections: list[str] = Field(default_factory=list)
    items: list[SharedItem] = Field(default_factory=list)


@router.post("/saved/share")
def create_share(req: ShareRequest, request: Request):
    if not req.items:
        raise HTTPException(400, "No items to share")
    if len(req.items) > MAX_ITEMS:
        raise HTTPException(400, f"Too many items (max {MAX_ITEMS})")

    user = get_current_user(request)
    owner_id = user.get("id") if user else None
    token = secrets.token_urlsafe(9)  # ~12 chars, URL-safe
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=SHARE_TTL_HOURS)
    payload = {
        "watershed": req.watershed,
        "sections": req.sections,
        "items": [i.model_dump() for i in req.items],
    }

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO shared_collections
                    (share_token, owner_user_id, watershed, payload, item_count, expires_at)
                VALUES (:tok, :owner, :ws, CAST(:payload AS jsonb), :n, :exp)
            """),
            {"tok": token, "owner": owner_id, "ws": req.watershed,
             "payload": json.dumps(payload), "n": len(req.items), "exp": expires_at},
        )

    return {
        "token": token,
        "url": f"/path/shared/{token}",
        "expires_at": expires_at.isoformat(),
        "item_count": len(req.items),
    }


@router.get("/saved/shared/{token}")
def resolve_share(token: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT payload, watershed, item_count, expires_at, created_at
                FROM shared_collections
                WHERE share_token = :tok AND expires_at > now()
            """),
            {"tok": token},
        ).fetchone()
    if not row:
        # 404 covers both "never existed" and "expired" — don't leak which.
        raise HTTPException(404, "This shared link is invalid or has expired (links last 24 hours).")

    payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
    return {
        "watershed": row[1],
        "sections": payload.get("sections", []),
        "items": payload.get("items", []),
        "item_count": row[2],
        "expires_at": row[3].isoformat(),
        "created_at": row[4].isoformat(),
    }
