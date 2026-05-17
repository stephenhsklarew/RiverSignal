"""Admin console API routes.

All routes here are gated by `get_current_admin` and operate on
`gold.curated_species_photos` + `audit.curated_species_photos_log`.

Endpoints
---------
GET    /admin/curated-photos                 list every curated row
GET    /admin/curated-photos/{species_key}   one row + last 5 audit entries
PUT    /admin/curated-photos/{species_key}   upsert (creates if missing); writes audit row
DELETE /admin/curated-photos/{species_key}   delete row; writes audit row
GET    /admin/curated-photos/{species_key}/history  full audit timeline
GET    /admin/inat/photos?scientific_name=...       iNat search proxy (1h LRU cache)
POST   /admin/self/revoke                    self-service admin revocation (OF-6)
"""
from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.lib.admin_auth import get_current_admin
from pipeline.db import engine


router = APIRouter(tags=["admin"])


# ── Curated photos: list ───────────────────────────────────────────

@router.get("/admin/curated-photos")
def list_curated_photos(admin: dict = Depends(get_current_admin)):
    """Return every curated species photo with provenance."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT species_key, common_name, scientific_name, photo_url,
                   inat_user_handle, license, source,
                   updated_by_user_id, updated_at
            FROM gold.curated_species_photos
            ORDER BY species_key
        """)).fetchall()
    return [
        {
            "species_key":      r[0],
            "common_name":      r[1],
            "scientific_name":  r[2],
            "photo_url":        r[3],
            "inat_user_handle": r[4],
            "license":          r[5],
            "source":           r[6],
            "updated_by_user_id": str(r[7]) if r[7] else None,
            "updated_at":       r[8].isoformat() if r[8] else None,
        }
        for r in rows
    ]


# ── Curated photos: editor (single species + recent history) ───────

class CuratedPhotoPayload(BaseModel):
    """Upsert payload for the per-species editor."""
    common_name:        str = Field(..., max_length=120)
    scientific_name:    str | None = Field(None, max_length=120)
    photo_url:          str = Field(..., max_length=2048)
    inat_observation_id: int | None = None
    inat_user_handle:   str | None = Field(None, max_length=80)
    license:            str | None = Field(None, max_length=40)
    source:             str = Field("wikimedia", max_length=40)


@router.get("/admin/curated-photos/{species_key}")
def get_curated_photo(species_key: str, admin: dict = Depends(get_current_admin)):
    """One row + inline last 5 audit entries (OF-7)."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT species_key, common_name, scientific_name, photo_url,
                   inat_observation_id, inat_user_handle, license, source,
                   updated_by_user_id, updated_at
            FROM gold.curated_species_photos
            WHERE species_key = :sk
        """), {"sk": species_key}).fetchone()
        audit_rows = conn.execute(text("""
            SELECT action, prev_photo_url, new_photo_url, changed_by_user_id, changed_at
            FROM audit.curated_species_photos_log
            WHERE species_key = :sk
            ORDER BY changed_at DESC
            LIMIT 5
        """), {"sk": species_key}).fetchall()

    return {
        "species": {
            "species_key":         row[0] if row else species_key,
            "common_name":         row[1] if row else None,
            "scientific_name":     row[2] if row else None,
            "photo_url":           row[3] if row else None,
            "inat_observation_id": row[4] if row else None,
            "inat_user_handle":    row[5] if row else None,
            "license":             row[6] if row else None,
            "source":              row[7] if row else None,
            "updated_by_user_id":  str(row[8]) if (row and row[8]) else None,
            "updated_at":          row[9].isoformat() if (row and row[9]) else None,
            "exists":              row is not None,
        },
        "recent_changes": [
            {
                "action":         a[0],
                "prev_photo_url": a[1],
                "new_photo_url":  a[2],
                "changed_by_user_id": str(a[3]) if a[3] else None,
                "changed_at":     a[4].isoformat() if a[4] else None,
            }
            for a in audit_rows
        ],
    }


