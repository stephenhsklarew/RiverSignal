"""Sample mode — cap how many records each adapter pulls, for LOCAL staging only.

Onboarding a new watershed used to mean pulling the *full* volume from every
source locally (iNaturalist alone has run to 260k+ observations for a single
bbox, NHDPlus to 100k+ flowlines). That's wasteful when all you want locally is
to confirm each adapter, view, endpoint, and UI surface *works* before deploying
to prod, where the real (full) ingest runs.

Sample mode sets a process-global per-source record cap. The CLI turns it on via
`--sample` (`pipeline.cli ingest ... --sample [--sample-max N]`). Adapters and the
shared ArcGIS helpers consult it to (a) truncate a fetched result list, (b) break
out of a pagination loop early, or (c) clamp an API page-size parameter.

NEVER enable this in the Cloud Run jobs — it is a local-staging convenience only.
Prod must always ingest the full source.
"""

# Process-global cap. None = sampling disabled (pull everything, the default).
_SAMPLE_LIMIT: int | None = None

# Default cap when `--sample` is given without `--sample-max`. Small on purpose:
# enough rows to exercise every parse/write path and light up each UI surface,
# far below 10% of any real source's volume.
DEFAULT_SAMPLE_MAX = 400


def set_sample(limit: int | None) -> None:
    """Set (or clear, with None) the global per-source record cap."""
    global _SAMPLE_LIMIT
    _SAMPLE_LIMIT = limit


def sample_limit() -> int | None:
    """Current per-source cap, or None when sampling is disabled."""
    return _SAMPLE_LIMIT


def is_sampling() -> bool:
    return _SAMPLE_LIMIT is not None


def cap_records(seq):
    """Truncate a fetched list to the sample cap (no-op when disabled).

    Use right after a single-shot fetch, before the write loop:
        records = cap_records(records)
    """
    if _SAMPLE_LIMIT is None:
        return seq
    return seq[: _SAMPLE_LIMIT]


def clamp_page(default: int) -> int:
    """Clamp an API/ArcGIS page-size to the cap (no-op when disabled).

    Use where an adapter sets per_page / resultRecordCount / limit:
        per_page = clamp_page(PAGE_SIZE)
    """
    if _SAMPLE_LIMIT is None:
        return default
    return min(default, _SAMPLE_LIMIT)


def should_stop(count_so_far: int) -> bool:
    """True once enough records have been pulled to stop paginating.

    Use at the bottom of a pagination loop:
        if should_stop(created):
            break
    """
    if _SAMPLE_LIMIT is None:
        return False
    return count_so_far >= _SAMPLE_LIMIT
