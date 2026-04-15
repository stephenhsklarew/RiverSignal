"""Image caching pipeline — download and serve species, fossil, and mineral images locally.

Downloads thumbnails from source URLs (iNaturalist, GBIF, Wikipedia, etc.)
and stores them locally so the frontend serves from our cache instead of
hitting external servers on every page load.

Usage:
    python -m pipeline.cache_images                  # Cache all new images
    python -m pipeline.cache_images --type species   # Species only
    python -m pipeline.cache_images --type fossils   # Fossils only
    python -m pipeline.cache_images --type minerals  # Minerals only
    python -m pipeline.cache_images --stats          # Show cache stats
"""

import hashlib
import os
import sys
import time

import click
import httpx
from rich.console import Console
from rich.progress import Progress
from sqlalchemy import text

from pipeline.db import engine

console = Console()

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'images', 'cache')
SPECIES_DIR = os.path.join(CACHE_DIR, 'species')
FOSSILS_DIR = os.path.join(CACHE_DIR, 'fossils')
MINERALS_DIR = os.path.join(CACHE_DIR, 'minerals')

# Serve path prefix (what the frontend uses)
CACHE_URL_PREFIX = '/images/cache'


def url_to_filename(url: str) -> str:
    """Generate a deterministic filename from a URL."""
    h = hashlib.md5(url.encode()).hexdigest()
    ext = '.jpg'
    if '.png' in url.lower():
        ext = '.png'
    elif '.webp' in url.lower():
        ext = '.webp'
    elif '.gif' in url.lower():
        ext = '.gif'
    return f"{h}{ext}"


def download_image(client: httpx.Client, url: str, dest_path: str) -> bool:
    """Download an image to dest_path. Returns True on success."""
    if os.path.exists(dest_path):
        return True  # Already cached
    try:
        resp = client.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(dest_path, 'wb') as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False


def cache_species_images():
    """Cache species gallery photos from iNaturalist."""
    os.makedirs(SPECIES_DIR, exist_ok=True)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT photo_url FROM gold.species_gallery
            WHERE photo_url IS NOT NULL AND photo_url != ''
        """)).fetchall()

    urls = [r[0] for r in rows]
    console.print(f"Species: {len(urls)} unique photos to cache")

    cached = 0
    skipped = 0
    failed = 0

    with httpx.Client(follow_redirects=True, headers={"User-Agent": "RiverSignal/1.0"}) as client:
        with Progress() as progress:
            task = progress.add_task("Caching species...", total=len(urls))
            for url in urls:
                fname = url_to_filename(url)
                dest = os.path.join(SPECIES_DIR, fname)
                if os.path.exists(dest):
                    skipped += 1
                elif download_image(client, url, dest):
                    cached += 1
                else:
                    failed += 1
                progress.update(task, advance=1)
                if cached % 100 == 0 and cached > 0:
                    time.sleep(0.1)  # gentle rate limit

    console.print(f"  [green]Cached: {cached}, Skipped: {skipped}, Failed: {failed}[/green]")

    # Update database with cached URLs
    _update_cached_urls('species_gallery', 'photo_url', SPECIES_DIR, f'{CACHE_URL_PREFIX}/species')


def cache_fossil_images():
    """Cache fossil specimen images from GBIF/museums."""
    os.makedirs(FOSSILS_DIR, exist_ok=True)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT image_url FROM fossil_occurrences
            WHERE image_url IS NOT NULL AND image_url != ''
        """)).fetchall()

    urls = [r[0] for r in rows]
    console.print(f"Fossils: {len(urls)} unique images to cache")

    cached = 0
    skipped = 0
    failed = 0

    with httpx.Client(follow_redirects=True, headers={"User-Agent": "RiverSignal/1.0"}) as client:
        with Progress() as progress:
            task = progress.add_task("Caching fossils...", total=len(urls))
            for url in urls:
                fname = url_to_filename(url)
                dest = os.path.join(FOSSILS_DIR, fname)
                if os.path.exists(dest):
                    skipped += 1
                elif download_image(client, url, dest):
                    cached += 1
                else:
                    failed += 1
                progress.update(task, advance=1)

    console.print(f"  [green]Cached: {cached}, Skipped: {skipped}, Failed: {failed}[/green]")

    _update_cached_urls('fossil_occurrences', 'image_url', FOSSILS_DIR, f'{CACHE_URL_PREFIX}/fossils')


