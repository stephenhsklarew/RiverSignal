# Verification Report: Mad River (Ohio) — `mad_river_oh`

| | |
|---|---|
| **Watershed slug** | `mad_river_oh` |
| **Display label** | Mad River (OH) |
| **States** | OH |
| **Date** | 2026-05-30 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Step 1 inventory** | `mad_river_oh-source-inventory-2026-05-25.md` |
| **Branch** | `add-watershed/mad_river_oh` (9 commits) |
| **Scope this session** | **Local-only** — built + verified locally. Prod deploy (terraform apply, push, prod job-execute, freshness POST) **DEFERRED** to a later session per the user's Step-0 Q6 revision. |

---

## Summary

Mad River (OH) — the platform's **first Midwest / Ohio-River-Basin watershed** — is
fully onboarded and verified **locally**. The §3.6 feature-coverage grid below shows ✓ on
every surface McKenzie lights up, except the documented OH-specific gaps (WQP/wetlands
returned 0 for the bbox; restoration/fire are PNW-or-N/A) which are captured as follow-on
beads.

**Headline:** `gold.trip_quality_daily` = **273 rows (3 reaches × 91 days)**, matching the
McKenzie reference shape. All **12 Playwright UX smoke tests pass** for `mad_river_oh`.

**Update 2026-05-30 — P1/P2 bead pass complete (commits `7278149`..`ba4d5b1`).** All ten
P1/P2 follow-on beads were addressed (see "P1/P2 bead resolution" below). Net effect on the
grid: Water Quality, Stocking, River-Story-timeline, and ODGS Geology all moved to ✓.
Wetlands and the fish-passage/restoration source integrations remain genuinely deferred with
precise diagnoses. Two real latent bugs were fixed along the way (restoration `State='OR'`
hardcode; WQP/ArcGIS adapters now retry transient outages).

### Environment notes (local DB was mid-repair)
The local DB (`postgresql@17` on :5433) was stopped and its `alembic_version` sat ahead of
actual schema. Three pre-existing missing objects had to be re-created from their canonical
migration DDL before the chain could reach head and TQS could run (all idempotent
`CREATE/ADD ... IF NOT EXISTS`, full backup taken first → `backups/local-20260530-preonboard-madriver.dump`):
`gold.curated_species_photos`, `public.data_status_cache`, and the
`gold.trip_quality_daily.forecast_inputs_payload` column. **None are Mad-River-specific** —
they are local-DB drift and are already covered by committed migrations (`uu21`, `a1c2d3e4f5b6`,
`x5b6c7d8e9f0`); prod, being at head, already has them. The full `pipeline refresh` also stalls
for hours in the optional `refresh_predictions()` step on this local DB (non-sargable
DOY-average full scans over 9.5M `time_series` rows); the medallion MV refreshes themselves are
fast (3–6 s each) and were run directly.

---

## §3.1 Bronze / curated row counts (local DB, 2026-05-30)

| Table | Rows (mad_river_oh) | Driven by |
|---|---:|---|
| `time_series` | 282,518 | usgs + prism + biodata + wqp_bugs |
| `observations` | 267,072 | inaturalist + usgs + biodata + gbif |
| `stream_flowlines` | 9,102 | nhdplus |
| `fossil_occurrences` | 1,838 | pbdb (142) + idigbio + gbif |
| `impaired_waters` | 148 | impaired (EPA ATTAINS) — **smoke-test passed** |
| `mineral_deposits` | 165 | mrds |
| `watershed_boundaries` | 144 | wbd |
| `geologic_units` | ✓ (bbox) | macrostrat (23 new in bbox) |
| `recreation_sites` | 10 | curated `curated_mad_river_oh_v0` (RIDB sparse for OH) |
| `geologic_units` (odgs) | 561 | **ODGS 24K adapter (P1 bead)** |
| `interventions` (fish_stocking) | 2 | **brown-trout C&R seed (P1 bead, mr10)**; ohio_stocking put-and-take feed has no Mad-River rows |
| `wetlands` | **0** | nwi — data exists (25,696 polys) but MapServer times out on dense geometry; needs state-geodatabase bulk load (see beads) |

