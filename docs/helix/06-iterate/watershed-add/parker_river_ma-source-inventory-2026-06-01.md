# Source Inventory & Gap Report: Parker River (Massachusetts)

| | |
|---|---|
| **Watershed slug** | `parker_river_ma` |
| **Display name** | Parker River (MA) |
| **States** | MA |
| **Date** | 2026-06-01 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (analysis-only; user evaluating whether to onboard) |
| **Status** | **Step 1 analysis only — NOT added. No Step-2 commitment.** This is a viability assessment, not an onboarding. |

> **Headline recommendation: DO NOT onboard as-is for v1.** Parker River is the platform's first *coastal estuarine* system, and its signature fishery (Plum Island Sound striped bass + the river-herring run) is a tide/bait-driven saltwater fishery that the current freshwater catch-probability model, hatch chart, and water-temperature surfaces do **not** represent. The data-feed plumbing is largely solvable; the **product/model fit is the blocker.** Details and two narrower options at the end.

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `parker_river_ma` (state suffix; "Parker River" is ambiguous nationally) | proposed |
| Display name | Parker River (MA) | proposed |
| States | MA (Essex County) | — |
| Headwaters | Pentucket Pond area, **Georgetown, MA**; flows through Byfield (Newbury) | USGS NHD; PRCWA |
| Mouth | **Plum Island Sound** estuary → Gulf of Maine, at the **Parker River National Wildlife Refuge** (Plum Island) | USGS NHD; USFWS |
| Gauge coords | 42.7529, -70.9456 (Parker R at Byfield) | USGS site record |
| Bbox (proposed) | `north=42.85, south=42.65, east=-70.75, west=-71.05` | agent research + gauge location; covers basin + Plum Island Sound + NWR |
| HUC8 code | **`01090001`** (USGS groups the Parker under the Merrimack-region HUC8; it is a discrete small coastal basin) | USGS site record (`huc_cd`) |
| NWS forecast office | **BOX** (Boston / Norton, MA) covers Essex County | api.weather.gov |
| Drainage area | **21.3 mi²** at the Byfield gauge (freshwater); full tidal basin ~80 mi² incl. estuary | USGS `drain_area_va` |
| Primary fishery | **Coastal/estuarine: striped bass + bluefish** (Plum Island Sound/jetty); **river-herring run** (alewife/blueback, DMF sentinel river); plus **stocked-trout ponds** (Rock Pond, Pentucket Pond) and warmwater panfish | MA DMF; MassWildlife; On The Water; PRCWA |

This would be the **first New England / Atlantic-seaboard / estuarine watershed** on a platform whose 9 current watersheds are all inland rivers (6 PNW, Green UT/WY, Shenandoah VA/WV, Mad River OH). Implications:

- **It is structurally unlike every existing watershed.** The others are freshwater trout/bass rivers scored on flow, water temp, insect hatches, and stocking. Parker's headline fishery is a **saltmarsh-estuary striper fishery driven by tides, salinity, ocean temperature, and baitfish (herring/peanut-bunker) migrations** — none of which the current Go Score / catch-probability model represents.
- All Western adapters (StreamNet, ODFW `fishing`, WDFW `washington`, UDWR `utah`, `streamnet`, `snotel`, BLM, `ohio_stocking`, `virginia`, `west_virginia`) return empty — same solved "out-of-region returns empty" posture as Shenandoah/Mad River.
- **DeepTrail content is weak here:** eastern-MA bedrock is metamorphic/igneous (Avalon/Nashoba terranes); PBDB returned only **12 occurrences** in-bbox. No rich fossil surface like Mad River's 129 Paleozoic-carbonate occurrences.
- **Genuinely novel content** if the fishery model were extended: the DMF-monitored **river-herring run** (a "hatch" analog), salt-marsh restoration, active **Larkin Mill dam removal**, and the Plum Island Ecosystems LTER.

---

## §1.1 — Feature → source map (per app, for Parker River MA)

