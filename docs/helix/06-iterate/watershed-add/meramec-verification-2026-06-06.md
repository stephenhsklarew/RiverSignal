# Verification: Meramec River (Missouri) — Phase A (local, pre-deploy)

| | |
|---|---|
| **Watershed** | `meramec` (Meramec River) |
| **Date** | 2026-06-06 |
| **Branch** | `feat/onboard-meramec-phase-a` |
| **Inventory** | `docs/helix/06-iterate/watershed-add/meramec-source-inventory-2026-06-05.md` |
| **Status** | Step 2 complete locally; **stopped at §2.8 Gate 1** (push-to-main) awaiting approval. All data verified on the local DB; prod ingest happens at Gate 2. |

Local staging used `--sample` per runbook §2.3, so bronze counts are intentionally small (presence, not McKenzie-scale volume); real volumes land after the Gate-2 prod ingest.

## §3.1 Schema counts (local DB, sampled)

| Table | Count | Notes |
|---|---|---|
| `observations` | 674 | iNat + USGS + biodata + WQP (sampled) |
| `time_series` | 38,190 | USGS gauges (4) + NWS |
| `geologic_units` (source=`mo_geology`) | 400 | **new MGS adapter** — live MGS Bedrock service |
| `mineral_deposits` | 500 | MRDS — Old Lead Belt / Washington Co. barite (485 w/ commodity images) |
| `fossil_occurrences` | 1,096 | PBDB + iDigBio + GBIF (Mississippian crinoids) |
| `fossils_with_images` | **0** | ⚠ fossil-images backfill is a separate monthly job — runs at §2.8 Gate 2 |
| `impaired_waters` | 516 | EPA ATTAINS — **incl. Big River lead/sediment 303(d)** |
| `silver.river_reaches` | 4 | Upper / Middle / Lower / Big River |
| `silver.flow_quality_bands` | 4 | USGS daily-value percentiles |
| `gold.trip_quality_daily` | 364 | 4 reaches × 91 days |
| `curated_hatch_chart` | 12 | Ozark smallmouth + Maramec Spring trout |
| `fly_shops_guides` | 5 | Feather-Craft + 2 guides + 2 outfitters |
| `rockhounding_sites` | 2 | Washington Co. barite/tiff + Steelville gravel-bar chert |
| `recreation_sites` (`curated_meramec_v0`) | 12 | MO state parks + Mark Twain NF + MDC areas |
| `river_stories` | 3 | adult/kids/expert (LLM, Meramec-specific) |
| `gold.species_gallery` | 324 | photos present |
| `gold.species_by_reach` | 20 | |

## §3.2 Integrity invariants

- ✅ Reach centroids inside bbox: **4/4**
- ✅ Flow-band ordering (`low ≤ ideal_low ≤ ideal_high ≤ high`): **4/4**
- ✅ `gold.trip_quality_daily.tqs ∈ [0,100]`: **364/364**
- ✅ All 4 reach `primary_usgs_site_id` are real NWIS gauges (07014000 / 07014500 / 07019000 / 07018500)

## §3.3 API smoke (local :8001 unless noted)

| Endpoint | Result |
|---|---|
| `/sites/meramec` | ✅ "Meramec River" / meramec |
| `/reaches?watershed=meramec` | ✅ 4 reaches |
| `/trip-quality` | ✅ watershed_tqs **84** |
| `/sites/meramec/conditions/live` | ✅ 4 gauges / 6 readings *(fresh build :8002; stale :8001 returned 0 pre-WS_GAUGES)* |
| `/sites/meramec/weather` | ✅ 8 NWS periods *(fresh build :8002)* |
| `/sites/meramec/recreation` | ✅ 12 |
| `/sites/meramec/species` | ✅ 324 |
| `/sites/meramec/river-story` | ✅ 3,526 chars, Meramec-specific (no stale fallback) |
| `/sites/meramec/catch-probability` | ✅ overall **79**, 8 species, live water_temp **22.2 °C** (Huzzah 07014000) |
| `/sites/meramec/story` (timeline) | ⚠ 0 events (cross-watershed MV sparse for new watershed) |
| **Fish Present ↔ Catch Probability parity** | ✅ holds — all 8 catch-prob species present in `/fishing/species`, cp non-empty |

## §3.6 Feature-coverage grid

| App | Feature | Status | Notes |
|---|---|---|---|
| RiverSignal | Site dashboard | ✓ | 4 gauges, 38k time-series |
| RiverSignal | Water quality | ✓ | WQP MO providers |
| RiverSignal | 303(d) impaired | ✓ **standout** | Big River lead/sediment TMDL in ATTAINS |
| RiverSignal | Fish-consumption advisory | ✓ | Big River reach health note (me01) |
| RiverPath | Go Score | ✓ | TQS 84; 4 reaches; live temp at Huzzah, proxy elsewhere |
| RiverPath | River Now hero | ✓ | conditions + weather (fresh build) |
| RiverPath | River Story | ✓ | LLM 3 levels |
| RiverPath | Hatch | ✓ | 12 spp (needs_entomologist_review) |
| RiverPath | Catch Probability / Fish Present | ✓ | 8 species, parity holds |
| RiverPath | Stocking | ✗ | **No MDC machine-readable source** — P2 bead (manual seed / scraper) |
| RiverPath | Recreation / Explore | ✓ | 12 curated (MO parks not in RIDB) |
| RiverPath | Fly shops / guides | ✓ | 5 (needs_owner_verification) |
| RiverPath | Snowpack | ✗ | none in MO (expected) |
| DeepTrail | Geology | ✓ | **mo_geology** (400) + Macrostrat |
| DeepTrail | Caves/karst | ✓ | mineral/geology + curated |
| DeepTrail | Fossils | ⚠ | 1,096 records, **0 images** until fossil-images job (Gate 2) |
| DeepTrail | Minerals | ✓ **standout** | 500 MRDS — Old Lead Belt + barite |
| DeepTrail | Rockhounding | ⚠ | 2 conservative sites (galena excluded — contamination/liability) |

## Follow-on beads (from ⚠ / ✗)

- **P2** — Author a Missouri stocking adapter (`missouri`) or curated seed: MDC publishes no machine-readable stocking feed (HTML newsroom + phone hotline only). 4 trout parks + St. Louis winter-trout lakes. Inventory §1.4.
- **P2** — Run `riversignal-fossil-images` at Gate 2 so Meramec fossils get images (currently 0; the recurring miss).
- **P3** — `mineral_shops` seed (no verifiable St. Louis shops surfaced this pass).
- **P3** — Maramec Spring trout vs. warmwater-float two-mode hatch chart split (entomologist review).
- **P3** — Meramec-specific splash/DeepTrail photos (currently a verified v0 placeholder).

## Remaining before "done"

- **§2.6.6 Playwright browser smoke** not run in this session; all of its underlying API assertions verified above. Recommend running `WATERSHED=meramec BASE_URL=http://localhost:5173 npx playwright test tests/watershed-smoke.spec.ts` against the dev server before/at Gate 1.
- **§2.8 Gates 1–4** (push → CI deploy → prod one-shot ingest incl. fossil-images → freshness cache bust) — all gated on explicit user approval.
- **§2.7 `terraform apply`** — `mo_geology -w meramec` arg committed; apply is a separate gated step (full plan first).
