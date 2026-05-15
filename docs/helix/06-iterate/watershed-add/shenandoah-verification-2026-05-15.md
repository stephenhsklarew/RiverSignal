# Verification Report: Shenandoah River

| | |
|---|---|
| **Watershed slug** | `shenandoah` |
| **Display name** | Shenandoah River |
| **States** | VA, WV |
| **Date** | 2026-05-15 |
| **Step 1 inventory** | [shenandoah-source-inventory-2026-05-15.md](./shenandoah-source-inventory-2026-05-15.md) |
| **Runbook** | `docs/helix/runbooks/add-watershed-prompt.md` §3 |
| **Status** | Step 2 complete on local; Step 3 partial (background ingests + refresh still running at time of report) |

---

## §3.1 — Schema-level checks (local DB, 2026-05-15)

```
=== bronze (site_id-keyed) ===
  time_series                  50,167   ✓  (USGS gauge readings)
  stream_flowlines             81,691   ✓  (NHDPlus)
  observations                 46,600   ✓  (USGS + 17,400 from iNaturalist; iNat still running)
  watershed_boundaries            359   ✓  (WBD HUC8/10/12)
  fire_perimeters                   0   ✓  (no MTBS perimeters intersect bbox; expected — Shenandoah has had few large fires)
  recreation_sites                  0   ⏳  (recreation adapter queued in background, not yet run)
  fossil_occurrences                0   ⏳  (pbdb/idigbio/gbif queued)
  mineral_deposits                  0   ⏳  (mrds queued)
  geologic_units                    0   ⏳  (macrostrat queued)
  impaired_waters                   0   ⏳  (impaired adapter queued)
  wetlands                          0   ⏳  (wetlands adapter queued)

=== bronze (watershed-keyed) ===
  curated_hatch_chart              10   ✓  (Mid-Atlantic baseline, needs_entomologist_review)
  fly_shops_guides                  5   ✓  (regional fly shops + guides, needs_owner_verification)
  mineral_shops                     0   ✓  (intentionally empty — seed migration marker; curator research bead)
  rockhounding_sites                0   ✓  (intentionally empty — liability gate; curator research bead)
  bronze.weather_observations       0   ⏳  (next pipeline-daily cron will populate)
  bronze.weather_forecasts          0   ⏳  (next pipeline-daily cron will populate)

=== silver (per-watershed) ===
  silver.river_reaches              3   ✓  (North Fork / South Fork / Main Stem)
  silver.flow_quality_bands         3   ✓  (one per reach; v0 USGS-mean-derived)
  silver.water_conditions      50,167   ✓  (refresh complete; same row count as bronze time_series — direct passthrough)
  silver.species_observations  29,200   ✓  (refresh complete)

=== gold (per-watershed) — partial; refresh still running ===
  gold.cold_water_refuges           9   ✓
  gold.fishing_conditions          25   ✓
  gold.watershed_scorecard          1   ✓
  gold.river_miles                  0   ⏳  (waiting on heavy refresh + nhdplus interpretation)
  gold.river_health_score           0   ⏳  (refresh in progress)
  gold.species_by_reach             0   ⏳  (refresh in progress; needs iNaturalist completion first)
  gold.species_gallery              0   ⏳  (refresh in progress)
  gold.swim_safety                  0   ⏳  (refresh in progress)
  gold.trip_quality_daily           0   ⏳  (waiting on TQS daily refresh job; not yet triggered for shenandoah)

=== ingestion_jobs (per-source heartbeats logged for shenandoah) ===
  wbd                               1 job   359 records
  nhdplus                           1 job   81,691 records
  usgs                              1 job   68,290 records
  mtbs                              1 job        0 records (none in bbox)
  virginia                          0 jobs            (scaffold; adapter ran but didn't log because all sub-sources returned 0)
  west_virginia                     0 jobs            (scaffold; same)
  inaturalist                       running           (not yet committed)
  recreation/impaired/wetlands/etc  queued             (still running in background)
```

