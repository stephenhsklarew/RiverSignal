# Verification: Clinch River (VA) onboarding — STEP 3

| | |
|---|---|
| **Watershed slug** | `clinch_river_va` |
| **Display name** | Clinch River (no state suffix, per runbook §2.1) |
| **Date** | 2026-06-03 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Inventory** | `clinch_river_va-source-inventory-2026-06-01.md` |
| **Status** | **Local staging COMPLETE + verified.** Prod deploy pending §2.8 gates. |

## STEP 0 answers (user-confirmed 2026-06-03)
- Sequence: **Clinch first, then New River** (sequential).
- Prod: **go to prod this session, gated** (pause at each §2.8 gate).
- STEP 0 defaults accepted (HUC8 +0.05° buffer; stop on paid keys; gate non-commercial
  from B2B; annotate-only for untracked-basin confluence; ship v0 curation `needs_review`).

## Local staging used SAMPLE MODE (`--sample`)
All §2.3 ingests ran with `--sample` (cap ~400/source). **The row counts below are
intentionally small** — they verify each adapter/view/endpoint/surface *works*, not
prod-scale volume. The full ingest runs at §2.8 Gate 2 on prod (without `--sample`).

## §3.1 Schema counts (local, sampled)
| Table | Count | Driven by |
|---|---|---|
| silver.river_reaches | 2 | cl01 (Upper@Cleveland, Lower@Dungannon) |
| silver.flow_quality_bands | 2 | cl02 |
| curated_hatch_chart | 10 | cl03 (Shenandoah VA-Appalachian clone) |
| river_stories | 3 | cl04 (adult/kids/expert, LLM) |
| fly_shops_guides | 3 | cl05 (1 fly_shop + 2 guide_service) |
| recreation_sites | 12 | cl06 (boat_ramp 4 / fishing_access 3 / trailhead 2 / campground 2 / day_use 1) |
| sites.boundary | set (~3,290 km²) | cl07 (HUC8 06010205 only) |
| gold.species_by_reach | 15 | heavy refresh |
| gold.species_gallery | 245 | heavy refresh |
| fossil_occurrences (by-watershed) | 453 | pbdb + idigbio + gbif |
| mineral_deposits (by-watershed) | 230 | mrds |
| gold.trip_quality_daily | 182 (2 reaches × 91d) | tqs_daily_refresh |

## §3.3 API smoke (local :8001) — all green
- `/sites/clinch_river_va` → "Clinch River", bbox present, boundary non-null.
- `/trip-quality` → **watershed_tqs 84**, best_reach `clinch_river_va_lower`, confidence 100.
- `/catch-probability` → **overall 88 (excellent)**, water_temp 21.2 °C (live, Cleveland gauge —
  the temp differentiator works), flow 195 cfs, hatch 13 active, 7 game species.
- **Fish Present ↔ Catch Probability parity: HOLDS** — all 7 catch-prob species present in
  `/fishing/species` (8th, rock bass, is non-game → correctly absent).
- `/river-story` → 3,233-char adult narrative (factually grounded: 46 mussel species, etc.).
- `/recreation` → 12, `/fly-shops` → 3, `/fishing/hatch-confidence` → 12/13 insects with photos.

## §2.6.6 Playwright watershed-smoke — 12/12 PASS
Run: `WATERSHED=clinch_river_va BASE_URL=http://localhost:5173 API_BASE=http://localhost:8001/api/v1`.
**Gotcha learned:** the production `vite build` bakes in the PROD `VITE_API_BASE`, so the SPA
served by the local API (:8001) calls prod and shows nothing for a local-only watershed.
Smoke the UI via the **dev server (:5173)**, which points at the local API. (Added to follow-ups.)

## §3.6 Feature-coverage grid
| App | Feature | Status | Notes |
|---|---|---|---|
| RiverPath | Go Score / TQS | ✓ | 84 watershed, both reaches scored |
| RiverPath | River Now hero (live temp+flow) | ✓ | Cleveland gauge: temp 21.2 °C + flow live |
| RiverPath | Catch Probability | ✓ | 88, 7 game species |
| RiverPath | Fish Present (parity) | ✓ | == Catch Probability |
| RiverPath | River Story | ✓ | 3 levels, `is_draft` |
| RiverPath | Hatch | ✓ | 10 curated, 12/13 with photos |
| RiverPath | Recreation /explore | ✓ | 12 sites, all valid filter keys |
| RiverPath | Fly shops + Guides | ✓ | 3 (needs_owner_verification) |
| RiverPath | Stocking | ✗ | 0 — Clinch main stem is warm-water (not stocked); no current Clinch-basin DWR stockings (Clinch Mtn WMA waters drain to the Holston). Seasonal/sparse — P3 bead. |
| RiverSignal | Boundary / map | ✓ | HUC8-filtered union, ~3,290 km² |
| RiverSignal | Species gallery | ✓ | 245 rows |
| DeepTrail | Fossils | ✓ | 453 (sampled; full at Gate 2) |
| DeepTrail | Minerals (MRDS) | ✓ | 230 |
| DeepTrail | Mineral shops | ⚠ | 0 — no verified SW-VA shop sourced; P3 bead (don't fabricate) |
| DeepTrail | Rockhounding sites | ⚠ | 0 — high-liability, none verified; P3 bead. The Clinch is a mussel-conservation priority — collecting is sensitive. |
| RiverSignal | Wetlands (NWI) | ⚠ | 0 — transient empty / sparse ridge-valley; re-check on prod |
| RiverSignal | Restoration | ⚠ | 0 — restoration adapter is PNW-scoped (TNC/DEQ extension is a follow-on) |

## Lower-reach flow caveat
Gauge 03524740 (Dungannon) reports temperature + conductance + pH but **no discharge**, so the
Lower Clinch reach's flow sub-score degrades to no-data (honest); its bands use Cleveland as a
documented proxy. Temperature still scores. Upper Clinch (Cleveland) has full flow + temp.

## Follow-on beads (to file)
- P3: VA DWR Clinch-basin stocking is seasonal/sparse — revisit attribution + a stocking_locations
  seed when Clinch-basin waters appear in the schedule.
- P3: Clinch trout-tributary reach (Big Cedar / Indian creeks) — add an ungauged coldwater reach.
- P3: mineral_shops + rockhounding_sites for the Clinch (verified sources only).
- P2: restoration adapter — extend beyond PNW (TNC Clinch Valley / VA DEQ TMDL).
- P3: NWI wetlands returned 0 — confirm on prod (full ingest); re-run if still 0.
