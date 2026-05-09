"""User observation endpoints: photo upload, species typeahead, list observations."""

import base64
import hashlib
import json
import pathlib
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import text

from pipeline.db import engine

router = APIRouter(tags=["user-observations"])

PHOTO_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / ".user_photos"
PHOTO_DIR.mkdir(exist_ok=True)
THUMB_DIR = PHOTO_DIR / "thumbs"
THUMB_DIR.mkdir(exist_ok=True)

# ── Security constants ──
MAX_PHOTO_BYTES = 10 * 1024 * 1024  # 10 MB max photo size
MAX_TEXT_LENGTH = 500  # Max length for text fields
ALLOWED_CATEGORIES = {"fish", "bird", "insect", "plant", "mammal", "amphibian", "reptile",
                      "fossil", "rock", "mineral", "crystal", "landscape", "other"}
ALLOWED_APPS = {"riverpath", "deeptrail"}
# JPEG: FF D8 FF, PNG: 89 50 4E 47
IMAGE_SIGNATURES = {b'\xff\xd8\xff': '.jpg', b'\x89PNG': '.png'}

# Rate limiting: IP -> list of timestamps
_rate_limit: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX = 10  # max submissions per window
RATE_LIMIT_WINDOW = 300  # 5 minute window


def _sanitize_text(val: str | None, max_len: int = MAX_TEXT_LENGTH) -> str | None:
    """Strip HTML tags and limit length."""
    if not val:
        return val
    clean = re.sub(r'<[^>]+>', '', val)  # strip HTML tags
    clean = clean.replace('\x00', '')     # strip null bytes
    return clean[:max_len].strip()


def _check_rate_limit(ip: str) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = time.time()
    _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit[ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit[ip].append(now)
    return True


def _validate_image(photo_bytes: bytes) -> str:
    """Validate image bytes. Returns extension or raises HTTPException."""
    for sig, ext in IMAGE_SIGNATURES.items():
        if photo_bytes[:len(sig)] == sig:
            return ext
    raise HTTPException(400, "Invalid image format. Only JPEG and PNG are accepted.")


def _get_gcs_token() -> str:
    """Get an access token for GCS uploads (works on Cloud Run via metadata server)."""
    import httpx
    try:
        resp = httpx.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"}, timeout=5,
        )
        return resp.json().get("access_token", "")
    except Exception:
        return ""