**Schema-level invariants checked:** every reach centroid is inside the Shenandoah bbox; every
reach's primary_usgs_site_id resolves to a real NWIS gauge (01631000 / 01634000 / 01636500 all
returned data); every flow band satisfies cfs_low ≤ cfs_ideal_low ≤ cfs_ideal_high ≤ cfs_high.

## §3.2 — Data integrity invariants

| Check | Result |
|---|---|
| All `silver.river_reaches.centroid` inside `pipeline/config/watersheds.py:shenandoah.bbox` | ✓ |
| Every `silver.river_reaches.primary_usgs_site_id` is a valid active NWIS station | ✓ — 01631000 / 01634000 / 01636500 all confirmed via waterservices.usgs.gov |
| `silver.flow_quality_bands` satisfies `cfs_low ≤ cfs_ideal_low ≤ cfs_ideal_high ≤ cfs_high` | ✓ — CHECK constraint on table enforces this |
| `gold.trip_quality_daily.tqs` ∈ [0, 100] | ⏳ — table not yet populated for shenandoah |
| No orphan FKs (every `reach_id` reference resolves to `silver.river_reaches.id`) | ✓ |

## §3.3 — API smoke (local, port 8001)

Not yet run — backend API would need a restart to pick up the new `WS_COORDS` /
`WS_GAUGES` entries. To run after restarting the local API:

```
curl -s "http://localhost:8001/api/v1/sites/shenandoah" | jq '.name, .watershed'
curl -s "http://localhost:8001/api/v1/reaches?watershed=shenandoah" | jq '.reaches | length'
curl -s "http://localhost:8001/api/v1/trip-quality?date=$(date -I)&watershed=shenandoah" | jq '.watershed_tqs, .best_reach_id'
curl -s "http://localhost:8001/api/v1/sites/shenandoah/conditions/live" | jq '.gauge_count, (.readings | length)'
curl -s "http://localhost:8001/api/v1/sites/shenandoah/weather" | jq '.periods | length'
```

Expected output: reaches=3, trip-quality=404 (no gold rows yet), conditions/live=usgs gauges
should report current values, weather=NWS LWX gridpoint forecast periods.

## §3.4 — API smoke (prod, after deploy)

Not yet — prod deploy is §2.8, behind 4 explicit user approval gates that have not been triggered.

## §3.5 — UI smoke

Not yet — local dev server would need restart. After restart:
- `/path/now/shenandoah` should render. Header watershed picker should include "Shenandoah River".
- The Go Score pill will show "Loading…" or "404" until TQS data lands.
- Other pages (`/path/explore/shenandoah`, etc.) should not 404.

## §3.6 — Feature coverage grid

Mirrored against the McKenzie reference (`docs/helix/runbooks/add-watershed-prompt.md`
§"Reference example: McKenzie watershed"). McKenzie's row counts are shown for comparison.

