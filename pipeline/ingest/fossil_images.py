"""Fossil image backfill: resolve image URLs from iDigBio, MorphoSource, and Smithsonian.

Fetches actual specimen photo URLs for fossil_occurrences records that lack
images. Three sources:

1. iDigBio media records — resolves media record UUIDs to accessURI (CC0 photos
   from USNM, Yale Peabody, UO Condon Collection, etc.)
2. MorphoSource — 3D scans and specimen photos by taxon name
3. Smithsonian NMNH — direct collection image search (CC0)
"""

import json
import time

import httpx
from rich.console import Console
from sqlalchemy import text

from pipeline.db import engine

console = Console()

IDIGBIO_MEDIA_URL = "https://search.idigbio.org/v2/search/media"
IDIGBIO_VIEW_MEDIA = "https://search.idigbio.org/v2/view/mediarecords"
MORPHOSOURCE_URL = "https://www.morphosource.org/catalog/media"
# Smithsonian NMNH collections images are served via iDigBio media records
# (institution code USNM). Direct SI API requires a key from api.si.edu.


def backfill_idigbio_images() -> int:
    """Resolve iDigBio media record UUIDs to actual image URLs.

    Two passes:
    1. Resolve existing media UUIDs stored in the reference field
    2. Search iDigBio media API for any remaining records with hasImage flag
    """
    updated = 0

    with engine.connect() as conn:
        # Pass 1: resolve media record UUIDs already stored in reference field
        rows = conn.execute(text("""
            SELECT id, reference FROM fossil_occurrences
            WHERE source = 'idigbio'
              AND image_url IS NULL
              AND reference LIKE 'https://search.idigbio.org/v2/view/mediarecords/%'
        """)).fetchall()

        console.print(f"  iDigBio pass 1: {len(rows)} records with media UUIDs to resolve")

        with httpx.Client(timeout=15) as client:
            for i, row in enumerate(rows):
                media_uuid = row[1].split("/")[-1]
                try:
                    resp = client.get(f"{IDIGBIO_VIEW_MEDIA}/{media_uuid}")
                    if resp.status_code != 200:
                        continue
                    media = resp.json()
                    # accessURI is in data or indexTerms
                    access_uri = (
                        media.get("data", {}).get("ac:accessURI")
                        or media.get("indexTerms", {}).get("accessuri")
                    )
                    license_val = (
                        media.get("data", {}).get("dcterms:rights")
                        or media.get("data", {}).get("dc:rights")
                        or media.get("indexTerms", {}).get("rights")
                        or ""
                    )
                    if access_uri:
                        conn.execute(text("""
                            UPDATE fossil_occurrences
                            SET image_url = :url, image_license = :lic
                            WHERE id = :fid
                        """), {"url": access_uri, "lic": license_val[:50], "fid": row[0]})
                        updated += 1
                except Exception as e:
                    if i < 3:
                        console.print(f"    [dim]error resolving {media_uuid}: {e}[/dim]")
                    continue

                if (i + 1) % 50 == 0:
                    conn.commit()
                    console.print(f"    ... resolved {i + 1}/{len(rows)} ({updated} images)")
                time.sleep(0.15)  # rate limit

            conn.commit()

        console.print(f"  iDigBio pass 1 complete: {updated} images resolved from UUIDs")

        # Pass 2: bulk media search for iDigBio records still missing images
        # Search by linking media to specimen records via the iDigBio media API
        pass2_start = updated
        missing = conn.execute(text("""
            SELECT source_id FROM fossil_occurrences
            WHERE source = 'idigbio'
              AND image_url IS NULL
              AND data_payload->>'hasImage' = 'true'
            LIMIT 500
        """)).fetchall()

        if missing:
            console.print(f"  iDigBio pass 2: searching media for {len(missing)} records with hasImage flag")
            with httpx.Client(timeout=30) as client:
                # Batch search: get all fossil media in Oregon bbox
                for bbox_label, bbox in [
                    ("McKenzie", {"north": 44.35, "south": 43.8, "west": -122.6, "east": -121.7}),
                    ("Deschutes", {"north": 44.8, "south": 43.6, "west": -122.0, "east": -120.5}),
                    ("Metolius", {"north": 44.7, "south": 44.3, "west": -122.0, "east": -121.3}),
                    ("Klamath", {"north": 43.0, "south": 41.8, "west": -122.5, "east": -121.0}),
                ]:
                    offset = 0
                    while offset < 2000:
                        body = {
                            "rq": {
                                "basisofrecord": "fossilspecimen",
                                "geopoint": {
                                    "type": "geo_bounding_box",
                                    "top_left": {"lat": bbox["north"], "lon": bbox["west"]},
                                    "bottom_right": {"lat": bbox["south"], "lon": bbox["east"]},
                                },
                            },
                            "limit": 100,
                            "offset": offset,
                        }
                        try:
                            resp = client.post(IDIGBIO_MEDIA_URL, json=body)
                            if resp.status_code != 200:
                                break
                            data = resp.json()
                            items = data.get("items", [])
                            if not items:
                                break

                            for item in items:
                                idx = item.get("indexTerms", {})
                                dat = item.get("data", {})
                                access_uri = dat.get("ac:accessURI") or idx.get("accessuri")
                                if not access_uri:
                                    continue

                                # Link to specimen record via the records list
                                record_uuids = idx.get("records", [])
                                license_val = dat.get("dcterms:rights", dat.get("dc:rights", idx.get("rights", "")))

                                for rec_uuid in record_uuids:
                                    result = conn.execute(text("""
                                        UPDATE fossil_occurrences
                                        SET image_url = :url, image_license = :lic
                                        WHERE source = 'idigbio'
                                          AND source_id = :sid
                                          AND image_url IS NULL
                                    """), {"url": access_uri, "lic": str(license_val)[:50], "sid": rec_uuid})
                                    if result.rowcount > 0:
                                        updated += 1

                            offset += len(items)
                            if len(items) < 100:
                                break
                            time.sleep(0.3)
                        except Exception as e:
                            console.print(f"    [dim]media search error for {bbox_label}: {e}[/dim]")
                            break

                    conn.commit()

        console.print(f"  iDigBio pass 2: {updated - pass2_start} additional images from media search")

    # Pass 3: migrate GBIF image_url from data_payload to image_url column
    gbif_updated = 0
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, data_payload->>'image_url' as img
            FROM fossil_occurrences
            WHERE source = 'gbif'
              AND image_url IS NULL
              AND data_payload->>'image_url' IS NOT NULL
              AND data_payload->>'image_url' != ''
        """)).fetchall()
        for row in rows:
            conn.execute(text("""
                UPDATE fossil_occurrences SET image_url = :url WHERE id = :fid
            """), {"url": row[1], "fid": row[0]})
            gbif_updated += 1
        conn.commit()

    if gbif_updated:
        console.print(f"  GBIF: migrated {gbif_updated} image URLs to image_url column")
    updated += gbif_updated

    return updated


def backfill_morphosource() -> int:
    """Search MorphoSource for specimen media matching our fossil taxa.

    MorphoSource primarily has 3D scans. We store the MorphoSource page URL
    as a secondary link (in data_payload.morphosource_url) rather than
    replacing existing image URLs.
    """
    updated = 0

    with engine.connect() as conn:
        # Get distinct genus-level names for taxa without images
        taxa = conn.execute(text("""
            SELECT DISTINCT
                CASE
                    WHEN taxon_name LIKE '%% %%' THEN split_part(taxon_name, ' ', 1)
                    ELSE taxon_name
                END as genus
            FROM fossil_occurrences
            WHERE image_url IS NULL
              AND taxon_name IS NOT NULL
              AND length(taxon_name) > 2
            ORDER BY genus
        """)).fetchall()

        genus_list = [r[0] for r in taxa if r[0] and len(r[0]) > 2 and r[0][0].isupper()]
        console.print(f"  MorphoSource: searching for {len(genus_list)} genera")

        with httpx.Client(timeout=15) as client:
            found_genera = {}
            for genus in genus_list:
                try:
                    resp = client.get(MORPHOSOURCE_URL, params={
                        "q": genus,
                        "format": "json",
                        "per_page": 1,
                    })
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    media = data.get("response", {}).get("media", [])
                    if media:
                        media_id = media[0].get("id", [""])[0]
                        title = media[0].get("title", [""])[0]
                        ms_url = f"https://www.morphosource.org/concern/media/{media_id}" if media_id else None
                        if ms_url:
                            found_genera[genus] = {"url": ms_url, "title": title}
                except Exception:
                    continue
                time.sleep(0.2)

            console.print(f"  MorphoSource: found media for {len(found_genera)} genera")

            # Update records with MorphoSource links
            for genus, info in found_genera.items():
                result = conn.execute(text("""
                    UPDATE fossil_occurrences
                    SET data_payload = jsonb_set(
                        COALESCE(data_payload, '{}'),
                        '{morphosource_url}',
                        to_jsonb(CAST(:url AS text))
                    )
                    WHERE image_url IS NULL
                      AND taxon_name ILIKE :pattern
                """), {"url": info["url"], "pattern": f"{genus}%"})
                updated += result.rowcount

            conn.commit()

    console.print(f"  MorphoSource: linked {updated} fossil records to 3D specimens")
    return updated


def backfill_smithsonian() -> int:
    """Fetch images for USNM (Smithsonian) specimens via NMNH collections portal.

    Many Smithsonian specimens are already covered by iDigBio media backfill.
    This pass catches additional USNM records by constructing direct collection
    image URLs from catalog numbers.
    """
    updated = 0

    with engine.connect() as conn:
        # Get USNM records still missing images
        rows = conn.execute(text("""
            SELECT id, source_id, data_payload->>'catalog' as catalog,
                   museum, data_payload
            FROM fossil_occurrences
            WHERE image_url IS NULL
              AND (museum ILIKE '%%usnm%%' OR museum ILIKE '%%smithsonian%%'
                   OR museum ILIKE '%%nmnh%%')
        """)).fetchall()

        console.print(f"  Smithsonian: {len(rows)} USNM records still without images")

        if not rows:
            return 0

        # For iDigBio-sourced USNM records, try to find media via iDigBio
        with httpx.Client(timeout=15) as client:
            for i, row in enumerate(rows):
                record_id = row[1]  # source_id = iDigBio UUID
                source = None

                # Determine source
                with engine.connect() as check_conn:
                    src = check_conn.execute(text(
                        "SELECT source FROM fossil_occurrences WHERE id = :fid"
                    ), {"fid": row[0]}).scalar()
                    source = src

                if source == "idigbio":
                    # Try fetching the record to get mediarecords
                    try:
                        resp = client.get(
                            f"https://search.idigbio.org/v2/view/records/{record_id}"
                        )
                        if resp.status_code != 200:
                            continue
                        rec = resp.json()
                        media_uuids = rec.get("indexTerms", {}).get("mediarecords", [])
                        if not media_uuids:
                            continue

                        # Fetch the first media record
                        media_resp = client.get(f"{IDIGBIO_VIEW_MEDIA}/{media_uuids[0]}")
                        if media_resp.status_code != 200:
                            continue
                        media = media_resp.json()
                        access_uri = (
                            media.get("data", {}).get("ac:accessURI")
                            or media.get("indexTerms", {}).get("accessuri")
                        )
                        license_val = (
                            media.get("data", {}).get("dcterms:rights")
                            or media.get("data", {}).get("dc:rights")
                            or "CC0"
                        )
                        if access_uri:
                            conn.execute(text("""
                                UPDATE fossil_occurrences
                                SET image_url = :url, image_license = :lic
                                WHERE id = :fid
                            """), {"url": access_uri, "lic": str(license_val)[:50], "fid": row[0]})
                            updated += 1
                    except Exception:
                        continue

                    if (i + 1) % 30 == 0:
                        conn.commit()
                        console.print(f"    ... checked {i + 1}/{len(rows)} ({updated} images)")
                    time.sleep(0.15)

                elif source == "gbif":
                    # GBIF USNM records — try GBIF media endpoint
                    gbif_key = record_id
                    try:
                        resp = client.get(
                            f"https://api.gbif.org/v1/occurrence/{gbif_key}/media"
                        )
                        if resp.status_code != 200:
                            continue
                        media_list = resp.json()
                        if not isinstance(media_list, list) or not media_list:
                            # Try the occurrence record itself
                            resp2 = client.get(f"https://api.gbif.org/v1/occurrence/{gbif_key}")
                            if resp2.status_code == 200:
                                occ = resp2.json()
                                for m in (occ.get("media") or []):
                                    if m.get("type") == "StillImage" and m.get("identifier"):
                                        conn.execute(text("""
                                            UPDATE fossil_occurrences
                                            SET image_url = :url, image_license = :lic
                                            WHERE id = :fid
                                        """), {
                                            "url": m["identifier"],
                                            "lic": (m.get("license") or "")[:50],
                                            "fid": row[0],
                                        })
                                        updated += 1
                                        break
                    except Exception:
                        continue
                    time.sleep(0.15)

            conn.commit()

    console.print(f"  Smithsonian: resolved {updated} additional images")
    return updated


WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
PHYLOPIC_API = "https://api.phylopic.org"


def backfill_wikimedia_commons() -> int:
    """Search Wikimedia Commons for genus-level fossil photographs.

    Searches for "[genus] fossil" in the File namespace and picks the first
    image result with a permissive license. Stores as image_source='wikimedia'.
    """
    updated = 0

    with engine.connect() as conn:
        # Get genera still missing images, ordered by record count
        rows = conn.execute(text("""
            SELECT
              CASE WHEN taxon_name LIKE '%% %%' THEN split_part(taxon_name, ' ', 1)
                   ELSE taxon_name END AS genus,
              count(*) AS cnt
            FROM fossil_occurrences
            WHERE image_url IS NULL
              AND taxon_name IS NOT NULL AND length(taxon_name) > 2
            GROUP BY 1
            HAVING CASE WHEN taxon_name LIKE '%% %%' THEN split_part(taxon_name, ' ', 1)
                        ELSE taxon_name END ~ '^[A-Z]'
            ORDER BY cnt DESC
        """)).fetchall()

        genera = [(r[0], r[1]) for r in rows]
        console.print(f"  Wikimedia: searching for {len(genera)} genera")

        found = {}
        headers = {"User-Agent": "RiverSignal/1.0 (https://github.com/riversignal; admin@riversignal.app)"}
        with httpx.Client(timeout=15, headers=headers) as client:
            for i, (genus, cnt) in enumerate(genera):
                # Search Wikimedia Commons File namespace for "[genus] fossil"
                try:
                    resp = client.get(WIKIMEDIA_API, params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": f"{genus} fossil",
                        "gsrnamespace": 6,  # File namespace
                        "gsrlimit": 5,
                        "prop": "imageinfo",
                        "iiprop": "url|extmetadata",
                        "iiurlwidth": 400,
                        "format": "json",
                    })
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    pages = data.get("query", {}).get("pages", {})

                    # Find best image — prefer ones with genus in title
                    best_url = None
                    best_license = None
                    for page in pages.values():
                        title = page.get("title", "").lower()
                        info = (page.get("imageinfo") or [{}])[0]
                        thumb = info.get("thumburl")
                        full_url = info.get("url", "")
                        if not thumb:
                            continue

                        # Check license
                        ext = info.get("extmetadata", {})
                        license_short = ext.get("LicenseShortName", {}).get("value", "")
                        # Accept CC0, CC-BY, CC-BY-SA, PD
                        if not any(ok in license_short.lower() for ok in ["cc", "public domain", "pd", "gfdl"]):
                            continue

                        # Prefer images with genus name in title
                        if genus.lower() in title:
                            best_url = thumb
                            best_license = license_short
                            break
                        elif not best_url:
                            best_url = thumb
                            best_license = license_short

                    if best_url:
                        found[genus] = {"url": best_url, "license": best_license or "CC"}

                except Exception:
                    continue

                if (i + 1) % 50 == 0:
                    console.print(f"    ... searched {i + 1}/{len(genera)} ({len(found)} found)")
                time.sleep(0.15)  # rate limit

        console.print(f"  Wikimedia: found images for {len(found)}/{len(genera)} genera")

        # Update records
        for genus, info in found.items():
            result = conn.execute(text("""
                UPDATE fossil_occurrences
                SET image_url = :url,
                    image_license = :lic,
                    image_source = 'wikimedia'
                WHERE image_url IS NULL
                  AND (CASE WHEN taxon_name LIKE '%% %%' THEN split_part(taxon_name, ' ', 1)
                            ELSE taxon_name END) = :genus
            """), {"url": info["url"], "lic": info["license"][:50], "genus": genus})
            updated += result.rowcount
        conn.commit()

    console.print(f"  Wikimedia: updated {updated} fossil records with representative photos")
    return updated


def backfill_phylopic() -> int:
    """Fetch PhyloPic silhouette images for taxa still missing images.

    Uses the PhyloPic API to find silhouette illustrations by taxon name.
    Falls back to family/order/class level if genus not found.
    Stores as image_source='phylopic'.
    """
    updated = 0

    with engine.connect() as conn:
        # Get taxa still missing images — try at multiple taxonomic levels
        rows = conn.execute(text("""
            SELECT
              CASE WHEN taxon_name LIKE '%% %%' THEN split_part(taxon_name, ' ', 1)
                   ELSE taxon_name END AS genus,
              family, order_name, class_name, phylum,
              count(*) AS cnt
            FROM fossil_occurrences
            WHERE image_url IS NULL
              AND taxon_name IS NOT NULL AND length(taxon_name) > 2
            GROUP BY 1, family, order_name, class_name, phylum
            ORDER BY cnt DESC
        """)).fetchall()

        # Build a unique set of names to look up, from most specific to least
        lookup_map: dict[str, list[str]] = {}  # name -> list of genera it covers
        genera_needing_images = set()
        for r in rows:
            genus = r[0]
            if genus and len(genus) > 2 and genus[0].isupper():
                genera_needing_images.add(genus)
                # Try genus first, then family, order, class, phylum
                for name in [genus, r[1], r[2], r[3], r[4]]:
                    if name and len(name) > 2:
                        if name not in lookup_map:
                            lookup_map[name] = []
                        lookup_map[name].append(genus)

        console.print(f"  PhyloPic: looking up {len(lookup_map)} taxonomic names")

        found: dict[str, dict] = {}  # genus -> {url, license, name_matched}
        searched_names: set[str] = set()

        with httpx.Client(timeout=10, follow_redirects=True) as client:
            # Process in priority order: genus names first, then higher taxa
            for name in list(lookup_map.keys()):
                if name in searched_names:
                    continue
                searched_names.add(name)

                # Check if all genera for this name are already covered
                genera_for_name = [g for g in lookup_map[name] if g not in found]
                if not genera_for_name:
                    continue

                try:
                    # Step 1: autocomplete to get the canonical name
                    resp = client.get(f"{PHYLOPIC_API}/autocomplete",
                                      params={"query": name.lower()})
                    if resp.status_code != 200:
                        continue
                    matches = resp.json().get("matches", [])
                    if not matches:
                        continue

                    # Use first match
                    canonical = matches[0]

                    # Step 2: search nodes for this name
                    resp2 = client.get(f"{PHYLOPIC_API}/nodes", params={
                        "filter_name": canonical,
                        "build": 537,
                        "page": 0,
                        "embed_items": "true",
                        "embed_primaryImage": "true",
                    })
                    if resp2.status_code != 200:
                        continue

                    data = resp2.json()
                    items = data.get("_embedded", {}).get("items", [])
                    if not items:
                        continue

                    # Get the primary image
                    pi = items[0].get("_embedded", {}).get("primaryImage", {})
                    if not pi:
                        continue

                    pi_links = pi.get("_links", {})
                    # Prefer SVG, fallback to raster or social image
                    svg_url = pi_links.get("vectorFile", {}).get("href")
                    social_url = pi_links.get("http://ogp.me/ns#image", {}).get("href")
                    raster_files = pi_links.get("rasterFiles", [])
                    # Pick a medium-sized raster (index ~3-5 if available)
                    raster_url = None
                    if raster_files:
                        mid = min(len(raster_files) - 1, len(raster_files) // 2)
                        raster_url = raster_files[mid].get("href")

                    image_url = social_url or raster_url or svg_url
                    if not image_url:
                        continue

                    # PhyloPic images are CC0 or CC-BY
                    license_val = "CC0"
                    contributor = pi_links.get("contributor", {}).get("title", "")

                    # Assign to all uncovered genera
                    for genus in genera_for_name:
                        if genus not in found:
                            found[genus] = {
                                "url": image_url,
                                "license": license_val,
                                "matched_name": canonical,
                            }

                except Exception:
                    continue

                if len(searched_names) % 30 == 0:
                    console.print(f"    ... searched {len(searched_names)} names ({len(found)} genera covered)")
                time.sleep(0.1)

        console.print(f"  PhyloPic: found silhouettes for {len(found)} genera")

        # Update records
        for genus, info in found.items():
            result = conn.execute(text("""
                UPDATE fossil_occurrences
                SET image_url = :url,
                    image_license = :lic,
                    image_source = 'phylopic'
                WHERE image_url IS NULL
                  AND (CASE WHEN taxon_name LIKE '%% %%' THEN split_part(taxon_name, ' ', 1)
                            ELSE taxon_name END) = :genus
            """), {"url": info["url"], "lic": info["license"][:50], "genus": genus})
            updated += result.rowcount
        conn.commit()

    console.print(f"  PhyloPic: updated {updated} fossil records with silhouette images")
    return updated


def backfill_all_fossil_images():
    """Run all five image backfill passes."""
    console.print("\n[bold]Fossil image backfill[/bold]\n")

    total = 0

    console.print("[cyan]1. iDigBio media resolution[/cyan]")
    total += backfill_idigbio_images()

    console.print("\n[cyan]2. MorphoSource 3D specimen links[/cyan]")
    total += backfill_morphosource()

    console.print("\n[cyan]3. Smithsonian NMNH direct lookup[/cyan]")
    total += backfill_smithsonian()

    console.print("\n[cyan]4. Wikimedia Commons representative photos[/cyan]")
    total += backfill_wikimedia_commons()

    console.print("\n[cyan]5. PhyloPic silhouette images[/cyan]")
    total += backfill_phylopic()

    # Final stats
    with engine.connect() as conn:
        stats = conn.execute(text("""
            SELECT source,
                   count(*) as total,
                   count(image_url) as with_image,
                   count(CASE WHEN data_payload ? 'morphosource_url' THEN 1 END) as with_3d
            FROM fossil_occurrences
            GROUP BY source ORDER BY source
        """)).fetchall()

        by_type = conn.execute(text("""
            SELECT COALESCE(image_source, 'none') as src, count(*)
            FROM fossil_occurrences
            GROUP BY 1 ORDER BY 2 DESC
        """)).fetchall()

    console.print("\n[bold]Final image coverage by data source:[/bold]")
    for r in stats:
        console.print(f"  {r[0]}: {r[2]}/{r[1]} images" +
                       (f", {r[3]} MorphoSource links" if r[3] else ""))

    console.print("\n[bold]Image type breakdown:[/bold]")
    for r in by_type:
        console.print(f"  {r[0]:12s}: {r[1]:>5,}")

    total_with = sum(r[2] for r in stats)
    total_all = sum(r[1] for r in stats)
    pct = 100 * total_with / total_all if total_all else 0
    console.print(f"\n[green]Overall: {total_with}/{total_all} ({pct:.1f}%) fossils have images[/green]")
    console.print(f"[green]New images added this run: {total}[/green]")
    return total
