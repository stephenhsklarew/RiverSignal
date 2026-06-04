# Verification: Chattahoochee (GA) onboarding — STEP 3 (Phase A)

| | |
|---|---|
| **Watershed slug** | `chattahoochee` |
| **Display name** | Chattahoochee River (no suffix) |
| **Date** | 2026-06-04 |
| **Inventory** | `chattahoochee-source-inventory-2026-05-25.md` |
| **Scope** | **PHASE A.** Live dam-release adapter (`usace_sam_hydropower`) + iNat prod firehose mitigation DEFERRED to Phase B (RiverSignal-c8155522; spec `plan-2026-06-04-chattahoochee-dam-release-safety.md`). |
| **Status** | **Local staging COMPLETE + verified.** Prod deploy pending §2.8 gates. |

Local staging used SAMPLE MODE (`--sample`) — incl. the iNaturalist firehose (~445k/5y),
capped to 400 locally; counts below are intentionally small.

## §3.1 Schema counts (local, sampled)
| Table | Count | Notes |
|---|---|---|
| silver.river_reaches | 4 | Headwaters / Lake Lanier / **Tailwater⭐** / Metro |
| silver.flow_quality_bands | 4 | Lanier = headwaters-inflow proxy |
| curated_hatch_chart | 10 | Buford tailwater + Blue Ridge baseline |
| river_stories | 3 | LLM |
| fly_shops_guides | 5 | Unicoi/Cohutta/Fish Hawk/River Through Atlanta/Reel Job |
| rockhounding_sites | 2 | **Dahlonega Gold Belt** — Crisson + Consolidated gold mines |
| recreation_sites | 12 | CRNRA + Lake Lanier + NF + state parks (valid filter keys) |
| sites.boundary | set (~6,671 km²) | GeoJSON seed, HUC8 03130001+03130002 |
| geologic_units (ga_geology) | 400 | UGA ITOS Blue Ridge metamorphic |
| mineral_deposits (mrds) | 500 | Dahlonega gold belt (the project's richest MRDS slice) |
| interventions (ga_trout) | 7 | Chattahoochee-system trout stockings (incl. Lanier Tailwater) |
| gold.trip_quality_daily | 364 (4 reaches × 91d) | |
| gold.species_by_reach | 29 | |

## §3.3 API smoke (local) — green
- `/trip-quality` → **84**, best reach `chattahoochee_lanier`.
- `/catch-probability` → **79**, **water_temp 19.9 °C** (live — tailwater + metro gauges report temp,
  unlike New River), 8 game species.
- **Fish Present ↔ Catch Probability parity HOLDS** (8 catch-prob ⊆ 15 `/fishing/species`).
- river story 3 levels; recreation 12; fly shops 5; rockhounding 2; boundary set.

## §2.6.6 Playwright watershed-smoke — 12/12 PASS (local, dev server).
## Dam-safety: static **TailwaterSafetyCard** renders on `/path/now/chattahoochee`
("Buford Dam controls this water" + USACE release-schedule + SERFC inflow links). Verified.

## §3.6 Feature-coverage grid
| App | Feature | Status | Notes |
|---|---|---|---|
| RiverPath | Go Score / TQS | ✓ | 84; 4 reaches |
| RiverPath | River Now hero (flow + temp) | ✓ | tailwater + metro gauges report temp |
| RiverPath | **Dam-release safety** | ⚠ (static) | Phase A static USACE banner on the tailwater; LIVE feed deferred to Phase B |
| RiverPath | Catch Probability / Fish Present | ✓ | 79; parity holds |
| RiverPath | River Story / Hatch / Recreation / Fly shops | ✓ | hatch flagged single-chart caveat (tailwater vs headwaters) |
| RiverPath | Stocking | ✓ | **ga_trout** (new adapter) — 7 Chattahoochee stockings from the GA DNR weekly PDF |
| RiverSignal | Boundary / Species gallery | ✓ | GeoJSON seed; gallery refreshed |
| RiverSignal | Water quality / E. coli | ✓ | WQP (GA EPD + Chattahoochee Riverkeeper); usgs param 99407 added (comes on next usgs run) |
| DeepTrail | Geology | ✓ | **ga_geology** (new adapter) 400 units + Macrostrat |
| DeepTrail | Minerals (MRDS) | ✓ | 500 — Dahlonega Gold Belt |
| DeepTrail | Rockhounding | ✓ | Dahlonega gold mines (Crisson + Consolidated) |
| DeepTrail | Fossils | ⚠ | sparse (Blue Ridge metamorphic basement — expected) |
| DeepTrail | Mineral shops | ⚠ | not curated (P3 — don't fabricate Atlanta shop details) |

## Deferred to Phase B / follow-on beads
- **Live Buford Dam release feed** (`usace_sam_hydropower` + dynamic banner) — RiverSignal-c8155522.
- **iNaturalist prod firehose** (~445k/5y) — tile-pagination + rarity-weighting (P0 UX, cross-cutting).
  Prod ingest at Gate 2 will pull a bounded window to avoid swamping at launch (see §2.8 plan).
- mineral_shops Atlanta-metro curation (P3); single-vs-two hatch charts (curator).