| App | Feature | Required data | Status for Parker River MA |
|---|---|---|---|
| **RiverSignal** | Site dashboards | USGS NWIS | ⚠ — **1 freshwater gauge** (01101000 Byfield); adjacent Ipswich gauge 01102000 in-bbox. **No water-temp parameter** at Byfield (see below). |
| RiverSignal | Water quality | EPA WQP | ✓✓ — **820 WQP station rows** in bbox (MassDEP + PIE-LTER + EPA). Among the richest WQ surfaces on the platform. |
| RiverSignal | Macroinvertebrate quality | WQP_BUGS | ✓ — MassDEP submits macroinvertebrate samples to WQP. |
| RiverSignal | 303(d) impaired | EPA ATTAINS / MassDEP Integrated List | ✓ — MA reports to ATTAINS; **MassDEP 2022 Integrated List is a queryable ArcGIS Feature Service** (`IL_2022_ARC`/`_POLY`). Confirm specific Parker/Plum Island AU listing by query. Clean machine-readable source. |
| RiverSignal | Watershed geometry | WBD + NHDPlus | ✓ — federal CONUS. |
| RiverSignal | Wetlands | USFWS NWI | ✓ — extensive Plum Island Sound salt marsh. |
| RiverSignal | Restoration tracking | (PNW-scoped today) | ⚠ — MA analogue: **MA Div. of Ecological Restoration (DER)** project map + Restoration Potential Model; **PIE-LTER** salt-marsh experiments. Adapter extension required. |
| RiverSignal | Fire recovery | MTBS | ✗ N/A — no wildfire footprint; graceful empty. |
| **RiverPath** | Go Score — flow | USGS gauge | ✓ — discharge (00060) + gage height (00065) at Byfield. |
| RiverPath | Go Score — **water temp** | USGS gauge temp (00010) | ✗ **GAP — Byfield gauge reports NO water temperature.** Temp sub-score + live-temp hero would be blank unless modeled from WQP/air-temp. The same code path that produced the `-1799966.2°F` bug must degrade cleanly to "no data" here. |
| RiverPath | Go Score — weather | NWS | ✓ — BOX gridpoints. |
| RiverPath | Go Score — **hatch** | curated_hatch_chart | ✗ **Largely N/A.** An insect-emergence chart is irrelevant to a tide/bait-driven estuary fishery; only marginally relevant to the stocked-trout ponds. The real "hatch" analog is the **herring run + baitfish migrations** — not currently modeled. |
| RiverPath | River Now hero | USGS instantaneous + NWS | ⚠ — works, but no live water temp. |
| RiverPath | Photo observations | iNaturalist | ✓✓ — **66,529 all-time / 45,535 last-5y** research-grade obs in bbox (Plum Island NWR is a major nature destination). 241 research-grade ray-finned-fish obs. |
| RiverPath | **Catch probability** | freshwater species model | ✗ **MODEL MISMATCH (primary blocker).** See §Model-fit. Striped bass is nominally in the model, but as a *river/impoundment* species — not an estuarine, tide-and-herring-driven striper fishery. |
| RiverPath | **Stocking schedule** | State hatchery feed | ⚠ — MassWildlife **does** stock the Parker + Rock/Pentucket Ponds, but the "Trout Stocking Report" is an **HTML map/table with no verified CSV/API** and mass.gov UA-gates scrapers. Brittle. New `massachusetts` adapter. |
| RiverPath | **River-herring run** (novel) | MA DMF diadromous counts | ⚠ — Parker is a DMF **sentinel count river** (multi-decade series; ~86K in 2024, ~28K in 2025). But counts are **HTML/PDF annual reports, no structured feed**. High-value novel content; brittle ingest. |
| RiverPath | Fish passage | USFWS NFPP / MA DER | ⚠✓ — strong narrative: **Larkin Mill Dam removal active** (~$2.5M, NOAA/USFWS/DMF); six dams w/ fishways. Verify federal NFPP feed coverage. |
| RiverPath | Swim safety | Derived | ✓ — but no water temp degrades the comfort sub-score. |
| RiverPath | Snowpack | SNOTEL | ✗ N/A — no relevant SNOTEL; coastal basin. Acceptable empty. |
| RiverPath | Recreation sites | RIDB | ⚠ — **Parker River NWR is on Recreation.gov (gateway 1557)** → RIDB API, but **requires a free registered API key** (DEMO_KEY 401s). MassWildlife WMA layer via MassGIS (exact service URL unverified). |
| RiverPath | Fly shop / guide directory | Manual | ✓ (manual seed) — real market exists but is **saltwater-guide-dominated**: Surfland Bait & Tackle (Newbury), Rocco's (Rowley), Bridge Road Bait & Tackle; charters Shadowcaster, Polaris, Obsessed, Manolin, Summer Job (all striper-focused). |
| **DeepTrail** | Geology units | Macrostrat + MassGIS | ✓ — Macrostrat CONUS; **MassGIS ArcGIS REST** (`SurfGeo24k`, `Bedrock_*`, `BEDROCKLITHOLOGY_POLY`) is a clean new source. Avalon/Nashoba terrane content. |
| DeepTrail | Fossil sites | PBDB + iDigBio + GBIF | ✗ weak — **only 12 PBDB occurrences** in-bbox (metamorphic basement). Thin content surface. |
| DeepTrail | Rockhound / mineral / MRDS | Manual + MRDS | ⚠ sparse — eastern-MA granite/pegmatite; modest at best. |

