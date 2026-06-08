"""Canonical fish-species naming (FEAT-026, Phase 1).

`gold.species_by_reach` is a UNION of many sources, each with its own naming, so
the same fish shows up as near-duplicates: case/whitespace ("rainbow trout" vs
"Rainbow Trout"), suffix noise ("Chinook" vs "Chinook Salmon"), subspecies
("Coastal Rainbow Trout"), and run-timing baked into the name ("Fall/Spring
Chinook", "Summer/Winter Steelhead"). `scientific_name` is unreliable (often a
common-name string or NULL), so it can't be the dedup key.

`canonicalize()` maps a raw (common_name, scientific_name) to a stable canonical
entry — `key` (dedup/curation key), `label` (display), and `run` (the run-timing
form, if any, stripped from the name so it can become a badge rather than a
separate row).

Product decision (2026-06-08): Steelhead and Rainbow Trout stay SEPARATE
canonical entries even though both are Oncorhynchus mykiss — anglers treat the
sea-run and resident forms as different fish. We only collapse the noise *within*
each form (Summer/Winter Steelhead → Steelhead; Coastal/Redband/Rainbow → Rainbow
Trout). Kokanee (landlocked Sockeye) is likewise kept separate by the same logic.
"""
from __future__ import annotations

from dataclasses import dataclass

# Leading run-timing words: stripped from the key, surfaced as `run`.
_RUN_PREFIXES = ("spring", "fall", "summer", "winter", "autumn")

# Leading descriptor words that denote a sub-form rolling up to the base
# species (NOT a run). Stripped, not recorded.
_DESCRIPTOR_PREFIXES = ("coastal", "interior", "westslope", "inland")

# Canonical display label keyed by the normalized base name (after prefix strip
# + spacing fixes). Anything not listed falls back to Title Case of the base.
_CANONICAL: dict[str, str] = {
    "chinook": "Chinook Salmon",
    "chinook salmon": "Chinook Salmon",
    "king salmon": "Chinook Salmon",
    "coho": "Coho Salmon",
    "coho salmon": "Coho Salmon",
    "silver salmon": "Coho Salmon",
    "sockeye": "Sockeye Salmon",
    "sockeye salmon": "Sockeye Salmon",
    "chum": "Chum Salmon",
    "chum salmon": "Chum Salmon",
    "pink salmon": "Pink Salmon",
    "kokanee": "Kokanee",            # landlocked sockeye — kept separate (form)
    "kokanee salmon": "Kokanee",
    "steelhead": "Steelhead",        # anadromous O. mykiss — separate from rainbow
    "rainbow": "Rainbow Trout",
    "rainbow trout": "Rainbow Trout",
    "redband": "Rainbow Trout",      # resident subspecies → rainbow
    "redband trout": "Rainbow Trout",
    "cutthroat": "Cutthroat Trout",
    "cutthroat trout": "Cutthroat Trout",
    "musky": "Muskellunge",
    "muskellunge": "Muskellunge",
    "walleye": "Walleye",
    "walleyed pike": "Walleye",
}


@dataclass(frozen=True)
class Canon:
    key: str           # dedup + curation key (lowercased canonical label)
    label: str         # display common name
    run: str | None    # run-timing form if the raw name carried one


def canonicalize(
    common_name: str | None,
    scientific_name: str | None = None,
    overrides: dict[str, str] | None = None,
) -> Canon:
    raw = " ".join((common_name or "").split())

    # Admin override (gold.species_aliases) wins — handles the long tail the
    # deterministic rules below can't infer (e.g. "Columbia River Redband
    # Trout"). `overrides` maps a lowercased raw name → canonical display label.
    if overrides:
        ov = overrides.get(raw.lower())
        if ov:
            return Canon(key=ov.lower(), label=ov, run=None)

    base = raw.lower()
    run: str | None = None

    # Strip one leading run-timing word (record it).
    for p in _RUN_PREFIXES:
        if base.startswith(p + " "):
            run = p
            base = base[len(p) + 1:]
            break

    # Strip one leading descriptor word (sub-form → base species).
    for p in _DESCRIPTOR_PREFIXES:
        if base.startswith(p + " "):
            base = base[len(p) + 1:]
            break

    # Spacing nicknames.
    base = base.replace("small mouth", "smallmouth").replace("large mouth", "largemouth")

    label = _CANONICAL.get(base, base.title() if base else raw.title())
    return Canon(key=label.lower(), label=label, run=run)
