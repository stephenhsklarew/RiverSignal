"""User observation endpoints: photo upload, species typeahead, list observations."""

import base64
import hashlib
import pathlib
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["user-observations"])

PHOTO_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / ".user_photos"
PHOTO_DIR.mkdir(exist_ok=True)
THUMB_DIR = PHOTO_DIR / "thumbs"
THUMB_DIR.mkdir(exist_ok=True)


class ObservationCreate(BaseModel):
    source_app: str = "riverpath"  # riverpath or deeptrail
    photo_base64: str | None = None  # base64 encoded JPEG/PNG
    latitude: float | None = None
    longitude: float | None = None
    observed_at: str | None = None  # ISO datetime string
    species_name: str | None = None
    common_name: str | None = None
    category: str | None = None  # fish, bird, insect, plant, mammal, fossil, rock, mineral, etc.
    notes: str | None = None
    watershed: str | None = None


@router.post("/observations/user")
def create_user_observation(body: ObservationCreate, request: Request):
    """Save a user-submitted observation with optional photo."""
    from app.routers.auth import get_current_user
    current_user = get_current_user(request)
    obs_id = str(uuid.uuid4())
    photo_path = None
    thumb_path = None

    # Save photo to disk
    if body.photo_base64:
        try:
            # Strip data URI prefix if present
            b64 = body.photo_base64
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            photo_bytes = base64.b64decode(b64)

            # Determine extension from first bytes
            ext = ".jpg"
            if photo_bytes[:4] == b'\x89PNG':
                ext = ".png"

            photo_filename = f"{obs_id}{ext}"
            photo_file = PHOTO_DIR / photo_filename
            photo_file.write_bytes(photo_bytes)
            photo_path = f"/api/v1/observations/user/photo/{photo_filename}"

            # Create thumbnail (just store full image path — resize client-side)
            thumb_path = photo_path
        except Exception:
            pass  # Photo save failed silently — observation still created

    # Parse observed_at
    observed_at = None
    if body.observed_at:
        try:
            observed_at = datetime.fromisoformat(body.observed_at.replace("Z", "+00:00"))
        except Exception:
            observed_at = datetime.utcnow()
    else:
        observed_at = datetime.utcnow()

    # Map category to iconic_taxon for the bronze layer
    CATEGORY_TO_ICONIC: dict[str, str] = {
        "fish": "Actinopterygii", "bird": "Aves", "insect": "Insecta",
        "plant": "Plantae", "mammal": "Mammalia", "reptile": "Reptilia",
        "amphibian": "Amphibia", "fossil": "Fossil", "rock": "Geology",
        "mineral": "Geology", "crystal": "Geology",
    }

    with engine.connect() as conn:
        # 1. Save to user_observations table (full detail)
        conn.execute(text("""
            INSERT INTO user_observations
                (id, source_app, photo_path, photo_thumbnail, latitude, longitude, location,
                 observed_at, species_name, common_name, category, notes, watershed)
            VALUES
                (:id, :app, :photo, :thumb, :lat, :lon,
                 CASE WHEN :lat IS NOT NULL AND :lon IS NOT NULL
                      THEN ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) ELSE NULL END,
                 :obs_at, :species, :common, :cat, :notes, :ws)
        """), {
            "id": obs_id, "app": body.source_app,
            "photo": photo_path, "thumb": thumb_path,
            "lat": body.latitude, "lon": body.longitude,
            "obs_at": observed_at,
            "species": body.species_name, "common": body.common_name,
            "cat": body.category, "notes": body.notes,
            "ws": body.watershed,
        })

        # 2. Also insert into bronze observations table
        #    source_type = username if logged in, else 'user'
        if body.species_name and body.latitude and body.longitude:
            # Determine source_type: use username if logged in
            username = current_user.get("username", "") if current_user else ""
            source_type = username if username else "user"
            user_id = current_user["id"] if current_user else None

            # Link user_observation to user account
            if user_id:
                conn.execute(text(
                    "UPDATE user_observations SET user_id = :uid WHERE id = :oid"
                ), {"uid": user_id, "oid": obs_id})

            # Find the site_id for this watershed
            site_id = None
            if body.watershed:
                site_row = conn.execute(text(
                    "SELECT id FROM sites WHERE watershed = :ws"
                ), {"ws": body.watershed}).fetchone()
                if site_row:
                    site_id = site_row[0]

            if not site_id:
                # Find nearest site
                site_row = conn.execute(text("""
                    SELECT id FROM sites
                    ORDER BY ST_Distance(
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(
                            ((bbox->>'west')::float + (bbox->>'east')::float) / 2,
                            ((bbox->>'south')::float + (bbox->>'north')::float) / 2
                        ), 4326)::geography
                    )
                    LIMIT 1
                """), {"lat": body.latitude, "lon": body.longitude}).fetchone()
                if site_row:
                    site_id = site_row[0]

            if site_id:
                iconic = CATEGORY_TO_ICONIC.get((body.category or "").lower(), "Unknown")
                conn.execute(text("""
                    INSERT INTO observations
                        (id, site_id, source_type, source_id, observed_at,
                         taxon_name, iconic_taxon, location, latitude, longitude,
                         quality_grade, data_payload)
                    VALUES
                        (gen_random_uuid(), :site_id, :source_type, :source_id, :obs_at,
                         :taxon, :iconic,
                         ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :lat, :lon,
                         'user_submitted',
                         :payload)
                    ON CONFLICT (source_type, source_id) DO NOTHING
                """), {
                    "site_id": site_id,
                    "source_type": source_type,
                    "source_id": f"{source_type}:{obs_id}",
                    "obs_at": observed_at,
                    "taxon": body.species_name,
                    "iconic": iconic,
                    "lat": body.latitude, "lon": body.longitude,
                    "payload": f'{{"common_name": "{body.common_name or ""}", "photo_url": "{photo_path or ""}", "source": "{source_type}", "notes": "{body.notes or ""}", "app": "{body.source_app}"}}',
                })

        conn.commit()

    return {
        "id": obs_id,
        "photo_url": photo_path,
        "message": "Observation saved",
    }