class ObservationCreate(BaseModel):
    source_app: str = "riverpath"
    photo_base64: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    observed_at: str | None = None
    species_name: str | None = None
    common_name: str | None = None
    category: str | None = None
    notes: str | None = None
    watershed: str | None = None

    @field_validator('source_app')
    @classmethod
    def validate_app(cls, v: str) -> str:
        if v not in ALLOWED_APPS:
            raise ValueError(f'source_app must be one of {ALLOWED_APPS}')
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        if v and v.lower() not in ALLOWED_CATEGORIES:
            raise ValueError(f'category must be one of {ALLOWED_CATEGORIES}')
        return v.lower() if v else v

    @field_validator('latitude')
    @classmethod
    def validate_lat(cls, v: float | None) -> float | None:
        if v is not None and (v < -90 or v > 90):
            raise ValueError('latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_lon(cls, v: float | None) -> float | None:
        if v is not None and (v < -180 or v > 180):
            raise ValueError('longitude must be between -180 and 180')
        return v


@router.post("/observations/user")
def create_user_observation(body: ObservationCreate, request: Request):
    """Save a user-submitted observation with optional photo."""
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(429, "Too many submissions. Please wait a few minutes.")

    from app.routers.auth import get_current_user
    current_user = get_current_user(request)
    obs_id = str(uuid.uuid4())
    photo_path = None
    thumb_path = None

    # Sanitize text inputs
    body.species_name = _sanitize_text(body.species_name)
    body.common_name = _sanitize_text(body.common_name)
    body.notes = _sanitize_text(body.notes, 1000)
    body.watershed = _sanitize_text(body.watershed, 50)

    # Save photo
    if body.photo_base64:
        try:
            # Strip data URI prefix if present
            b64 = body.photo_base64
            if "," in b64:
                b64 = b64.split(",", 1)[1]

            # Check base64 size before decoding (base64 is ~33% larger than binary)
            if len(b64) > MAX_PHOTO_BYTES * 1.4:
                raise HTTPException(413, f"Photo too large. Maximum size is {MAX_PHOTO_BYTES // (1024*1024)} MB.")

            photo_bytes = base64.b64decode(b64)

            if len(photo_bytes) > MAX_PHOTO_BYTES:
                raise HTTPException(413, f"Photo too large. Maximum size is {MAX_PHOTO_BYTES // (1024*1024)} MB.")

            # Validate image magic bytes
            ext = _validate_image(photo_bytes)
            photo_filename = f"{obs_id}{ext}"

            # Save to GCS in production, local filesystem in dev
            import os
            gcs_bucket = os.environ.get("GCS_BUCKET_ASSETS")
            storage_backend = os.environ.get("STORAGE_BACKEND", "local")

            if storage_backend == "gcs" and gcs_bucket:
                import httpx
                gcs_url = f"https://storage.googleapis.com/upload/storage/v1/b/{gcs_bucket}/o?uploadType=media&name=user_photos/{photo_filename}"
                content_type = "image/png" if ext == ".png" else "image/jpeg"
                resp = httpx.post(gcs_url, content=photo_bytes, headers={
                    "Content-Type": content_type,
                    "Authorization": f"Bearer {_get_gcs_token()}",
                }, timeout=30)
                if resp.status_code in (200, 201):
                    photo_path = f"https://storage.googleapis.com/{gcs_bucket}/user_photos/{photo_filename}"
                else:
                    # Fallback to local
                    photo_file = PHOTO_DIR / photo_filename
                    photo_file.write_bytes(photo_bytes)
                    photo_path = f"/api/v1/observations/user/photo/{photo_filename}"
            else:
                photo_file = PHOTO_DIR / photo_filename
                photo_file.write_bytes(photo_bytes)
                photo_path = f"/api/v1/observations/user/photo/{photo_filename}"

            thumb_path = photo_path
        except HTTPException:
            raise
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
          try:
            # Determine source_type: use username if logged in
            username = (current_user.get("username", "") or "") if isinstance(current_user, dict) else ""
            source_type = username if username else "user"
            user_id = current_user["id"] if isinstance(current_user, dict) and "id" in current_user else None

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
                    "payload": json.dumps({
                        "common_name": body.common_name or "",
                        "photo_url": photo_path or "",
                        "source": source_type,
                        "notes": body.notes or "",
                        "app": body.source_app,
                    }),
                })
          except Exception as e:
            print(f"WARNING: Failed to insert into bronze observations: {e}")

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


@router.get("/observations/user/geojson")
def user_observations_geojson(
    watershed: str | None = Query(None),
    limit: int = Query(500, le=5000),
):
    """Return all user-submitted observations as GeoJSON for map display."""
    conditions = ["latitude IS NOT NULL AND longitude IS NOT NULL"]
    params: dict = {"limit": limit}

    if watershed:
        conditions.append("watershed = :ws")
        params["ws"] = watershed

    where = " AND ".join(conditions)
    with engine.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT species_name, common_name, latitude, longitude,
                   observed_at, photo_path, category, notes, watershed
            FROM user_observations
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT :limit
        """), params).fetchall()

    features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r[3], r[2]]},
        "properties": {
            "taxon_name": r[0] or "",
            "common_name": r[1] or "",
            "observed_at": str(r[4].date()) if r[4] else "",
            "photo_url": r[5] or "",
            "quality_grade": "user_submitted",
            "source": "user",
            "category": r[6] or "",
            "notes": r[7] or "",
            "watershed": r[8] or "",
        },
    } for r in rows]

    return {"type": "FeatureCollection", "features": features, "count": len(features)}


@router.get("/observations/user/photo/{filename}")
def serve_user_photo(filename: str):
    """Serve a user-uploaded photo. Checks GCS first, then local filesystem."""
    import os
    from fastapi.responses import FileResponse, RedirectResponse

    safe_name = pathlib.Path(filename).name
    gcs_bucket = os.environ.get("GCS_BUCKET_ASSETS")
    storage_backend = os.environ.get("STORAGE_BACKEND", "local")

    # In GCS mode, redirect to the public GCS URL
    if storage_backend == "gcs" and gcs_bucket:
        return RedirectResponse(
            url=f"https://storage.googleapis.com/{gcs_bucket}/user_photos/{safe_name}",
            status_code=302,
        )

    # Local filesystem fallback
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
