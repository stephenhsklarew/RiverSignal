# Source Inventory & Gap Report: Mad River (Ohio)

| | |
|---|---|
| **Watershed slug** | `mad_river_oh` |
| **Display name** | Mad River |
| **States** | OH |
| **Date** | 2026-05-25 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (via `/add-watershed` skill — gap-analysis only; user evaluating whether to onboard) |
| **Status** | Step 1 complete — **research-only, no Step 2 commitment yet**. Companion inventory: `chattahoochee-source-inventory-2026-05-25.md` |

---

## Step 0 — Pre-flight clarification (CONFIRMED by user 2026-05-30)

User acknowledged all six answers on 2026-05-30 via the `/add-watershed` skill before any Step 2 work began.

| # | Question | Confirmed answer | Notes |
|---|---|---|---|
| Q1 | HUC boundary level | **HUC8 `05080001` + 0.05° buffer** (bbox N40.60/S39.65/E-83.45/W-84.30) | As proposed in inventory |
| Q2 | Paid-API tolerance | **Stop and ask** if any v1 source needs a paid key | Won't trigger — all OH feeds are ORC §149.43 public record |
| Q3 | B2B license filter | **Tag with `license` + `commercial:true\|false`; do NOT gate** | Shenandoah posture. **Overrides the runbook's ADR-008 gate-by-default** — user chose tag-only for Mad River |
| Q4 | Confluence into existing watershed | N/A — Mad → Great Miami → Ohio River; Great Miami is not on the platform | Skipped |
| Q5 | Curation pace | **Ship v0 with `needs_review=true` flags** on hatch chart / fly shops / rockhound sites | OH brown-trout-on-limestone hatch chart flagged `needs_entomologist_review=true` |
| Q6 | Target ship date | **Ship this session** — drive to prod through the four §2.8 approval gates | Tighter than inventory's "no deadline" assumption; terraform apply + prod deploy happen this session |
| **Scope** | If onboarded, author 1 new state adapter (`ohio_stocking`) for v0+P1; extend `restoration` and verify `impaired`/ATTAINS for OH as P2 | Materially smaller scope than Shenandoah (1 new adapter vs 2) |

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `mad_river_oh` (suffix disambiguates from Mad River VT and Mad River CA) | proposed |
| Display name | Mad River | proposed |
| States | OH | user |
| Headwaters | Springs near Campbell Hill (Logan County, OH — highest point in Ohio at 1,549 ft); also fed by glacial outwash aquifer | USGS NHDPlus + Ohio DGS |
| Mouth | Confluence with the **Great Miami River at Dayton, OH** (Great Miami is not currently tracked on the platform) | USGS NHDPlus |
| Bbox (proposed) | `north=40.60, south=39.65, east=-83.45, west=-84.30` | Refined from agent research; covers Logan / Champaign / Clark / Greene / Montgomery county portions of the basin + 0.05° buffer |
| HUC8 code | `05080001` (Upper Great Miami headwaters; Mad is the principal cold-water sub-basin) | USGS WBD |
| NWS forecast office | **ILN** (Wilmington, OH) covers the entire 52-county CWA including Logan / Champaign / Clark / Montgomery | api.weather.gov/points |
| Drainage area at mouth | ~660 mi² | USGS basin reports |
| Primary fishery | **Brown trout** (Mad River is one of only two stocked trout streams in Ohio; ~11,500 yearling browns stocked annually at ~500/mile every mid-October); smallmouth bass in lower reaches; warmwater panfish | Ohio DNR Division of Wildlife; CFRTU brown-trout program |

This would be the **first Midwest / Ohio-River-Basin watershed** on the platform. Implications:

- All PNW-specific adapters (StreamNet, ODFW, WDFW, UDWR, DOGAMI, PCSRF, SNOTEL, BLM SMA) return empty — same posture as Shenandoah. Already a solved problem.
- The brown-trout-on-limestone-spring fishery is structurally similar to Mossy Creek (Shenandoah) — the existing East-Coast hatch chart can seed Ohio with `needs_review=true`.
- Rich **Paleozoic carbonate paleo** surface (Ordovician–Devonian) gives DeepTrail genuinely new content (PBDB has 129 occurrences in bbox).
- Glacial-outwash hydrology means stable summer baseflow — unlike Shenandoah's rainfall-driven runoff, the Mad's TQS flow sub-score should rarely flag low-flow stress.

---

## §1.1 — Feature → source map (per app, for Mad River OH)