@router.get("/observations/user")
def list_user_observations(
    source_app: str = Query("riverpath"),
    watershed: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    """List user-submitted observations."""
    conditions = ["source_app = :app"]
    params: dict = {"app": source_app, "limit": limit}

    if watershed:
        conditions.append("watershed = :ws")
        params["ws"] = watershed

    where = " AND ".join(conditions)
    with engine.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT id, photo_path, photo_thumbnail, latitude, longitude,
                   observed_at, species_name, common_name, category, notes, watershed
            FROM user_observations
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit
        """), params).fetchall()

    return [{
        "id": str(r[0]),
        "photo_url": r[1],
        "thumbnail_url": r[2],
        "latitude": r[3],
        "longitude": r[4],
        "observed_at": r[5].isoformat() if r[5] else None,
        "species_name": r[6],
        "common_name": r[7],
        "category": r[8],
        "notes": r[9],
        "watershed": r[10],
    } for r in rows]


@router.get("/observations/user/photo/{filename}")
def serve_user_photo(filename: str):
    """Serve a user-uploaded photo."""
    from fastapi.responses import FileResponse

    # Sanitize filename
    safe_name = pathlib.Path(filename).name
    photo_file = PHOTO_DIR / safe_name
    if not photo_file.exists():
        raise HTTPException(404, "Photo not found")
    content_type = "image/png" if safe_name.endswith(".png") else "image/jpeg"
    return FileResponse(photo_file, media_type=content_type)


@router.get("/observations/typeahead")
def species_typeahead(
    q: str = Query(..., min_length=2),
    app: str = Query("riverpath"),
    limit: int = Query(10, le=30),
):
    """Typeahead search for species/rock names.

    For riverpath: searches species_gallery common_name and taxon_name.
    For deeptrail: searches fossil taxon names and rockhounding rock types.
    """
    pattern = f"%{q}%"

    with engine.connect() as conn:
        if app == "deeptrail":
            rows = conn.execute(text("""
                (SELECT DISTINCT common_name as name, 'fossil' as type
                 FROM fossil_occurrences
                 WHERE common_name ILIKE :q AND common_name IS NOT NULL AND common_name != ''
                 LIMIT :half)
                UNION ALL
                (SELECT DISTINCT rock_type as name, 'rock' as type
                 FROM rockhounding_sites
                 WHERE rock_type ILIKE :q
                 LIMIT :half)
                UNION ALL
                (SELECT DISTINCT commodity as name, 'mineral' as type
                 FROM mineral_deposits
                 WHERE commodity ILIKE :q AND site_name NOT ILIKE 'Unnamed%%'
                 LIMIT :half)
                LIMIT :limit
            """), {"q": pattern, "half": limit // 2, "limit": limit}).fetchall()
        else:
            rows = conn.execute(text("""
                SELECT DISTINCT
                    COALESCE(common_name, taxon_name) as name,
                    COALESCE(taxonomic_group, 'Unknown') as type
                FROM gold.species_gallery
                WHERE (common_name ILIKE :q OR taxon_name ILIKE :q)
                ORDER BY name
                LIMIT :limit
            """), {"q": pattern, "limit": limit}).fetchall()

    return [{"name": r[0], "type": r[1]} for r in rows if r[0]]
