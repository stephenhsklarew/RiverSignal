# Design Plan: Warmwater Species Coverage

**Date**: 2026-05-15
**Status**: CONVERGED (post-collaborative review, 2026-05-16)
**Refinement Rounds**: 1 (solo) + 6 forks resolved with product owner

## Collaborative Review Outcomes

| Fork | Decision | Notes |
|---|---|---|
| OF-1 Warmwater UI | **Mix into existing list** — no badge, no filter | Species list stays unified; warmwater entries sorted by score alongside salmonids |
| OF-2 Striped bass | **Include model entry now** | 1 line in `SPECIES_MODELS`; future-proofs for lower Potomac / James / lower Susquehanna adds |
| OF-3 Catfish | **Include both channel and flathead** | 2 lines; channel cat is relevant to Shenandoah summer warm stem; flathead is cheap insurance |
| OF-4 UDWR broadening | **Bundle into this plan** | Single WHERE clause + matview refresh; not worth its own plan |
| OF-5 FWS NFHP | **Spike now, in scope** | Investigate as part of this build; if useful, add as 5th UNION block to `species_by_reach`. Otherwise document and close |
| OF-6 Warmwater copy | **No copy v1** | Revisit only if support tickets warrant. Sparseness self-evident from species list |

**Scope**: Expand RiverSignal's species coverage and catch-probability scoring to handle warmwater game fish (smallmouth bass, largemouth bass, musky, walleye, striped bass, channel + flathead catfish, pickerel, panfish, white bass) with the same fidelity we give salmonids today. No new watersheds in this plan — keep scope tight, surface improvements within existing coverage first.

---

## Problem Statement

A user on `/path/now/shenandoah` opens the Catch Probability section and sees rainbow trout, brown trout, brook trout — but smallmouth bass, the river's signature species, is missing or underrated. The Shenandoah is a top-5 East Coast smallmouth fishery; RiverSignal currently presents it as a trout river with smallmouth as an afterthought. Same pattern shows up on the Green River (smallmouth, walleye, pikeminnow underrepresented) and would block any future expansion into mid-Atlantic / Midwest / Southeast warmwater systems (Susquehanna, James, lower Potomac, Roanoke, French Broad).

Three independent layers of trout bias compound to produce this gap, each fixable on its own but each only partially effective alone:

1. **Data ingestion** — `gold.species_by_reach` UNIONs four sources: ODFW (Oregon salmonid-focused), WDFW SalmonScape (Washington salmon-only), state stocking interventions (trout-heavy), and iNaturalist research-grade fish. The first three are biased toward salmonids by agency mandate. iNaturalist is the only catch-all, and warmwater anglers post to iNat at a tiny fraction of the rate they post to bass-specific apps.

2. **Catch-probability scoring** (`pipeline/predictions/catch_forecast.py`) — The `SPECIES_MODELS` dict has 10 entries: 9 cold-water salmonids and a single generic `"bass"` entry with no smallmouth/largemouth distinction. Any other warmwater species (musky, walleye, striper, catfish, panfish, pickerel) falls back to a default model with `temp_opt: (8, 18)` °C — salmonid-shaped. So even when a warmwater species *is* in the species table, the catch probability will say "low — too warm" exactly when the fish should be in peak.

3. **Watershed selection** — Six of eight active watersheds are cold-water PNW systems where warmwater game fish don't biologically exist. Not a bug; just means layers 1 and 2 only affect 2 of 8 watersheds today (Green River, Shenandoah). The fix to layers 1 and 2 unlocks future warmwater watersheds, but doesn't require them.

This plan fixes layers 1 and 2. Layer 3 is out of scope (deferred to a separate watershed-add plan).

---

## Requirements

### Functional