| App | Feature | Required data | Existing adapter | Status for Mad River OH |
|---|---|---|---|---|
| **RiverSignal** | Site dashboards | USGS NWIS time series | `usgs` | ✓ — 2 primary gauges (Eagle City, Springfield) + Zanesfield + Indian Lake |
| RiverSignal | Restoration tracking | OWRI / NOAA RC / PCSRF | `restoration` | ⚠ — PNW-scoped today; needs OH analogue (EPA Section 319 grants + OEPA SWIF + H2Ohio) |
| RiverSignal | Fire recovery | MTBS perimeters | `mtbs` | ✗ N/A — no significant wildfire footprint W-central OH; graceful empty (handled) |
| RiverSignal | Water quality | EPA WQP | `wqp` | ✓ — 151 stations in bbox; OH EPA submits under provider `21OHIO_WQX` |
| RiverSignal | Macroinvertebrate quality | EPA WQP_BUGS | `wqp_bugs` | ✓ — `21OHIO_WQX` contributes macroinvertebrate samples |
| RiverSignal | 303(d) impaired | EPA ATTAINS | `impaired` | ⚠ — OH submits 2024 IR to ATTAINS, but federal adapter's `huc=05080001` query returned 0 in agent test; likely needs `state=OH` + `reportingCycle=2024` parameterization. **Smoke-test required before launch** |
| RiverSignal | Land ownership / access | BLM SMA, USFS, state parks | `blm_sma`, `recreation` | ⚠ — RIDB covers USACE C.J. Brown Reservoir + Caesar Creek Lake; **misses ODNR state parks (Buck Creek SP campground, Kiser Lake SP)** which use ReserveOhio (no public API) |
| RiverSignal | Watershed geometry | USGS WBD + NHDPlus | `wbd`, `nhdplus` | ✓ — federal CONUS |
| RiverSignal | Wetlands | USFWS NWI | `wetlands` | ✓ — abundant glacial wetlands in upper Mad |
| **RiverPath** | Go Score — flow + temp sub-scores | USGS gauges | `usgs` | ✓ |
| RiverPath | Go Score — weather | NWS forecast | `nws`, `nws_forecast` | ✓ — ILN gridpoints |
| RiverPath | Go Score — hatch | `curated_hatch_chart` | manual seed | ✗ — no OH hatch chart. Seed from East-Coast limestone-stream baseline (BWO, Sulphur, Caddis, Trico, Hendrickson, Sulphur Dun, Slate Drake) with `needs_entomologist_review=true` |
| RiverPath | Go Score — access | MTBS + closures | `mtbs` + manual | ⚠ — MTBS empty; closures: ODNR special-regs published as HTML/PDF (no structured feed) — manual seed |
| RiverPath | River Now hero | USGS instantaneous + NWS current | live | ✓ |
| RiverPath | Photo observations | iNaturalist | `inaturalist` | ✓ — ~99K research-grade obs in 5y in bbox |
| RiverPath | **Stocking schedule** | State hatchery feeds | `fishing` (OR) / `washington` / `utah` | ⚠ — **NEW `ohio_stocking` adapter required**. DataOhio "Fish Stocking Records" dashboard (back to 1970) + ODNR DoW trout-stockings page. Risk: ODNR page is CDN/UA-gated (404'd on WebFetch); DataOhio may be Tableau/PowerBI embed without CSV |
| RiverPath | Fish passage | USGS / state passage barriers | `fish_passage` | ⚠ — verify USFWS NFPP nationwide feed against Huffman Dam removal (2003) + lowhead dams documented in OH |
| RiverPath | Swim safety | Derived | `gold.swim_safety` | ✓ |
| RiverPath | Snowpack | NRCS SNOTEL | `snotel` | ✗ — SNOTEL is Western US only. Acceptable empty (Mad is spring-fed, not snow-fed) |
| RiverPath | Recreation sites | RIDB | `recreation` | ⚠ — federal coverage only (USACE C.J. Brown); ODNR state parks miss |
| RiverPath | Fly shop directory | Manual | `fly_shops_guides` | ⚠ — research targets: Mad River Outfitters (Columbus), Mike's Place (Springfield), Buckeye United Fly Fishers |
| RiverPath | Guide service directory | Manual | `fly_shops_guides` (type='guide') | ⚠ — small market; 2-4 row target |
| **DeepTrail** | Geology units | Macrostrat + state geology | `macrostrat`, `dogami` | ⚠ — Macrostrat OK; **NEW `odgs` adapter** is high-value (ODGS ArcGIS REST live at `gis.ohiodnr.gov/arcgis/rest/services/DGS_Services/Bedrock_Geology_24K_AGOL/{Map,Feature}Server`, 24K + 500K resolutions) |
| DeepTrail | Fossil sites | PBDB + iDigBio + GBIF | `pbdb`, `idigbio`, `gbif` | ✓ — **129 PBDB occurrences** in bbox (Ord/Sil/Dev carbonate fauna — corals, brachiopods, bryozoans); rich content surface |
| DeepTrail | Rockhound sites | Manual | `rockhounding_sites` | ⚠ — modest targets: Clark County calcite geodes, Logan County glacial erratics, Bellefontaine quarry fossils |
| DeepTrail | Mineral & rock shop directory | Manual | `mineral_shops` | ⚠ — 1-2 target rows (Columbus / Dayton area) |
| DeepTrail | Mineral deposits | USGS MRDS | `mrds` | ⚠ sparse — limestone/dolomite/sand-gravel industrial only; no metallics. Graceful coverage but unimpressive |

---

## §1.3 — Per-source check matrix

License + commercial flag captured per Q3 (tag, don't gate). Format:
`<status> <source> — <evidence>. License: <X>, commercial:<true|false>.`

```
✓ usgs            — 2 active stream gauges + ancillary: 03267900 Mad R at St Paris Pike at Eagle City (310 mi² DA, Clark Co.), 03269500 Mad R near Springfield, plus Zanesfield + Indian Lake.   License: Public Domain, commercial:true
✓ nws             — ILN (Wilmington OH) covers all 5 basin counties.   License: Public Domain, commercial:true
✓ nws_forecast    — Same ILN coverage for 7-day forecast.   License: Public Domain, commercial:true
✓ inaturalist     — ~99,410 research-grade observations in bbox (-84.30,39.65,-83.45,40.60) since 2021.   License: CC-BY-NC (photo URLs FALSE; observation metadata commercial:true)
✗ mtbs            — No significant wildfire footprint in W-central OH; layer returns empty (acceptable).   License: Public Domain (N/A here)
✓ wbd             — HUC8 05080001 boundary available.   License: Public Domain, commercial:true
✓ nhdplus         — Stream flowlines for entire Mad system.   License: Public Domain, commercial:true
✓ wqp             — 151 monitoring stations in bbox via WQP /Station/search; both USGS-OH and 21OHIO_WQX providers.   License: Public Domain, commercial:true
✓ wqp_bugs        — 21OHIO_WQX contributes macroinvertebrate samples.   License: Public Domain, commercial:true
⚠ impaired        — OH submits 2024 IR via EPA ATTAINS; federal adapter query with huc=05080001 returned 0 in agent test. Likely needs state=OH + reportingCycle=2024. SMOKE-TEST REQUIRED before launch.   License: Public Domain, commercial:true
✓ wetlands        — USFWS NWI: abundant glacial wetlands across upper Mad.   License: Public Domain, commercial:true
✓ prism           — CONUS coverage.   License: Academic Free, commercial:true
⚠ recreation      — RIDB: USACE C.J. Brown Reservoir (Buck Creek SP overlay) + Caesar Creek Lake. MISSES ODNR-only state parks (Buck Creek SP campground via ReserveOhio, Kiser Lake SP) — ODNR uses ReserveOhio.com with no public API.   License: Public Domain, commercial:true
✓ biodata         — USGS BioData: OH fish + macroinvertebrate sites present.   License: Public Domain, commercial:true
✓ gbif            — Global biodiversity records; iNat firehose flows to GBIF.   License: CC-BY 4.0, commercial:true
✓ idigbio         — OH specimen records well-collected.   License: varies (CC0 / CC-BY mostly), commercial:true
✓ pbdb            — 129 occurrences in bbox: Ordovician (Richmondian), Silurian (Aeronian/Llandovery), Devonian (Famennian) — corals, brachiopods, bryozoans.   License: CC0, commercial:true
✓ macrostrat      — Macrostrat columns cover OH; tied to USGS state geology compilations.   License: CC-BY 4.0, commercial:true
⚠ mrds            — Sparse: industrial minerals only (limestone/dolomite/sand-gravel); no metallic deposits. Direct WFS bbox queries failed (400/typename mismatch) in agent test; adapter should still return a handful.   License: Public Domain, commercial:true
⚠ restoration     — `restoration` adapter is PNW-scoped (OWRI / PCSRF / NOAA RC). OH analogue: EPA Section 319 grants + OEPA Surface Water Improvement Fund + H2Ohio program datasets. Adapter extension required for any OH coverage.   License: Public Domain, commercial:true
⚠ fish_passage    — Adapter exists but PNW-skewed. Mad River has documented Huffman Dam removal (2003) + several lowhead dams. Verify against USFWS NFPP national feed.   License: Public Domain, commercial:true
⚠ ohio_stocking   — NEW adapter. DataOhio "Fish Stocking Records" dashboard (1970→present) + ODNR DoW trout-stockings page (https://ohiodnr.gov/buy-and-apply/hunting-fishing-boating/fishing-resources/trout-stockings — currently CDN/UA-gated). Mad River specifically: ~11,500 brown-trout yearlings stocked annually at ~500/mile every mid-October.   License: ORC §149.43 public records, commercial:true
⚠ odgs_geology    — NEW adapter. Ohio DNR Division of Geological Survey. ArcGIS REST live: gis.ohiodnr.gov/arcgis/rest/services/DGS_Services/Bedrock_Geology_24K_AGOL/{Map,Feature}Server (24K + 500K resolutions). UNIT_CODE / UNIT_LITH / UNIT_AGE fields. No explicit license — ORC §149.43 applies.   License: Public Records (ORC §149.43), commercial:true
⚠ odnr_regs       — NEW adapter (or static seed). OH special-regulation streams (Mad River C&R section, gear restrictions). HTML; quarterly cadence.   License: Public Records, commercial:true
⚠ ohio_state_parks — NEW adapter (or skip). ReserveOhio.com is the booking system; no public API. May require scrape or defer.   License: Public Records, commercial:true
✗ snotel          — Western US only.   N/A
✗ blm_sma         — No BLM land in OH.   N/A
✗ dogami / streamnet / washington / utah / fishing — PNW/UT-specific.   N/A
✗ curated_hatch_chart — No OH hatch chart. Seed from East-Coast limestone-stream baseline (BWO, Sulphur, Hendrickson, Caddis, Trico, Slate Drake) with needs_entomologist_review=true.   License: project-curated, commercial:true
✗ fly_shops_guides — No Mad River rows. Targets: Mad River Outfitters (Columbus), Mike's Place (Springfield), Buckeye United Fly Fishers.   License: project-curated, commercial:true
✗ mineral_shops    — No Mad River rows. 1-2 target rows in Columbus / Dayton metro area.   License: project-curated, commercial:true
✗ rockhounding_sites — No Mad River rows. Conservative targets: Clark County calcite geodes, Logan County glacial erratics (viewing only on most), Bellefontaine quarry fossils.   License: project-curated, commercial:true
```

Totals: **15 ✓** (work as-is), **8 ⚠** (existing adapter needs extension or new adapter authoring), **8 ✗** (not applicable to this watershed OR manual curation seeds needed).

---

## §1.4 — Gap report + recommended fills

| Gap | Recommended fill | Cost / effort | License + commercial | Blocker for v1? |
|---|---|---|---|---|
| **OH trout stocking (Mad R brown trout)** | New adapter `ohio_stocking` — primary path: DataOhio "Fish Stocking Records" dashboard (back to 1970); fallback: ODNR DoW trout-stockings page (currently CDN/UA-gated, may require UA header tweak or ORC §149.43 records request). | **2.5d** (or up to 5d if DataOhio is a Tableau/PowerBI embed without CSV export) | ORC §149.43 public record, commercial:true | **Yes for signature feature** — Mad River is one of OH's only 2 stocked trout streams. `gold.stocking_schedule` MV degrades gracefully to empty (verified pattern) |
| **`impaired` (ATTAINS) smoke-test fix for OH** | Verify federal adapter resolves OHEPA assessment units for HUC 05080001. Likely a 1-line query-shape fix (add `state=OH` + `reportingCycle=2024`). | **0.5d** | Public Domain, commercial:true | **Yes** — water-quality surface ships blank for OH otherwise |
| **ODGS bedrock geology layer** | New adapter `odgs` — ArcGIS FeatureServer at `gis.ohiodnr.gov/arcgis/rest/services/DGS_Services/Bedrock_Geology_24K_AGOL/FeatureServer`. Follow `geology.py` `GeologicUnitsAdapter` pattern. Both 24K (basin-scale) and 500K (regional) layers. | **1d** | Public Records (ORC §149.43), commercial:true | No — DeepTrail can ship with Macrostrat-only for v1; ODGS unlocks 24K detail (much sharper than Macrostrat) |
| **ODNR special-regulation streams** | Static seed migration `silver.reach_regulations` for the C&R section + gear restrictions on Mad River. Quarterly recheck. | ~0.5d | Public Records, commercial:true | No — TQS access sub-score over-promises on a special-reg stream without this, but operational risk is low |
| **Restoration (OH analogue)** | Extend `restoration.py` to pull from EPA Section 319 grants + OEPA Surface Water Improvement Fund + H2Ohio program datasets. | ~2d | Public Domain, commercial:true | No — RiverSignal restoration view ships sparse |
| **Fish passage (OH detail)** | Verify `fish_passage` adapter pulls USFWS NFPP nationally for OH (Huffman Dam, lowhead dam inventory). | ~0.5d | Public Domain, commercial:true | No |
| **ODNR state parks (Buck Creek, Kiser Lake)** | Scrape ReserveOhio (~2d, fragile) or defer; RIDB already covers USACE/federal in basin. | ~2d or defer | Public Records, commercial:true | No — RIDB covers C.J. Brown which is the primary recreation surface |
| **Hatch chart for Mad River** | Auto-seed from East-Coast limestone-stream baseline (BWO, Sulphur, Hendrickson, Caddis, Trico, Slate Drake). Flag `needs_entomologist_review=true`. OH limestone-spring mayfly mix likely closer to Mossy Creek (Shenandoah) than to Pacific NW. | ~1 hour | Project-curated, commercial:true | No |
| **Fly shops + guides directory** | Manual research + seed. Target 3-5 rows (smaller market than Shenandoah). | ~1 hour | Project-curated, commercial:true | No |
| **Mineral shops directory** | Manual research + seed. Target 1-2 rows. | ~30 min | Project-curated, commercial:true | No |
| **Rockhounding sites** | Conservative seed: Clark County calcite geodes, Logan County glacial erratics (viewing), Bellefontaine quarry. 1-3 rows. | ~1-2 hours | Project-curated, commercial:true | No |
| **SNOTEL snowpack** | None — geographic mismatch. Accept empty. | 0 | N/A | No |
| **MTBS fire perimeters** | None — minimal OH coverage. Accept empty. | 0 | N/A | No |
| **Catch-prediction model priors** | Same East-Coast-species posture as Shenandoah; reuse priors (brown trout, smallmouth) | 0 (already opened as Shenandoah follow-on) | derived | No |

---

## §1.5 — Estimated adapter authoring scope (Step 2 preview)

| Adapter | Effort | Required for v1 RiverPath ship | Priority |
|---|---|---|---|
| `ohio_stocking` | ~2.5d (up to 5d if DataOhio embed turns out to be Tableau without CSV) | RiverPath stocking panel + signature feature | **P0** |
| `impaired` ATTAINS smoke-test fix for OH | ~0.5d | RiverSignal impaired-waters layer | **P0** |
| `odgs` ArcGIS REST (bedrock geology) | ~1d | DeepTrail geology detail | **P1** |
| `restoration.py` extension (OH 319 + SWIF + H2Ohio) | ~2d | RiverSignal restoration tracking | **P2** |
| `fish_passage` OH verification pass | ~0.5d | RiverPath fish passage panel | **P2** |
| `odnr_regs` (static seed) | ~0.5d | TQS access sub-score | **P2** |
| ReserveOhio state parks scrape | ~2d | RiverPath recreation completeness | **P3** (defer) |
| Adapter wiring / fixtures / tests | ~1d | — | **P0** (overhead) |

**Total v0+P0 scope: ~4.0d** (`ohio_stocking` + ATTAINS smoke-test + wiring).
**Total v0+P0+P1: ~5.0d** (adds ODGS bedrock geology).
**Total full scope: ~9.5d** (everything above).

Recommendation: ship **v0+P0** first (signature stocking adapter + ATTAINS fix + base watershed wiring + curation seeds + frontend wiring). Open P1/P2/P3 work as follow-on beads after the watershed is visibly live.

---

## §1.6 — Watershed config preview (Step 2.1)

```python
# pipeline/config/watersheds.py
"mad_river_oh": {
    "name": "Mad River",
    "description": (
        "Mad River from headwater springs near Campbell Hill (Logan "
        "County, OH — highest point in Ohio) through Champaign and "
        "Clark counties to the Great Miami confluence at Dayton. "
        "Spring-fed limestone-influenced stream; one of only two "
        "stocked trout fisheries in Ohio. First Midwest / Ohio-River "
        "Basin watershed on the platform."
    ),
    "bbox": {
        "north": 40.60,
        "south": 39.65,
        "east": -83.45,
        "west": -84.30,
    },
},
```

---

## §1.7 — Reach inventory preview (Step 2.4)

Three v0 reaches anchored on USGS gauges + the regulated trout section:

| Reach ID | Name (short) | Primary USGS gauge | Typical species | Warm-water? | Notes |
|---|---|---|---|---|---|
| `mad_river_oh_upper` | Upper Mad (Logan Co. headwaters to Urbana) | 03267900 Mad R at Eagle City *(downstream proxy until upper gauge found)* | brown_trout, brook_trout (rare), creek chub | false (cold spring-fed) | needs_guide_review; verify if any upper-basin gauge exists |
| `mad_river_oh_trout_section` | Mad River C&R Trout Section (Champaign/Clark Co. — the stocked stretch) | 03267900 Eagle City | brown_trout (stocked + holdover), rainbow_trout (limited), smallmouth_bass (lower edge) | partial (cold mainstem, warm in summer afternoons) | needs_guide_review — confirm exact C&R boundaries with ODNR |
| `mad_river_oh_lower` | Lower Mad (Springfield to Dayton mouth) | 03269500 Mad R nr Springfield | smallmouth_bass, rock_bass, channel_catfish | true (warm-water dominant below Springfield) | needs_guide_review |

---

## §1.8 — Step 2 / Step 3 sequence recommendation

1. Commit this inventory under a Step-1 commit.
2. Watershed config entry (§2.1) — single dict entry in `pipeline/config/watersheds.py`.
3. v0 curation seeds (§2.4) — reaches, flow bands, hatch chart, fly shops, mineral shops, rockhounding sites — all `needs_review=true`. One commit per artifact.
4. Author `ohio_stocking` adapter (§2.2) — module-docstring license declaration per ADR-008; unit test against captured fixtures.
5. **Fix `impaired` ATTAINS query for OH** — small touch in `app/pipeline/ingest/impaired.py` (verify `state=OH` + `reportingCycle=2024` parameters land OH assessment units in HUC 05080001).
6. Run all applicable existing adapters scoped to `-w mad_river_oh` (§2.3). Skip all PNW/UT-specific ones (already handled in adapter dispatch).
7. (P1) Author `odgs` adapter if time permits in same pass.
8. Wire frontend (§2.6) — ~13 files per runbook hit table; add `mad_river_oh: 'Mad River (OH)'` (with state suffix in display label since "Mad River" alone is ambiguous across VT/CA/OH).
9. Refresh medallion + TQS daily refresh (§2.5).
10. **Pause for user review** before §2.7 (terraform args) and §2.8 (prod deploy with 4 explicit approval gates).
11. Write Step 3 verification report (`mad_river_oh-verification-<date>.md`).

---

## Comparison summary (vs Chattahoochee GA)

| Dimension | Mad River OH | Chattahoochee GA |
|---|---|---|
| USGS gauges in bbox | 2 active | 9 active |
| iNat 5y obs in bbox | ~99K | ~445K |
| WQP stations | 151 | dense (state + Riverkeeper) |
| New adapters required for v0 | 1 (`ohio_stocking`) | 2 (`ga_trout` + `usace_sam_hydropower`) |
| v0+P1 effort | **~4d** | ~8d |
| Full scope | ~9.5d | ~12d |
| Critical-path risk | ODNR page is CDN/UA-gated (stocking adapter could grow from 2.5d → 5d if DataOhio is Tableau embed) | Buford Dam release/safety scrape (safety-critical, fragile HTML scrape, no JSON API) |
| Signature DeepTrail content | **129 PBDB carbonate fossils** (Ord/Sil/Dev) — genuinely new content surface | Dahlonega Gold Belt (richest MRDS slice in project) |
| Signature RiverPath content | Brown-trout-on-spring-creek stocking schedule | Tailwater trout + Atlanta urban-river + dam-release safety |

**Recommendation (carried over from gap-analysis comparison):** load **Mad River OH next** — half the effort, cleaner risk profile, opens the Midwest paleo content surface. Defer Chattahoochee until iNat-firehose pagination + dam-release-safety adapter pattern can be designed as their own beads.

---

**End of Step 1 inventory. No Step-2 commitment made yet — awaiting user direction.**