def cache_mineral_images():
    """Cache mineral deposit images."""
    os.makedirs(MINERALS_DIR, exist_ok=True)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT image_url FROM mineral_deposits
            WHERE image_url IS NOT NULL AND image_url != ''
        """)).fetchall()

    urls = [r[0] for r in rows]
    console.print(f"Minerals: {len(urls)} unique images to cache")

    cached = 0
    skipped = 0
    failed = 0

    with httpx.Client(follow_redirects=True, headers={"User-Agent": "RiverSignal/1.0"}) as client:
        with Progress() as progress:
            task = progress.add_task("Caching minerals...", total=len(urls))
            for url in urls:
                fname = url_to_filename(url)
                dest = os.path.join(MINERALS_DIR, fname)
                if os.path.exists(dest):
                    skipped += 1
                elif download_image(client, url, dest):
                    cached += 1
                else:
                    failed += 1
                progress.update(task, advance=1)

    console.print(f"  [green]Cached: {cached}, Skipped: {skipped}, Failed: {failed}[/green]")

    _update_cached_urls('mineral_deposits', 'image_url', MINERALS_DIR, f'{CACHE_URL_PREFIX}/minerals')


def _update_cached_urls(table: str, url_column: str, cache_dir: str, url_prefix: str):
    """Update the database to add cached_image_url for successfully cached images."""
    # Ensure column exists
    with engine.connect() as conn:
        try:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS cached_image_url VARCHAR"))
            conn.commit()
        except Exception:
            conn.rollback()

        # Get all source URLs
        rows = conn.execute(text(f"""
            SELECT DISTINCT {url_column} FROM {table}
            WHERE {url_column} IS NOT NULL AND {url_column} != ''
        """)).fetchall()

        updated = 0
        for r in rows:
            url = r[0]
            fname = url_to_filename(url)
            if os.path.exists(os.path.join(cache_dir, fname)):
                cached_url = f"{url_prefix}/{fname}"
                conn.execute(text(f"""
                    UPDATE {table} SET cached_image_url = :cached
                    WHERE {url_column} = :src AND (cached_image_url IS NULL OR cached_image_url != :cached)
                """), {"cached": cached_url, "src": url})
                updated += 1

        conn.commit()
        console.print(f"  Updated {updated} rows with cached URLs in {table}")


def show_stats():
    """Show image cache statistics."""
    for name, dir_path in [('Species', SPECIES_DIR), ('Fossils', FOSSILS_DIR), ('Minerals', MINERALS_DIR)]:
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            size_mb = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files) / (1024 * 1024)
            console.print(f"{name}: {len(files)} files, {size_mb:.1f} MB")
        else:
            console.print(f"{name}: not cached yet")


@click.command()
@click.option('--type', 'img_type', type=click.Choice(['species', 'fossils', 'minerals', 'all']), default='all')
@click.option('--stats', is_flag=True, help='Show cache statistics only')
def main(img_type: str, stats: bool):
    """Download and cache images from external sources."""
    if stats:
        show_stats()
        return

    console.print("[bold]Image Cache Pipeline[/bold]")

    if img_type in ('species', 'all'):
        cache_species_images()
    if img_type in ('fossils', 'all'):
        cache_fossil_images()
    if img_type in ('minerals', 'all'):
        cache_mineral_images()

    console.print("\n[bold green]Done![/bold green]")
    show_stats()


if __name__ == '__main__':
    main()