---

## §1.3 — Per-source check matrix (verified)

License/commercial tagged per the Shenandoah/Mad River "tag, don't gate" posture (Q3).

```
⚠ usgs            — 1 freshwater gauge 01101000 Parker R at Byfield (DA 21.3 mi²), discharge+gage height only, NO WATER TEMP (00010 absent). Adjacent 01102000 Ipswich R in-bbox. License: Public Domain, commercial:true
✓ nws / nws_observations — WFO BOX (Norton, MA) covers Essex County. License: Public Domain, commercial:true
✓ inaturalist     — 66,529 all-time / 45,535 last-5y research-grade obs in bbox; 241 fish. License: CC-BY-NC (photos commercial:false; metadata commercial:true)
✓ wqp             — 820 monitoring-station rows in bbox (MassDEP, PIE-LTER, EPA). License: Public Domain, commercial:true
✓ wqp_bugs        — MassDEP macroinvertebrate samples via WQP. License: Public Domain, commercial:true
✓ impaired/ATTAINS— MassDEP 2022 Integrated List as ArcGIS Feature Service (IL_2022_ARC/_POLY) + EPA ATTAINS. Confirm Parker/Plum Island AU by query. License: Public Domain / MassGIS open, commercial:true
✓ wbd / nhdplus   — federal CONUS; Parker basin geometry + flowlines. License: Public Domain, commercial:true
✓ wetlands (NWI)  — extensive Plum Island Sound salt marsh. License: Public Domain, commercial:true
✓ prism           — CONUS. License: Academic Free, commercial:true
✓ gbif / biodata  — iNat firehose to GBIF; USGS BioData MA sites (verify). License: CC-BY 4.0 / Public Domain, commercial:true
✓ macrostrat      — CONUS columns. License: CC-BY 4.0, commercial:true
✓ massgis_geology — NEW source. arcgisserver.digital.mass.gov/.../AGOL (SurfGeo24k, Bedrock_*, BEDROCKLITHOLOGY_POLY). Clean REST. License: MassGIS open / USGS PD, commercial:true
⚠ recreation (RIDB) — Parker River NWR gateway 1557; requires FREE API KEY (DEMO_KEY 401, ~50 req/min). License: federal PD (access agreement), commercial:true
⚠ restoration     — PNW-scoped adapter. MA analogue: DER project map + RPM (ArcGIS), PIE-LTER (EDI data portal). Extension required. License: open (unverified specifics), commercial:true
⚠ fish_passage    — Larkin Mill removal active; six fishways. Verify USFWS NFPP national feed for Parker. License: Public Domain, commercial:true
⚠ massachusetts   — NEW adapter. Trout stocking ("Trout Stocking Report") = HTML map/table, NO verified CSV/API, mass.gov UA-gates scrapers. Brittle. License: mass.gov terms (unverified), commercial:unverified
⚠ ma_dmf_herring  — NEW (or manual seed). Parker = DMF sentinel river; counts in annual HTML/PDF only, no structured feed. High-value novel content. License: unverified, commercial:unverified
⚠ pbdb / idigbio / mrds — sparse: 12 PBDB occurrences; metamorphic basement; thin DeepTrail content. License: CC0 / PD, commercial:true
✗ curated_hatch_chart — Largely N/A for an estuary fishery; herring/bait-run calendar is the real analog (not modeled). License: project-curated
✗ snotel / mtbs   — N/A (coastal; no wildfire). 
✗ streamnet / fishing(OR) / washington / utah / virginia / west_virginia / ohio_stocking — out-of-region, empty.
✓ fly_shops_guides — manual seed; saltwater-dominated (Surfland, Rocco's, Bridge Road; Shadowcaster/Polaris/Obsessed/Manolin/Summer Job charters). License: project-curated, commercial:true
```

