# Design note: Curation Admin Console

| | |
|---|---|
| **Date** | 2026-06-08 |
| **Status** | **Proposed** — enumeration + recommendation; not yet built. |
| **Origin** | Across app development and watershed onboarding, many datasets are hand-curated (or LLM-drafted then human-reviewed), but most are editable only by authoring an alembic migration or running a script. A few have `/admin` editors (`curated_species_photos`, `river_stories`) and two more have backends but no UI (`curated_insect_photos`, `watershed_splash`). There is no single place to see what needs curating or to do it. |
| **Related** | FEAT-007 (Fishing Intelligence), FEAT-023 (Watershed-First Admin Photos), FEAT-024 (Splash Card Editor), `plan-2026-06-05-admin-watershed-first-photo-workflow.md`, `plan-2026-05-18-insect-photo-curation.md`, `runbooks/add-watershed-prompt.md` §1.3/§2.4. |

## Problem
- The curation workload is real and recurring — every onboarded watershed needs reaches defined, species lists set, hatch charts seeded, flow bands computed, and business directories researched — but the only entry points are migrations and scripts.
- Onboarding auto-drafts v0 rows with `needs_review=true` / `source='v0 auto-seed…'`, yet nothing surfaces that backlog for a curator to approve/correct.
- Data-correctness bugs we hit (extirpated brook trout in Fish Present; the Ask oracle and Fish Present diverging on steelhead) trace back to curated `typical_species` that could only be fixed by shipping a migration.
- Existing admin pages (`/admin/photos`, `/admin/river-stories`) are reachable only by direct URL — there is no hub or "what needs doing" view.

## The curated datasets (enumeration)

### Foundational — reach definition
**Reach definition / segmentation** is the editorial act of dividing a river into reaches and is the **parent of most other curation**: how many reaches, where each boundary falls (USGS gauges, dams/reservoirs, named confluences, regulation boundaries), and per reach the `id`, `name`, `short_label`, `river_mile_start/end`, `bbox`, `centroid_lat/lon`, `primary_usgs_site_id`, `primary_snotel_station_id`, `general_flow_bearing`, `is_warm_water`. Table: **`silver.river_reaches`**. Today authored only via `<rev>_seed_<slug>_reaches.py` migrations (runbook §2.4.1). Everything below that is reach-scoped (`typical_species`, flow bands, hatch chart, Go Score, most RiverPath surfaces) hangs off these rows, so adding/removing/renaming a reach ripples downstream — the editor must be cascade-aware. **Guide-reviewed.**

### Already editable in `/admin` (CRUD + audit)
| Dataset | Table | Admin path | UI |
|---|---|---|---|
| Fish species photos | `gold.curated_species_photos` | `/admin/curated-photos` (+audit) | ✅ `AdminPhotosPage` |
| River stories (3 levels + audio) | `river_stories` | `/admin/river-stories` | ✅ `AdminRiverStoriesPage` |
| Insect/prey photos | `gold.curated_insect_photos` | `/admin/curated-insect-photos` (+audit) | ❌ backend only |
| Watershed splash card | `gold.watershed_splash` | `/admin/watershed-splash` (+audit) | ❌ backend only |

### Curated, NOT editable anywhere (migrations/scripts only)
| Dataset | Table | Drives | Sensitivity |
|---|---|---|---|
| **Reach species** | `silver.river_reaches.typical_species` | Fish Present + Catch Probability (brook-trout / steelhead issues live here) | High — unfiltered, surfaces verbatim |
| **Hatch chart** | `curated_hatch_chart` (+`fly_patterns`, `photo_url`) | Go Score, Hatch tab | Entomologist-reviewed |
| **Flow bands** | `silver.flow_quality_bands` | Go Score flow sub-score | Angler-reviewed |
| **Fly shops / guides** | `fly_shops_guides` | RiverPath directories | Per-watershed research; never fabricate |
| **Mineral / rock shops** | `mineral_shops` | DeepTrail directory | Per-watershed research; never fabricate |
| **Rockhounding sites** | `rockhounding_sites` | DeepTrail | **Liability-sensitive** — conservative entries only |
| **Fly-tying videos** | `fly_tying_videos` | Hatch "Tie it" links | Per-pattern curation |
| **Insect→fly map** | `silver.insect_fly_patterns` | Hatch recommendations | Cross-watershed |
| **Deep-time stories** | `deep_time_stories` | DeepTrail | Curator + LLM |
| Fossil common names | `fossil_occurrences.common_name` | Fossil UI | Code-level lookup (low priority) |
| Mineral commodity names | `mineral_deposits.commodity` | Mineral UI | Code-level lookup (low priority) |

Excluded as *enrichment-pipeline* (not hand-curated): fossil images, mineral images.

## Recommendation

Standardize on the pattern that already works: **`/admin/<dataset>` CRUD guarded by `get_current_admin`, every write mirrored to `audit.<table>_log`, with a matching `<AdminRoute>`-gated React page (list → detail → edit → history).**

1. **Admin hub at `/admin`** — landing grid of dataset cards with row counts + a `needs review` badge, linking to each editor. Biggest usability win; none exists today.
2. **Global "Needs Review" queue** — list every row across curated tables flagged `needs_review=true` / `source='v0 auto-seed…'`. Turns the runbook §2.4 checklist into actionable work.
3. **Per-watershed curation dashboard** — for a selected watershed, show each dataset's status (rows present? needs review? empty?) — the §2.4 checklist, live. This is the "make onboarding curation available through /admin" answer.
4. **Build editors in impact order:**
   - **Tier 0 — foundational:** `silver.river_reaches` reach definition (cascade-aware) + `typical_species`.
   - **Tier 1 — correctness:** `curated_hatch_chart` (+fly_patterns/photo_url), `flow_quality_bands`.
   - **Quick wins (backend exists):** wire frontend for `curated_insect_photos` + `watershed_splash`.
   - **Tier 2 — structured data entry:** `fly_shops_guides`, `mineral_shops`, `rockhounding_sites` (form UI with a required "verified source URL" field reduces the fabrication risk).
   - **Tier 3 — content:** `fly_tying_videos`, `insect_fly_patterns`, `deep_time_stories`.
   - **Tier 4 — lookups:** fossil common names, commodity names.
5. **Metadata-driven CRUD framework** — model each curated table as a config entry (table, columns, validators, scope key, audit log) so new curated tables become config, not bespoke pages.

## Open questions
- Reach-definition editor: how far to take cascade handling on reach delete/rename (block if children exist vs. soft-deprecate vs. cascade-edit)?
- Do business-directory edits need a second-reviewer approval step before publish (liability for `rockhounding_sites`)?
- Should the Needs-Review queue and per-watershed dashboard read live or off the `data_status_cache`?

## Not in scope
Implementation. This note captures the enumeration and approach only.