@router.put("/admin/curated-photos/{species_key}")
def upsert_curated_photo(
    species_key: str,
    payload: CuratedPhotoPayload,
    admin: dict = Depends(get_current_admin),
):
    """Insert or update curated photo. Single transaction with the audit log."""
    species_key = species_key.lower().strip()
    if not species_key:
        raise HTTPException(400, "species_key cannot be empty")

    with engine.connect() as conn, conn.begin():
        prev = conn.execute(text("""
            SELECT photo_url, common_name, scientific_name
            FROM gold.curated_species_photos
            WHERE species_key = :sk
        """), {"sk": species_key}).fetchone()
        is_insert = prev is None

        conn.execute(text("""
            INSERT INTO gold.curated_species_photos
                (species_key, common_name, scientific_name, photo_url,
                 inat_observation_id, inat_user_handle, license, source,
                 updated_by_user_id, updated_at)
            VALUES (:sk, :cn, :sn, :url, :oid, :uh, :lic, :src, :uid, now())
            ON CONFLICT (species_key) DO UPDATE
              SET common_name         = EXCLUDED.common_name,
                  scientific_name     = EXCLUDED.scientific_name,
                  photo_url           = EXCLUDED.photo_url,
                  inat_observation_id = EXCLUDED.inat_observation_id,
                  inat_user_handle    = EXCLUDED.inat_user_handle,
                  license             = EXCLUDED.license,
                  source              = EXCLUDED.source,
                  updated_by_user_id  = EXCLUDED.updated_by_user_id,
                  updated_at          = EXCLUDED.updated_at
        """), {
            "sk": species_key,
            "cn": payload.common_name,
            "sn": payload.scientific_name,
            "url": payload.photo_url,
            "oid": payload.inat_observation_id,
            "uh": payload.inat_user_handle,
            "lic": payload.license,
            "src": payload.source,
            "uid": admin["id"],
        })

        conn.execute(text("""
            INSERT INTO audit.curated_species_photos_log
                (species_key, action, prev_photo_url, new_photo_url,
                 prev_common_name, new_common_name,
                 prev_scientific, new_scientific,
                 changed_by_user_id)
            VALUES (:sk, :act, :pu, :nu, :pcn, :ncn, :psc, :nsc, :uid)
        """), {
            "sk": species_key,
            "act": "insert" if is_insert else "update",
            "pu": prev[0] if prev else None,
            "nu": payload.photo_url,
            "pcn": prev[1] if prev else None,
            "ncn": payload.common_name,
            "psc": prev[2] if prev else None,
            "nsc": payload.scientific_name,
            "uid": admin["id"],
        })

    return {"ok": True, "species_key": species_key, "action": "insert" if is_insert else "update"}


@router.delete("/admin/curated-photos/{species_key}")
def delete_curated_photo(species_key: str, admin: dict = Depends(get_current_admin)):
    """Delete a curated row. Writes the deletion to the audit log."""
    species_key = species_key.lower().strip()
    with engine.connect() as conn, conn.begin():
        prev = conn.execute(text("""
            SELECT photo_url, common_name, scientific_name
            FROM gold.curated_species_photos
            WHERE species_key = :sk
        """), {"sk": species_key}).fetchone()
        if not prev:
            raise HTTPException(404, "species_key not found")

        conn.execute(
            text("DELETE FROM gold.curated_species_photos WHERE species_key = :sk"),
            {"sk": species_key},
        )
        conn.execute(text("""
            INSERT INTO audit.curated_species_photos_log
                (species_key, action, prev_photo_url, new_photo_url,
                 prev_common_name, prev_scientific,
                 changed_by_user_id)
            VALUES (:sk, 'delete', :pu, NULL, :pcn, :psc, :uid)
        """), {
            "sk": species_key,
            "pu": prev[0],
            "pcn": prev[1],
            "psc": prev[2],
            "uid": admin["id"],
        })
    return {"ok": True, "species_key": species_key, "action": "delete"}