Rough tally: **~13 ✓** (work as-is, several *richer* than prior watersheds — WQP, iNat, impaired, geology), **~6 ⚠** (gauge-temp gap, RIDB key, restoration/passage extensions, 2 brittle new MA feeds), **~7 ✗** (out-of-region empties + hatch-chart N/A + the catch-probability model mismatch).

---

## §1.2 — Model-fit assessment (THE BLOCKER)

The data plumbing is mostly fine; **the product model is the problem.**

- The platform scores fishing via a **freshwater catch-probability model** (salmonids; warmwater bass/walleye/musky/catfish/sunfish/pickerel) keyed on **water temperature, flow, insect hatch activity, and stocking** — and a freshwater **hatch chart**.
- Parker's actual draw is the **Plum Island Sound striped-bass + river-herring estuary fishery**, governed by **tide stage, salinity, ocean temperature, and herring/peanut-bunker bait migrations**. "Striped bass" being a model key does **not** make a river-tuned model correct for an inlet/jetty/tidal-marsh striper fishery.
- The **freshwater pond component** (Rock Pond, Pentucket Pond: stocked trout + largemouth/pickerel/panfish) **does** fit the existing model — but it is a minor slice of the watershed's angling identity.
- **Correction worth flagging:** no sea-run brook trout here — eDNA sampling found the Parker devoid of brook trout (surviving MA salters are South Shore/Cape Cod). Don't seed salters.
- The **water-temp gap** (no 00010 at the only freshwater gauge) and **hatch-chart irrelevance** mean two RiverPath sub-scores are blank or meaningless out of the box.

Net: onboarding Parker without an estuarine/tidal fishery model would ship a river-intelligence page that mischaracterizes the place — confidently scoring a freshwater fishery that isn't the real fishery.

---

## §1.4 — Gap report + recommended fills