#### F1. Expanded catch-probability species models
1. `SPECIES_MODELS` in `pipeline/predictions/catch_forecast.py` gains entries for the following species with thermal optimum, peak months, flow preference, and stocking-boost flag derived from the fisheries literature cited in §References:
   - `smallmouth bass`: `temp_opt: (18, 24)`, `peak_months: [5, 6, 7, 8, 9]`, `flow_pref: "moderate"`, `stocking_boost: False`
   - `largemouth bass`: `temp_opt: (20, 27)`, `peak_months: [6, 7, 8]`, `flow_pref: "low"`, `stocking_boost: False`
   - `musky` (incl. tiger muskellunge): `temp_opt: (16, 22)`, `peak_months: [5, 6, 9, 10]`, `flow_pref: "moderate"`, `stocking_boost: True`
   - `walleye`: `temp_opt: (15, 22)`, `peak_months: [4, 5, 6, 9, 10]`, `flow_pref: "moderate"`, `stocking_boost: True`
   - `striped bass`: `temp_opt: (12, 22)`, `peak_months: [4, 5, 6, 9, 10, 11]`, `flow_pref: "high"`, `stocking_boost: False`
   - `channel catfish`: `temp_opt: (24, 29)`, `peak_months: [6, 7, 8, 9]`, `flow_pref: "low"`, `stocking_boost: True`
   - `flathead catfish`: `temp_opt: (24, 30)`, `peak_months: [6, 7, 8]`, `flow_pref: "low"`, `stocking_boost: False`
   - `chain pickerel`: `temp_opt: (15, 22)`, `peak_months: [3, 4, 5, 10, 11]`, `flow_pref: "low"`, `stocking_boost: False`
   - `bluegill` / `sunfish` / `panfish`: `temp_opt: (20, 28)`, `peak_months: [5, 6, 7, 8]`, `flow_pref: "low"`, `stocking_boost: True`
   - `white bass`: `temp_opt: (16, 24)`, `peak_months: [4, 5, 6]`, `flow_pref: "moderate"`, `stocking_boost: False`
2. The generic `"bass"` fallback is kept but moved to the bottom of the matching order so `"smallmouth"` and `"largemouth"` match first.
3. Matching is still substring (`if key in name_lower:`) — order matters: longer/more-specific keys first.

#### F2. State warmwater dataset adapters
4. **VA DWR smallmouth surveys** — already partially wired (`pp16k7l8m9n0_explode_va_dwr_species_arrays.py`). Verify research-grade smallmouth observations on the Shenandoah surface in `species_by_reach` and confirm scoring picks them up under the new `smallmouth bass` model.
5. **UDWR warmwater fisheries** — extend the existing UDWR ingest to pull non-trout records (smallmouth, walleye, pikeminnow). The trout-only filter was a scope choice in `f7a8b9c0d1e2_fix_udwr_stocking_data.py`; broaden it.
6. **FWS National Fish Habitat Partnership data** — research whether the FWS NFHP REST API exposes per-stream species occurrence data we can add as a fifth UNION block in `species_by_reach`. If not, document the gap and defer.

#### F3. Frontend display
7. No required frontend work for v1 — Catch Probability already iterates over whatever species the API returns. New species automatically appear.
8. Validate species emoji/icon coverage in `frontend/src/components/SpeciesIcon.tsx` (or equivalent). If smallmouth/musky/walleye/striper/catfish lack icons, add SVGs (one day of design work, can be deferred to v1.1).

#### F4. Refresh + verification
9. After F2, refresh `gold.species_by_reach` (matview). Verify with: `SELECT common_name, count(*) FROM gold.species_by_reach WHERE watershed IN ('shenandoah', 'green_river') GROUP BY 1 ORDER BY 2 DESC LIMIT 30;`
10. Spot-check `/api/v1/sites/shenandoah/fishing/catch-probability` returns smallmouth with a high score in summer (June water_temp ≈ 22°C → expected score in the 70–85 range).

### Non-Functional

