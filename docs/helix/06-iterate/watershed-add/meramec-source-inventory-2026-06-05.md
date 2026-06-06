# Source Inventory & Gap Report: Meramec River (Missouri)

| | |
|---|---|
| **Watershed slug** | `meramec` |
| **Display name** | Meramec River |
| **States** | MO (entirely) |
| **Date** | 2026-06-05 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (gap-analysis only; user evaluating whether to onboard) |
| **Status** | Step 1 complete — **research-only, no Step 2 commitment yet**. |

---

## Step 0 — Pre-flight clarification (deferred — confirm before Step 2 if user chooses this watershed)

| # | Question | Assumed default | Material effect if different |
|---|---|---|---|
| Q1 | HUC boundary level | **Three HUC8s** — `07140102` Meramec main stem (+ `07140103` Bourbeuse, `07140104` Big River) + 0.05° buffer | If only the main stem (`07140102`) is in scope, the Big River lead-contamination story and the Bourbeuse drop out. Recommend all three for a complete basin. |
| Q2 | Paid-API tolerance | Stop and ask if any v1 source needs a paid key | None expected — all candidate MO feeds are RSMo Ch. 610 (Sunshine Law) public record |
| Q3 | B2B license filter | Tag with `license` + `commercial:true\|false`; do not gate | All MO state-agency data is public record + `commercial:true` |
| Q4 | Confluence into existing watershed | N/A — Meramec → Mississippi River south of St. Louis; no downstream platform watershed | Skipped |
| Q5 | Curation pace | Ship v0 with `needs_review=true` on hatch chart / fly shops / rockhound sites | Smallmouth float-stream + spring-fed trout-park mix; expect one hatch chart won't fit both |
| Q6 | Target ship date | No deadline | — |
| **Scope** | If onboarded: **0 safety-critical adapters** (no dam). 1 easy new adapter (`mo_geology`, ArcGIS REST). **Stocking has no machine-readable upstream** — decide manual-seed vs. fragile HTML scrape. | Materially **lighter** than Chattahoochee (no Buford-style dam-release safety adapter) but with one awkward gap: MDC publishes no structured stocking data. |

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `meramec` | proposed |
| Display name | Meramec River | proposed (suffix-free per house style) |
| States | MO (100%) | — |
| Headwaters | Ozark plateau, Dent County, SE of **Salem, MO** | [USGS NHDPlus / Wikipedia](https://en.wikipedia.org/wiki/Meramec_River) |
| Mouth | **Mississippi River** just south of St. Louis, near **Arnold / Oakville** (Jefferson / St. Louis county line) | Wikipedia |
| Length | ~218 mi (free-flowing) | Wikipedia |
| Drainage area | ~3,980 mi² full basin (MDC inventories the main stem at 2,149 mi² + Big ~960 + Bourbeuse ~843 separately) | [MDC Meramec WIA](https://mdc.mo.gov/sites/default/files/2021-12/200_2021_MeramecRiver.pdf) |
| Major tributaries | **Bourbeuse River** (north), **Big River** (south), Huzzah Creek, Courtois Creek | MDC |
| Key impoundments | **NONE on the main stem.** Proposed Meramec Park Dam (Union Lake) was **killed by a 12-county referendum on 1978-08-08** (~64% against) and de-authorized 1981; the river is free-flowing. No major dam on Big River or Bourbeuse. | [Sierra Club](https://www.sierraclub.org/missouri/eastern-missouri/sierrascape/s2003m06/01_25_years); Wikipedia |
| Bbox (proposed) | `north=38.65, south=37.55, east=-90.25, west=-91.65` | Refined from verified gauge coords (Steelville 37.998/-91.361 → Eureka 38.505/-90.590 → Oakville confluence) + buffer |
| HUC8 codes | `07140102` (Meramec), `07140103` (Bourbeuse), `07140104` (Big River) — all Region 07 (Upper Mississippi) | USGS NWIS site `huc_cd` |
| NWS forecast office | **LSX** (St. Louis) covers the lower/middle basin + metro; far-SW headwaters near Salem may edge to **SGF** (Springfield) | [api.weather.gov/points/38.50,-90.59](https://api.weather.gov/points/38.50,-90.59) |
| Primary fishery | **Premier smallmouth bass float stream** (the Steelville reach is "the Floating Capital"); **rainbow trout at Maramec Spring** (one of MO's 4 trout parks); goggle-eye/rock bass, spotted & largemouth bass, channel catfish, walleye | MDC |
| Notable land status | **Meramec State Park** (Fisher Cave), **Onondaga Cave State Park** (Onondaga + Cathedral caves), **Maramec Spring Park** (private — James Foundation; MDC-stocked trout), **Mark Twain National Forest** (Salem/Potosi districts — Huzzah/Courtois), **Castlewood SP** + **Route 66 SP** in the St. Louis suburbs | Missouri State Parks; USFS |

### What makes Meramec distinctive (vs prior watersheds)

- **No dam = no safety-critical adapter.** Unlike Chattahoochee (Buford Dam tailwater surge), the Meramec is free-flowing. The dominant hazard is **rainfall-driven flash flooding** in a flashy karst basin (record floods 2015, 2017) — served adequately by existing NWS + real-time gage-height (00065) feeds. This removes the single biggest cost driver Chattahoochee carried.
- **Water-temperature gap.** Of 8 verified gauges, **only Huzzah Creek (07014000) reports real-time water temperature (00010)**. The main-stem gauges (Steelville, Sullivan, Eureka) and Bourbeuse-at-Union report discharge + gage height only. Go Score's temp sub-score will fall back to the climatology proxy on the main-stem reaches, and Catch Probability will render its "no water-temperature gauge" note there — both already-handled degradations, but worth surfacing to the curator.
- **Big River lead legacy = standout water-quality narrative.** The Big River drains the historic **Old Lead Belt**; the **Big River Mine Tailings Superfund site** (NPL 1992, 100M+ tons tailings) drives a **MO DNR 303(d)/TMDL for lead, zinc, and sediment** and an **active fish-consumption advisory**. This is the strongest impaired-waters story on the platform.
- **Rich DeepTrail content.** PBDB returns **165 collections / 735 occurrences** in-bbox (Mississippian crinoids — MO's state fossil — + brachiopods); MRDS is dense in the St. Francois/Washington-county lead-and-barite districts; the basin is exceptionally **cave-rich** (Meramec Caverns, Onondaga, Fisher).
- **iNaturalist volume is high** (~226K research-grade basin-wide; ~162K in the St. Louis suburban corridor — ~17–24× a rural Ozark watershed). The tile-pagination + rarity-weighting mitigation shipped for Chattahoochee applies directly; no new cross-cutting work expected.

---

## §1.1 — Feature → source map (per app, for Meramec)

| App | Feature | Required data | Existing adapter | Status for Meramec |
|---|---|---|---|---|
| **RiverSignal** | Site dashboards | USGS NWIS time series | `usgs` | ✓ — 8 active gauges across the 3 HUC8s |
| RiverSignal | Restoration tracking | OWRI / NOAA RC / PCSRF | `restoration` | ⚠ — PNW-scoped; no MO open-record restoration registry surfaced |
| RiverSignal | Fire recovery | MTBS perimeters | `mtbs` | ⚠ — sparse; some Mark Twain NF perimeters |
| RiverSignal | Water quality | EPA WQP | `wqp` | ✓ — MO DNR (STORET) + USGS providers; >1M PoR rows for MO |
| RiverSignal | Macroinvertebrate quality | EPA WQP_BUGS | `wqp_bugs` | ✓ — MO biological data in WQP |
| RiverSignal | 303(d) impaired | EPA ATTAINS | `impaired` | ✓ **standout** — **Big River Lead & Sediment TMDL** (lead/zinc/sediment, St. Francois/Jefferson Co.) on MO 2022 303(d) list |
| RiverSignal | Fish-consumption advisory (health) | MO DHSS / DNR advisory | NEW (manual seed) | ⚠ — **Big River lead advisory** is a notable health surface; no API — static seed |
| RiverSignal | Land ownership / access | BLM SMA, USFS, state parks | `blm_sma`, `recreation` | ⚠ — no BLM in MO; Mark Twain NF in RIDB; MO state parks not in RIDB |
| RiverSignal | Watershed geometry | USGS WBD + NHDPlus | `wbd`, `nhdplus` | ✓ — federal CONUS |
| RiverSignal | Wetlands | USFWS NWI | `wetlands` | ✓ — federal CONUS |
| **RiverPath** | Go Score — flow + temp | USGS gauges | `usgs` | ⚠ — flow everywhere; **real-time temp only at Huzzah 07014000**. Main-stem reaches use climatology proxy (already handled) |
| RiverPath | Go Score — weather | NWS forecast | `nws`, `nws_forecast` | ✓ — LSX gridpoints |
| RiverPath | Go Score — hatch | `curated_hatch_chart` | manual seed | ✗ — no Meramec chart. Seed Ozark smallmouth-stream hatches + Maramec Spring trout; `needs_entomologist_review=true` |
| RiverPath | Go Score — access | flooding + closures | `mtbs` + manual | ✓ — **no dam-release hazard**; flash-flood signal via gage height |
| RiverPath | River Now hero | USGS instantaneous + NWS | live | ✓ |
| RiverPath | Photo observations | iNaturalist | `inaturalist` | ⚠ — high volume (~226K/5y basin); Chattahoochee's tile-pagination/rarity mitigation applies — no new work |
| RiverPath | **Stocking schedule** | State hatchery feeds | `fishing`/`washington`/`utah`/… | ⚠ — **no machine-readable MDC source** (see §1.4). 4 trout parks (Maramec Spring daily Mar 1–Oct 31) + St. Louis winter trout lakes. Manual seed or fragile HTML scrape |
| RiverPath | Fish passage | USGS/state barriers | `fish_passage` | ⚠ — PNW-skewed; low-head structures only (no major dam) |
| RiverPath | Swim safety | derived | `gold.swim_safety` | ✓ — plus the Big River metals advisory as an overlay |
| RiverPath | Snowpack | NRCS SNOTEL | `snotel` | ✗ — none in MO. Accept empty |
| RiverPath | Recreation sites | RIDB | `recreation` | ⚠ — Mark Twain NF (Red Bluff CG #232391, MTNF gateway #1086) in RIDB; MO state parks (Meramec, Onondaga Cave) + private Maramec Spring NOT in RIDB |
| RiverPath | Fly shop / guide directory | Manual | `fly_shops_guides` | ⚠ — Feather Craft (St. Louis), Missouri on the Fly, Missouri Fly Life Guide Co.; large float-outfitter market (Steelville corridor) |
| **DeepTrail** | Geology units | Macrostrat + state geology | `macrostrat`, `dogami` | ⚠ — Macrostrat OK; **NEW `mo_geology`** via MGS ArcGIS REST `gis.dnr.mo.gov/host/rest/services/geology/` (bedrock 24k/100k/500k, alluvium, **cave_density**, abandoned_mines) |
| DeepTrail | Fossil sites | PBDB + iDigBio + GBIF | `pbdb`, `idigbio`, `gbif` | ✓ **rich** — 165 colls / 735 occ in-bbox (Mississippian crinoids + brachiopods) |
| DeepTrail | Caves / karst | derived | `mo_geology` cave_density + manual | ⚠ — Meramec Caverns, Onondaga + Cathedral, Fisher Cave — strong content; MGS publishes a `cave_density` layer |
| DeepTrail | Rockhound sites | Manual | `rockhounding_sites` | ⚠ — barite "tiff"/tiff-roses (Washington Co — Old Mines, Potosi), galena (lead belt, access-restricted), Ozark chert/druzy quartz (Steelville) |
| DeepTrail | Mineral & rock shop directory | Manual | `mineral_shops` | ⚠ — St. Louis metro candidates |
| DeepTrail | Mineral deposits | USGS MRDS | `mrds` | ✓ **standout** — Old Lead Belt (galena/sphalerite) + Washington Co. Barite District; very dense MRDS slice |

---

## §1.3 — Per-source check matrix

License + commercial flag captured per Q3 (tag, don't gate). Format:
`<status> <source> — <evidence>. License: <X>, commercial:<true|false>.`

```
✓ usgs            — 8 active gauges: 07013000 Meramec near Steelville (Q+GH), 07014000 Huzzah Cr near Steelville (Q+GH+TEMP — ONLY real-time 00010 in basin), 07014500 Meramec near Sullivan (Q+GH), 07016500 Bourbeuse at Union (Q+GH), 07019000 Meramec near Eureka (Q+GH), 07017200 Big R at Irondale (dv), 07018100 Big R near Richwoods (Q+GH), 07018500 Big R at Byrnesville (Q+GH).   License: Public Domain, commercial:true
⚠ usgs (water temp) — Real-time water temperature (00010) at ONLY Huzzah Cr 07014000. Main-stem Meramec + Bourbeuse report discharge + gage height only. Go Score temp sub-score → climatology proxy on main-stem reaches (already handled); Catch Probability shows "no gauge" note.   License: Public Domain, commercial:true
✓ nws             — WFO LSX (St. Louis) covers basin; SGF edge at SW headwaters.   License: Public Domain, commercial:true
✓ nws_forecast    — Same LSX coverage, 7-day.   License: Public Domain, commercial:true
⚠ inaturalist     — ~226K research-grade obs basin-wide (~162K in lower/STL-suburb corridor) since 2021. ~17–24× a rural Ozark watershed. Use the tile-pagination + rarity weighting already shipped for Chattahoochee.   License: CC-BY-NC (photo URLs FALSE; metadata commercial:true)
✓ wbd             — HUC8s 07140102 / 07140103 / 07140104.   License: Public Domain, commercial:true
✓ nhdplus         — Flowlines for the full Meramec/Bourbeuse/Big systems.   License: Public Domain, commercial:true
✓ wqp             — MO DNR (STORET) + USGS (NWIS) providers; >1M PoR rows statewide (statecode US:29).   License: Public Domain, commercial:true
✓ wqp_bugs        — MO biological-monitoring data flows through WQP.   License: Public Domain, commercial:true
✓ impaired        — STANDOUT: Big River Lead & Sediment TMDL (lead/zinc/sediment) on MO 2022 EPA-approved 303(d) list. Federal ATTAINS adapter should pull as-is; verify Big River segments present.   License: Public Domain, commercial:true
✓ wetlands        — USFWS NWI full CONUS.   License: Public Domain, commercial:true
✓ prism           — CONUS mid-continent coverage.   License: Academic Free, commercial:true
⚠ mtbs            — Sparse; a few Mark Twain NF perimeters.   License: Public Domain, commercial:true
✓ recreation      — RIDB: Mark Twain NF (Red Bluff CG #232391; MTNF gateway #1086). Covers federal in-basin rec. State parks + private Maramec Spring not in RIDB.   License: Public Domain, commercial:true
✓ biodata         — USGS BioData covers MO fish + macroinvert sites.   License: Public Domain, commercial:true
✓ gbif            — Global records; MO well-collected (iNat firehose mirrors here).   License: CC-BY 4.0, commercial:true
✓ idigbio         — MO specimen records present.   License: varies (CC0/CC-BY), commercial:true
✓ pbdb            — RICH: 165 collections / 735 occurrences in-bbox; Mississippian crinoids (MO state fossil) + brachiopods.   License: CC0, commercial:true
✓ macrostrat      — MO covered (USGS state compilation); coarser than MGS 24k — use as fallback to mo_geology.   License: CC-BY 4.0, commercial:true
✓ mrds            — STANDOUT: Old Lead Belt (St. Francois Co. — galena/sphalerite) + Washington Co. Barite District ("tiff"). Very dense.   License: Public Domain, commercial:true
⚠ restoration     — PNW-scoped (OWRI/PCSRF/NOAA RC); no MO open-record equivalent surfaced. Out-of-scope v1.   License: varies, commercial:true
⚠ fish_passage    — PNW-skewed; in-basin only low-head structures (no major dam).   License: Public Domain, commercial:true
⚠ mo_geology      — NEW adapter. MGS ArcGIS REST gis.dnr.mo.gov/host/rest/services/geology/ (bedrock + bedrock_24k/100k/500k, alluvium, cave_density, abandoned_mines). Same pattern as ga_geology / odgs. Hub downloads (GeoJSON/shp) at gis-modnr.opendata.arcgis.com.   License: Public Domain (state-published), commercial:true
⚠ missouri (stocking) — NO machine-readable upstream. MDC publishes stocking only via HTML newsroom prose + a recorded Fish Stocking Hotline (636-300-9651) + on-site postings. data.mo.gov (Socrata) has NO MDC stocking dataset. Options: manual seed (4 trout parks + STL winter lakes) or fragile newsroom scrape or open-records request.   License: Public Records (RSMo Ch. 610), commercial:true
✗ snotel          — None in MO.   N/A
✗ blm_sma         — No BLM land in basin.   N/A
✗ dogami / streamnet / washington / utah / fishing / georgia / virginia / ohio_stocking — other-state specific.   N/A
✗ curated_hatch_chart — No Meramec chart. Seed Ozark smallmouth-stream pattern + Maramec Spring trout; needs_entomologist_review=true. Single chart unlikely to fit both float-stream smallmouth AND spring trout park — flag for curator.   License: project-curated, commercial:true
✗ fly_shops_guides — No Meramec rows. Targets: Feather Craft (St. Louis), Missouri on the Fly, Missouri Fly Life Guide Co.; float outfitters (Ozark Outdoors, Bass River Resort, Huzzah Valley, etc.).   License: project-curated, commercial:true
✗ mineral_shops    — No Meramec rows. St. Louis metro candidates.   License: project-curated, commercial:true
✗ rockhounding_sites — No Meramec rows. Targets: barite/tiff (Washington Co — Old Mines, Potosi), galena (lead belt, access-restricted), Steelville chert/druzy quartz. NOT mozarkite/Keokuk geodes (those are out-of-basin).   License: project-curated, commercial:true
```

Totals: **16 ✓** (work as-is), **9 ⚠** (new adapter / extension / volume or coverage concern), **6 ✗** (N/A or manual-curation seed).

---

## §1.4 — Gap report + recommended fills

| Gap | Recommended fill | Cost / effort | License + commercial | Blocker for v1? |
|---|---|---|---|---|
| **MDC stocking has no structured source** | Decide: **(a) v0 manual seed** of the 4 trout parks (Maramec Spring daily Mar 1–Oct 31) + STL winter-trout lakes, refreshed seasonally; or **(b) fragile `missouri` newsroom HTML scraper**; or **(c) open-records request** for stocking logs. Recommend **(a) for v0** — automatability is low. | (a) ~2–3h seed · (b) ~3–4d fragile scrape | Public Records, commercial:true | **No** if (a) — stocking panel ships from seed; only the live feed is deferred |
| **Real-time water temp (Go Score)** | Only Huzzah 07014000 has live 00010. Use it as the upper-basin temp anchor; main-stem reaches fall back to the climatology proxy (already implemented) and Catch Probability shows the "no gauge" note (already implemented). Optionally model temp from air-temp later. | ~0 (already handled) | Public Domain, commercial:true | No |
| **MO Geological Survey geology** | New adapter `mo_geology` — MGS ArcGIS REST `gis.dnr.mo.gov/host/rest/services/geology/`. Identical pattern to `ga_geology`/`odgs`. Bonus `cave_density` + `abandoned_mines` layers. | **~1d** | Public Domain, commercial:true | No — DeepTrail ships Macrostrat-only v1 |
| **Big River lead 303(d)/TMDL ingest** | Verify `impaired` (ATTAINS) pulls the Big River Lead & Sediment TMDL segments. High-impact narrative. | ~0.5d (verify) | Public Domain, commercial:true | No — but signature water-quality content |
| **Big River fish-consumption advisory (health/safety)** | Static seed of the MO advisory (do-not-eat Big River fish downstream of the tailings site) as a reach-level health note. | ~1h | Public Records, commercial:true | No — but unusual, high-trust safety surface |
| **iNaturalist volume** | Reuse Chattahoochee tile-pagination + rarity weighting. No new work if that shipped. | ~0 | — | No |
| **Hatch chart** | Auto-seed two-mode (Ozark smallmouth-stream + Maramec Spring trout), `needs_entomologist_review=true`. | ~1–3h | project-curated | No |
| **Fly shops + guides + float outfitters** | Manual seed 5–8 rows (Feather Craft, Missouri on the Fly, Missouri Fly Life; Steelville outfitters). | ~2–3h | project-curated | No |
| **Rockhounding sites** | Manual seed: barite/tiff (Washington Co.), Steelville chert/druzy quartz, galena (note access/contamination). 3–5 rows. | ~2h | project-curated | No |
| **Mineral shops** | Manual seed, St. Louis metro. 3–5 rows. | ~1h | project-curated | No |
| **MO state-park recreation** | Meramec SP / Onondaga Cave SP not in RIDB; manual seed or accept the federal (MTNF) RIDB coverage. | ~1h or defer | varies | No |
| **Restoration (MO analogue)** | None surfaced; out-of-scope v1. | — | — | No |
| **SNOTEL** | None in MO. Accept empty. | 0 | N/A | No |

---

## §1.5 — Estimated adapter authoring scope (Step 2 preview)

| Adapter / task | Effort | Required for v1 RiverPath ship | Priority |
|---|---|---|---|
| Stocking **v0 manual seed** (4 trout parks + STL winter lakes) | ~2–3h | RiverPath stocking panel | **P0** |
| `impaired` verify (Big River Pb/Zn/sediment TMDL) | ~0.5d | RiverSignal water-quality + signature content | **P0** |
| Big River fish-advisory static seed | ~1h | Health/safety surface | **P0** |
| WQP validation (MO DNR STORET + USGS providers) | ~0.5d | RiverSignal water quality | **P0** |
| Curation seeds (reaches, flow bands, hatch, fly shops, rockhound, river stories) | ~1d | RiverPath/DeepTrail | **P0** |
| Adapter wiring / fixtures / frontend (~18 files per runbook §2.6) | ~1–1.5d | — | **P0** (overhead) |
| `mo_geology` (MGS ArcGIS REST + cave_density) | ~1d | DeepTrail geology + karst | **P1** |
| `missouri` stocking HTML scraper (replaces manual seed) | ~3–4d (fragile) | live stocking feed | **P2 / defer** |

**Total v0+P0 scope: ~3.5–4.0d** (no safety adapter; stocking via manual seed; iNat mitigation already shipped).
**Total v0+P0+P1: ~4.5–5.0d** (adds `mo_geology`).
**Full scope incl. live stocking scraper: ~8–9d.**

This is **roughly half of Chattahoochee's ~8d v0+P0**, because (1) there is no dam → no safety-critical adapter, and (2) the iNat-firehose mitigation already exists. The one awkward spot is stocking automatability, which we sidestep at v0 with a manual seed.

---

## §1.6 — Watershed config preview (Step 2.1)

```python
# pipeline/config/watersheds.py
"meramec": {
    "name": "Meramec River",
    "description": (
        "Free-flowing Ozark karst river from headwaters near Salem, MO "
        "through the Steelville float corridor, Meramec and Onondaga Cave "
        "state parks, and the St. Louis suburbs to the Mississippi River "
        "near Arnold. A premier smallmouth-bass float stream with a "
        "spring-fed rainbow-trout park at Maramec Spring; the Big River "
        "tributary carries a lead-mining (Old Lead Belt) legacy with a "
        "Superfund TMDL and fish-consumption advisory. First Missouri / "
        "mid-continent karst watershed on the platform."
    ),
    "bbox": {
        "north": 38.65,
        "south": 37.55,
        "east": -90.25,
        "west": -91.65,
    },
},
```

---

## §1.7 — Reach inventory preview (Step 2.4)

Four v0 reaches (Big River is structurally distinct because of the lead/sediment advisory; Maramec Spring trout folded into the upper reach with a note):

| Reach ID | Name (short) | Primary USGS gauge | Typical species | Warm-water? | Notes |
|---|---|---|---|---|---|
| `meramec_upper` | Upper Meramec / Steelville float corridor (Huzzah, Courtois; Maramec Spring trout park) | **07014000** Huzzah Cr (only basin gauge with live water temp) — proxy main stem via 07013000 | smallmouth_bass, rock_bass, spotted_bass, rainbow_trout (Maramec Spring) | partial (warm river; cold spring branch) | needs_guide_review — Smallmouth SMA (Hwy 8 → Bird's Nest); Red Ribbon trout area; Maramec Spring daily trout stocking |
| `meramec_middle` | Middle Meramec (Sullivan — Meramec SP / Onondaga Cave SP) | 07014500 Meramec near Sullivan (no live temp) | smallmouth_bass, largemouth_bass, channel_catfish, rock_bass | true | needs_guide_review — cave/karst corridor; classic float reach |
| `meramec_lower` | Lower Meramec (Eureka → Mississippi confluence; St. Louis suburbs) | 07019000 Meramec near Eureka (no live temp) | smallmouth_bass, largemouth_bass, channel_catfish, walleye, white_bass | true | needs_guide_review — Castlewood SP / Route 66 SP; urban use; flash-flood prone |
| `big_river` | Big River (Old Lead Belt tributary) | 07018500 Big R at Byrnesville | smallmouth_bass, spotted_bass, channel_catfish | true | needs_guide_review — **LEAD/SEDIMENT 303(d) TMDL + fish-consumption advisory**; surface health note |

(Bourbeuse River, gauge 07016500 at Union, is a candidate 5th reach — deferred to a follow-on.)

---

## §1.8 — Step 2 / Step 3 sequence recommendation

1. Commit this inventory under a Step-1 commit.
2. Watershed config entry (§2.1).
3. v0 curation seeds (§2.4) — reaches (4), flow bands, hatch chart(s), fly shops, mineral shops, rockhounding sites, river stories, **Big River fish-advisory note** — all `needs_review=true`. One commit per artifact.
4. **Stocking v0 manual seed** — 4 trout parks (Maramec Spring daily-stock pattern) + St. Louis winter-trout lakes. Flag `source='manual_seed'`, revisit live feed as P2.
5. Verify `impaired` (ATTAINS) pulls the Big River Lead & Sediment TMDL segments; validate WQP MO providers.
6. Run all applicable existing adapters scoped to `-w meramec` (§2.3) — usgs, nws, inaturalist (with tile-pagination), wqp/wqp_bugs, pbdb/idigbio/gbif, mrds, macrostrat, recreation, biodata, wbd, nhdplus, wetlands, prism.
7. (P1) Author `mo_geology` adapter (MGS ArcGIS REST + cave_density).
8. Wire frontend (§2.6 — ~18 files: WATERSHED_ORDER, WATERSHED_LABELS, AlertsOptInSheet WATERSHEDS, SOURCE_META, useFreshness, map centroids, photos/taglines, weather WS_COORDS/WS_GAUGES, etc.).
9. Refresh medallion + TQS daily refresh (§2.5).
10. **Pause for user review** before §2.7 (terraform job args) and §2.8 (prod deploy gates).
11. Write Step 3 verification report (`meramec-verification-<date>.md`) with a **water-temp-proxy sanity check** (confirm main-stem reaches degrade gracefully) and the **Big River advisory** surfaced in the feature-coverage grid.

---

## Comparison summary (vs Chattahoochee GA)

| Dimension | Meramec MO | Chattahoochee GA |
|---|---|---|
| USGS gauges in bbox | 8 active (across 3 HUC8s) | 9 active |
| Real-time water-temp gauges | **1** (Huzzah 07014000) — main stem proxied | several (incl. tailwater 02334430) |
| Dam / safety-critical adapter | **None — free-flowing** (Meramec Park Dam defeated 1978) | **Buford Dam tailwater** — safety-critical scrape required |
| iNat 5y obs in bbox | ~226K (high; mitigation already exists) | ~445K (drove the mitigation work) |
| 303(d) content | **Standout — Big River lead/sediment TMDL + fish advisory** | moderate (urban E. coli) |
| PBDB content | **Rich — 165 colls / 735 occ (Mississippian crinoids)** | Near-zero (metamorphic) |
| MRDS content | **Standout — Old Lead Belt + Washington Co. barite** | Standout — Dahlonega Gold Belt |
| Caves / karst | **Exceptional — Meramec Caverns, Onondaga, Fisher** | none notable |
| State geology adapter | `mo_geology` (MGS ArcGIS REST — easy, P1) | `ga_geology` (UGA ITOS — easy, P1) |
| New adapters required for v0 | **0** (stocking via manual seed; mo_geology is P1) | 2 (`ga_trout` + `usace_sam_hydropower`, one safety-critical) |
| Stocking data | **No machine-readable source** (manual seed for v0) | weekly PDF (`ga_trout` adapter) |
| v0+P0 effort | **~3.5–4d** | ~8d |
| Full scope | ~8–9d (incl. fragile stocking scraper) | ~12d |
| Signature RiverPath content | Smallmouth float stream + Maramec Spring trout park | Tailwater trout + dam-release safety |
| Signature DeepTrail content | Old Lead Belt minerals + Ozark caves + Mississippian crinoids | Dahlonega Gold Belt minerals |

**Recommendation:** Meramec is a **low-effort, high-content** onboarding candidate — about **half** the v0 cost of Chattahoochee because it carries no dam-safety adapter and the iNat mitigation already exists. The two judgment calls before Step 2 are (1) **stocking** — accept a manual v0 seed (recommended) rather than build a fragile MDC newsroom scraper, and (2) **water temperature** — accept main-stem climatology-proxy degradation (already implemented), with Huzzah Creek as the only live-temp anchor. The Big River lead-legacy TMDL + fish advisory and the Old Lead Belt / Ozark-cave content make it an unusually strong DeepTrail + water-quality story for modest engineering.

---

**End of Step 1 inventory. No Step-2 commitment made yet — awaiting user direction.**
