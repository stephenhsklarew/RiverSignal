# Source Inventory & Gap Report: New River (Virginia)

| | |
|---|---|
| **Watershed slug** | `new_river_va` |
| **Display name** | New River (VA) |
| **States** | VA (Grayson, Carroll, Wythe, Pulaski, Montgomery, Giles) |
| **Date** | 2026-06-01 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (analysis-only; user evaluating whether to onboard) |
| **Status** | **Step 1 analysis only — NOT added.** Companion: `clinch_river_va-source-inventory-2026-06-01.md`. |

> **Headline: excellent on-model fishery and the biggest/most-popular of the four, but with one notable gap — no water temperature at any mainstem gauge** (same blank temp sub-score as the MA basins). Premier smallmouth/musky/walleye big river, strongest guide market of the four, rich DeepTrail fossils, and the existing **`virginia` adapter already covers stocking/regs/geology/parks.** Kanawha/Ohio basin.

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `new_river_va` (state suffix; the New continues into WV — see overlap note) | proposed |
| Display name | New River (VA) | proposed |
| States | VA (in scope); NC headwaters + WV downstream out of scope | — |
| Headwaters (in scope) | NC line near Galax / Mouth of Wilson, VA; **flows north** | USGS NHD |
| Mouth (in scope) | WV state line at Glen Lyn, VA (→ New River Gorge, WV — separate famous fishery, not in scope) | USGS NHD |
| Bbox (proposed, **needs tightening**) | `north=37.45, south=36.50, east=-80.50, west=-81.55` | gauges + basin; see overlap note |
| HUC8 codes | **`05050001` (Upper New) + `05050002` (Middle New)** — Kanawha/Ohio basin | USGS `huc_cd` |
| NWS forecast office | **RNK** (Blacksburg, VA) | api.weather.gov |
| Drainage area | **2,767 mi²** at Radford / **3,770 mi²** at Glen Lyn — a **large** river | USGS `drain_area_va` |
| Length | ~160 mi in VA; one of the oldest rivers in North America | VA DWR |
| Primary fishery | **Warmwater big-river: smallmouth bass** (marquee) + **trophy muskellunge** + **walleye**; spotted/largemouth/rock bass, redbreast/bluegill, catfish, crappie; **Claytor Lake** adds striped/hybrid striped bass, largemouth, crappie | VA DWR |

**bbox overlap note:** provisional bbox bleeds into WV (caught Bluestone, East River, Brush Creek WV gauges) and toward the NC line — tighten to the VA New corridor. **Cross-state caveat:** the New continues downstream into the WV **New River Gorge** (a separate, famous fishery); if a WV New is ever onboarded, deconflict the state-line bbox edge. Two HUC8s (05050001 + 05050002) — confirm the watershed config covers both or scope to one.

---

## §1.1 — Feature → source map (deltas; VA-wide feeds already built for Shenandoah)

| Feature | Status for New | Note |
|---|---|---|
| USGS gauges | ✓✓✓ **5 mainstem** — Galax 03164000, Ivanhoe 03165500, Allisonia 03168000, Radford 03171000 (2,767 mi²), Glen Lyn 03176500 (3,770 mi²) — + Little River, Reed Creek, Walker Creek, Wolf Creek, Chestnut Creek tribs | best gauge density of the four |
| **Water temperature** | ✗ **GAP — none of the mainstem gauges report temp (00010).** Temp sub-score + live-temp hero blank (the recent `-1799966.2°F` fix hardens the bad-value path; confirm "no data" renders cleanly) | same gap as MA / Parker |
| Go Score — flow | ✓✓ discharge + gage height at 5 gauges; dam-regulated reaches (Claytor) | — |
| Catch probability | ✓✓ **On-model and then some** — smallmouth, musky, walleye, striped bass, largemouth, sunfish all in `SPECIES_MODELS`. State-record musky/smallmouth/walleye water | excellent fit |
| Stocking / regs | ✓ **Already ingested** (`virginia`). Mainstem: bass 14–22" slot; musky slot/seasonal; Claytor striped-bass seasons. Trout: Big Stony Creek (Giles) special-reg section + seasonal trib stockings | extend attribution |
| Hatch chart | ⚠ **Low value** — big warmwater river is **crayfish/hellgrammite/baitfish-driven**, not mayfly-hatch driven. Recommend a forage/seasonal-presentation model over an insect hatch chart | honest gap |
| iNaturalist | ✓✓ 73,170 all-time / 49,363 last-5y / 1,506 fish (bbox-inflated) | — |
| Water quality / impaired | ✓✓ Rich WQP; EPA ATTAINS (VA DEQ) | — |
| Geology | ✓ **Already built** (`virginia` DGMR ArcGIS). Valley & Ridge / Blue Ridge edge | low effort |
| **Fossils (PBDB)** | ✓✓ **2,413 occurrences** — rich Paleozoic content. Strong DeepTrail | — |
| Recreation | ✓✓ **New River Trail State Park** (57-mi rail-trail, Galax→Pulaski; access at Galax, Fries, Ivanhoe, Foster Falls, Allisonia, Draper), **Claytor Lake State Park**, many DWR ramps | best recreation surface of the four |
| Fly shops / guides | ✓✓ **Robust inland market** — Greasy Creek Outfitters (Willis), Tangent Outfitters (Pembroke/Radford), New River Fly Fishing, New River Charter, Appalachian Outdoor Adventures (Pearisburg), New River Outdoor Co. (Pearisburg) | strongest of the four |
| Dams | note — Fields, Fries, Byllesby, Buck, **Claytor** (137-ft, 1938, AEP). Flow-regulation context for Go Score | — |
| restoration / snotel / mtbs / Western adapters | ⚠ / ✗ as for Clinch | — |

