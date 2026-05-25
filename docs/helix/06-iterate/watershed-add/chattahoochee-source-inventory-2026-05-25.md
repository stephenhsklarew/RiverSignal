# Source Inventory & Gap Report: Chattahoochee River (Upper, Georgia)

| | |
|---|---|
| **Watershed slug** | `chattahoochee` |
| **Display name** | Chattahoochee River |
| **States** | GA (mostly); minor AL on lower main stem outside Upper HUC8 |
| **Date** | 2026-05-25 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (via `/add-watershed` skill — gap-analysis only; user evaluating whether to onboard) |
| **Status** | Step 1 complete — **research-only, no Step 2 commitment yet**. Companion inventory: `mad_river_oh-source-inventory-2026-05-25.md` |

---

## Step 0 — Pre-flight clarification (deferred — to confirm before Step 2 if user chooses this watershed)

| # | Question | Assumed default (matches Shenandoah) | Material effect if different |
|---|---|---|---|
| Q1 | HUC boundary level | HUC8 `03130001` (Upper Chattahoochee) + 0.05° buffer | If HUC10 desired, splits Blue Ridge headwaters / Lanier basin / Metro Atlanta / Below West Point |
| Q2 | Paid-API tolerance | Stop and ask if any v1 source needs a paid key | None expected — all candidate GA feeds are OCGA §50-18-70 (Open Records) |
| Q3 | B2B license filter | Tag with `license` + `commercial:true\|false`; do not gate | Same as Shenandoah — all GA state-agency data is `Public Records` + `commercial:true` |
| Q4 | Confluence into existing watershed | N/A — Chattahoochee → West Point Lake → AL/GA state line → eventually Apalachicola; none on platform | Skipped |
| Q5 | Curation pace | Ship v0 with `needs_review=true` flags on hatch chart / fly shops / rockhound sites | The Buford Dam tailwater + Atlanta-CRNRA mix is unusual — expect curator pushback on a single hatch chart serving both |
| Q6 | Target ship date | No deadline | — |
| **Scope** | If onboarded, author 2 new adapters (`ga_trout` stocking + `usace_sam_hydropower` Buford Dam release schedule) plus `ga_geology` and iNat-firehose mitigation | Materially larger scope than Mad River OH (2 new adapters vs 1, one of which is safety-critical) |

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `chattahoochee` | proposed |
| Display name | Chattahoochee River | proposed |
| States | GA (~95% of bbox); minor AL only at downstream edge of HUC | user |
| Headwaters | Blue Ridge Mountains, Chattahoochee–Oconee National Forest near Helen, GA (Brasstown Bald area, White / Union counties) | USGS NHDPlus |
| Mouth (of Upper HUC) | West Point Lake at GA/AL state line; full river continues to Apalachicola Bay (not in scope for v1) | USGS WBD |
| Key impoundments in-basin | **Buford Dam → Lake Sidney Lanier** (USACE Mobile District, hydropower + flood control); Morgan Falls Dam (Georgia Power) | USACE; Georgia Power |
| Bbox (proposed) | `north=34.65, south=33.10, east=-83.55, west=-84.95` | Refined from agent research; covers Blue Ridge headwaters → Lake Lanier → metro Atlanta → West Point Lake + 0.05° buffer |
| HUC8 code | `03130001` (Upper Chattahoochee) | USGS WBD |
| NWS forecast office | **FFC** (Peachtree City — Atlanta CWA; co-located with Southeast River Forecast Center). Covers entire HUC8. | api.weather.gov/points |
| Drainage area at West Point Lake outlet | ~3,440 mi² (Upper Chattahoochee) | USGS basin reports |
| Primary fishery | **Tailwater rainbow + brown trout** below Buford Dam (cold-water release from Lake Lanier; ~16 mi of trout water through CRNRA); striped bass + spotted bass in Lake Lanier; smallmouth + redeye bass in headwater tribs above Helen | GA DNR Wildlife Resources Division |
| Notable land status | **Chattahoochee River National Recreation Area (CRNRA)** — NPS unit, 15 disjoint land units interleaved with private/county/city parcels through metro Atlanta (Cobb, Fulton, DeKalb, Forsyth, Gwinnett counties); Chattahoochee NF in headwaters; Lake Lanier shoreline = USACE | NPS; USFS; USACE |

