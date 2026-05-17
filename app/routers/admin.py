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


def _detect_source(photo_url: str, client_hint: str | None) -> str:
    """Pick a `source` label from the URL host rather than trusting the
    client. The frontend's selectedObs-based heuristic gives the wrong
    answer if a curator pastes an iNat URL by hand."""
    url = (photo_url or '').lower()
    if 'inaturalist' in url:
        return 'inaturalist'
    if 'wikimedia' in url or 'wikipedia' in url:
        return 'wikimedia'
    return client_hint or 'manual'


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
    (filtered to the same scope, per OF-7).

    When the requested scope has no row yet, we also return a
    `global_fallback` payload built from the species's global ('*') row
    if one exists — the editor uses this to pre-seed common_name and
    scientific_name so the iNat search button is immediately usable
    after picking 'Add scope'."""
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

        # If the requested scope doesn't have a row yet and the request
        # is for a per-watershed scope, look up the species's global
        # default so the editor can pre-seed.
        global_fallback = None
        if row is None and ws != GLOBAL_WATERSHED:
            g = conn.execute(text("""
                SELECT common_name, scientific_name, photo_url
                FROM gold.curated_species_photos
                WHERE species_key = :sk AND watershed = '*'
            """), {"sk": species_key}).fetchone()
            if g:
                global_fallback = {
                    "common_name":     g[0],
                    "scientific_name": g[1],
                    "photo_url":       g[2],
                }

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
        "global_fallback": global_fallback,
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

        # Override the client-supplied source if the URL host disagrees
        # (e.g. pasted iNat URL with client's default 'wikimedia').
        detected_source = _detect_source(payload.photo_url, payload.source)

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
            "src": detected_source,
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

    # iNat's per_page max is 200; 50 gives ~4 pages of 12 in the admin
    # candidate grid without spamming the API.
    params: dict[str, Any] = {
        "taxon_name": name,
        "quality_grade": "research",
        "photos": "true",
        "per_page": 50,
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


# ── River-story narrative editor + audio regeneration ─────────────

READING_LEVELS = ("kids", "adult", "expert")


def _validate_reading_level(lvl: str) -> str:
    v = (lvl or "").strip().lower()
    if v not in READING_LEVELS:
        raise HTTPException(400, f"reading_level must be one of {READING_LEVELS}")
    return v


class RiverStoryPayload(BaseModel):
    narrative: str = Field(..., min_length=1, max_length=10000)


@router.get("/admin/river-stories")
def list_river_stories(admin: dict = Depends(get_current_admin)):
    """Every (watershed, reading_level) row + whether a cached audio file
    exists. Frontend renders one card per row, grouped by watershed."""
    from app.audio_cache import get_audio_url
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT watershed, reading_level, narrative, generated_at,
                   updated_by_user_id, updated_at
            FROM river_stories
            ORDER BY watershed,
                     CASE reading_level
                       WHEN 'kids' THEN 0
                       WHEN 'adult' THEN 1
                       WHEN 'expert' THEN 2 ELSE 9 END
        """)).fetchall()
    out: list[dict] = []
    for r in rows:
        filename = f"{r[0]}_{r[1]}.mp3"
        audio_url = get_audio_url("river_stories", filename)
        out.append({
            "watershed":         r[0],
            "reading_level":     r[1],
            "narrative":         r[2],
            "narrative_length":  len(r[2] or ""),
            "generated_at":      r[3].isoformat() if r[3] else None,
            "updated_by_user_id": str(r[4]) if r[4] else None,
            "updated_at":        r[5].isoformat() if r[5] else None,
            "audio_url":         audio_url if audio_url and audio_url.startswith("http") else (
                f"/api/v1/sites/{r[0]}/river-story-audio?reading_level={r[1]}" if audio_url else None
            ),
            "has_audio":         audio_url is not None,
        })
    return out


