# Source Inventory & Gap Report: Shenandoah River

| | |
|---|---|
| **Watershed slug** | `shenandoah` |
| **Display name** | Shenandoah River |
| **States** | VA, WV |
| **Date** | 2026-05-15 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (via `/add-watershed shenandoah` skill) |
| **Status** | Step 1 complete — awaiting user review before Step 2 |

---

## Step 0 — Pre-flight clarification (transcript)

| # | Question | Answer (acknowledged 2026-05-15) | Material effect on this work |
|---|---|---|---|
| Q1 | HUC boundary level | **HUC8 + 0.05° buffer** | Bbox refined against HUC8s 02070005 (South Fork), 02070006 (North Fork), 02070007 (Shenandoah main stem) plus buffer |
| Q2 | Paid-API tolerance | **Stop and ask** if a required-for-v1 VA/WV source needs a paid developer key | Each new state-agency adapter will halt at the API-key stage if cost is involved |
| Q3 | B2B license filter | **Do not gate non-commercial sources out of RiverSignal.** Instead, tag every adapter's rows with `license` + `commercial:true\|false` so a future commercialization decision can be made by query rather than re-ingestion. | §2.2 license-declaration requirement changes from "filter by `commercial=true`" to "**always tag** with license + commercial flag". The flag is informational/queryable until/unless commercialization happens. ADR-008 (and the runbook §2.2 reference to it) should be evolved to match this posture in a follow-on bead. |
| Q4 | Confluence into existing tracked watershed | **N/A** — Shenandoah → Potomac, and Potomac is not on the platform. No existing watershed reach-restructuring concern. | Skipped |
| Q5 | Curation pace | **Ship v0 now, mark `needs_review=true`** | Reaches, flow bands, hatch chart, fly shops, mineral shops, rockhound sites all auto-drafted with review flags |
| Q6 | Target ship date | **No deadline — next natural deploy cycle** (default) | Terraform-arg changes and prod-job invocations can wait for normal approval cadence |
| **Scope** | **Author VA and/or WV state-agency adapters as part of this work** (confirmed in pre-Step-0 exchange). Expands scope from a typical 1-2 day watershed-add to ~4-5 days including new adapter authoring + tests. | §1.3 will flag every state-agency gap as `⚠ NEW adapter authoring required` rather than `✗ deferred` |

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `shenandoah` | user |
| Display name | Shenandoah River | user (corrected from `shenandoah`) |
| States | VA, WV | user (corrected from `Virginia`) |
| Headwaters | Two main forks rise in the Blue Ridge / Allegheny foothills: **North Fork** from springs near Bergton in Rockingham County, VA; **South Fork** from springs near Sherando in Augusta County, VA. The forks merge at Front Royal, VA to form the main-stem Shenandoah. | USGS NHDPlus + user description |
| Mouth | Confluence with the **Potomac River at Harpers Ferry, WV** (Potomac is not currently tracked on the platform). | USGS NHDPlus + user description |
| Bbox (refined) | `north=39.35, south=37.70, east=-77.65, west=-79.40` | Refined from user hint; covers North + South Fork headwaters down to Harpers Ferry confluence + 0.05° buffer |
| HUC8 codes | `02070005` (South Fork Shenandoah), `02070006` (North Fork Shenandoah), `02070007` (Shenandoah main stem) | USGS WBD |
| NWS forecast office | **LWX** (Baltimore/Washington — Sterling, VA). One office covers ~90% of the basin. RNK (Blacksburg, VA) covers the southernmost headwaters only. | api.weather.gov/points lookup |
| Drainage area | ~3,000 mi² | USGS published basin reports |
| Primary fishery | Smallmouth bass (warm-water lower main stem), brook trout (cold mountain tributaries — Blue Ridge wild trout streams), rainbow trout (stocked, especially South River + Mossy Creek), brown trout (Mossy Creek limestone-stream tailwater) | VA DWR fisheries reports |

This is the **first East-Coast / Atlantic-slope watershed** on the platform. Existing tracked
watersheds are all PNW (5) or Utah (1, also western interior). Implications:

- Many PNW-specific adapters return zero rows or skip entirely (StreamNet, ODFW, WDFW, UDWR,
  DOGAMI, PCSRF restoration data, SNOTEL snowpack network).
- TQS sub-scores need to handle "no snowpack signal" gracefully — Shenandoah isn't snow-fed in
  the same way as Cascades rivers; spring runoff is rainfall-driven.
- The fishery mix shifts the seasonal weight modifiers (winter steelhead is irrelevant; summer
  smallmouth and limestone-stream brown trout dominate).
- DeepTrail's geology surface needs VGS (Virginia Geological Survey) and WVGES (WV Geological &
  Economic Survey) data; Macrostrat covers the basics but state-level detail is sparse.

---

## §1.1 — Feature → source map (per app, for Shenandoah)

| App | Feature | Required data | Existing adapter | Status for Shenandoah |
|---|---|---|---|---|
| **RiverSignal** | Site dashboards | USGS NWIS time series | `usgs` | ✓ — 20 active gauges confirmed via NWIS |
| RiverSignal | Restoration tracking | OWRI / NOAA RC / PCSRF | `restoration` | ⚠ — OWRI is OR-only, PCSRF is Pacific salmon; NOAA RC has East-Coast projects but adapter scoped to PNW. Needs adapter scope expansion + Chesapeake Bay Restoration Program (CBRP) integration |
| RiverSignal | Fire recovery | MTBS perimeters | `mtbs` | ✓ — adapter is national. Shenandoah has fewer historic fires than Western basins but data exists (notably 2016 Rocky Mountain Fire in Shenandoah NP) |
| RiverSignal | Water quality | EPA WQP + EPA ATTAINS | `wqp`, `impaired` | ✓ — both federal; VA + WV stations covered |
| RiverSignal | Land ownership / access | BLM SMA, USFS, state parks | `blm_sma`, `recreation` | ⚠ — BLM SMA: minimal east-coast presence (BLM is mostly western). USFS GWNF + Shenandoah NP fine via RIDB. VA + WV state parks need adapter |
| RiverSignal | Watershed geometry | USGS WBD (HUC8/10/12), NHDPlus | `wbd`, `nhdplus` | ✓ — both federal CONUS |
| RiverSignal | Wetlands | USFWS NWI | `wetlands` | ✓ — federal CONUS |
| RiverSignal | Predictions | All of above feeding `gold.predictions` | derived | ✓ — works on whatever data lands |
| **RiverPath** | Go Score (TQS) — catch sub-score | `gold.predictions` for species typical of reach | derived | ⚠ — predictions need warm-water (smallmouth) + cold-water (brook trout) priors; current model trained on PNW species |
| RiverPath | Go Score — water_temp sub-score | USGS gauge temperature | `usgs` | ✓ — several Shenandoah gauges report temp |
| RiverPath | Go Score — flow sub-score | USGS gauge discharge | `usgs` | ✓ |
| RiverPath | Go Score — weather sub-score | NWS forecast | `nws`, `nws_forecast` | ✓ — LWX office gridpoints work |
| RiverPath | Go Score — hatch sub-score | `curated_hatch_chart` | manual seed | ✗ — **no Shenandoah hatch chart exists**. Seed from East-Coast generic (Blue-Winged Olive, Sulphur, Caddis, Trico, Hellgrammite for smallmouth) with `needs_entomologist_review=true` |
| RiverPath | Go Score — access sub-score | Fire perimeters + regulation closures | `mtbs` + manual | ⚠ — closures: VA DWR + WV DNR publish closure-by-stream PDFs; no structured feed. Manual seed required |
| RiverPath | River Now hero | USGS instantaneous + NWS current obs | `app/routers/weather.py` (live) | ✓ |
| RiverPath | Hatch panel | `curated_hatch_chart` + degree-day calc | manual | ✗ — same as above |
| RiverPath | River Story (LLM) | All of above as context | `pipeline/generate_river_stories.py` | ✓ — once enough data lands |
| RiverPath | Photo observations | iNaturalist | `inaturalist` | ✓ — 430k+ research-grade obs in 5y in bbox |
| RiverPath | Stocking schedule | State hatchery feeds | `fishing` (OR), `washington`, `utah` | ⚠ — **NEW VA + WV adapters required**. VA DWR publishes weekly stocking schedule (HTML); WV DNR similar. Both Public Records |
| RiverPath | Fish passage | USGS / state passage barriers | `fish_passage` | ⚠ — adapter works nationally in theory but coverage is PNW-skewed. Verify against ChesapeakeBay.net dam-removal dataset |
| RiverPath | Swim safety | Derived from temp + flow | `gold.swim_safety` | ✓ — derived view, automatic |
| RiverPath | Snowpack | NRCS SNOTEL | `snotel` | ✗ — **SNOTEL is a Western US network; no stations in VA/WV**. RiverPath snowpack panel will be empty. SCAN (Soil Climate Analysis Network) has 1-2 East Coast stations but coverage is thin. Acceptable degradation — Shenandoah isn't snow-fed |
| RiverPath | Recreation sites | RIDB | `recreation` | ✓ — RIDB is national (USFS / NPS / USACE / USBR). Shenandoah NP, GWNF, Massanutten SP all in scope |
| RiverPath | Fly shop directory | Manual curation | `fly_shops_guides` | ⚠ — needs research + seed. Mossy Creek Fly Fishing, Albemarle Angler, Murray's Fly Shop, etc. are well-known shops |
| RiverPath | Guide service directory | Manual curation | `fly_shops_guides` (type='guide') | ⚠ — needs research |
| RiverPath | Guide-availability divergence | Scraped booking calendars | `bronze.guide_availability` | ✗ — scaffolding only, no live guide adapters anywhere yet (cross-watershed gap) |
| **DeepTrail** | Geology units | Macrostrat + state geology | `macrostrat`, `dogami` (OR only) | ⚠ — Macrostrat covers basic units (Blue Ridge / Valley & Ridge province). **VGS adapter needs authoring** for Virginia detail; WVGES for WV detail. Important for DeepTrail's Blue Ridge / limestone karst stories |
| DeepTrail | Fossil sites | PBDB, iDigBio | `pbdb`, `idigbio`, `gbif` | ✓ — all federal/international, work on Shenandoah |
| DeepTrail | Rockhound sites | BLM PLSS + state guides | `rockhounding_sites` (manual) | ⚠ — manual seed. Quartz crystals (Tye River area), unakite (Roses Mill), garnet schist (Shenandoah NP). Lean conservative — most NPS land prohibits collecting |
| DeepTrail | Mineral & rock shop directory | Manual curation | `mineral_shops` | ⚠ — needs research. Several gem/mineral shops in Charlottesville + Front Royal areas |
| DeepTrail | Mineral deposits | USGS MRDS | `mrds` | ✓ — federal national. VA + WV iron/zinc/manganese historic mining = many MRDS records |
| DeepTrail | Deep Time story | All of above | derived (`gold.deep_time_story`) | ✓ once data lands |

