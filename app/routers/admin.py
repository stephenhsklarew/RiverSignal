"""Admin console API routes.

All routes here are gated by `get_current_admin` and operate on
`gold.curated_species_photos` + `audit.curated_species_photos_log`.

Per-watershed scoping (ah33b4c5d6e7): rows are keyed on
`(species_key, watershed)`. Watershed `'*'` = global default; any other
value (e.g. `'mckenzie'`) is a per-watershed override. Public lookup
(in app/routers/fishing.py) prefers watershed-specific over global.

Endpoints
---------
GET    /admin/curated-photos                                       list every row (all scopes)
GET    /admin/curated-photos/{species_key}?watershed=...           one row + last 5 audit entries
PUT    /admin/curated-photos/{species_key}?watershed=...           upsert; writes audit row
DELETE /admin/curated-photos/{species_key}?watershed=...           delete; writes audit row
GET    /admin/curated-photos/{species_key}/history?watershed=...   full audit timeline (omit ws → all scopes)
GET    /admin/inat/photos?scientific_name=...                      iNat search proxy (1h LRU cache)
POST   /admin/self/revoke                                          self-service admin revocation (OF-6)
"""
from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.lib.admin_auth import get_current_admin
from pipeline.db import engine


router = APIRouter(tags=["admin"])

# DB sentinel for "applies to every watershed". Keep all-watershed rows
# under one well-known value so the public lookup query in fishing.py
# can do a single OR-style match without NULL semantics.
GLOBAL_WATERSHED = '*'

# Allowlist used by the watershed-scope selector; mirrors WATERSHEDS in
# pipeline/config/watersheds.py. Kept in code so a malformed query string
# can't insert a row with an arbitrary watershed value.
VALID_WATERSHEDS = {
    'mckenzie', 'deschutes', 'metolius', 'klamath', 'johnday',
    'skagit', 'green_river', 'shenandoah',
}


def _validate_watershed(watershed: str) -> str:
    """Accept '*' or one of the known watershed slugs; reject anything else."""
    ws = (watershed or '').strip().lower()
    if ws == GLOBAL_WATERSHED:
        return ws
    if ws in VALID_WATERSHEDS:
        return ws
    raise HTTPException(400, f"watershed must be '*' or one of {sorted(VALID_WATERSHEDS)}")


# ── Curated photos: list ───────────────────────────────────────────