@router.get("/admin/curated-photos/{species_key}/history")
def curated_photo_history(species_key: str, admin: dict = Depends(get_current_admin)):
    """Full audit timeline for a species, newest first."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT action, prev_photo_url, new_photo_url,
                   prev_common_name, new_common_name,
                   prev_scientific, new_scientific,
                   changed_by_user_id, changed_at
            FROM audit.curated_species_photos_log
            WHERE species_key = :sk
            ORDER BY changed_at DESC
        """), {"sk": species_key}).fetchall()
    return {
        "species_key": species_key,
        "events": [
            {
                "action":               r[0],
                "prev_photo_url":       r[1],
                "new_photo_url":        r[2],
                "prev_common_name":     r[3],
                "new_common_name":      r[4],
                "prev_scientific_name": r[5],
                "new_scientific_name":  r[6],
                "changed_by_user_id":   str(r[7]) if r[7] else None,
                "changed_at":           r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ],
    }


# ── iNat search proxy with 1h LRU cache ───────────────────────────

_INAT_CACHE: dict[tuple[str, int], list[dict[str, Any]]] = {}
_INAT_TTL_SECS = 3600


def _inat_cache_key(scientific_name: str) -> tuple[str, int]:
    """Hour-bucketed key so cached entries automatically expire."""
    bucket = int(time.time()) // _INAT_TTL_SECS
    return (scientific_name.lower().strip(), bucket)


@router.get("/admin/inat/photos")
def inat_search(
    scientific_name: str,
    admin: dict = Depends(get_current_admin),
):
    """Return up to 12 research-grade iNat observation photos for a species.

    Cached in-memory for 1 hour per scientific_name to stay polite to iNat.
    """
    name = scientific_name.strip()
    if not name or " " not in name:
        raise HTTPException(400, "scientific_name must be a binomial (Genus species)")

    key = _inat_cache_key(name)
    if key in _INAT_CACHE:
        return {"candidates": _INAT_CACHE[key], "cached": True}

    # Drop expired keys (older buckets) opportunistically.
    current_bucket = key[1]
    for k in list(_INAT_CACHE):
        if k[1] < current_bucket:
            _INAT_CACHE.pop(k, None)

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(
                "https://api.inaturalist.org/v1/observations",
                params={
                    "taxon_name": name,
                    "quality_grade": "research",
                    "photos": "true",
                    "per_page": 12,
                    "order_by": "votes",
                    "order": "desc",
                },
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        return {"candidates": [], "error": f"iNaturalist API error: {e}"}

    candidates: list[dict[str, Any]] = []
    for obs in data.get("results", []):
        photos = obs.get("photos") or []
        if not photos:
            continue
        p = photos[0]
        candidates.append({
            "observation_id":  obs.get("id"),
            "photo_url":       (p.get("url") or "").replace("/square.", "/medium."),
            "photographer":    (obs.get("user") or {}).get("login"),
            "license_code":    p.get("license_code") or "all_rights_reserved",
            "observed_on":     obs.get("observed_on"),
            "place_guess":     obs.get("place_guess"),
            "taxon_name":      ((obs.get("taxon") or {}).get("name")),
        })

    _INAT_CACHE[key] = candidates
    return {"candidates": candidates, "cached": False}


# ── Self-service admin revocation (OF-6) ──────────────────────────

@router.post("/admin/self/revoke")
def revoke_self_admin(admin: dict = Depends(get_current_admin)):
    """Flip the calling user's is_admin to false. Requires re-grant via SQL."""
    with engine.connect() as conn, conn.begin():
        conn.execute(
            text("UPDATE users SET is_admin = false WHERE id = :uid"),
            {"uid": admin["id"]},
        )
    return {"ok": True, "is_admin": False}
