# Source Inventory & Gap Report: Clinch River (Virginia)

| | |
|---|---|
| **Watershed slug** | `clinch_river_va` |
| **Display name** | Clinch River (VA) |
| **States** | VA (SW Virginia: Tazewell, Russell, Wise, Scott) |
| **Date** | 2026-06-01 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (analysis-only; user evaluating whether to onboard) |
| **Status** | **Step 1 analysis only — NOT added.** Companion: `new_river_va-source-inventory-2026-06-01.md`. |

> **Headline: the strongest candidate of the four analyzed (Parker, Ipswich, Clinch, New).** On-model warmwater fishery (smallmouth/musky/walleye/sauger), **live water temperature at both mainstem gauges** (the gap that hurt the MA basins and the New), the existing **`virginia` adapter already covers stocking/regs/geology/parks**, rich DeepTrail fossils, and a genuinely unique **aquatic-biodiversity "what's alive" story** (most imperiled freshwater mussel fauna in North America). Would be the platform's **first Tennessee-River-basin watershed**.

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `clinch_river_va` (state suffix; Clinch continues into TN) | proposed |
| Display name | Clinch River (VA) | proposed |
| States | VA | — |
| Headwaters | Near Tazewell, VA (confluence of Little R. forks); flows SW | USGS NHD |
| Mouth (in scope) | TN state line near Clinchport/Scott Co. (→ Tennessee R. basin; Norris Lake in TN, not in scope) | USGS NHD |
| Bbox (proposed, **needs tightening**) | `north=37.30, south=36.55, east=-81.30, west=-82.75` | gauges + basin; see overlap note |
| HUC8 code | **`06010205`** (Upper Clinch — **Tennessee River basin**, a region new to the platform) | USGS `huc_cd` |
| NWS forecast office | **RNK** (Blacksburg, VA) covers SW VA | api.weather.gov |
| Drainage area | **533 mi²** at Cleveland; ~1,500 mi² for the full VA Clinch by Scott Co. | USGS `drain_area_va` |
| Primary fishery | **Warmwater: smallmouth bass** (marquee), **muskellunge**, **walleye/sauger**, spotted/largemouth bass, rock bass, redbreast/longear sunfish, crappie, channel/flathead catfish; **trout in coldwater tributaries** (stocked) | VA DWR waterbody report |

**bbox overlap note:** the provisional bbox bleeds into adjacent basins (it caught S/M/N Fork Holston, Russell Fork, Pound, Bluestone gauges) — counts below are taken on it and are inflated. A production bbox must be tightened to the Clinch mainstem corridor (Tazewell→Scott). First TN-basin watershed: all Atlantic/Ohio-basin-specific assumptions are fine (federal feeds are national), and the `virginia` adapter is state-keyed, not basin-keyed.

---

## §1.1 — Feature → source map (deltas; VA-wide feeds already built for Shenandoah)