- **No new external API dependencies** beyond optional FWS NFHP (F2 step 6). VA DWR and UDWR adapters already exist; we're extending filter scopes.
- **Backward compatibility**: cold-water species scoring must not regress. Smoke test by comparing catch-probability output for `/sites/mckenzie/fishing/catch-probability` before and after — should be identical (no salmonid models change).
- **Performance**: `species_by_reach` is a materialized view refreshed on the daily refresh cron. New rows from expanded ingests increase row count by an estimated 10–25% (warmwater species are sparser than salmonids in iNat); refresh time impact is negligible.

---

## Data Model

No schema changes. Three matview-internal changes:

1. **VA DWR** — already explodes species arrays (`pp16k7l8m9n0`). Verify the explosion covers all surveyed species, not just trout.
2. **UDWR** — broaden filter in the existing ingest to pass through warmwater species records.
3. **`SPECIES_MODELS` dict** — 10 new entries in `catch_forecast.py`.

Optional follow-up (deferred): if FWS NFHP turns out to be useful, add a fifth UNION block to `species_by_reach`. New columns would not be needed.

---

## Architecture Decisions

### AD-1. Keep `SPECIES_MODELS` as a literal dict, not a DB table

**Alternatives considered:**
- Move species models to a `gold.species_models` table for easy ops tuning without redeploy.
- Keep as literal Python dict in `catch_forecast.py`.

**Decision: keep as Python dict.**
**Rationale:** 10 → 20 species is a one-time expansion. Models drift slowly (fisheries literature, not real-time). The cost of a DB lookup per scoring call would exceed the cost of a code change every few years. Revisit if we ever reach 100+ species or if a non-engineer needs to tune.

### AD-2. Substring matching with order, not exact match or regex

**Alternatives considered:**
- Exact match on canonical names with a synonym table.
- Regex per species.
- Substring matching (current approach).

**Decision: substring with explicit ordering (longest-specific first).**
**Rationale:** Current code already substring-matches. Inputs come from heterogeneous sources (iNat scientific names, ODFW species fields, stocking descriptions) and synonyms are unbounded ("smallie", "bronzeback", "spotted bass" is a *different* species, "Micropterus dolomieu"). Substring + order is forgiving and debuggable. The order matters: `"smallmouth"` must be matched before `"bass"` so the specific model wins.

### AD-3. Defer new warmwater watershed additions

**Alternatives considered:**
- Bundle a new watershed (Susquehanna / lower Potomac / James) into this plan.
- Ship F1+F2 only; new watersheds in a follow-up.

**Decision: defer.**
**Rationale:** Adding a watershed is a multi-week effort following `docs/helix/runbooks/add-watershed-prompt.md` and brings its own data-completeness checklist. Mixing it in delays the smaller improvements that already pay off on Shenandoah and Green River. Two existing watersheds will validate the species/scoring work before we commit to new geography.

### AD-4. Icons can lag the model expansion

**Alternatives considered:**
- Block F1 ship until all new species have icons.
- Ship F1 with a generic-fish fallback icon, add specific icons in v1.1.

**Decision: ship with fallback.**
**Rationale:** Catch Probability text is the value; icon polish is secondary. A generic fish glyph is fine for v1 and prevents F1 from being blocked on design work.

---

## Implementation Ordering

### Phase 0 — Audit (½ day)
1. Run `SELECT common_name, count(*) FROM gold.species_by_reach GROUP BY 1 ORDER BY 2 DESC` to see today's species distribution.
2. Verify the `bass` substring fallback path with a smoke test: catch probability for smallmouth in Shenandoah at 22°C summer → confirm the *generic* model is what gets used today.
3. Decide whether to do F2 step 6 (FWS NFHP research) now or skip it.

### Phase 1 — Species models (½ day)
4. Add the 10 new entries to `SPECIES_MODELS` in `pipeline/predictions/catch_forecast.py`.
5. Re-order the dict so longest/most-specific keys come first.
6. Add a `species_models_smoke.py` test script (not full pytest — just runnable locally) that verifies each new species scores >70 when conditions are inside its `temp_opt` during a `peak_month`.

