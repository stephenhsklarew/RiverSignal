"""Trip feedback endpoint (plan §6 feedback section).

POST /api/v1/trip-feedback — anonymous-callable. Records a 1-5 rating
for a reach + trip_date. Authed users have user_id populated from the
JWT cookie; anonymous submissions store user_id = NULL.
"""
from datetime import date as date_t
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.routers.auth import get_current_user
from pipeline.db import engine

router = APIRouter(tags=["trip-feedback"])


class TripFeedbackBody(BaseModel):
    reach_id: str = Field(..., min_length=1, max_length=80)
    trip_date: date_t
    rating: int = Field(..., ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=500)
    tqs_at_view: Optional[int] = Field(None, ge=0, le=100)


@router.post("/trip-feedback", status_code=status.HTTP_201_CREATED)
def post_trip_feedback(body: TripFeedbackBody, request: Request):
    if body.trip_date > date_t.today():
        raise HTTPException(400, "trip_date cannot be in the future")

    user = get_current_user(request)
    user_id = user["id"] if user else None

    with engine.connect() as conn:
        # Validate reach exists
        exists = conn.execute(
            text("SELECT 1 FROM silver.river_reaches WHERE id = :rid AND is_active = true"),
            {"rid": body.reach_id},
        ).fetchone()
        if not exists:
            raise HTTPException(404, f"Unknown reach: {body.reach_id}")

        conn.execute(
            text("""
                INSERT INTO user_trip_feedback
                    (user_id, reach_id, trip_date, rating, notes, tqs_at_view)
                VALUES (:uid, :rid, :td, :rating, :notes, :tqs)
            """),
            {
                "uid": user_id, "rid": body.reach_id, "td": body.trip_date,
                "rating": body.rating, "notes": body.notes,
                "tqs": body.tqs_at_view,
            },
        )
        conn.commit()
    return {"ok": True}