@router.get("/admin/curated-photos")
def list_curated_photos(admin: dict = Depends(get_current_admin)):
    """Every curated row across all scopes. Frontend groups by species_key
    and renders the watershed scope (global '*' or specific) on each card.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT species_key, watershed, common_name, scientific_name, photo_url,
                   inat_user_handle, license, source,
                   updated_by_user_id, updated_at
            FROM gold.curated_species_photos
            ORDER BY species_key,
                     CASE WHEN watershed = '*' THEN 0 ELSE 1 END,
                     watershed
        """)).fetchall()
    return [
        {
            "species_key":      r[0],
            "watershed":        r[1],
            "common_name":      r[2],
            "scientific_name":  r[3],
            "photo_url":        r[4],
            "inat_user_handle": r[5],
            "license":          r[6],
            "source":           r[7],
            "updated_by_user_id": str(r[8]) if r[8] else None,
            "updated_at":       r[9].isoformat() if r[9] else None,
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
def get_curated_photo(
    species_key: str,
    watershed: str = Query(GLOBAL_WATERSHED, description="'*' for global default, or a watershed slug"),
    admin: dict = Depends(get_current_admin),
):
    """One row at the requested scope + inline last 5 audit entries
    (filtered to the same scope, per OF-7)."""
    ws = _validate_watershed(watershed)
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT species_key, watershed, common_name, scientific_name, photo_url,
                   inat_observation_id, inat_user_handle, license, source,
                   updated_by_user_id, updated_at
            FROM gold.curated_species_photos
            WHERE species_key = :sk AND watershed = :ws
        """), {"sk": species_key, "ws": ws}).fetchone()
        audit_rows = conn.execute(text("""
            SELECT action, prev_photo_url, new_photo_url, watershed,
                   changed_by_user_id, changed_at
            FROM audit.curated_species_photos_log
            WHERE species_key = :sk AND watershed = :ws
            ORDER BY changed_at DESC
            LIMIT 5
        """), {"sk": species_key, "ws": ws}).fetchall()

    return {
        "species": {
            "species_key":         row[0] if row else species_key,
            "watershed":           row[1] if row else ws,
            "common_name":         row[2] if row else None,
            "scientific_name":     row[3] if row else None,
            "photo_url":           row[4] if row else None,
            "inat_observation_id": row[5] if row else None,
            "inat_user_handle":    row[6] if row else None,
            "license":             row[7] if row else None,
            "source":              row[8] if row else None,
            "updated_by_user_id":  str(row[9]) if (row and row[9]) else None,
            "updated_at":          row[10].isoformat() if (row and row[10]) else None,
            "exists":              row is not None,
        },
        "recent_changes": [
            {
                "action":         a[0],
                "prev_photo_url": a[1],
                "new_photo_url":  a[2],
                "watershed":      a[3],
                "changed_by_user_id": str(a[4]) if a[4] else None,
                "changed_at":     a[5].isoformat() if a[5] else None,
            }
            for a in audit_rows
        ],
    }


@router.put("/admin/curated-photos/{species_key}")
def upsert_curated_photo(
    species_key: str,
    payload: CuratedPhotoPayload,
    watershed: str = Query(GLOBAL_WATERSHED, description="'*' for global default, or a watershed slug"),
    admin: dict = Depends(get_current_admin),
):
    """Insert or update curated photo at the requested scope. Single
    transaction with the audit log."""
    species_key = species_key.lower().strip()
    if not species_key:
        raise HTTPException(400, "species_key cannot be empty")
    ws = _validate_watershed(watershed)

    with engine.connect() as conn, conn.begin():
        prev = conn.execute(text("""
            SELECT photo_url, common_name, scientific_name
            FROM gold.curated_species_photos
            WHERE species_key = :sk AND watershed = :ws
        """), {"sk": species_key, "ws": ws}).fetchone()
        is_insert = prev is None

        conn.execute(text("""
            INSERT INTO gold.curated_species_photos
                (species_key, watershed, common_name, scientific_name, photo_url,
                 inat_observation_id, inat_user_handle, license, source,
                 updated_by_user_id, updated_at)
            VALUES (:sk, :ws, :cn, :sn, :url, :oid, :uh, :lic, :src, :uid, now())
            ON CONFLICT (species_key, watershed) DO UPDATE
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
            "ws": ws,
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
                (species_key, watershed, action,
                 prev_photo_url, new_photo_url,
                 prev_common_name, new_common_name,
                 prev_scientific, new_scientific,
                 changed_by_user_id)
            VALUES (:sk, :ws, :act, :pu, :nu, :pcn, :ncn, :psc, :nsc, :uid)
        """), {
            "sk": species_key,
            "ws": ws,
            "act": "insert" if is_insert else "update",
            "pu": prev[0] if prev else None,
            "nu": payload.photo_url,
            "pcn": prev[1] if prev else None,
            "ncn": payload.common_name,
            "psc": prev[2] if prev else None,
            "nsc": payload.scientific_name,
            "uid": admin["id"],
        })

    return {"ok": True, "species_key": species_key, "watershed": ws,
            "action": "insert" if is_insert else "update"}


@router.delete("/admin/curated-photos/{species_key}")
def delete_curated_photo(
    species_key: str,
    watershed: str = Query(GLOBAL_WATERSHED),
    admin: dict = Depends(get_current_admin),
):
    """Delete a curated row at the requested scope. Audit-logged."""
    species_key = species_key.lower().strip()
    ws = _validate_watershed(watershed)
    with engine.connect() as conn, conn.begin():
        prev = conn.execute(text("""
            SELECT photo_url, common_name, scientific_name
            FROM gold.curated_species_photos
            WHERE species_key = :sk AND watershed = :ws
        """), {"sk": species_key, "ws": ws}).fetchone()
        if not prev:
            raise HTTPException(404, "no row at that (species_key, watershed) scope")

        conn.execute(
            text("DELETE FROM gold.curated_species_photos "
                 "WHERE species_key = :sk AND watershed = :ws"),
            {"sk": species_key, "ws": ws},
        )
        conn.execute(text("""
            INSERT INTO audit.curated_species_photos_log
                (species_key, watershed, action,
                 prev_photo_url, new_photo_url,
                 prev_common_name, prev_scientific,
                 changed_by_user_id)
            VALUES (:sk, :ws, 'delete', :pu, NULL, :pcn, :psc, :uid)
        """), {
            "sk": species_key,
            "ws": ws,
            "pu": prev[0],
            "pcn": prev[1],
            "psc": prev[2],
            "uid": admin["id"],
        })
    return {"ok": True, "species_key": species_key, "watershed": ws, "action": "delete"}


@router.get("/admin/curated-photos/{species_key}/history")
def curated_photo_history(
    species_key: str,
    watershed: str | None = Query(None, description="Filter to one scope; omit for all scopes"),
    admin: dict = Depends(get_current_admin),
):
    """Full audit timeline for a species, newest first. When `watershed`
    is provided, filters to that single scope; otherwise returns every
    scope's edits interleaved."""
    where = "WHERE species_key = :sk"
    params: dict = {"sk": species_key}
    if watershed is not None:
        ws = _validate_watershed(watershed)
        where += " AND watershed = :ws"
        params["ws"] = ws

    with engine.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT action, watershed,
                   prev_photo_url, new_photo_url,
                   prev_common_name, new_common_name,
                   prev_scientific, new_scientific,
                   changed_by_user_id, changed_at
            FROM audit.curated_species_photos_log
            {where}
            ORDER BY changed_at DESC
        """), params).fetchall()
    return {
        "species_key": species_key,
        "watershed":   params.get("ws"),  # None when omitted = "all scopes"
        "events": [
            {
                "action":               r[0],
                "watershed":            r[1],
                "prev_photo_url":       r[2],
                "new_photo_url":        r[3],
                "prev_common_name":     r[4],
                "new_common_name":      r[5],
                "prev_scientific_name": r[6],
                "new_scientific_name":  r[7],
                "changed_by_user_id":   str(r[8]) if r[8] else None,
                "changed_at":           r[9].isoformat() if r[9] else None,
            }
            for r in rows
        ],
    }


# ── iNat search proxy with 1h LRU cache ───────────────────────────

_INAT_CACHE: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
_INAT_TTL_SECS = 3600


def _inat_cache_key(scientific_name: str, watershed: str) -> tuple[str, str, int]:
    """Hour-bucketed key so cached entries automatically expire.
    Cache is per (name, watershed) so global vs per-watershed searches
    don't share a slot."""
    bucket = int(time.time()) // _INAT_TTL_SECS
    return (scientific_name.lower().strip(), watershed, bucket)


def _watershed_bbox(watershed: str) -> dict[str, float] | None:
    """Look up the bbox for a watershed (None for the global sentinel '*')."""
    if watershed == GLOBAL_WATERSHED:
        return None
    try:
        from pipeline.config.watersheds import WATERSHEDS
    except ImportError:
        return None
    return (WATERSHEDS.get(watershed) or {}).get("bbox")


@router.get("/admin/inat/photos")
def inat_search(
    scientific_name: str,
    watershed: str = Query(GLOBAL_WATERSHED, description="'*' for global search, or a watershed slug to filter to its bbox"),
    admin: dict = Depends(get_current_admin),
):
    """Return up to 12 research-grade iNat observation photos for a species.

    When `watershed` is a real slug (not '*'), the search is restricted
    to iNat observations inside that watershed's bbox via the swlat /
    swlng / nelat / nelng query params. Results are vastly more useful
    editorially — an Oregon brown trout shot for /path/now/mckenzie
    instead of a New Zealand specimen.

    Cached in-memory for 1 hour per (scientific_name, watershed).
    """
    name = scientific_name.strip()
    if not name or " " not in name:
        raise HTTPException(400, "scientific_name must be a binomial (Genus species)")
    ws = _validate_watershed(watershed)

    key = _inat_cache_key(name, ws)
    if key in _INAT_CACHE:
        return {"candidates": _INAT_CACHE[key], "cached": True, "watershed": ws}

    # Drop expired keys (older buckets) opportunistically.
    current_bucket = key[2]
    for k in list(_INAT_CACHE):
        if k[2] < current_bucket:
            _INAT_CACHE.pop(k, None)

    params: dict[str, Any] = {
        "taxon_name": name,
        "quality_grade": "research",
        "photos": "true",
        "per_page": 12,
        "order_by": "votes",
        "order": "desc",
    }
    bbox = _watershed_bbox(ws)
    if bbox:
        params.update({
            "swlat": bbox["south"],
            "swlng": bbox["west"],
            "nelat": bbox["north"],
            "nelng": bbox["east"],
        })

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(
                "https://api.inaturalist.org/v1/observations",
                params=params,
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        return {"candidates": [], "error": f"iNaturalist API error: {e}", "watershed": ws}

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
    return {"candidates": candidates, "cached": False, "watershed": ws}


# ── TEMP DIAG (remove after debugging brook trout on deschutes) ───

@router.get("/admin/_diag/curated/{species_key}")
def diag_curated(species_key: str):
    """Public, read-only. Returns every curated row for a species_key so
    we can confirm the per-watershed override actually persisted."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT species_key, watershed, photo_url, source, updated_at
            FROM gold.curated_species_photos
            WHERE species_key = :sk
            ORDER BY watershed
        """), {"sk": species_key.lower().strip()}).fetchall()
    return [
        {
            "species_key": r[0],
            "watershed":   r[1],
            "photo_url":   r[2],
            "source":      r[3],
            "updated_at":  r[4].isoformat() if r[4] else None,
        }
        for r in rows
    ]


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