### Curated seeds (alembic)
| Table | Rows | Flag |
|---|---:|---|
| `silver.river_reaches` | 3 | needs_guide_review |
| `silver.flow_quality_bands` | 3 | from real USGS p10/p30/p70/p90 |
| `curated_hatch_chart` | 10 | needs_entomologist_review |
| `fly_shops_guides` | 2 | needs_owner_verification |
| `mineral_shops` | 0 | intentional (no fabrication) |
| `rockhounding_sites` | 3 | viewing/permission-required |
| `river_stories` | 3 | adult/kids/expert (regenerated Ohio-correct) |

## Gold tables surfacing Mad River
| MV | Rows (mad_river_oh) |
|---|---:|
| `gold.species_gallery` | 10,999 |
| `gold.hatch_chart` | 4,452 |
| `gold.swim_safety` | 442 |
| `gold.trip_quality_daily` | **273** (3 reaches × 91 days) |
| `gold.species_by_reach` | 115 |
| `gold.stocking_schedule` | **2** (after P1 bead — ohio_dnr brown-trout) |
| `gold.water_quality_monthly` | **9,753** (after P1 wqp bead) |
| `gold.river_story_timeline` | **148** (after P2 bead) |
| `geologic_units (odgs)` | **561** (after P1 ODGS bead) |
| `gold.river_health_score` | not re-measured — the local refresh of this MV is pathologically slow (29 min+; seasonal temp aggregation over 9.5M rows). Prod-grade DB refreshes it normally. |

TQS by reach: `mad_river_oh_lower` avg 70 · `mad_river_oh_trout_section` avg 57 ·
`mad_river_oh_upper` avg 58. Watershed TQS (today) = 64, best reach = `mad_river_oh_lower`.

---

## §3.3 API smoke (local :8001) — all non-error

| Endpoint | Result |
|---|---|
| `/sites/mad_river_oh` | ✓ `{name:"Mad River", watershed:"mad_river_oh"}` |
| `/reaches?watershed=` | ✓ 3 |
| `/trip-quality?date=…` | ✓ watershed_tqs 64, best `mad_river_oh_lower` |
| `/sites/…/conditions/live` | ✓ gauge_count 2, 3 readings |
| `/sites/…/weather` | ✓ 8 periods (NWS ILN gridpoint) |
| `/sites/…/recreation` | ✓ 10 |
| `/sites/…/species` | ✓ 5,000 (capped) |
| `/sites/…/river-story` | ✓ Ohio-correct narrative |
| `/sites/…/story` (timeline) | ⚠ 0 events (sparse OH interventions — see gaps) |

`sites.boundary` is set in the DB (1 geometry); the `/sites/{w}` JSON omits it by design
(parity with shenandoah — the map fetches it via a separate endpoint).

## §2.6.6 Playwright UX smoke — **12/12 pass**
`WATERSHED=mad_river_oh npx playwright test tests/watershed-smoke.spec.ts` → splash card +
image, river story (Ohio, not Deschutes/McKenzie), stocking map, catch-probability species,
hatch photos, /path/explore cards, saved heart, boundary non-null, homepage map < 30 s,
species gallery > 0, rocks (fossils/minerals) > 0, /trail picker lists "Mad River (OH)".

---

## §3.6 Feature-coverage grid (vs the McKenzie reference)

