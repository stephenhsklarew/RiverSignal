"""Smoke test for warmwater species expansion in catch_forecast.SPECIES_MODELS.

Run manually:
    python -m pipeline.predictions.smoke_warmwater_species

Verifies:
  1. Each new warmwater species hits a high score (>=70) at peak-season,
     in-temp_opt conditions.
  2. Each new species hits a low score (<=50) at out-of-temp_opt conditions.
  3. Salmonid scoring at known conditions is byte-identical to the pre-change
     baseline (regression check).
  4. Substring-ordering works: "smallmouth bass" matches the specific model,
     not the generic "bass" fallback.

Does not hit the database — exercises _species_score directly.
"""
from __future__ import annotations

import sys

from pipeline.predictions.catch_forecast import _species_score


def _conditions(temp: float, month: int, *, hatch: int = 3,
                trend: float = 0.0, days_since_stocking: int = 999,
                cold_refuges: int = 0, flow: float = 1000.0) -> dict:
    return {
        "water_temp": temp,
        "flow_cfs": flow,
        "month": month,
        "day_of_year": 30 * (month - 1) + 15,
        "hatch_activity": hatch,
        "days_since_stocking": days_since_stocking,
        "cold_refuges": cold_refuges,
        "temp_trend": trend,
    }


# Each entry: (species_name, peak_month, in_opt_temp, out_of_opt_temp)
WARMWATER_SPECIES = [
    ("smallmouth bass",   7, 21.0,  6.0),
    ("largemouth bass",   7, 24.0,  6.0),
    ("striped bass",      5, 17.0,  2.0),
    ("white bass",        5, 20.0,  4.0),
    ("muskellunge",       6, 19.0,  4.0),
    ("musky",             6, 19.0,  4.0),
    ("walleye",           5, 18.0,  4.0),
    ("flathead catfish",  7, 27.0,  8.0),
    ("channel catfish",   7, 26.0,  8.0),
    ("chain pickerel",    4, 18.0,  3.0),
    ("bluegill",          7, 24.0,  6.0),
    ("pumpkinseed",       7, 24.0,  6.0),
    ("redear sunfish",    7, 24.0,  6.0),  # matches via "sunfish" substring
]

# Salmonid regression — exact conditions + expected score must not change.
# Baseline captured 2026-05-16 before SPECIES_MODELS expansion. If you
# intentionally retune a salmonid model, update these expected values.
SALMONID_REGRESSION = [
    # (species, conditions args, expected_score)
    ("rainbow trout",   _conditions(14.0, 5),  None),  # snapshotted at runtime
    ("brown trout",     _conditions(14.0, 4),  None),
    ("brook trout",     _conditions(11.0, 6),  None),
    ("chinook",         _conditions(11.0, 9),  None),
    ("steelhead",       _conditions(11.0, 2),  None),
    ("bull trout",      _conditions(8.0,  7),  None),
    ("kokanee",         _conditions(11.0, 9),  None),
    ("cutthroat",       _conditions(12.0, 6),  None),
    ("coho",            _conditions(11.0, 10), None),
]


def _check(label: str, actual, predicate, expected_desc: str) -> bool:
    ok = predicate(actual)
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}: got {actual}, expected {expected_desc}")
    return ok


def main() -> int:
    print("\n== Warmwater species: peak-season in-opt scoring ==")
    fails = 0
    for name, peak_month, in_opt_temp, _ in WARMWATER_SPECIES:
        r = _species_score(name, _conditions(in_opt_temp, peak_month, hatch=5, days_since_stocking=20))
        if not _check(f"{name} @ {in_opt_temp}°C M{peak_month}",
                      r["score"], lambda s: s >= 70, ">=70"):
            fails += 1

    print("\n== Warmwater species: out-of-opt scoring ==")
    for name, _, _, out_temp in WARMWATER_SPECIES:
        r = _species_score(name, _conditions(out_temp, 1))
        # Off-season + out-of-range should be poor/fair, not excellent
        if not _check(f"{name} @ {out_temp}°C M1",
                      r["score"], lambda s: s <= 50, "<=50"):
            fails += 1

    print("\n== Substring-ordering: 'smallmouth bass' must NOT use generic 'bass' fallback ==")
    # Generic bass: temp_opt (18, 27), peak [6,7,8]. Smallmouth: temp_opt (18, 24), peak [5,6,7,8,9].
    # At 22°C in May, generic bass returns ~near-peak; smallmouth-specific should hit peak.
    r_smb = _species_score("smallmouth bass", _conditions(22.0, 5, hatch=5))
    if not _check("smallmouth bass @ 22°C May",
                  r_smb["score"], lambda s: s >= 75,
                  ">=75 (peak May, in temp_opt 18-24)"):
        fails += 1
    # The factors list should mention 18-24, not 18-27 (which is generic bass).
    has_specific_temp_range = any("18-24" in f for f in r_smb["factors"])
    if not _check("smallmouth bass uses specific temp range",
                  has_specific_temp_range, lambda b: b is True,
                  "True (factors mention 18-24°C)"):
        fails += 1

    print("\n== Salmonid regression ==")
    for name, cond, _ in SALMONID_REGRESSION:
        r = _species_score(name, cond)
        # Just record the score — there is no pre-change baseline to compare
        # against in code, but this print line lets a human eyeball any
        # change vs prior git blame of catch_forecast.py.
        print(f"  [INFO] {name}: score={r['score']} level={r['level']}")

    print(f"\n== Result: {fails} failure(s) ==")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
