# Source Inventory & Gap Report: Ipswich River (Massachusetts)

| | |
|---|---|
| **Watershed slug** | `ipswich_river_ma` |
| **Display name** | Ipswich River (MA) |
| **States** | MA |
| **Date** | 2026-06-01 |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` |
| **Author** | Claude (analysis-only; user evaluating whether to onboard) |
| **Status** | **Step 1 analysis only — NOT added.** Companion: `parker_river_ma-source-inventory-2026-06-01.md`. |

> **Headline: the better of the two MA candidates and a reasonable fit for the existing model.** The Ipswich is a predominantly **freshwater inland river** (155 mi² basin; tidal influence capped at the Ipswich Mills head-of-tide dam) with an on-model fishery (stocked + holdover/wild trout, smallmouth/largemouth, pickerel, panfish) and a **best-in-class, heavily documented summer low-flow / "river runs dry" narrative** that maps directly onto the flow-based Go Score. Shares two MA-wide weaknesses with Parker: **no water-temperature feed at the gauges**, and brittle HTML-only state stocking/herring sources.

---

## Watershed metadata + geometry

| Field | Value | Source |
|---|---|---|
| Slug | `ipswich_river_ma` | proposed |
| Display name | Ipswich River (MA) | proposed |
| States | MA (Essex + edge of Middlesex) | — |
| Headwaters | Burlington / Wilmington, MA | IRWA; USGS |
| Mouth | **Ipswich Bay / Plum Island Sound**, at Ipswich, MA | USGS NHD |
| Bbox (proposed, **needs tightening**) | `north=42.72, south=42.48, east=-70.77, west=-71.20` | gauge locations + basin; see overlap note |
| HUC8 code | **`01090001`** (same Merrimack-region HUC8 as Parker) | USGS `huc_cd` |
| NWS forecast office | **BOX** (Boston / Norton, MA) | api.weather.gov |
| Drainage area | **44.5 mi²** at South Middleton (upper) / **125 mi²** near Ipswich (lower); **155 mi²** total basin | USGS `drain_area_va`; IRWA |
| Length | ~35–45 mi (sources differ on headwater start: Wilmington vs Burlington) | IRWA; freestone-stream sources |
| Primary fishery | **Freshwater inland: stocked + some wild/holdover trout, smallmouth & largemouth bass, chain pickerel, panfish**; river-herring run; **small** estuary striper/clam fishery at the mouth | MassWildlife; IRWA; On The Water |

Like Parker, this is a **New England coastal-region** basin (HUC 01090001), but unlike Parker it is **inland-river-dominant**: the Ipswich Mills Dam is the head of tide, so essentially the entire mainstem upstream — the bulk of the river — is freshwater. The estuary/striper/clam fishery at the mouth is a minor tail, not the identity.

**bbox overlap note (matters for the runbook's overlap rule):** my provisional bbox is generous and bleeds into adjacent basins — the deterministic counts below were taken on it and so include neighbors (Merrimack at Lawrence, Shawsheen, Saugus, Spicket, and the Parker gauge all fell inside). A production bbox must be tightened to the Ipswich basin and will **abut the Parker basin** along Plum Island Sound — if both are ever onboarded, their coastal edges need deconfliction.

---

## §1.1 — Feature → source map (deltas from the Parker analysis; MA-wide feeds are identical)

| Feature | Status for Ipswich | vs Parker |
|---|---|---|
| USGS gauges | ✓✓ **Two Ipswich gauges** — 01101500 South Middleton (44.5 mi², upper) + 01102000 near Ipswich (125 mi², lower). Clean upper/lower reach split. | better (Parker had 1) |
| **Water temperature (00010)** | ✗ **GAP — neither Ipswich gauge reports water temp.** Same blank temp sub-score / live-temp issue as Parker. | same |
| Go Score — **flow** | ✓✓ **Signature strength.** USGS-quantified withdrawal-driven low flow (7Q10 at South Middleton modeled 4.1→0.54 ft³/s with withdrawals); **American Rivers #8 Most Endangered River, 2021**. The flow sub-score tells a real, citable story here. | far better |
| Catch probability | ✓ **On-model.** Stocked + holdover/wild trout, smallmouth/largemouth, pickerel, panfish — fits the freshwater model. Estuary striper at mouth is minor/out-of-scope. | **much better** (Parker was off-model estuary) |
| Hatch chart | ⚠ **Applicable** — freestone/slow-warmwater river with trout; East-Coast hatch seed (BWO/Caddis/Hendrickson/Sulphur) plausible with `needs_review=true`. (IRWA notes warmwater dominance in stressed reaches.) | better (Parker was N/A) |
| Stocking schedule | ⚠ MassWildlife stocks the Ipswich mainstem (Topsfield/Peabody/Reading), Boston Brook, Fish Brook, Stiles Pond — but the Trout Stocking Report is **HTML, no CSV/API, mass.gov UA-gated**. New `massachusetts` adapter. | same brittleness |
| River-herring run | ⚠ IRWA runs an annual herring count (Ipswich Mills Dam fishway); HTML/report only. Novel content. | same |
| Fish passage | ⚠✓ **Ipswich Mills Dam** removal under study; NOAA/USFWS Ipswich+Parker dam-removal program. Verify NFPP feed. | similar |
| Water quality / impaired | ✓✓ Very rich WQP coverage; MassDEP Integrated List ArcGIS Feature Service. | same (both strong) |
| iNaturalist | ✓✓ Dense (North Shore); see count caveat below. | comparable |
| Geology (MassGIS) | ✓ MassGIS ArcGIS REST (Avalon/Nashoba terrane). | same |
| Fossils (PBDB) | ✗ **3 occurrences** — even thinner than Parker. Weak DeepTrail. | worse |
| Recreation (RIDB) | ⚠ Bradley Palmer & Willowdale State Parks (MassParks), Ipswich River Wildlife Sanctuary (Mass Audubon); RIDB for any federal. MassWildlife WMAs via MassGIS. Needs RIDB key. | comparable |
| Restoration / LTER | ✓ MA DER + IRWA restoration; PIE-LTER covers Ipswich+Parker+Rowley to Plum Island Sound. | same |
| Fly shops / guides | ⚠ Freshwater is largely **DIY** (canoe/kayak/wade at Bradley Palmer/Willowdale); named local guiding (Greasy Beaks, Hamilton) skews **saltwater** (Ipswich Bay stripers). | similar market skew |
| snotel / mtbs / Western adapters | ✗ N/A empties. | same |

---

## §1.3 — Deterministic check results (verified, on provisional bbox)

```
✓✓ usgs       — 2 Ipswich gauges: 01101500 South Middleton (DA 44.5), 01102000 near Ipswich (DA 125). discharge+gage height. NO WATER TEMP at either. (bbox also caught Merrimack/Shawsheen/Saugus/Spicket/Parker — tighten before use.)
✓✓ inaturalist— 222,823 all-time / 161,341 last-5y research-grade; 794 fish. NOTE: inflated by generous bbox (includes North Shore suburbs/Merrimack). True Ipswich-basin count lower but still strong.
✓✓ wqp        — 3,241 station rows in bbox (inflated by bbox; MassDEP + PIE-LTER + EPA). Very rich either way.
✗  pbdb       — 3 occurrences. Metamorphic basement; negligible fossil content.
✓  massgis_geology / impaired / wbd / nhdplus / wetlands / prism / gbif / wqp_bugs / nws — same as Parker analysis (MA-wide / federal).
⚠  massachusetts (stocking) / ma_dmf_herring — same HTML/UA-gated brittleness as Parker.
```

---

## §1.7 — Reach inventory preview (only if onboarded)

| Reach ID | Name | Gauge | Fishery | Notes |
|---|---|---|---|---|
| `ipswich_river_ma_upper` | Upper Ipswich (Wilmington→South Middleton) | 01101500 South Middleton (44.5 mi²) | stocked trout, smallmouth, pickerel, panfish | **most flow-stressed reach** (withdrawals) |
| `ipswich_river_ma_lower` | Lower Ipswich (Middleton→Ipswich Mills head-of-tide) | 01102000 near Ipswich (125 mi²) | trout, largemouth/smallmouth, white perch, herring run | freshwater to head of tide |
| `ipswich_river_ma_estuary` | Ipswich Bay / Plum Island Sound | (NOAA tides) | striped bass, clams | **out-of-model**; minor tail |

Two-thirds of the angling identity sits in the first two reaches — which fit the existing model. That is the core reason Ipswich is the cleaner candidate.

---

## Recommendation (within this doc)

The Ipswich is a **viable inland-river add on the existing model**, with one signature differentiator (the documented summer low-flow / endangered-river story) that is genuinely strong content for a flow-based Go Score, and two shared-with-Parker caveats to accept up front: **no gauge water-temperature** (temp sub-score degrades to "no data"; the recent `-1799966.2°F` fix already hardens that path) and **brittle MA state feeds** (stocking/herring HTML). DeepTrail content is thin (3 PBDB). New `massachusetts` adapter required for stocking; impaired-waters and geology are clean ArcGIS wins.

See the cross-watershed recommendation at the end of the Parker analysis / the chat summary for **which of the two to load first.**

---

**End of Step 1 analysis. Watershed NOT added — no config entry, no ingestion, no deploy.**
