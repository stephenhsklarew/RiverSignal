# Verification Report: Ipswich River (MA)

| | |
|---|---|
| **Watershed slug** | `ipswich_river_ma` |
| **Display name** | Ipswich River (MA) |
| **States** | MA |
| **Date** | 2026-06-02 (prod deploy + ingest ran into 2026-06-03 UTC) |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` (STEP 3) |
| **Source inventory** | `ipswich_river_ma-source-inventory-2026-06-01.md` |
| **Status** | **LIVE on prod.** First New-England-coastal-region watershed; first MA state adapter. |
| **Prod URL** | https://riversignal-api-x6ka75yaxa-uw.a.run.app |
| **Deployed image** | `…/api:eda93cd…` (origin/main) |

---

## Deploy path (non-trivial — recovered from a concurrent-merge race)

Onboarding ran via `/add-watershed`. Two infra hazards from the parallel multi-agent worktrees sharing this repo (the `project_parallel_watershed_onboarding` memory):

1. **PR #12 merge was truncated** to commit `d84fb5e` (a concurrent push reset the remote branch head mid-merge), so `origin/main` got only the config + adapter — migrations/wiring/seeds/terraform were dropped and prod 404'd the watershed. **Recovered** via PR #13 (re-applied the 4 dropped commits on top of current main; added a push-verify-before-merge check to prevent recurrence).
2. **Alembic chain entanglement** — `ip03` had chained onto the parallel agent's `ph03b1c2d3e4` (SMS `users.phone_hash`) migration, which was never committed to main; the prod migrate would have failed to resolve it. **Fixed** by re-pointing `ip03.down_revision → ip02` so the Ipswich chain is self-contained (`ro2so3idx4567 → ip01 … ip06`).
3. **Boundary** shipped as a static GeoJSON seed (`ip06`) because `wbd` isn't a scheduled prod job (so the `ST_Union`-from-`watershed_boundaries` approach is a no-op on prod — true for every watershed). PR #14.

Prod gates executed with explicit approval: Gate 1 (deploy), terraform apply, Gate 2 (ingest jobs), Gate 3 (freshness POST), + the off-hours `refresh-heavy`. Gate 4 (post-wbd boundary UPDATE) was made moot by the `ip06` seed.

---

## §3.1–3.2 Schema + integrity (local DB, mirrors prod after migrate)

- 1 site, **2 reaches** (`ipswich_river_ma_upper` @ 01101500, `ipswich_river_ma_lower` @ 01102000), 2 flow-quality bands.
- Both reach centroids inside the bbox; both `primary_usgs_site_id` resolve to live NWIS gauges; flow bands satisfy `cfs_low ≤ ideal_low ≤ ideal_high ≤ cfs_high` (1/7/33/103 and 2/19/83/249).
- `gold.trip_quality_daily`: 182 rows (2 reaches × 91 days); TQS values in [0,100].

## §3.3–3.4 API smoke (PROD, post-deploy + ingest + refresh-heavy)

| Endpoint | Result |
|---|---|
| `/sites/ipswich_river_ma` | 200, bbox east −70.80 (tightened) |
| `/trip-quality?date=2026-06-03` | **watershed_tqs 78**, best reach `ipswich_river_ma_upper` |
| `/sites/.../conditions/live` | 2 gauges, 2 readings (discharge) |
| `/sites/.../weather` | 8 NWS periods (office BOX) |
| `/sites/.../fishing/species` (Fish Present) | **69 rows, 68 with photo** |
| `/sites/.../catch-probability` | **13 game species, overall 65** |
| **Fish Present ↔ Catch Probability parity** | **✓ holds** — every catch-prob species present in Fish Present |
| `/sites/.../river-story` | 3,419 chars |
| `/sites/.../recreation` | 7 curated sites |
| `/fossils/near/42.65/-70.95` | 16 fossils, 8 with image (~50%) |

> Note: 13 game species on prod vs 22 in the local pre-tightening build is **correct** — the bbox was tightened to the Ipswich Mills head-of-tide, excluding the estuary/coast (and its species). The `/path/now` Fish Present card renders the 13, matching Catch Probability.

## §3.6 Feature-coverage grid (prod)

| App | Feature | Status | Notes |
|---|---|---|---|
| RiverSignal | Site dashboard | ✅ | live |
| RiverSignal | Water quality (WQP) | ⚠ | **`wqp` ingested 0 despite 3,088 stations in-box — bead** |
| RiverSignal | Macroinvertebrate (wqp_bugs) | ✅ | 627 |
| RiverSignal | 303(d) impaired | ✅ | 223 (EPA ATTAINS) |
| RiverSignal | Restoration | ✅ | 27 (NOAA) |
| RiverSignal | Fire recovery | ✗ N/A | no MA wildfire (graceful empty) |
| RiverPath | Go Score / TQS | ✅ | **78**, flow sub-score reflects the documented low-flow stress |
| RiverPath | Water-temp sub-score | ⚠ | no gauge reports 00010 → neutral default (bead) |
| RiverPath | River Now (live + weather) | ✅ | 2 gauges, 8 NWS periods |
| RiverPath | Fish Present | ✅ | 69 (68 photos) |
| RiverPath | Catch Probability | ✅ | 13 game species, parity holds |
| RiverPath | River Story | ✅ | 3 reading levels |
| RiverPath | Recreation | ✅ | 7 curated (RIDB had 0 — MA gap filled by seed) |
| RiverPath | Photo observations (iNat) | ✅ | ~66K obs (tightened bbox) |
| RiverPath | Hatch | ⚠ | **0 — no curated hatch chart seeded (bead)** |
| RiverPath | Stocking | ✗ | **MA DFW UA-gated/JS-rendered → P2 bead** (empty, no placeholders per §2.4.5) |
| RiverPath | Snowpack | ✗ N/A | coastal, no relevant SNOTEL |
| DeepTrail | Geology units | ⚠ | **macrostrat sparse in New England; `geology/at` returns 0 — MassGIS geology bead** |
| DeepTrail | Fossils | ✅⚠ | 16 (8 with image, ~50% — below the ~85% norm; thin New England fossil record) |
| DeepTrail | Minerals (MRDS) | ✅ | 66 |
| — | Boundary | ✅ | set via `ip06` GeoJSON seed (not exposed by any API; no user-facing effect) |

## Follow-on beads (every ⚠ / ✗ above)

- **P2** Author a working MA DFW stocking path (headless-browser render or public-records data request) — mass.gov UA-gates the Trout Stocking Report; adapter ships empty today.
- **P2** Investigate `wqp` returning 0 for `ipswich_river_ma` despite 3,088 WQP stations in-bbox (provider/param-shape; MassDEP submits as `MASSDEP`/`21MASSDEP`?).
- **P2** Boundary platform-fix: make `wbd` a scheduled prod job (or ship boundary seeds for all watersheds) and backfill `mad_river_oh` + `shenandoah` (both NULL on prod); also expose `boundary` via the API if the homepage map is meant to use it.
- **P2** MA DMF river-herring counts seed (Ipswich is a DMF sentinel river) — annual HTML/PDF, no structured feed.
- **P3** Curated hatch chart for the Ipswich (East-Coast warmwater + put-and-take-trout seed; `needs_entomologist_review`).
- **P3** MassGIS bedrock/surficial geology adapter (Avalon/Nashoba terrane) — macrostrat is sparse here.
- **P3** Fly-shop / guide + mineral-shop + rockhounding curation (saltwater-skewed local market: Surfland, Greasy Beaks, etc.).
- **P3** Estuary/tidal fishery model — the Plum Island Sound striper fishery is intentionally out of v0 TQS scope; revisit if an estuarine scoring path is built.

## Deliverables checklist

- [x] Source inventory + STEP 0 transcript
- [x] `watersheds.py` entry (HUC10 bbox, tightened to head-of-tide)
- [x] Existing adapters run; bronze landed (prod)
- [x] New `massachusetts` adapter merged + tests (5 pass)
- [x] Seed migrations: reaches, flow bands, river stories, recreation, boundary
- [x] `gold.trip_quality_daily` populated (Go Score 78 on prod)
- [x] Frontend dicts wired (~18 files; tsc + vite build clean)
- [x] Playwright watershed-smoke 12/12 (local)
- [x] terraform applied to prod (weekly job includes `massachusetts`)
- [x] CI deploy succeeded; prod one-shot ingest jobs run; refresh-heavy run
- [x] Fish Present ↔ Catch Probability parity verified on prod
- [x] `/data-status/refresh` POST'd
- [x] This verification report
- [ ] Re-run Playwright smoke against prod `BASE_URL` — deferred (local smoke passed 12/12; prod surfaces verified via API above)

---

**Ipswich River (MA) is live on production.** Remaining items are tracked as follow-on beads above; none block the v0 experience.