| Gap | Fill | Effort | Blocker for v1? |
|---|---|---|---|
| **Estuarine/tidal fishery model** (tide, salinity, ocean temp, bait runs) | New scoring path; integrate NOAA tides/currents + herring run calendar. Net-new modeling, not adapter work. | **High (weeks)** | **YES** — this is the real fishery |
| **Catch-probability mismatch** | Either build the estuary model above, or restrict v0 to freshwater ponds only (weak product) | High or scope-cut | **YES** |
| **No water temperature at gauge** | Model temp from WQP/air-temp, or source a nearby temp logger; ensure clean "no data" (post the `-1799966.2°F` fix) | 1–2d | Yes for temp sub-score |
| **Hatch chart N/A** | Replace with a herring-run / baitfish-migration calendar for this watershed type | 1–2d (after model) | Partial |
| **MA trout stocking** (HTML, UA-gated) | New `massachusetts` adapter; headless/UA scrape of Trout Stocking Report; or records request | 2–4d (brittle) | No (ponds only) |
| **DMF river-herring counts** (HTML/PDF) | New feed or manual annual seed; sentinel-river series | 1–3d | No (but it's the best novel content) |
| **MassDEP impaired (ArcGIS)** | Wire ArcGIS Feature Service `IL_2022_ARC/_POLY`; confirm Parker AU | 0.5d | No — clean win |
| **MassGIS geology (ArcGIS)** | New source config off `arcgisserver.digital.mass.gov` | 1d | No — clean win |
| **RIDB API key** | Register free key + accept access agreement | <0.5d | No |
| **Restoration (MA DER + PIE-LTER)** | Extend `restoration`; DER project map + EDI/LTER packages | 2–3d | No |
| **Fish passage** | Verify USFWS NFPP for Parker (Larkin Mill removal) | 0.5d | No |
| **Fossils/DeepTrail** | Accept sparse (12 PBDB); MassGIS geology carries DeepTrail | 0 | No |

---

## §1.6 — Watershed config preview (only if onboarded)

```python
# pipeline/config/watersheds.py
"parker_river_ma": {
    "name": "Parker River (MA)",
    "description": (
        "Parker River from headwaters near Georgetown through Byfield "
        "to the Plum Island Sound estuary and Parker River National "
        "Wildlife Refuge, Essex County MA. First New England coastal / "
        "estuarine watershed on the platform; striped-bass + "
        "river-herring estuary fishery with stocked-trout ponds. "
        "NOTE: estuarine fishery is a poor fit for the freshwater "
        "catch-probability model — see source inventory."
    ),
    "bbox": {"north": 42.85, "south": 42.65, "east": -70.75, "west": -71.05},
},
```

---

## §1.7 — Reach inventory preview (only if onboarded)

| Reach ID | Name | Gauge | Fishery | Notes |
|---|---|---|---|---|
| `parker_river_ma_ponds` | Headwater ponds (Rock Pond, Pentucket Pond, Georgetown) | 01101000 (proxy) | stocked rainbow/brown trout, largemouth bass, chain pickerel, panfish | **Fits existing model** |
| `parker_river_ma_mainstem` | Freshwater mainstem (Georgetown→Byfield) | 01101000 Byfield | river herring (run), stocked trout, white perch | herring run = novel; no live temp |
| `parker_river_ma_estuary` | Plum Island Sound / NWR / jetty | (no gauge; NOAA tides) | striped bass, bluefish, mackerel | **Does NOT fit model — needs estuary scoring** |

---

## Comparison summary (vs Mad River OH, the last add)

| Dimension | Parker River MA | Mad River OH |
|---|---|---|
| Fishery type | **Coastal estuary striper + herring run** (novel, off-model) | Inland spring-creek brown trout (on-model) |
| USGS gauges in bbox | 1 freshwater (no temp) + 1 adjacent | 2 active |
| Water temperature feed | **None at gauge** | present |
| iNat 5y obs | 45,535 | ~99K |
| WQP stations | **820 (very rich)** | 151 |
| PBDB fossils | **12 (thin)** | 129 (rich) |
| Clean ArcGIS feeds | impaired + MassGIS geology | ODGS geology |
| New adapters for v0 | `massachusetts` (stocking, HTML/brittle) + herring | `ohio_stocking` |
| Hatch chart | **largely N/A** | East-Coast limestone seed works |
| Model fit | **Poor (blocker)** | Good |
| Drainage area | 21.3 mi² (smallest by far) | ~660 mi² |

---

## Recommendation

**Do not onboard Parker River for v1 in the current platform shape.** The blocker is not data availability — MA's water-quality, geology, impaired-waters, iNat, and recreation feeds are strong (several richer than existing watersheds) — it's that **the platform's freshwater fishery model fundamentally does not describe a tidal saltmarsh-estuary striper/herring fishery.** Shipping it as-is would confidently mis-score the place, and two RiverPath sub-scores (water temp, hatch) are blank/irrelevant from day one.

Two viable paths if interest is high:

1. **Defer until an estuarine/tidal fishery model exists** (tide + salinity + ocean-temp + bait-run scoring, with a herring-run "hatch" calendar). Parker River is then an *excellent* flagship for that capability — DMF sentinel herring data, active dam removal, PIE-LTER, and a major striper destination. This is **weeks** of net-new modeling, not adapter plumbing.

2. **Scope a freshwater-pond-only v0** (Rock Pond / Pentucket Pond stocked trout + warmwater, on the existing model) with the estuary explicitly out of scope. This fits the model but captures little of the watershed's real angling identity — a weak, arguably misleading product. Not recommended on its own.

If the goal is "another clean inland watershed next," Parker River is the wrong pick; a freshwater New England trout river (e.g., a Deerfield/Swift tailwater) would onboard far more cleanly on the existing model.

---

**End of Step 1 analysis. Watershed NOT added — no `watersheds.py` entry, no ingestion, no deploy. Awaiting user direction.**
