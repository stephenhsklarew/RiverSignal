"""Audio file resolution — checks GCS (production) or local filesystem (dev)."""

import os
import pathlib

_GCS_BUCKET = os.environ.get("GCS_BUCKET_ASSETS")
_STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent


def get_audio_url(audio_type: str, filename: str) -> str | None:
    """Return a servable audio URL, or None if the file doesn't exist.

    audio_type: 'river_stories' | 'deep_time' | 'campfire'
    filename: e.g. 'mckenzie_adult.mp3'

    In GCS mode: returns a public GCS URL.
    In local mode: returns an API path if the local file exists.
    """
    if _STORAGE_BACKEND == "gcs" and _GCS_BUCKET:
        # GCS public URL — files were synced by migrate-to-production.sh
        return f"https://storage.googleapis.com/{_GCS_BUCKET}/audio/{audio_type}/{filename}"

    # Local filesystem
    dir_map = {
        "river_stories": ".river_story_audio",
        "deep_time": ".deep_time_audio",
        "campfire": ".campfire_cache",
    }
    local_dir = _PROJECT_ROOT / dir_map.get(audio_type, audio_type)
    local_file = local_dir / filename
    if local_file.exists() and local_file.stat().st_size > 0:
        return str(local_file)
    return None


def get_audio_bytes(audio_type: str, filename: str) -> bytes | None:
    """Return audio file bytes, or None if not found.

    In GCS mode: fetches from GCS via HTTP.
    In local mode: reads from local filesystem.
    """
    if _STORAGE_BACKEND == "gcs" and _GCS_BUCKET:
        import httpx
        url = f"https://storage.googleapis.com/{_GCS_BUCKET}/audio/{audio_type}/{filename}"
        try:
            resp = httpx.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        return None

    # Local filesystem
    dir_map = {
        "river_stories": ".river_story_audio",
        "deep_time": ".deep_time_audio",
        "campfire": ".campfire_cache",
    }
    local_dir = _PROJECT_ROOT / dir_map.get(audio_type, audio_type)
    local_file = local_dir / filename
    if local_file.exists():
        return local_file.read_bytes()
    return None


def put_audio_bytes(audio_type: str, filename: str, content: bytes,
                    content_type: str = "audio/mpeg") -> str | None:
    """Write `content` to the configured backend (GCS in prod, local in dev).

    Returns a servable URL (or None on failure). Used by the admin
    "regenerate audio" endpoint so curators can refresh a river-story
    MP3 without leaving the UI.
    """
    if _STORAGE_BACKEND == "gcs" and _GCS_BUCKET:
        try:
            from google.cloud import storage  # lazy import — only needed in prod
            client = storage.Client()
            bucket = client.bucket(_GCS_BUCKET)
            blob_path = f"audio/{audio_type}/{filename}"
            blob = bucket.blob(blob_path)
            blob.cache_control = "public, max-age=3600"
            blob.upload_from_string(content, content_type=content_type)
            return f"https://storage.googleapis.com/{_GCS_BUCKET}/{blob_path}"
        except Exception:
            return None

    # Local filesystem
    dir_map = {
        "river_stories": ".river_story_audio",
        "deep_time": ".deep_time_audio",
        "campfire": ".campfire_cache",
    }
    local_dir = _PROJECT_ROOT / dir_map.get(audio_type, audio_type)
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / filename
    local_file.write_bytes(content)
    return str(local_file)