### Phase 2 — UDWR warmwater extension (NO-OP, FINDING RECORDED 2026-05-16)
7. ~~Identify the UDWR ingest filter in `pipeline/ingest/utah.py`~~ — **no such filter exists**. The adapter (`_ingest_udwr_stocking`) already pulls every species UDWR stocks for the `GREEN RIVER` and `FLAMING GORGE` waterbodies. Trout dominance in the data is genuine, not filtered.
8. **Real gap on Green River**: most native warmwater game fish (smallmouth, walleye, Colorado pikeminnow) live in the Wyoming-side headwaters and Desolation/Canyonlands sections where UDWR has no jurisdiction. Better coverage would require a **Wyoming Game & Fish** or **Utah DWR research surveys (non-stocking)** adapter — both watershed-scope expansions outside this plan.
9. **Action**: this phase is closed without code changes. The Phase 1 species-model additions still apply if iNat or future data sources surface these species.

### Phase 3 — VA DWR coverage verification (½ day)
10. Read `pp16k7l8m9n0_explode_va_dwr_species_arrays.py` end-to-end. Confirm smallmouth survey rows reach `species_by_reach` for Shenandoah.
11. If they do, no work needed beyond a smoke test. If they don't, add the missing transformation.

### Phase 4 — FWS NFHP spike (NEGATIVE OUTCOME, DOCUMENTED 2026-05-16)
12. **Spike findings**:
    - NFHP's flagship deliverable is the "Index of Anthropogenic Stressors" and similar habitat condition products rolled up at HUC-8 / HUC-12 scale, published via ScienceBase as static geodatabases / shapefiles.
    - **No queryable REST or WFS endpoint** for programmatic per-reach access — access is static file download via ScienceBase, which has been unreliable in spike testing (503s, timeouts).
    - **Product type mismatch**: NFHP scores habitat *condition* (e.g. "moderately stressed") at watershed scale, not *species occurrence*. It can't tell us "smallmouth bass is present at this reach."
13. **Decision**: do not integrate NFHP for warmwater species coverage. The data exists but is the wrong shape for our use case.
14. **Note for future work**: if we want to surface warmwater species occurrence from external sources, **GBIF is the better path** — the repo already has `pipeline/ingest/gbif.py`. A filtered GBIF query for Centrarchidae / Esocidae / Ictaluridae / Moronidae taxa, scoped to each watershed's bbox, would return per-occurrence records with lat/long. That's its own scoped expansion (likely a follow-up plan), not this one.

### Phase 5 — Smoke + ship (COMPLETE 2026-05-16)
14. `pipeline/predictions/smoke_warmwater_species.py` written and run. Outcome:
    - 13/13 new warmwater species score ≥70 at peak-season + in-temp_opt conditions
    - 13/13 score ≤50 out of season
    - Substring ordering verified: `"smallmouth bass"` routes to its specific model (temp_opt 18–24), not generic `"bass"` fallback (18–27)
    - Salmonid scoring at known conditions unchanged (regression check)
15. **Pending operator actions before user-visible ship**:
    - Run migration on prod: `gcloud run jobs execute riversignal-migrate --region us-west1`
    - Verify `SELECT common_name, count(*) FROM gold.species_by_reach WHERE watershed IN ('shenandoah','green_river') GROUP BY 1 ORDER BY 2 DESC LIMIT 30;` shows the new `reach_curated` rows
    - Hit `/api/v1/sites/shenandoah/fishing/catch-probability` and confirm smallmouth appears with score in the 70–85 range during summer months
16. Commit + push.