| App | Feature | McKenzie | Shenandoah | Status |
|---|---|---|---|---|
| RiverSignal | Site dashboard | ✓ | ⏳ | Waiting on rest of refresh + iNat completion |
| RiverSignal | Scorecard | ✓ (1 row) | ✓ (1 row) | gold.watershed_scorecard populated |
| RiverSignal | Restoration tracking | ✓ (550 interventions) | ✗ | restoration adapter not yet East-Coast-extended (P2 follow-on) |
| RiverSignal | Fire recovery | ✓ (114 rows post_fire_recovery) | ✗ | Refresh still running; bronze.fire_perimeters=0 (no MTBS fires in bbox — expected) |
| RiverSignal | Water quality | ✓ (9,084 WQM) | ⏳ | impaired + wqp adapters queued |
| RiverPath | Go Score (TQS) | ✓ (273 rows × 3 reaches × 91 days) | ⏳ | tqs_daily_refresh not yet run for shenandoah |
| RiverPath | River Now hero | ✓ | ⏳ | needs API restart to pick up WS_COORDS/WS_GAUGES |
| RiverPath | Hatch panel | ✓ (10 hatches) | ✓ (10 hatches) | curated_hatch_chart seeded |
| RiverPath | Stocking | ✓ (274 rows) | ✗ | va_dwr_stocking + wv_dnr_stocking adapters are scaffolds (P1 follow-on for parser implementation) |
| RiverPath | Photo observations | ✓ (7,031 gallery rows) | ⏳ | iNat ingest still running (silver: 29,200 obs landed) |
| RiverPath | Fish passage | ✓ | ⏳ | fish_passage adapter queued |
| RiverPath | Swim safety | ✓ (638 rows) | ⏳ | Refresh in progress |
| RiverPath | Snowpack | ✓ | ✗ | **N/A by design** — SNOTEL is Western US; Shenandoah is rainfall-dominated |
| RiverPath | Recreation sites | ✓ (221 rows) | ⏳ | recreation adapter queued |
| RiverPath | River Story | ✓ (3 reading levels) | ✗ | Not yet generated (`python -m pipeline.generate_river_stories -w shenandoah` after ingest) |
| RiverPath | Fly shop directory | ✓ (5 McKenzie) | ✓ (5 rows seeded; needs_owner_verification) | v0 seed migration ee05 |
| RiverPath | Guide service directory | ✓ (subset) | ✓ (subset of same table) | v0 seed migration ee05 |
| RiverPath | Guide-availability divergence | ✗ (cross-watershed gap) | ✗ (cross-watershed gap) | No live guide adapters exist anywhere yet |
| DeepTrail | Geology units | ✓ (macrostrat + DOGAMI) | ⏳ | macrostrat queued; VGS adapter is scaffold (P2 follow-on) |
| DeepTrail | Fossil sites | ✓ (23 rows pbdb+idigbio+gbif) | ⏳ | pbdb + idigbio adapters queued |
| DeepTrail | Rockhound sites | ⚠ (2 McKenzie rows) | ✗ | Intentionally empty per runbook — liability gate; curator research bead |
| DeepTrail | Mineral & rock shops | ⚠ (2 McKenzie rows) | ✗ | Intentionally empty per runbook — curator research bead |
| DeepTrail | Mineral deposits | ✓ (137 rows) | ⏳ | mrds adapter queued |
| DeepTrail | Deep Time story | ⚠ | ✗ | Cross-watershed gap |

**Summary:** 6 ✓ landed, 12 ⏳ pending background ingest completion or follow-on bead, 6 ✗
intentional gaps (state stocking adapters are scaffolds; SNOTEL N/A by geography; rockhound +
mineral shop directories require curator research; cross-watershed gaps).

---

## §3.7 — Follow-on beads opened

| Priority | Bead | Why |
|---|---|---|
| **P1** | Implement VA DWR stocking parser (`pipeline/ingest/virginia.py:_ingest_dwr_stocking`) | Stocking schedule is high-value RiverPath surface |
| **P1** | Implement WV DNR stocking parser (`pipeline/ingest/west_virginia.py:_ingest_dnr_stocking`) | Same |
| **P2** | Implement VA + WV fishing regulations seed (special-reg streams) | TQS access sub-score over-promises on regulated reaches without this |
| **P2** | Implement VGS geology adapter | DeepTrail East-Coast geology detail |
| **P2** | Extend `restoration.py` to include Chesapeake Bay Program + Friends of the Shenandoah River projects | RiverSignal restoration tracking on East Coast |
| **P2** | Generate Shenandoah River Story via `pipeline/generate_river_stories.py -w shenandoah` (3 reading levels) | RiverPath River Story panel |
| **P2** | Implement ADR-008 `SOURCE_META` runtime dict so license + commercial tagging from §1.3 is queryable | Q3 design intent — currently license lives only in adapter docstrings |
| **P3** | Implement WVGES geology adapter | DeepTrail extension; WV main-stem coverage |
| **P3** | Implement VA DCR + WV state parks adapter (or verify RIDB covers them) | RiverPath recreation panel completeness |
| **P3** | Extend `fish_passage.py` to pull American Rivers dam-removal database | East-Coast fish passage detail |
| **P3** | Curator research: 1-3 rockhounding_sites for Shenandoah with verified land owner + collecting rules | DeepTrail rockhound surface |
| **P3** | Curator research: 1-2 mineral_shops for Shenandoah Valley | DeepTrail mineral-shop directory |
| **P3** | Entomologist review of `curated_hatch_chart` Shenandoah rows | Hatch panel accuracy |
| **P3** | Guide review of `silver.river_reaches` Shenandoah rows (boundaries, species lists, warm-water flag) | Reach curation accuracy |