This would be the **first urban watershed** on the platform (Atlanta = ~6M metro pop. flowing through the basin). Implications:

- **iNaturalist firehose**: ~445K research-grade obs in 5y in bbox is **4.5× Shenandoah's volume and the densest watershed yet considered**. Naïve ingest + UI will swamp; tile-based pagination + species-rarity weighting required before launch.
- **Safety-critical messaging**: Buford Dam hydropower releases raise tailwater 2-4 ft within minutes. A "no live release feed" failure mode could put anglers/tubers in danger. Requires explicit cache-and-stale-warning posture in `usace_sam_hydropower` adapter.
- **Land ownership patchwork**: RIDB covers CRNRA + Chattahoochee NF + Lake Lanier USACE — that's ~95% of in-basin federal recreation. GA State Parks (Vogel, Unicoi, Smithgall Woods, FD Roosevelt) use ReserveAmerica with no public API; modest coverage loss.
- **Standout DeepTrail content**: Dahlonega Gold Belt (Lumpkin County — historic Au/Cu mines along basin's eastern flank) is probably the richest MRDS slice the project would surface anywhere.
- **PBDB near-empty**: Blue Ridge here is Precambrian/early-Paleozoic metamorphic — fossil-poor.

---

## §1.1 — Feature → source map (per app, for Chattahoochee)

| App | Feature | Required data | Existing adapter | Status for Chattahoochee |
|---|---|---|---|---|
| **RiverSignal** | Site dashboards | USGS NWIS time series | `usgs` | ✓ — 9 active gauges covering Buford Dam tailwater through Whitesburg |
| RiverSignal | Restoration tracking | OWRI / NOAA RC / PCSRF | `restoration` | ⚠ — PNW-scoped today; no GA-specific open-record restoration registry surfaced |
| RiverSignal | Fire recovery | MTBS perimeters | `mtbs` | ✓ — sparse but present in Chattahoochee NF |
| RiverSignal | Water quality | EPA WQP | `wqp` | ✓ — dense GA EPD (`21GAEPD_WQX`) + Chattahoochee Riverkeeper (`CHATTAHOOCHEERIVERKEEPER`) providers already in WQP |
| RiverSignal | Macroinvertebrate quality | EPA WQP_BUGS | `wqp_bugs` | ✓ — GA EPD biological-monitoring data flows through WQP |
| RiverSignal | 303(d) impaired | EPA ATTAINS | `impaired` | ✓ — GA 2024 305(b)/303(d) IR in ATTAINS; GA EPD also publishes shapefile/KMZ |
| RiverSignal | E. coli / pathogens | USGS BacteriALERT (NWIS param 99407) | `usgs` | ⚠ — already in NWIS at sites 02335000, 02335880, 02336000; verify current `usgs` adapter pulls param 99407 |
| RiverSignal | Land ownership / access | BLM SMA, USFS, state parks | `blm_sma`, `recreation` | ⚠ — no BLM in GA; CRNRA + Chattahoochee NF + Lake Lanier USACE all in RIDB; GA State Parks miss (ReserveAmerica, no API) |
| RiverSignal | Watershed geometry | USGS WBD + NHDPlus | `wbd`, `nhdplus` | ✓ — federal CONUS |
| RiverSignal | Wetlands | USFWS NWI | `wetlands` | ✓ — federal CONUS |
| **RiverPath** | Go Score — flow + temp sub-scores | USGS gauges | `usgs` | ✓ — Buford Dam tailwater gauge (02334430) is the critical one for the trout fishery |
| RiverPath | Go Score — weather | NWS forecast | `nws`, `nws_forecast` | ✓ — FFC gridpoints |
| RiverPath | Go Score — hatch | `curated_hatch_chart` | manual seed | ✗ — no Chattahoochee hatch chart. Seed: tailwater-style (BWO, midges year-round, sulphurs, caddis) with `needs_entomologist_review=true` |
| RiverPath | Go Score — access | MTBS + closures + **dam release safety** | `mtbs` + manual + NEW | ⚠ — **dam release schedule is critical safety signal**, not just an access nicety. See §1.4. |
| RiverPath | River Now hero | USGS instantaneous + NWS current | live | ✓ |
| RiverPath | Photo observations | iNaturalist | `inaturalist` | ⚠ — works, but **~445K obs/5y in bbox** is 4.5× Shenandoah's; needs tile-based pagination + rarity weighting before launch |
| RiverPath | **Stocking schedule** | State hatchery feeds | `fishing` / `washington` / `utah` | ⚠ — **NEW `ga_trout` adapter required**. GA DNR-WRD publishes weekly stocking as ReportLab-generated PDF at `gadnr.org/sites/default/files/wrd/pdf/trout/Weekly_Stocking_Report.pdf` — table extraction needed |
| RiverPath | **Dam release safety** (signature) | USACE Mobile District generation schedule | NEW | ⚠ — **NEW `usace_sam_hydropower` adapter required**. Buford Dam hourly generation only at HTML pages `water.sam.usace.army.mil/buford.htm` + `spatialdata.sam.usace.army.mil/hydropower/`; no JSON API. Safety-critical |
| RiverPath | Fish passage | USGS / state passage barriers | `fish_passage` | ⚠ — PNW-skewed; coverage in basin includes Morgan Falls and several headwater barriers |
| RiverPath | Swim safety | Derived (now includes E. coli signal) | `gold.swim_safety` | ✓ — already accommodates pathogen indicator if BacteriALERT 99407 is ingested |
| RiverPath | Snowpack | NRCS SNOTEL | `snotel` | ✗ — Southeast US, none. Acceptable empty |
| RiverPath | Recreation sites | RIDB | `recreation` | ✓ — CRNRA gateway 2626 (NPS), Chattahoochee NF (Upper Chattahoochee CG #10309362), Lake Lanier (USACE) all RIDB |
| RiverPath | Fly shop directory | Manual | `fly_shops_guides` | ⚠ — strong market: Cohutta Fishing Co. (Cartersville), Unicoi Outfitters (Helen / Atlanta), River Through Atlanta Guide Service, Buford Trout Club |
| RiverPath | Guide service directory | Manual | `fly_shops_guides` (type='guide') | ⚠ — sizeable: many guides on tailwater + Lanier striper guides |
| **DeepTrail** | Geology units | Macrostrat + state geology | `macrostrat`, `dogami` | ⚠ — Macrostrat OK; **NEW `ga_geology` adapter** via UGA ITOS ArcGIS REST at `maps.itos.uga.edu/arcgis/rest/services/FrameWork/PhysicalGeography/MapServer/1` (169 units, statewide, polygon-queryable, 1976 GGS map basis) |
| DeepTrail | Fossil sites | PBDB + iDigBio + GBIF | `pbdb`, `idigbio`, `gbif` | ⚠ — Macrostrat/PBDB return near-zero — Blue Ridge metamorphic basement is fossil-poor (acceptable but not a content surface) |
| DeepTrail | Rockhound sites | Manual | `rockhounding_sites` | ⚠ — **strong targets**: Dahlonega gold panning (Crisson Gold Mine, Consolidated Gold Mine — tourist-operated, both list-able), Graves Mountain (lazulite/kyanite/rutile — annual public dig), Diamond Hill amethyst (just outside basin in SC; flag as nearby) |
| DeepTrail | Mineral & rock shop directory | Manual | `mineral_shops` | ⚠ — Atlanta metro has 4-6 candidate shops |
| DeepTrail | Mineral deposits | USGS MRDS | `mrds` | ✓ **standout** — Dahlonega Gold Belt: Findley Mine (#10084726), hundreds of historic Au/Cu sites. Probably the richest MRDS slice in the project |

---

## §1.3 — Per-source check matrix

License + commercial flag captured per Q3 (tag, don't gate). Format:
`<status> <source> — <evidence>. License: <X>, commercial:<true|false>.`

```
✓ usgs            — 9 active gauges in HUC 03130001: 02334430 Buford Dam tailwater (critical for trout fishery + safety), 02334401 Buford Dam, 02335000 Norcross/Medlock Bridge, 02335450 Above Roswell, 02335810 Morgan Falls Dam, 02335880 Powers Ferry, 02336000 Atlanta/Paces Ferry, 02336490 GA-280, 02338000 Whitesburg.   License: Public Domain, commercial:true
✓ nws             — FFC (Peachtree City) covers entire HUC8; co-located with SERFC.   License: Public Domain, commercial:true
✓ nws_forecast    — Same FFC coverage for 7-day forecast.   License: Public Domain, commercial:true
⚠ inaturalist     — ~445,600 research-grade observations in bbox since 2021-01-01. 4.5× Shenandoah. Needs tile-paginated ingest + rarity weighting before naïve ingest.   License: CC-BY-NC (photo URLs FALSE; observation metadata commercial:true)
✓ mtbs            — National; sparse Chattahoochee NF wildfire perimeters present.   License: Public Domain, commercial:true
✓ wbd             — HUC8 03130001 boundary available.   License: Public Domain, commercial:true
✓ nhdplus         — Stream flowlines for entire Upper Chattahoochee system.   License: Public Domain, commercial:true
✓ wqp             — GA EPD submits via provider 21GAEPD_WQX; Chattahoochee Riverkeeper submits via CHATTAHOOCHEERIVERKEEPER (e.g., NWW07). Verified WQX presence.   License: Public Domain, commercial:true
✓ wqp_bugs        — GA EPD biological-monitoring data flows through WQP_BUGS.   License: Public Domain, commercial:true
✓ impaired        — GA 2024 305(b)/303(d) IR in ATTAINS; GA EPD also publishes shapefile/KMZ. Federal adapter should work as-is.   License: Public Domain, commercial:true
⚠ usgs_bacteria   — BacteriALERT (E. coli, NWIS param 99407) already in NWIS at sites 02335000, 02335880, 02336000. Verify current `usgs` adapter pulls param 99407.   License: Public Domain, commercial:true
✓ wetlands        — USFWS NWI: full CONUS coverage.   License: Public Domain, commercial:true
✓ prism           — CONUS coverage.   License: Academic Free, commercial:true
✓ recreation      — RIDB: CRNRA gateway 2626 (NPS, 15 units), Chattahoochee–Oconee NF (Upper Chattahoochee CG #10309362), Lake Lanier (USACE). All federal in-basin recreation is covered.   License: Public Domain, commercial:true
✓ biodata         — USGS BioData: GA fish + macroinvertebrate sites present.   License: Public Domain, commercial:true
✓ gbif            — Global biodiversity records; iNat firehose flows to GBIF (same volume warning applies if mirrored).   License: CC-BY 4.0, commercial:true
✓ idigbio         — GA specimen records well-collected.   License: varies (CC0 / CC-BY mostly), commercial:true
⚠ pbdb            — Blue Ridge here is Precambrian/early-Paleozoic metamorphic — essentially fossil-poor; PBDB will return near-zero. Acceptable degradation.   License: CC0, commercial:true
✓ macrostrat      — Units present statewide.   License: CC-BY 4.0, commercial:true
✓ mrds            — STANDOUT: Dahlonega Gold Belt (Lumpkin Co.); hundreds of historic Au/Cu sites along basin's eastern flank. Probably the richest MRDS slice in the project.   License: Public Domain, commercial:true
⚠ restoration     — `restoration` adapter is PNW-scoped (OWRI / PCSRF / NOAA RC). No GA-specific public registry equivalent to OWRI surfaced — out-of-scope for v1.   License: varies, commercial:true
⚠ fish_passage    — Adapter exists but PNW-skewed. In-basin barriers: Morgan Falls Dam, Buford Dam (both impassable), Roswell Mill ruins.   License: Public Domain, commercial:true
⚠ ga_trout        — NEW adapter. GA DNR-WRD weekly trout stocking PDF at https://gadnr.org/sites/default/files/wrd/pdf/trout/Weekly_Stocking_Report.pdf — ReportLab-generated, table extraction required. Covers Chattahoochee DH section (Sope Creek→US41) + tailwater.   License: OCGA §50-18-70 (Open Records), commercial:true
⚠ usace_sam_hydropower — NEW adapter. SAFETY-CRITICAL. Buford Dam hourly generation only via HTML at https://water.sam.usace.army.mil/buford.htm + http://spatialdata.sam.usace.army.mil/hydropower/. Inflow forecast at https://www.weather.gov/serfc/inflows_cmmg1. USACE A2W has no documented public REST API. Scrape required; cache aggressively; surface "data stale" rather than guess.   License: Public Domain (USACE), commercial:true
⚠ ga_geology      — NEW adapter. UGA ITOS ArcGIS REST at https://maps.itos.uga.edu/arcgis/rest/services/FrameWork/PhysicalGeography/MapServer/1 — 169 units, statewide, polygon-queryable. Derived from 1976 GGS map.   License: Public Domain (state-published derivative), commercial:true
⚠ ga_dnr_regs     — NEW adapter (or static seed). GA special-regulation streams: Chattahoochee DH (Delayed Harvest) section + Smith Creek + Dukes Creek seasonal closures. HTML; quarterly cadence.   License: Public Records, commercial:true
✗ ga_state_parks  — Vogel SP, Unicoi SP, Smithgall Woods SP, FD Roosevelt SP all on ReserveAmerica (no public API). ToS-restricted. Skip or fragile scrape (1-2d). RIDB already covers ~95% of in-basin federal recreation, so this is a small coverage loss.   License: varies; ToS-restricted
✗ snotel          — Southeast US, none.   N/A
✗ blm_sma         — No BLM land in GA.   N/A
✗ dogami / streamnet / washington / utah / fishing — PNW/UT-specific.   N/A
✗ curated_hatch_chart — No Chattahoochee hatch chart. Seed: tailwater-style (BWO, midges year-round, sulphurs in spring, caddis, terrestrials in summer) with needs_entomologist_review=true. NOTE: single hatch chart unlikely to fit both Buford tailwater and Blue Ridge headwater tribs — flag for curator decision.   License: project-curated, commercial:true
✗ fly_shops_guides — No Chattahoochee rows. Targets: Cohutta Fishing Co. (Cartersville), Unicoi Outfitters (Helen / Atlanta), River Through Atlanta Guide Service, Buford Trout Club, Reel Job Fishing Adventures.   License: project-curated, commercial:true
✗ mineral_shops    — No Chattahoochee rows. Targets: 4-6 candidate shops in Atlanta metro.   License: project-curated, commercial:true
✗ rockhounding_sites — No Chattahoochee rows. STRONG TARGETS: Crisson Gold Mine + Consolidated Gold Mine (tourist-operated Dahlonega panning), Graves Mountain (annual public dig — lazulite/kyanite/rutile), Diamond Hill amethyst (flag as nearby — outside basin).   License: project-curated, commercial:true
```

Totals: **15 ✓** (work as-is), **11 ⚠** (existing adapter needs extension or new adapter authoring, or volume/coverage concerns), **6 ✗** (not applicable to this watershed OR manual curation seeds needed).

---

## §1.4 — Gap report + recommended fills

| Gap | Recommended fill | Cost / effort | License + commercial | Blocker for v1? |
|---|---|---|---|---|
| **GA DNR-WRD trout stocking** | New adapter `ga_trout` — weekly PDF at `gadnr.org/sites/default/files/wrd/pdf/trout/Weekly_Stocking_Report.pdf` (ReportLab-generated; table extraction + dedup). Confirms Chattahoochee DH section + tailwater. | **2-3d** (PDF parse + dedup pattern) | OCGA §50-18-70 Open Records, commercial:true | **Yes** — defining feature of the watershed |
| **Buford Dam release / generation schedule (SAFETY)** | New adapter `usace_sam_hydropower` — scrape `spatialdata.sam.usace.army.mil/hydropower/` + `water.sam.usace.army.mil/buford.htm`. USACE A2W has no documented REST API. Inflow forecast graphics at `weather.gov/serfc/inflows_cmmg1`. **Safety-critical**: cache aggressively, fall back to SERFC inflow forecast, surface "data stale" rather than guess. | **3-4d** (scrape, no JSON; safety-critical QA cost includes failure-mode + UI banner design) | Public Domain (USACE), commercial:true | **Yes** — water-release timing is the #1 safety signal on this river; sudden generation releases raise tailwater 2-4 ft within minutes |
| **iNaturalist firehose volume mitigation** | Tile-based pagination + species-rarity weighting in `inaturalist` adapter to avoid swamping bronze with 30K *Sciurus carolinensis* photos and surface meaningful records (Etowah darter, hellbender candidates upstream). | **2-3d** (cross-cutting improvement — benefits every future urban watershed) | — | Yes for v1 UX quality; not a blocker for backend ingest correctness |
| **GA Geological Survey geology layer** | New adapter `ga_geology` — UGA ITOS ArcGIS REST at `maps.itos.uga.edu/arcgis/rest/services/FrameWork/PhysicalGeography/MapServer/1`. Identical pattern to ODGS / DOGAMI. | **1d** | Public Domain (state-published), commercial:true | No — DeepTrail ships with Macrostrat-only for v1; `ga_geology` adds polygon detail |
| **USGS BacteriALERT (E. coli) ingest** | Verify `usgs` adapter pulls NWIS param 99407 at the 3 BacteriALERT sites (02335000, 02335880, 02336000). | **0.5d** (verify only) | Public Domain, commercial:true | No — but high-impact for urban swim-safety panel |
| **GA special-regulation streams** | Static seed migration `silver.reach_regulations` for Chattahoochee DH (Delayed Harvest) section + Smith Creek + Dukes Creek. Quarterly recheck. | ~0.5d | Public Records, commercial:true | No — TQS access sub-score works without it |
| **GA State Parks** | Skip (ReserveAmerica scrape is ToS-risky and fragile). RIDB covers CRNRA + NF + Lake Lanier USACE = ~95% of in-basin federal rec. | 0 (defer) | ToS-restricted | No |
| **Restoration (GA analogue)** | No GA-specific open-record restoration registry surfaced. Out-of-scope for v1; would need agent investigation of GA EPD project lists + UCRR project DB. | — | varies | No |
| **Fish passage (GA detail)** | Verify `fish_passage` adapter pulls USFWS NFPP for in-basin barriers (Morgan Falls, Buford, Roswell Mill). | ~0.5d | Public Domain, commercial:true | No |
| **Hatch chart for Chattahoochee** | Auto-seed tailwater-style (BWO, midges year-round, sulphurs, caddis, terrestrials in summer). Flag `needs_entomologist_review=true`. **Curator-flag**: single chart unlikely to fit both Buford tailwater AND Blue Ridge headwater tribs — consider 2 charts. | ~1 hour (one chart) or ~3 hours (two charts) | Project-curated, commercial:true | No |
| **Fly shops + guides directory** | Manual research + seed. Target 5-8 rows (strong market). | ~2-3 hours | Project-curated, commercial:true | No |
| **Mineral shops directory** | Manual research + seed. Target 4-6 rows (Atlanta metro). | ~1 hour | Project-curated, commercial:true | No |
| **Rockhounding sites** | Strong targets: Crisson Gold Mine + Consolidated Gold Mine (Dahlonega — tourist-operated, fee-based), Graves Mountain (annual public dig — lazulite/kyanite/rutile). 3-5 rows. | ~2 hours | Project-curated, commercial:true | No — but unusually rich content surface for DeepTrail |
| **PBDB fossil content** | None — Blue Ridge metamorphic basement is fossil-poor. Accept empty. | 0 | N/A | No |
| **SNOTEL snowpack** | None — Southeast US. Accept empty. | 0 | N/A | No |
| **Catch-prediction model priors** | Reuse East-Coast warm-water + trout priors (already opened as Shenandoah follow-on) | 0 | derived | No |

---

## §1.5 — Estimated adapter authoring scope (Step 2 preview)

| Adapter | Effort | Required for v1 RiverPath ship | Priority |
|---|---|---|---|
| `ga_trout` (WRD stocking PDF) | ~2.5d | RiverPath stocking panel | **P0** |
| `usace_sam_hydropower` (Buford release/generation) | ~3.5d (incl. safety QA + UI staleness banner design) | RiverPath safety + trout fishery signal | **P0** |
| iNat firehose tile-pagination + rarity weighting | ~2.5d | RiverPath/DeepTrail UX quality; benefits every future urban watershed | **P0** (cross-cutting — would ship as its own bead but on Chattahoochee's critical path) |
| `usgs` adapter param 99407 (BacteriALERT) verify/extend | ~0.5d | RiverPath swim-safety panel | **P0** |
| WQP validation pass (`21GAEPD_WQX` + `CHATTAHOOCHEERIVERKEEPER` flow through `wqp` + `wqp_bugs`) | ~0.5d | RiverSignal water-quality surface | **P0** |
| `ga_geology` (UGA ITOS ArcGIS REST) | ~1d | DeepTrail geology detail | **P1** |
| `ga_dnr_regs` (static seed) | ~0.5d | TQS access sub-score | **P2** |
| Adapter wiring / fixtures / tests | ~1d | — | **P0** (overhead) |

**Total v0+P0 scope: ~8.0d** (stocking + Buford safety + iNat mitigation + bacteria + WQP validation + wiring).
**Total v0+P0+P1: ~9.0d** (adds GA geology).
**Total full scope: ~12.0d** (everything above).

Compared with Mad River OH's ~4.0d v0+P0 / ~9.5d full, Chattahoochee is **~2× the v0 effort** primarily due to (1) Buford Dam safety-critical adapter and (2) iNat-firehose mitigation that didn't matter at Shenandoah/Mad scales.

---

## §1.6 — Watershed config preview (Step 2.1)

```python
# pipeline/config/watersheds.py
"chattahoochee": {
    "name": "Chattahoochee River",
    "description": (
        "Upper Chattahoochee River from Blue Ridge headwaters near "
        "Helen, GA through Lake Sidney Lanier, the Buford Dam tailwater "
        "trout fishery, and the Chattahoochee River National Recreation "
        "Area (15 NPS units through metro Atlanta) to West Point Lake "
        "at the GA/AL state line. First urban watershed and first "
        "Southeast US watershed on the platform."
    ),
    "bbox": {
        "north": 34.65,
        "south": 33.10,
        "east": -83.55,
        "west": -84.95,
    },
},
```

---

## §1.7 — Reach inventory preview (Step 2.4)

Four v0 reaches (one more than Shenandoah/Mad because the Buford tailwater is structurally distinct from both headwaters and metro reaches):

| Reach ID | Name (short) | Primary USGS gauge | Typical species | Warm-water? | Notes |
|---|---|---|---|---|---|
| `chattahoochee_headwaters` | Blue Ridge Headwaters (White/Union/Habersham co., above Lanier) | (small headwater gauges if any; else proxy) | brook_trout, brown_trout, rainbow_trout, redeye_bass | false (cold) | needs_guide_review — Helen / Soque-confluence area |
| `chattahoochee_lanier` | Lake Sidney Lanier | 02334401 Buford Dam (impoundment) | striped_bass, spotted_bass, largemouth_bass, hybrid_bass | true (warm-water lake) | needs_guide_review — distinct fishery vs. river reaches |
| `chattahoochee_tailwater` | Buford Dam Tailwater (Buford → Morgan Falls — CRNRA trout water) | 02334430 Buford Dam tailwater | rainbow_trout, brown_trout | false (cold release) | **SIGNATURE REACH**. Safety-critical for dam-release messaging. needs_guide_review |
| `chattahoochee_metro` | Metro Atlanta (Morgan Falls → Whitesburg) | 02336000 Atlanta/Paces Ferry | striped_bass, spotted_bass, redbreast_sunfish, channel_catfish | true | needs_guide_review — water-quality nuance (E. coli surges after Atlanta rainfall) |

---

## §1.8 — Step 2 / Step 3 sequence recommendation

1. Commit this inventory under a Step-1 commit.
2. Watershed config entry (§2.1).
3. v0 curation seeds (§2.4) — reaches (4), flow bands, hatch chart(s), fly shops, mineral shops, rockhounding sites — all `needs_review=true`. One commit per artifact.
4. **iNat firehose mitigation first** (`inaturalist` adapter tile-pagination + rarity weighting) — this is cross-cutting infra that benefits every future urban watershed; ship it as its own commit before any GA-specific work.
5. Author `ga_trout` adapter (§2.2) — PDF parse pattern with captured fixtures.
6. Author `usace_sam_hydropower` adapter (§2.2) — **with explicit safety-fallback design**: cache last-good values, surface "data stale: N min" banner, fall back to SERFC inflow forecast graphic, write to `bronze.dam_release` not into `gold.predictions` directly.
7. Verify `usgs` adapter pulls NWIS param 99407 (BacteriALERT) — small touch + test.
8. Validate WQP providers `21GAEPD_WQX` + `CHATTAHOOCHEERIVERKEEPER` flow through `wqp` + `wqp_bugs`.
9. Run all applicable existing adapters scoped to `-w chattahoochee` (§2.3).
10. (P1) Author `ga_geology` adapter.
11. Wire frontend (§2.6) — ~13 files per runbook hit table. Add **dam-release safety banner component** for the tailwater reach (this is a new UI surface, not just a string).
12. Refresh medallion + TQS daily refresh (§2.5).
13. **Pause for user review** before §2.7 (terraform args) and §2.8 (prod deploy with 4 explicit approval gates).
14. Write Step 3 verification report (`chattahoochee-verification-<date>.md`) with **explicit safety-banner UX smoke test** and **iNat-volume sanity check** added to the standard McKenzie-mirror feature-coverage grid.

---

## Comparison summary (vs Mad River OH)

| Dimension | Chattahoochee GA | Mad River OH |
|---|---|---|
| USGS gauges in bbox | **9 active** (incl. Buford Dam tailwater 02334430) | 2 active |
| iNat 5y obs in bbox | **~445K** (densest yet — 4.5× Shenandoah) | ~99K |
| WQP stations | dense (state + Riverkeeper providers already in WQP) | 151 (state + macro) |
| MRDS content | **Standout — Dahlonega Gold Belt** (richest in project) | Sparse — industrial minerals only |
| PBDB content | Near-zero (metamorphic) | **Rich — 129 occurrences Ord-Sil-Dev** |
| New adapters required for v0 | **2** (`ga_trout` + `usace_sam_hydropower`) — one safety-critical | 1 (`ohio_stocking`) |
| Cross-cutting infra required for v0 | **iNat tile-pagination + rarity weighting** | None |
| v0+P0 effort | **~8d** | ~4d |
| Full scope | ~12d | ~9.5d |
| Critical-path risk | Buford Dam safety scrape (fragile HTML, no JSON API, mis-shipped messaging = safety liability) | ODNR stocking page CDN-gated (worst case grows from 2.5d → 5d) |
| Signature RiverPath content | Tailwater trout + Atlanta urban-river + dam-release safety banner | Brown-trout-on-spring-creek stocking |
| Signature DeepTrail content | Dahlonega Gold Belt (MRDS) | Ord-Dev carbonate fossils (PBDB) |

**Recommendation (carried over from gap-analysis comparison):** load **Mad River OH first**, then defer Chattahoochee until (a) iNat-firehose pagination ships as its own bead, and (b) a safety-critical-adapter design pattern is established for future urban watersheds. Chattahoochee is the higher-content watershed but ~2× the v0 effort, with safety-critical scope that benefits from its own dedicated focus.

---

**End of Step 1 inventory. No Step-2 commitment made yet — awaiting user direction.**