---

## §1.3 — Deterministic check results (verified, on provisional bbox)

```
✓✓✓ usgs       — 5 New mainstem gauges (Galax/Ivanhoe/Allisonia/Radford 2767/Glen Lyn 3770) + many tribs. NO WATER TEMP at mainstem gauges (Galax has precip 00045). (bbox caught WV Bluestone/East River — tighten.)
✓✓ inaturalist — 73,170 all-time / 49,363 last-5y / 1,506 fish (bbox-inflated)
✓✓ wqp         — 2,390 station rows
✓✓ pbdb        — 2,413 occurrences (rich Paleozoic — strong DeepTrail)
✓  virginia    — stocking + regs + DGMR geology + DCR parks ALREADY BUILT. Need: extend stocking watershed-attribution + stocking_schedule MV; handle two HUC8s.
✓  nws (RNK) / wbd / nhdplus / wetlands / prism / gbif / wqp_bugs — VA-wide / federal.
⚠  restoration — DEQ/TNC analogue; PNW adapter extension.
✗  snotel / mtbs / streamnet / fishing(OR) / washington / utah / west_virginia / ohio_stocking — out-of-region empties.
```

---

## §1.7 — Reach inventory preview (only if onboarded)

| Reach ID | Name | Gauge | Fishery | Notes |
|---|---|---|---|---|
| `new_river_va_upper` | Upper New (NC line→Ivanhoe/Allisonia) | 03164000 Galax, 03165500 Ivanhoe | smallmouth, musky, walleye | New River Trail corridor; no live temp |
| `new_river_va_claytor` | Claytor Lake reservoir | (Allisonia inflow 03168000) | striped/hybrid bass, largemouth, crappie | reservoir fishery; **Alabama bass** invasive flag |
| `new_river_va_lower` | Lower New (Radford→Glen Lyn/WV line) | 03171000 Radford (2767), 03176500 Glen Lyn (3770) | trophy smallmouth + musky | dam-regulated; no live temp |

---

## Recommendation (within this doc)

**A strong onboard candidate — the most popular, best-guided, best-recreation-served, and largest of the four** — but **second to the Clinch** primarily because **no mainstem gauge reports water temperature**, leaving the temp sub-score and live-temp hero blank out of the box (exactly the gap that weakened the MA basins). It is otherwise an outstanding on-model fit (smallmouth/musky/walleye), reuses the built `virginia` adapter, and has rich DeepTrail fossils. Extra scoping vs Clinch: it spans **two HUC8s**, is a **large 3,770 mi² river** needing more reaches, and has a **WV state-line edge** (future New-River-Gorge overlap). Pre-flight: tighten bbox off WV/NC, decide one vs two HUC8s, confirm the "no water temp" path renders as clean "no data," extend VA stocking attribution + MV.

---

**End of Step 1 analysis. Watershed NOT added — no config entry, no ingestion, no deploy.**