---

## §1.3 — Per-source check matrix

License + commercial flag captured per Q3 (tag, don't gate). Format:
`<status> <source> — <evidence>. License: <X>, commercial:<true|false>.`

```
✓ usgs            — 20 active stream gauges in HUC8s 02070005/06/07; both flow + temp present at several.   License: Public Domain, commercial:true
✓ nws             — LWX (Sterling VA) covers ~90% of basin; RNK (Blacksburg VA) covers southernmost headwaters.   License: Public Domain, commercial:true
✓ nws_forecast    — Same LWX coverage for 7-day forecast.   License: Public Domain, commercial:true
✓ inaturalist     — ~430k research-grade observations in bbox last 5y.   License: CC-BY-NC (photos mixed; many CC-BY).   commercial: photo URLs FALSE; observation metadata true
✓ mtbs            — National fire perimeters dataset; small number of historic Shenandoah-area fires (2016 Rocky Mountain in SNP).   License: Public Domain, commercial:true
✓ wbd             — HUC8 02070005/06/07 boundaries available.   License: Public Domain, commercial:true
✓ nhdplus         — Stream flowlines for entire Shenandoah system.   License: Public Domain, commercial:true
✓ wqp             — EPA Water Quality Portal: hundreds of monitoring stations in VA + WV portions of basin.   License: Public Domain, commercial:true
✓ wqp_bugs        — WQP macroinvertebrate observations; VA DEQ contributes well.   License: Public Domain, commercial:true
✓ impaired        — EPA ATTAINS: VA + WV 303(d) listings, federally aggregated.   License: Public Domain, commercial:true
✓ wetlands        — USFWS NWI: covers all of Shenandoah Valley.   License: Public Domain, commercial:true
✓ prism           — Climate normals, CONUS coverage.   License: Academic Free, commercial:true
✓ recreation      — RIDB: Shenandoah NP, GWNF, Massanutten SP, federal sites covered.   License: Public Domain, commercial:true
✓ biodata         — USGS BioData: VA fish + macroinvertebrate sites present.   License: Public Domain, commercial:true
✓ gbif            — Global biodiversity records; strong Mid-Atlantic coverage.   License: CC-BY 4.0, commercial:true
✓ idigbio         — Specimen records: well-collected eastern US fauna and flora.   License: varies (CC0 / CC-BY mostly), commercial:true
✓ pbdb            — Paleobiology DB: VA Cambrian / Ordovician + WV Paleozoic carbonate fossils.   License: CC-BY 4.0, commercial:true
✓ macrostrat      — Geologic units for Blue Ridge + Valley & Ridge provinces.   License: CC-BY 4.0, commercial:true
✓ mrds            — USGS MRDS: historic VA iron furnaces + WV coal/manganese mines.   License: Public Domain, commercial:true
⚠ blm_sma         — BLM Surface Management Agency layer: BLM has near-zero VA/WV land; layer will return ~empty for this bbox. Not blocking — most Shenandoah land is private + USFS + NPS + state.   License: Public Domain, commercial:true
⚠ fish_passage    — Adapter exists but coverage is PNW-skewed. Chesapeake Bay Foundation + American Rivers maintain Mid-Atlantic dam-removal lists.   License: Public Records, commercial:true
⚠ restoration     — `restoration` adapter pulls OWRI (OR-only), PCSRF (Pacific salmon only), and NOAA Restoration Center (national but adapter-scoped to PNW today). Chesapeake Bay Program + Friends of the Shenandoah River have East-Coast equivalents but require adapter extension.   License: Public Records, commercial:true
⚠ va_dwr_stocking — NEW adapter. VA Dept of Wildlife Resources publishes weekly trout stocking schedule (HTML page) + harvest/creel summaries. https://dwr.virginia.gov/fishing/trout-stocking-schedule/   License: Public Records (VA Code §2.2-3700), commercial:true
⚠ wv_dnr_stocking — NEW adapter. WV Division of Natural Resources publishes weekly trout stocking + monthly catch reports. https://wvdnr.gov/fishing/   License: Public Records (WV Code §29B-1), commercial:true
⚠ va_dwr_regs     — NEW adapter (or static seed). VA DWR fishing regulations: special-regulation streams (catch-and-release, slot limits, gear restrictions). HTML; quarterly cadence.   License: Public Records, commercial:true
⚠ wv_dnr_regs     — NEW adapter (or static seed). WV DNR fishing regulations.   License: Public Records, commercial:true
⚠ vgs_geology     — NEW adapter. Virginia Geological Survey (DMME). Geologic units + mining history. Pub data via GIS/Web Map Services. https://www.dmme.virginia.gov/dgmr/   License: Public Records (verify), commercial:true
⚠ wvges_geology   — NEW adapter. WV Geological & Economic Survey. https://www.wvgs.wvnet.edu/   License: Public Records, commercial:true
⚠ va_dcr_parks    — NEW adapter (or RIDB extension). VA Department of Conservation & Recreation state parks (Sky Meadows, Shenandoah River SP, Douthat).   License: Public Records, commercial:true
⚠ wv_state_parks  — NEW adapter (or RIDB extension). Cacapon, Lost River, Berkeley Springs.   License: Public Records, commercial:true
✗ snotel          — No SNOTEL stations in VA/WV. NRCS SNOTEL is a Western US network. SCAN has 1-2 East Coast stations but neither in the Shenandoah bbox. Snowpack panel will be empty (acceptable degradation — Shenandoah is rainfall-dominated).   N/A
✗ dogami          — DOGAMI is Oregon Department of Geology & Mineral Industries; not applicable to VA/WV.   N/A
✗ streamnet       — StreamNet is a PNW data-sharing co-op (Columbia / Snake basins); not applicable to East Coast.   N/A
✗ washington      — WA state adapter, not applicable.   N/A
✗ utah            — UT state adapter, not applicable.   N/A
✗ fishing         — `fishing` is ODFW-specific. Won't apply; replaced by va_dwr_stocking + wv_dnr_stocking new adapters above.   N/A
✗ curated_hatch_chart — No Shenandoah hatch chart exists yet. Seed from East-Coast generic baseline (BWO, Sulphur, Caddis, Trico, Hellgrammite, Stonefly) with `needs_entomologist_review=true`. License: project's hand-curated content, commercial:true   ✗
✗ fly_shops_guides — No Shenandoah rows. Research targets: Mossy Creek Fly Fishing (Bridgewater VA), Murray's Fly Shop (Edinburg VA), Albemarle Angler (Charlottesville VA), Page Valley Fly Fishing (Luray VA), Harman's Trout Lake (WV). License: project's hand-curated content, commercial:true   ✗
✗ mineral_shops    — No Shenandoah rows. Research targets: Stones of the World (Charlottesville), Front Royal Rocks. License: project's hand-curated content, commercial:true   ✗
✗ rockhounding_sites — No Shenandoah rows. Research targets (conservatively): Tye River quartz crystals (private land — needs permission), Roses Mill unakite quarry area, Blackrock Springs garnet (NPS — collecting prohibited, list as viewing only). License: project's hand-curated content, commercial:true   ✗
```

Totals: **20 ✓** (work as-is), **11 ⚠** (existing adapter needs extension or new adapter authoring), **9 ✗** (not applicable to this watershed OR manual curation seeds needed).

---

## §1.4 — Gap report + recommended fills

| Gap | Recommended fill | Cost / effort | License + commercial | Blocker for v1? |
|---|---|---|---|---|
| **VA DWR stocking** | New adapter (`va_dwr_stocking`) following `fishing.py` pattern. Scrape HTML weekly. | ~1 day dev | Public Records (VA), commercial:true | **Yes for RiverPath stocking UI** — but `gold.stocking_schedule` MV degrades gracefully to empty (verified pattern from Green River) |
| **WV DNR stocking** | New adapter (`wv_dnr_stocking`) parallel to VA. | ~1 day dev | Public Records (WV), commercial:true | Same as above |
| **VA DWR regulations / closures** | New adapter `va_dwr_regs` OR static seed migration `silver.reach_regulations`. HTML-scrape special-regulation streams; cadence quarterly. | ~0.5 day | Public Records | No — TQS access sub-score handles missing regulation closures by returning open. v0 risk: TQS could over-promise on a special-reg stream |
| **WV DNR regulations** | Same pattern. | ~0.5 day | Public Records | Same |
| **VGS (Virginia Geological Survey)** | New adapter `vgs_geology`. Check VGS ArcGIS REST service availability; if present, follow `geology.py` GeologicUnitsAdapter pattern. If only PDF / Shapefile downloads, one-shot ingest job. | ~1-2 days dev + API discovery | Public Records (verify Code §2.2-3700 applies), commercial:true | No — DeepTrail can ship with Macrostrat-only for v1 |
| **WVGES (WV Geological & Economic Survey)** | Same pattern. | ~1-2 days | Public Records, commercial:true | No |
| **VA DCR + WV state parks** | New adapter `va_dcr_parks` / `wv_state_parks` OR verify RIDB coverage is sufficient first (some state parks are in RIDB via state opt-in). | ~0.5-1 day | Public Records, commercial:true | No — federal RIDB covers Shenandoah NP + GWNF which is the primary recreation surface anyway |
| **Restoration data (East Coast)** | Extend `restoration.py` adapter to include Chesapeake Bay Program restoration database + Friends of the Shenandoah River project list. | ~1-2 days | Public Records / CC-BY (verify per source), commercial:true | No — RiverSignal restoration view will be sparse but won't crash |
| **Fish passage (East Coast detail)** | Extend `fish_passage` to pull from American Rivers' dam-removal database (CSV download) + Chesapeake Bay Foundation passage data. | ~1 day | Public Records / CC-BY, commercial:true | No |
| **Hatch chart for Shenandoah** | Auto-seed from East-Coast generic baseline (BWO, Sulphur, Caddis, Trico, Hellgrammite, Stonefly, Slate Drake). Flag `needs_entomologist_review=true`. | ~1 hour | Project-curated, commercial:true | No — RiverPath Hatch panel renders empty-state when no data |
| **Fly shops + guides directory** | Manual research + seed. Target 5-8 rows. | ~1-2 hours | Project-curated, commercial:true | No — RiverPath surface degrades gracefully |
| **Mineral shops directory** | Manual research + seed. Target 2-3 rows. | ~30 min | Project-curated, commercial:true | No — DeepTrail surface degrades gracefully |
| **Rockhounding sites** | Manual research + seed; CONSERVATIVE. Most Shenandoah land is NPS (collecting prohibited) or private. Target 1-3 rows max, all with verified land-owner + collecting-rules. | ~2-3 hours | Project-curated, commercial:true | No |
| **SNOTEL snowpack** | None — geographic mismatch. Accept empty. | 0 | N/A | No — RiverPath snowpack panel handles empty state |
| **Catch-prediction model priors** | Retrain `gold.predictions` with East-Coast species priors (smallmouth bass, brook trout, brown trout) OR fall back to neutral score for warm-water reaches. Open Phase B bead. | medium (model retrain) | derived | No for v1; catch sub-score is one of 6 |

**Pre-existing cross-watershed gaps surfaced during this inventory** (separate beads, not blocking Shenandoah ship):

| Pre-existing gap | Severity | Bead recommendation |
|---|---|---|
| `bronze.guide_availability` has zero adapters anywhere — scaffolding only | Med | P2 — author first guide adapter (any watershed) to validate the divergence-note path end-to-end |
| OWDP/wqp source-type divergence makes WQP rows invisible in freshness UI | Low | P3 — fix `owdp.py` to write `source_type='wqp'` or rename CLI key |
| ADR-008 `SOURCE_META` runtime dict not implemented; license metadata lives only in adapter docstrings | Med | P2 — implement `SOURCE_META` per ADR-008 so the per-row `license` + `commercial` tagging the user asked for in Q3 is queryable (currently we'd have to grep docstrings) |
| Stocking adapter pattern is duplicated per-state (`fishing.py`, `washington.py`, `utah.py`, soon VA + WV) | Low | P3 — extract a `StateStockingAdapter` base class to reduce duplication |

---

## §1.5 — Estimated adapter authoring scope (Step 2 preview)

Given the user confirmed authoring VA + WV state adapters, the Step 2 implementation breaks down as:

| Adapter | Effort | Required for v1 RiverPath ship | Priority |
|---|---|---|---|
| `va_dwr_stocking` | ~1d | RiverPath stocking panel | **P1** |
| `wv_dnr_stocking` | ~1d | RiverPath stocking panel | **P1** |
| `va_dwr_regs` (or seed migration) | ~0.5d | TQS access sub-score | **P2** — TQS works without it but over-promises on special-reg streams |
| `wv_dnr_regs` (or seed migration) | ~0.5d | Same | **P2** |
| `vgs_geology` | ~1.5d | DeepTrail geology surface | **P2** — Macrostrat baseline serves v1 |
| `wvges_geology` | ~1.5d | DeepTrail geology | **P3** — VGS handles most of basin; WV only on lower main-stem |
| `va_dcr_parks` / `wv_state_parks` | ~1d combined | RiverPath recreation panel | **P3** — RIDB sufficient for v1 |
| `restoration.py` extension (CBP + FotSR) | ~1.5d | RiverSignal restoration tracking | **P2** |
| `fish_passage.py` extension (American Rivers) | ~1d | RiverPath fish passage panel | **P3** |

**Total v0+P1 scope: ~2-3 days** (just stocking adapters + watershed wiring).
**Total v0+P1+P2: ~5-7 days** (adds regs, geology, restoration extension).
**Total full scope: ~9-12 days** (everything above).

Recommendation: ship **v0 + P1** first (stocking adapters + base watershed wiring + curation seeds + frontend wiring). Open P2 and P3 work as follow-on beads after the watershed is visibly live.

---

## §1.6 — Watershed config preview (Step 2.1)

```python
# pipeline/config/watersheds.py
"shenandoah": {
    "name": "Shenandoah River",
    "description": (
        "Shenandoah River from North Fork (Bergton, VA) and South Fork "
        "(Sherando, VA) headwaters through the Shenandoah Valley to the "
        "Potomac confluence at Harpers Ferry, WV. First Atlantic-slope "
        "watershed on the platform."
    ),
    "bbox": {
        "north": 39.35,
        "south": 37.70,
        "east": -77.65,
        "west": -79.40,
    },
},
```

---

## §1.7 — Reach inventory preview (Step 2.4)

Three v0 reaches anchored on USGS gauges + obvious confluences (mirrors McKenzie's 3-reach
structure):

| Reach ID | Name (short) | Primary USGS gauge | River mile | Typical species | Warm-water? | Notes |
|---|---|---|---|---|---|---|
| `shenandoah_north_fork` | North Fork | 01634000 (NF Shenandoah nr Strasburg, VA) | n/a | brook_trout, brown_trout, rainbow_trout, smallmouth_bass | false (cold tribs) | needs_guide_review |
| `shenandoah_south_fork` | South Fork | 01631000 (SF Shenandoah at Front Royal, VA) | n/a | brown_trout, rainbow_trout, smallmouth_bass | partial | needs_guide_review |
| `shenandoah_main_stem` | Main Stem | (no single gauge on main stem; use 01636500 Shenandoah River at Millville, WV) | n/a | smallmouth_bass, channel_catfish, fallfish | true (smallmouth dominant) | needs_guide_review |

A 4th reach for the limestone-stream subset (Mossy Creek, Beaver Creek) is a candidate but
would be the first cross-cutting non-mainstem reach — flag for guide review.

---

## §1.8 — Step 2 / Step 3 sequence recommendation

1. Commit this inventory (the document you're reading) under a Step-1 commit.
2. Watershed config entry (§2.1).
3. v0 curation seeds (§2.4) — reaches, flow bands, hatch chart, fly shops, mineral shops,
   rockhounding sites — all marked `needs_review=true`. One commit per artifact.
4. Author VA + WV stocking adapters (§2.2) — two new adapters with module-docstring license
   declarations per ADR-008. One commit per adapter with unit test.
5. Run all applicable existing adapters scoped to `-w shenandoah` (§2.3). Skip PNW-only adapters.
6. Wire frontend (§2.6) — touch ~13 files per the runbook's hit table.
7. Refresh medallion + TQS daily refresh (§2.5).
8. **Pause for user review** before §2.7 (terraform args for state adapter scheduling) and §2.8
   (prod deploy with 4 explicit approval gates).
9. After approval: terraform plan + apply (targeted), commit + push, watch deploy, execute prod
   jobs (with each Gate 1/2/3 ask).
10. Write Step 3 verification report (`shenandoah-verification-<date>.md`) — schema-level
    checks, API smoke (local + prod), feature-coverage grid mirrored against the McKenzie
    reference.

---

**End of Step 1 inventory. Ready for user review before Step 2 begins.**
