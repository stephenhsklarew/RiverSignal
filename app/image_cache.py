"""Image cache URL resolver — maps source URLs to local cached paths."""

import hashlib
import os

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'images', 'cache')
CACHE_URL_PREFIX = '/images/cache'


def _url_to_filename(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()
    ext = '.jpg'
    if '.png' in url.lower():
        ext = '.png'
    elif '.webp' in url.lower():
        ext = '.webp'
    elif '.gif' in url.lower():
        ext = '.gif'
    return f"{h}{ext}"


def get_cached_url(source_url: str | None, img_type: str = 'species') -> str | None:
    """Return cached URL if the image exists locally, else return source URL."""
    if not source_url:
        return None
    fname = _url_to_filename(source_url)
    cache_path = os.path.join(CACHE_DIR, img_type, fname)
    if os.path.exists(cache_path):
        return f"{CACHE_URL_PREFIX}/{img_type}/{fname}"
    return source_url