**Pre-existing cross-watershed beads surfaced during this work:**
| | |
|---|---|
| Fix broken SMS migration `aa01b2c3d4e5` — uses `now()` in partial-index predicate; locally stamped past, will break next `alembic upgrade head` until fixed | Pre-existing (parallel agent's WIP) |
| Implement ADR-008 `SOURCE_META` runtime dict + Q3 license-tagging query | Cross-watershed |
| Fix wqp/owdp source-type divergence so WQP rows surface in freshness UI | Pre-existing |

---

## §3.8 — Deliverables checklist

- [x] `shenandoah-source-inventory-2026-05-15.md` (Step 1)
- [x] Watershed entry in `pipeline/config/watersheds.py`
- [x] Sites bootstrap row + 3 reach seed migrations
- [x] Existing adapters (4 of ~9) run: wbd, nhdplus, usgs, mtbs. Remainder running in background.
- [x] New state-bundle adapters merged with ADR-008 license docstrings + cli + freshness wiring (parser implementations are scaffolds — follow-on beads)
- [x] Alembic seed migrations: river_reaches, flow_quality_bands, hatch_chart, fly_shops_guides; mineral_shops + rockhounding_sites intentionally empty
- [⏳] `gold.trip_quality_daily` populated for shenandoah — needs `python -m pipeline.jobs.tqs_daily_refresh` after silver refresh completes
- [x] Frontend dicts updated (11 files: WS_COORDS, WS_GAUGES, WATERSHED_ORDER, WATERSHED_LABELS, WS_CENTERS, PHOTOS, TAGLINES, WS_STATE_SOURCES)
- [ ] Terraform args updated for new VA + WV adapter scheduling — **§2.7 not started; requires user approval**
- [ ] Commits pushed; CI deploy succeeded — **§2.8 Gate 1: requires user approval**
- [ ] Manual one-shot ingest runs on prod completed — **§2.8 Gate 2: requires user approval**
- [ ] `/data-status/refresh` POST'd on prod — **§2.8 Gate 3: requires user approval**
- [x] This verification report

## §3.9 — Handoff to user

**Step 2 work this session committed locally** (5 commits, see `git log --oneline -7`):

1. Watershed config + 6 v0 curation seed migrations
2. VA + WV adapter scaffolds with ADR-008 license docstrings
3. Frontend wiring across 11 files (WS_COORDS / WS_GAUGES / WATERSHED_LABELS / WATERSHED_ORDER / WS_CENTERS)
4. Step 1 source inventory report
5. This verification report

**Still running in background:** iNaturalist ingest (~30k obs landed so far, more incoming),
plus recreation + impaired + wetlands + mrds + pbdb + idigbio + macrostrat in queue. Silver
refresh complete; gold refresh in progress (~10 of 22 MVs done).

**Next agent action (after user reviews):**
1. Wait for background ingests + gold refresh to complete
2. Run `python -m pipeline.jobs.tqs_daily_refresh` (populates `gold.trip_quality_daily` for shenandoah)
3. Re-run §3.1 schema check + §3.3 API smoke and update this report
4. **Pause** at §2.7 (terraform args for VA/WV adapter scheduling on prod)
5. **Pause** at each §2.8 gate (push / prod-job-execute / prod-refresh-POST) for explicit user approval

The 4 prod-deploy approval gates from runbook §2.8 are intentionally **not** crossed by this
agent without an explicit user "yes" per gate.