| Feature | Status for Clinch | Note |
|---|---|---|
| USGS gauges | ✓✓ **2 mainstem** — 03524000 Cleveland (533 mi²), 03524740 Dungannon — + Indian Creek tribs | good reach anchors |
| **Water temperature** | ✓✓ **BOTH gauges report temp (00010)** + conductance (00095); Dungannon adds DO (00300) + turbidity (63680) | **the differentiator** — full live-conditions hero works |
| Go Score — flow | ✓ discharge + gage height | — |
| Catch probability | ✓✓ **On-model** — smallmouth/musky/walleye/largemouth/sunfish all in `SPECIES_MODELS`; sauger/drum not modeled (minor, falls to generic) | excellent fit |
| Stocking schedule | ✓ **Already ingested** — VA DWR statewide schedule via existing `virginia` adapter; just extend watershed attribution beyond Shenandoah. Clinch-area trout waters: Big/Little Tumbling Creek, Laurel Bed Creek (Clinch Mtn WMA), Roaring Fork, Big Stony Creek, Big Cedar Creek | low effort |
| Regulations | ✓ Already ingested (`virginia`). Mainstem: bass 20" min/1 per day; musky 30" min; trout-tributary C&R regs | low effort |
| **Biodiversity / "what's alive"** (signature) | ✓✓ **Unique content.** Most imperiled freshwater-mussel fauna in N. America (~46–50 mussel spp., 29 imperiled; 100+ fish), **Clinch dace**, TNC **Clinch Valley Program** (Abingdon), dramatic fish-kill history (1967/1970 Carbo; **1998 Cedar Bluff** spill, largest single ESA loss since 1973). Structured USFWS critical-habitat + VT datasets | iNat 2,135 fish obs corroborates |
| Hatch chart | ⚠ High value for the **coldwater trout tributaries** (Appalachian freestone); optional for the warmwater mainstem (topwater/streamer forage model) | East-Coast seed + `needs_review` |
| iNaturalist | ✓✓ 92,076 all-time / 64,489 last-5y / 2,135 fish (bbox-inflated; still rich) | — |
| Water quality / impaired | ✓✓ Rich WQP; EPA ATTAINS (VA DEQ). The Clinch is a federal conservation priority → dense assessment | — |
| Geology | ✓ **Already built** — `virginia` adapter pulls VA DGMR geology ArcGIS (`energy.virginia.gov/.../DGMR/Geology`). SW VA Valley & Ridge | low effort |
| **Fossils (PBDB)** | ✓✓ **2,316 occurrences** in bbox — rich Paleozoic Valley & Ridge content. Strong DeepTrail | — |
| Recreation | ✓ **Clinch River State Park** (VA's 41st, 2021; first "blueway"); named DWR launches: Artrip, Carbo, Old Castlewood, The Retch. RIDB for Jefferson NF | — |
| Fly shops / guides | ✓ (manual seed) **Clinch Life Outfitters** (St. Paul), **Riverfeet Fly Fishing** (Abingdon/Damascus) | inland market, modest |
| restoration | ⚠ TNC Clinch Valley + VA DEQ TMDL; existing adapter PNW-scoped → extension or seed | — |
| snotel / mtbs / Western adapters | ✗ N/A empties | — |

---

## §1.3 — Deterministic check results (verified, on provisional bbox)

```
✓✓ usgs        — 2 Clinch mainstem gauges: 03524000 Cleveland (DA 533, params 00010/00060/00065/00095), 03524740 Dungannon (00010/00095/00400/63680). BOTH HAVE WATER TEMP. + Indian Creek tribs. (bbox also caught Holston/Russell Fork — tighten.)
✓✓ inaturalist — 92,076 all-time / 64,489 last-5y / 2,135 fish (bbox-inflated; rich either way)
✓✓ wqp         — 3,027 station rows
✓✓ pbdb        — 2,316 occurrences (rich Paleozoic Valley & Ridge — strong DeepTrail)
✓  virginia    — stocking + regs + DGMR geology + DCR parks ALREADY BUILT (Shenandoah). Need: extend stocking watershed-attribution + stocking_schedule MV to cover the new watershed (code TODO already noted in virginia.py).
✓  nws (RNK) / wbd / nhdplus / wetlands / prism / gbif / wqp_bugs — VA-wide / federal, work as-is.
⚠  restoration — TNC/DEQ analogue; PNW adapter needs extension.
✗  snotel / mtbs / streamnet / fishing(OR) / washington / utah / west_virginia / ohio_stocking — out-of-region empties.
```

---

## §1.7 — Reach inventory preview (only if onboarded)

| Reach ID | Name | Gauge | Fishery | Notes |
|---|---|---|---|---|
| `clinch_river_va_upper` | Upper Clinch (Tazewell→Cleveland) | 03524000 Cleveland (temp ✓) | smallmouth, musky, sauger, sunfish | Clinch dace tributaries here |
| `clinch_river_va_lower` | Lower Clinch (Cleveland→Dungannon→TN line) | 03524740 Dungannon (temp+DO+turb ✓) | smallmouth ("Retch" musky), walleye | best water-quality telemetry on the river |
| `clinch_river_va_trout_tribs` | Clinch Mtn WMA cold tributaries | (ungauged) | stocked + wild trout | Big/Little Tumbling, Laurel Bed — hatch chart applies |

---

## Recommendation (within this doc)

**Strong onboard candidate, and the cleanest of the four analyzed.** It hits the existing model squarely (smallmouth/musky/walleye), is the only one of the four with **live water temperature at its gauges** (so the temp sub-score and live-conditions hero work with no degradation), reuses the **already-built `virginia` adapter** (stocking/regs/geology/parks — minimal new code, mostly attribution-config + the stocking-MV TODO already flagged in `virginia.py`), has **rich DeepTrail fossils** (2,316 PBDB), and offers a **one-of-a-kind biodiversity/"what's alive" content surface** unmatched by any current watershed. Main pre-flight items: tighten bbox off adjacent Holston/Russell Fork basins; extend the VA stocking attribution + `gold.stocking_schedule` UNION; confirm Clinch-basin trout-tributary stockings against the live DWR table.

---

**End of Step 1 analysis. Watershed NOT added — no config entry, no ingestion, no deploy.**
