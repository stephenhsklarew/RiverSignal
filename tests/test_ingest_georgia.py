"""Unit tests for the ga_trout stocking parser/attribution (pure functions, no network)."""
import re

from pipeline.ingest.georgia import _ROW_RE, _is_chattahoochee_water


# Representative lines from the live GA DNR weekly stocking PDF (statewide).
SAMPLE_LINES = [
    "5/26/2026 White Chattahoochee River",
    "5/26/2026 Forsyth/Gwinnett Lanier Tailwater",
    "5/26/2026 Habersham Soque River",
    "5/29/2026 White Chattahoochee River (WMA)",
    "5/29/2026 White Smith Creek",
    "5/29/2026 White Low Gap Creek",
    # NOT Chattahoochee basin — must be excluded:
    "5/28/2026 Lumpkin Etowah River",          # Coosa/Alabama basin
    "5/27/2026 Union Nottely River",           # TVA/Hiwassee basin
    "5/29/2026 Fannin Toccoa River (F)",       # TVA basin
    "5/26/2026 Rabun Warwoman Creek",          # Savannah/Chattooga basin
    "5/29/2026 Hart Hartwell Tailwaters",      # Savannah basin
]


def test_row_regex_parses_date_county_waterbody():
    m = _ROW_RE.match("5/26/2026 Forsyth/Gwinnett Lanier Tailwater")
    assert m and m.group(1) == "5/26/2026"
    assert m.group(2) == "Forsyth/Gwinnett"   # county is one token, slash-pair OK
    assert m.group(3) == "Lanier Tailwater"


def test_chattahoochee_attribution_includes_basin_waters():
    assert _is_chattahoochee_water("Chattahoochee River", "White")
    assert _is_chattahoochee_water("Chattahoochee River (WMA)", "White")
    assert _is_chattahoochee_water("Lanier Tailwater", "Forsyth/Gwinnett")  # Buford tailwater
    assert _is_chattahoochee_water("Soque River", "Habersham")
    assert _is_chattahoochee_water("Smith Creek", "White")     # county-guarded ambiguous
    assert _is_chattahoochee_water("Low Gap Creek", "White")


def test_chattahoochee_attribution_excludes_other_basins():
    assert not _is_chattahoochee_water("Etowah River", "Lumpkin")       # Coosa basin
    assert not _is_chattahoochee_water("Nottely River", "Union")        # Hiwassee basin
    assert not _is_chattahoochee_water("Toccoa River (F)", "Fannin")    # TVA basin
    assert not _is_chattahoochee_water("Warwoman Creek", "Rabun")       # Savannah basin
    assert not _is_chattahoochee_water("Smith Creek", "Rabun")          # ambiguous in non-Chatt county


def test_full_sample_filters_to_chattahoochee_only():
    kept = []
    for line in SAMPLE_LINES:
        m = _ROW_RE.match(line.strip())
        assert m, f"row regex failed on: {line}"
        _date, county, waterbody = m.group(1), m.group(2), m.group(3).strip()
        if _is_chattahoochee_water(waterbody, county):
            kept.append(waterbody)
    assert "Lanier Tailwater" in kept
    assert "Chattahoochee River" in kept
    assert "Etowah River" not in kept
    assert "Toccoa River (F)" not in kept
    assert len(kept) == 6  # the 6 Chattahoochee-system rows above
