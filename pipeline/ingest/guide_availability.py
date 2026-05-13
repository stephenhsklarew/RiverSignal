"""Weekly guide-availability scrape into bronze.guide_availability.

Plan §3.0d. Per-guide adapter classes parse public booking pages. The
guide_id keys are stable hand-picked identifiers ('worldcast_mckenzie',
'patagonia_guides_deschutes', etc.); the seed list lives in
pipeline/ingest/guide_sources.yaml.

The opt-out list at pipeline/ingest/guide_optout.yaml is consulted on
every run; listed guide_ids are skipped immediately.

Each adapter is a small function returning a list of dicts:
    { reach_id, target_date, availability_pct, source_url }

The runner inserts those into bronze.guide_availability with the
guide_id. Daily-granularity UNIQUE index lives on the generated
fetched_date column so re-running the same day doesn't duplicate rows.

v1 ships with a stub adapter set so the pipeline runs end-to-end;
real adapters get added per-guide as opt-in agreements come in.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Callable

from sqlalchemy import text

from pipeline.db import engine


CONFIG_DIR = Path(__file__).resolve().parent / "guide_config"


def _load_yaml(name: str) -> list:
    p = CONFIG_DIR / name
    if not p.exists():
        return []
    # Tiny YAML reader without a dependency: assume the file is a list of
    # plain strings on individual lines, '#' for comments.
    out: list[str] = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            out.append(line[2:].strip())
        else:
            out.append(line)
    return out


def _adapter_stub(guide_id: str) -> list[dict]:
    """Stub adapter used when no real scraper exists for a guide.

    Returns an empty list so the runner is a no-op. Real adapters
    return dicts with reach_id / target_date / availability_pct.
    """
    return []


# Registry of guide_id → adapter function. Wire real scrapers here.
ADAPTERS: dict[str, Callable[[str], list[dict]]] = {}


def run() -> dict[str, int]:
    sources = _load_yaml("sources.txt")
    optout = set(_load_yaml("optout.txt"))
    written = 0
    skipped = 0

    with engine.connect() as conn:
        for guide_id in sources:
            if guide_id in optout:
                skipped += 1
                continue
            adapter = ADAPTERS.get(guide_id, _adapter_stub)
            try:
                rows = adapter(guide_id)
            except Exception as e:
                print(f"[guide-avail] {guide_id} adapter failed: {e}")
                continue
            for row in rows:
                conn.execute(text("""
                    INSERT INTO bronze.guide_availability
                        (guide_id, reach_id, target_date, availability_pct, source_url)
                    VALUES (:gid, :rid, :td, :avail, :url)
                """), {
                    "gid": guide_id, "rid": row["reach_id"],
                    "td": row["target_date"], "avail": row.get("availability_pct"),
                    "url": row.get("source_url"),
                })
                written += 1
        conn.commit()
    return {"sources_configured": len(sources), "skipped_optout": skipped, "rows_written": written}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
    sys.exit(0)
