"""Server-side persistence of a user's Saved bookmarks (cross-device sync).

GET    /saved/items                    → the current user's saved items
POST   /saved/items                    → bulk upsert (write-through + login merge)
DELETE /saved/items/{item_type}/{id}   → remove one saved item

All endpoints require a logged-in user (401 otherwise). A saved item is a
bookmark/snapshot — for a kept *shared observation* the payload carries the
original photographer/source/observed/visibility, and we never write it to
user_observations, so the original attribution and privacy are preserved.
"""
import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.routers.auth import get_current_user
from pipeline.db import engine

router = APIRouter(tags=["saved-items"])

MAX_ITEMS = 1000


class SavedItemIn(BaseModel):
    type: str
    id: str
    watershed: str | None = None
    # free-form display fields the Saved UI needs (label, sublabel, thumbnail,
    # latitude, longitude, and for observations observer/source/observedAt/
    # visibility/originObservationId)
    payload: dict = Field(default_factory=dict)


class BulkSaveRequest(BaseModel):
    items: list[SavedItemIn] = Field(default_factory=list)


def _require_user(request: Request) -> str:
    user = get_current_user(request)
    if not user or not user.get("id"):
        raise HTTPException(401, "Must be logged in")
    return user["id"]


@router.get("/saved/items")
def list_saved_items(request: Request):
    user_id = _require_user(request)
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT item_type, item_id, watershed, payload, saved_at
                FROM saved_items WHERE user_id = :uid
                ORDER BY saved_at
            """),
            {"uid": user_id},
        ).fetchall()
    items = []
    for r in rows:
        payload = r[3] if isinstance(r[3], dict) else json.loads(r[3] or "{}")
        items.append({
            "type": r[0], "id": r[1], "watershed": r[2],
            "savedAt": r[4].isoformat() if r[4] else None,
            **payload,
        })
    return {"items": items}


@router.post("/saved/items")
def upsert_saved_items(req: BulkSaveRequest, request: Request):
    user_id = _require_user(request)
    if len(req.items) > MAX_ITEMS:
        raise HTTPException(400, f"Too many items (max {MAX_ITEMS})")
    if not req.items:
        return {"upserted": 0}
    with engine.begin() as conn:
        for it in req.items:
            conn.execute(
                text("""
                    INSERT INTO saved_items (user_id, item_type, item_id, watershed, payload)
                    VALUES (:uid, :type, :id, :ws, CAST(:payload AS jsonb))
                    ON CONFLICT (user_id, item_type, item_id)
                    DO UPDATE SET payload = EXCLUDED.payload, watershed = EXCLUDED.watershed
                """),
                {"uid": user_id, "type": it.type, "id": it.id, "ws": it.watershed,
                 "payload": json.dumps(it.payload or {})},
            )
    return {"upserted": len(req.items)}


@router.delete("/saved/items/{item_type}/{item_id:path}")
def delete_saved_item(item_type: str, item_id: str, request: Request):
    user_id = _require_user(request)
    with engine.begin() as conn:
        conn.execute(
            text("""
                DELETE FROM saved_items
                WHERE user_id = :uid AND item_type = :type AND item_id = :id
            """),
            {"uid": user_id, "type": item_type, "id": item_id},
        )
    return {"deleted": True}