**Total actual effort**: ~½ day. Phase 0 audit took ~30 min, Phase 1 species models ~30 min, Phase 2 turned out to be a no-op (no filter existed), Phase 3 produced a higher-value alternative (the `silver.river_reaches.typical_species` UNION block), Phase 4 NFHP spike outcome was negative, Phase 5 smoke test passed first try.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| New `SPECIES_MODELS` entries shadow existing salmonid scoring via substring match collision | Low | Medium | Explicit ordering in the dict (`smallmouth` before `bass`, `brook trout` before `brook`, etc.). Smoke test compares pre/post for cold-water watersheds. |
| UDWR filter expansion pulls in non-game species (suckers, dace) and clutters the UI | Medium | Low | Filter at the ingest layer to game-fish-relevant taxa only; or filter at the API layer with a curated game-fish list. Defer until we see the actual row counts. |
| `temp_opt` ranges from literature don't match the local fish populations (e.g., Shenandoah smallmouth thermal tolerance differs from textbook Northern Lakes populations) | Medium | Medium | First version uses textbook values. Tune per-watershed only if user feedback or catch-probability calibration data warrants. Tracked as a v1.1 concern. |
| FWS NFHP API turns out to require a developer key, has rate limits we can't work around, or only exposes coarse HUC-12 data with no per-reach detail | Medium | Low | Phase 4 has an explicit decision gate: if the spike outcome is negative, document and proceed without it. Plan does not block on NFHP being useful. |
| iNat coverage for warmwater fish is so sparse the species table still looks empty for new species | High | Medium | Expected — F1+F2 maximize what *can* be surfaced from current sources. Layer 3 (new watershed adds) is the long-term fix for geographies where iNat is sparse. |

---

## Observability

- **Pre/post species-count comparison** logged at the end of Phase 2 and Phase 3 (just numbers in the dev journal, not a permanent dashboard).
- **Catch-probability spot-checks** documented in the PR description as before/after JSON snippets for one cold-water and one warmwater watershed.
- No new monitoring or alerts required — this is a data/scoring improvement, not a new runtime surface.

---

## Test Strategy

- **Unit-level**: A small `pipeline/predictions/test_catch_forecast_warmwater.py` (or extension of an existing test file) that asserts each new species hits its expected score window at known conditions inside and outside its `temp_opt`.
- **Integration-level**: Hit the live API for Shenandoah and Green River after each phase; capture before/after JSON in the PR.
- **Regression**: McKenzie + Deschutes + Metolius catch-probability output must be byte-identical before/after, since no salmonid models are touched.
- **No frontend tests required** — F3 is unchanged UI surface.

---

## Out of Scope

- New watersheds (Susquehanna, James, lower Potomac, Roanoke, French Broad, etc.). Each is its own add-watershed exercise.
- Species-specific UI affordances (per-species "best lure" recommendations, regulation lookups). Possible v1.1 once species coverage justifies it.
- Per-watershed-specific thermal tuning. Textbook values for v1; calibration later.
- TQS sub-score weighting changes — warmwater species don't change how the *overall* watershed score is computed, only the per-species catch probability.

---

## Locked Decisions

All forks resolved 2026-05-16 (see §Collaborative Review Outcomes at top of doc). No open questions remain.

---

## References

- ODFW species temperature preferences: `Bjornn & Reiser 1991 — Habitat Requirements of Salmonids in Streams`
- Smallmouth bass thermal tolerance: `Whitledge et al. 2006`, USGS smallmouth bass species profile
- Walleye / musky: `Hokanson 1977 — Temperature Requirements of Some Percids and Adaptations to the Seasonal Temperature Cycle`
- Striped bass: USFWS Atlantic Striped Bass Stock Assessment
- Existing related plans:
  - `plan-2026-05-14-tqs-forecast-history.md` (CONVERGED + IMPLEMENTED)
  - `plan-2026-05-15-sms-alerts.md` (IMPLEMENTED — relevant since SMS dispatch keys off `gold.trip_quality_watershed_daily`, downstream of species data)
- Add-a-watershed runbook (out of scope, but referenced as the path for layer 3): `docs/helix/runbooks/add-watershed-prompt.md`