| App | Feature | Has data? | Notes |
|---|---|---|---|
| RiverSignal | Site dashboard | ✓ | 2 active gauges + 17 ancillary; 282k time-series |
| RiverSignal | Scorecard | ✓ | watershed_scorecard populated |
| RiverSignal | Water quality | ✓ | **RESOLVED (P1)** — transient WQP outage masked the data; 10,475 owdp rows / 187 stations. `gold.water_quality_monthly` OH 0 → **9,753**. Adapter hardened (5xx retry). |
| RiverSignal | Macroinvertebrates | ✓ | wqp_bugs 748 |
| RiverSignal | 303(d) impaired | ✓ | ATTAINS bbox query → 148 assessment units (inventory's predicted fix was unnecessary — adapter is bbox-based, not HUC) |
| RiverSignal | Wetlands | ⚠ | `nwi` data exists (25,696 polys for bbox) but the USFWS NWI MapServer **times out on dense Eastern-US geometry** (90s for even 500 polys); also affects shenandoah. Adapter hardened for transient; **bulk geometry load needs the USFWS state geodatabase** (refined bead below). |
| RiverSignal | Restoration | ✗ | **P2 addressed** — fixed the `State='OR'` hardcode (was excluding all non-OR watersheds); NOAA Atlas genuinely has 0 projects in the OH bbox. OH 319/SWIF/H2Ohio = larger follow-on. |
| RiverSignal | Fire recovery | ✗ (N/A) | no significant W-central OH wildfire footprint — graceful empty |
| RiverSignal | Geometry/boundary | ✓ | wbd 144 HUC12s; sites.boundary set |
| RiverPath | Go Score + ranking | ✓ | trip_quality_daily 273; watershed pill 64 |
| RiverPath | River Now hero | ✓ | live USGS + NWS ILN |
| RiverPath | Hatch tab | ✓ | 10 curated (needs_entomologist_review) → gold.hatch_chart 4,452 |
| RiverPath | River Story | ✓ | 3 reading levels, Ohio-correct |
| RiverPath | Species cards | ✓ | species_gallery 10,999 (from 267k obs) |
| RiverPath | Photo observations | ✓ | iNaturalist 264,928 obs |
| RiverPath | Stocking | ✓ | **RESOLVED (P1)** — curated brown-trout C&R program seeded (mr10); `gold.stocking_schedule` MV extended with ohio_dnr branch (mr11) → **2 OH rows** surface in the panel + pinned on the map. |
| RiverPath | Swim safety | ✓ | swim_safety 442 |
| RiverPath | Snowpack | ✗ (N/A) | SNOTEL is Western-US only — Mad is spring-fed |
| RiverPath | Recreation / explore | ✓ | 10 curated sites (RIDB misses ODNR/ReserveOhio) |
| RiverPath | Fly shops / guides | ✓ | 2 (Mad River Outfitters; Buckeye United Fly Fishers) |
| RiverPath | River Story timeline | ✓ | **RESOLVED (P2)** — `gold.river_story_timeline` OH 0 → **148** after the stocking/WQ events landed. |
| RiverPath | Fish passage | ✗ | **P2 diagnosed** — the `fish_passage` adapter source is **ODFW Oregon-only** (`nrimp.dfw.state.or.us`), NOT the national USFWS NFPP feed the inventory assumed. OH coverage needs a new national source or a curated seed (refined bead below). |
| DeepTrail | Geology units | ✓ | **UPGRADED (P1)** — macrostrat **+ new ODGS 24K adapter** (561 bedrock unit polygons, source='odgs'). Much sharper than Macrostrat for OH. |
| DeepTrail | Fossil sites | ⚠→✓ | 1,838 occurrences (pbdb 142 Ord/Sil/Dev carbonate ✓ inventory predicted ~129). **CORRECTION 2026-06-01:** all 1,838 had **0 images** — the `fossil-images` backfill (separate monthly job, never run since onboarding) was missed at launch. Triggered `riversignal-fossil-images` to backfill; runbook §2.8 Gate 2 + §3.6 updated so this is a launch step going forward. |
| DeepTrail | Mineral deposits | ✓ | mrds 165 (industrial carbonate) |
| DeepTrail | Rockhound sites | ⚠ | 3 conservative viewing/permission entries |
| DeepTrail | Mineral & rock shops | ✗ | 0 (intentional — curator research needed) |

---

## P1/P2 bead resolution (addressed 2026-05-30, commits `7278149`..`ba4d5b1`)

All ten P1/P2 beads were worked. Outcomes:

| Pri | Bead | Outcome |
|---|---|---|
| **P1** | Mad River brown-trout STREAM stocking | ✅ **DONE** — `mr10` seeds 2 curated Oct C&R events (~11,500 yearlings) as `interventions(source=ohio_dnr)` + a `stocking_locations` pin. needs_review. |
| **P1** | Extend `gold.stocking_schedule` UNION ohio_dnr | ✅ **DONE** — `mr11` adds the ohio_dnr branch (mirrors hh08 va_dwr). MV shows **2 OH rows**. |
| **P1** | `wqp`/owdp = 0 | ✅ **DONE** — root cause was a **transient WQP 5xx outage** during the batch, not a scoping bug: the bbox has 187 OH stations / 10,475 results (`21OHIO_WQX` + USGS-OH). owdp.py hardened with 5xx/backoff retry; `gold.water_quality_monthly` OH 0 → **9,753**. |
| **P1** | `nwi` wetlands = 0 | ⚠️ **PARTIAL** — also transient at batch time, but the deeper issue is the USFWS NWI MapServer **times out on dense Eastern-US geometry** (90s for 500 polys; data = 25,696). `_arcgis_query` hardened (retry on 5xx/non-JSON/network). Full bulk load needs the **USFWS NWI state geodatabase download** (not the live MapServer) — see remaining beads. |
| **P1** | ODGS 24K geology adapter | ✅ **DONE** — `ODGSAdapter` (geology.py) + full wiring; **561 unit polygons** ingested. |
| **P2** | `restoration.py` OH | ✅ **ADDRESSED** — fixed the `State='OR'` hardcode (real latent bug). NOAA Atlas has 0 projects in the OH bbox; EPA §319/SWIF/H2Ohio = larger follow-on. |
| **P2** | `fish_passage` OH | ✅ **DIAGNOSED** — the adapter source is **ODFW Oregon-only**, not the national NFPP feed the inventory assumed. No OH data without a new source; not fabricated. See remaining beads. |
| **P2** | `odnr_regs` seed | ✅ **DONE** — `mr12` appends the C&R special-reg note to the trout-section reach. |
| **P2** | DataOhio dataset discovery | ✅ **CLOSED** — `data.ohio.gov` exposes no programmatic API (CKAN action endpoint 404; no data.gov entry). Tableau/PowerBI embed only; not adapter-able without scraping. Deferred. |
| **P2** | `gold.river_story_timeline` = 0 | ✅ **DONE** — once the stocking/WQ events landed and the MV was refreshed, OH = **148**. |

## Remaining follow-on beads (genuinely deferred)

| Pri | Bead | Why deferred |
|---|---|---|
| **P1→P2** | NWI wetlands bulk load via the USFWS **state geodatabase** (or a tiled small-bbox crawl) | the live MapServer can't serve dense OH geometry within timeouts |
| **P2** | EPA §319 grants + OEPA SWIF + H2Ohio restoration integration | new source adapters; NOAA Atlas has no inland-OH projects |
| **P2** | National fish-passage source (USFWS NFPP / dam inventory) or curated Mad River barrier seed | existing adapter is Oregon-only |
| **P3** | ReserveOhio state-parks scrape (Buck Creek SP campground, Kiser Lake SP) | RIDB covers USACE C.J. Brown; ODNR has no public API |
| **P3** | mineral_shops + more rockhounding/fly-shop curator research (Columbus/Dayton/Springfield) | no fabrication — needs verified listings |
| **chore** | Stale test `tests/test_api.py::test_list_sites` asserts `== 5` (DB has 9 watersheds) — pre-existing, unrelated | — |
| **chore** | Kids river-story slightly misreads "11,500 stocked brown trout" as a species count — curator pass | — |

---

## Deferred to the prod-deploy session (NOT done this session — local-only scope)

- [ ] `terraform apply` (weekly-job arg already authored in `cloud_run_jobs.tf`, **not applied**)
- [ ] Gate 1: push branch → main → CI deploy
- [ ] Gate 2: execute prod Cloud Run jobs (daily/weekly/monthly/tqs) for mad_river_oh
- [ ] Gate 3: POST `/api/v1/data-status/refresh` on prod
- [ ] Trigger `riversignal-pipeline-monthly` on prod (local ran pbdb/idigbio/gbif/mrds directly)
- [ ] Re-run Playwright smoke against prod `BASE_URL`

Each prod gate requires explicit per-gate user approval per runbook §2.8.

---

## Deliverables checklist

- [x] Step 1 source inventory (pre-existing, Step-0 transcript appended)
- [x] Watershed config in `pipeline/config/watersheds.py`
- [x] Existing adapters run; bronze rows landed
- [x] New adapter `ohio_stocking` + ADR-008 docstring + 3 unit tests + CLI/freshness wiring
- [x] Alembic seeds: reaches, flow bands, hatch, fly_shops, mineral_shops (empty), rockhounding, boundary, recreation, river_stories
- [x] `gold.trip_quality_daily` populated (273)
- [x] Frontend dicts wired (~22 sites); tsc + vite build clean
- [x] Terraform arg authored (not applied)
- [x] Playwright UX smoke 12/12 local
- [x] This verification report
- [ ] Prod deploy (deferred — see above)
