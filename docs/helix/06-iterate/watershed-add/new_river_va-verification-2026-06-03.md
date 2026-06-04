# Verification: New River (VA) onboarding — STEP 3

| | |
|---|---|
| **Watershed slug** | `new_river_va` |
| **Display name** | New River (no state suffix) |
| **Date** | 2026-06-03 |
| **Inventory** | `new_river_va-source-inventory-2026-06-01.md` |
| **Status** | **Local staging COMPLETE + verified.** Prod deploy pending §2.8 gates. |

## Local staging used SAMPLE MODE (`--sample`) — counts are small by design.

## §3.1 Schema counts (local, sampled)
| Table | Count | Notes |
|---|---|---|
| silver.river_reaches | 3 | Upper@Galax / Claytor Lake@Allisonia / Lower@Radford |
| silver.flow_quality_bands | 3 | from gauge percentiles (600–5,500 cfs — large river) |
| curated_hatch_chart | 10 | Appalachian baseline (secondary — warm-water forage fishery) |
| river_stories | 3 | LLM adult/kids/expert |
| fly_shops_guides | 5 | strongest guide market of the four |
| recreation_sites | 12 | New River Trail SP + Claytor Lake SP + DWR ramps (valid filter keys) |
| sites.boundary | set (~7,200 km²) | GeoJSON seed, HUC8 05050001+05050002 |
| gold.species_by_reach | 20 | |
| gold.trip_quality_daily | 273 (3 reaches × 91d) | |

## §3.3 API smoke (local) — green
- `/trip-quality` → **watershed_tqs 84**, best reach `new_river_va_claytor`.
- `/catch-probability` → **65**, **water_temp = None (degrades cleanly — New's known
  no-mainstem-temp gap)**, flow 692 cfs, **9 game species**. Score still computes from flow + season.
- **Fish Present ↔ Catch Probability parity HOLDS** (9 catch-prob species ⊆ 11 `/fishing/species`).
- river story 3 levels; recreation 12; fly shops 5; boundary set.

## §2.6.6 Playwright watershed-smoke — 12/12 PASS (local, via dev server :5173).

## §3.6 Feature-coverage grid
| App | Feature | Status | Notes |
|---|---|---|---|
| RiverPath | Go Score / TQS | ✓ | 84; all 3 reaches scored (flow-only) |
| RiverPath | River Now hero — flow | ✓ | 5 gauges, all discharge |
| RiverPath | River Now hero — water temp | ✗ | NO mainstem gauge reports temp → "no data" (the New's known gap; renders cleanly) |
| RiverPath | Catch Probability | ✓ | 65, 9 species (no temp factor) |
| RiverPath | Fish Present (parity) | ✓ | == Catch Probability |
| RiverPath | River Story / Hatch / Recreation / Fly shops | ✓ | hatch is secondary (forage fishery) |
| RiverSignal | Boundary / Species gallery | ✓ | GeoJSON seed; gallery 20+ |
| DeepTrail | Fossils / Minerals | ✓ | pbdb+idigbio+gbif / mrds (full at Gate 2) |
| DeepTrail | Mineral shops / Rockhounding | ⚠ | not curated (P3, don't fabricate) |

## Known gaps / follow-on beads (to file)
- **No mainstem water temperature** — temp sub-score is "no data" (inherent; would need a
  non-USGS temp source or a modeled estimate). P3.
- Hatch chart is a generic Appalachian baseline — a **forage/seasonal-presentation** model fits
  this warm-water river better. P3.
- mineral_shops / rockhounding_sites not curated. P3.
- restoration adapter PNW-scoped (New got 265 rows locally — better than Clinch; still verify).
- Claytor Lake: **Alabama bass** invasive flag noted in the reach.