@router.get("/admin/river-stories/{watershed}/{reading_level}")
def get_river_story(
    watershed: str,
    reading_level: str,
    admin: dict = Depends(get_current_admin),
):
    """One row + inline last 5 audit entries."""
    ws = _validate_watershed(watershed) if watershed != GLOBAL_WATERSHED else None
    if ws is None:
        raise HTTPException(400, "watershed required")
    lvl = _validate_reading_level(reading_level)

    from app.audio_cache import get_audio_url
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT watershed, reading_level, narrative, generated_at,
                   updated_by_user_id, updated_at
            FROM river_stories
            WHERE watershed = :ws AND reading_level = :lvl
        """), {"ws": ws, "lvl": lvl}).fetchone()
        audit_rows = conn.execute(text("""
            SELECT action, prev_narrative, new_narrative,
                   prev_audio_path, new_audio_path,
                   changed_by_user_id, changed_at
            FROM audit.river_stories_log
            WHERE watershed = :ws AND reading_level = :lvl
            ORDER BY changed_at DESC
            LIMIT 5
        """), {"ws": ws, "lvl": lvl}).fetchall()

    filename = f"{ws}_{lvl}.mp3"
    audio_url = get_audio_url("river_stories", filename)
    audio_serve_url = (
        audio_url if audio_url and audio_url.startswith("http")
        else (f"/api/v1/sites/{ws}/river-story-audio?reading_level={lvl}" if audio_url else None)
    )

    return {
        "story": {
            "watershed":        ws,
            "reading_level":    lvl,
            "narrative":        row[2] if row else None,
            "generated_at":     row[3].isoformat() if (row and row[3]) else None,
            "updated_by_user_id": str(row[4]) if (row and row[4]) else None,
            "updated_at":       row[5].isoformat() if (row and row[5]) else None,
            "audio_url":        audio_serve_url,
            "has_audio":        audio_url is not None,
            "exists":           row is not None,
        },
        "recent_changes": [
            {
                "action":         a[0],
                "prev_narrative": (a[1] or "")[:200] + ("…" if a[1] and len(a[1]) > 200 else ""),
                "new_narrative":  (a[2] or "")[:200] + ("…" if a[2] and len(a[2]) > 200 else ""),
                "prev_audio_path": a[3],
                "new_audio_path":  a[4],
                "changed_by_user_id": str(a[5]) if a[5] else None,
                "changed_at":     a[6].isoformat() if a[6] else None,
            }
            for a in audit_rows
        ],
    }


@router.put("/admin/river-stories/{watershed}/{reading_level}")
def upsert_river_story(
    watershed: str,
    reading_level: str,
    payload: RiverStoryPayload,
    admin: dict = Depends(get_current_admin),
):
    """Save edited narrative text. Audit-logged."""
    ws = _validate_watershed(watershed)
    if ws == GLOBAL_WATERSHED:
        raise HTTPException(400, "watershed required (not '*')")
    lvl = _validate_reading_level(reading_level)

    with engine.connect() as conn, conn.begin():
        prev = conn.execute(text("""
            SELECT narrative FROM river_stories
            WHERE watershed = :ws AND reading_level = :lvl
        """), {"ws": ws, "lvl": lvl}).fetchone()

        conn.execute(text("""
            INSERT INTO river_stories
                (watershed, reading_level, narrative, generated_at,
                 updated_by_user_id, updated_at)
            VALUES (:ws, :lvl, :n, now(), :uid, now())
            ON CONFLICT (watershed, reading_level) DO UPDATE
              SET narrative          = EXCLUDED.narrative,
                  generated_at       = EXCLUDED.generated_at,
                  updated_by_user_id = EXCLUDED.updated_by_user_id,
                  updated_at         = EXCLUDED.updated_at
        """), {"ws": ws, "lvl": lvl, "n": payload.narrative, "uid": admin["id"]})

        conn.execute(text("""
            INSERT INTO audit.river_stories_log
                (watershed, reading_level, action,
                 prev_narrative, new_narrative,
                 changed_by_user_id)
            VALUES (:ws, :lvl, 'narrative_update', :prev, :new, :uid)
        """), {
            "ws": ws, "lvl": lvl,
            "prev": prev[0] if prev else None,
            "new": payload.narrative,
            "uid": admin["id"],
        })

    return {"ok": True, "watershed": ws, "reading_level": lvl,
            "action": "update" if prev else "insert"}


@router.post("/admin/river-stories/{watershed}/{reading_level}/regenerate-audio")
def regenerate_river_story_audio(
    watershed: str,
    reading_level: str,
    admin: dict = Depends(get_current_admin),
):
    """Call OpenAI TTS on the current narrative, persist the MP3 to the
    configured backend (GCS in prod, local in dev), and audit-log the
    new audio path. Returns the new audio_url for immediate preview."""
    import os
    import httpx
    from app.audio_cache import get_audio_url, put_audio_bytes

    ws = _validate_watershed(watershed)
    if ws == GLOBAL_WATERSHED:
        raise HTTPException(400, "watershed required (not '*')")
    lvl = _validate_reading_level(reading_level)

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(503, "OPENAI_API_KEY not configured")

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT narrative FROM river_stories
            WHERE watershed = :ws AND reading_level = :lvl
        """), {"ws": ws, "lvl": lvl}).fetchone()
    if not row or not row[0]:
        raise HTTPException(404, "No narrative to synthesise. Save text first.")
    narrative: str = row[0]

    # OpenAI TTS — `nova` voice is what /api/v1/deep-time/narrate-async uses;
    # keep the river_story voice consistent with DeepTrail narration.
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            },
            json={"model": "tts-1", "voice": "nova", "input": narrative},
            timeout=60,
        )
        resp.raise_for_status()
        audio_bytes = resp.content
    except httpx.HTTPError as e:
        raise HTTPException(502, f"OpenAI TTS error: {e}") from e

    filename = f"{ws}_{lvl}.mp3"
    prev_path = get_audio_url("river_stories", filename)
    new_path = put_audio_bytes("river_stories", filename, audio_bytes)
    if not new_path:
        raise HTTPException(500, "Failed to persist audio to storage")

    with engine.connect() as conn, conn.begin():
        conn.execute(text("""
            INSERT INTO audit.river_stories_log
                (watershed, reading_level, action,
                 prev_audio_path, new_audio_path,
                 changed_by_user_id)
            VALUES (:ws, :lvl, 'audio_regenerate', :prev, :new, :uid)
        """), {
            "ws": ws, "lvl": lvl,
            "prev": prev_path, "new": new_path,
            "uid": admin["id"],
        })

    audio_serve_url = (
        new_path if new_path.startswith("http")
        else f"/api/v1/sites/{ws}/river-story-audio?reading_level={lvl}"
    )
    return {
        "ok": True,
        "watershed": ws,
        "reading_level": lvl,
        "audio_url": audio_serve_url,
        "audio_bytes": len(audio_bytes),
    }


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
