# Design note: Fish-species canonicalization

| | |
|---|---|
| **Date** | 2026-06-08 |
| **Status** | **In Build** — Phase 1 implemented; Phase 2 specified. |
| **Origin** | User report: "Fish Present" + `/admin/photos` show duplicate fish with slightly different names (Fall/Spring/Chinook; Summer Steelhead/Steelhead; Rainbow Trout/Rainbow). |
| **Related** | FEAT-026, FEAT-007 (Fish Present), FEAT-023 (admin curation). |

## Problem

`gold.species_by_reach` is a `UNION ALL` across ~6 sources (ODFW StreamNet, WDFW
SalmonScape, iNaturalist, state fish-habitat data, …). Each emits its own
`common_name`, an unreliable `scientific_name` (sometimes a real binomial,
sometimes a common-name string, often NULL), and sometimes a separate `run_type`.
Downstream, Fish Present and the admin fish list group by the **raw** name, so the
same fish appears many times:

- case/whitespace: `rainbow trout` vs `Rainbow Trout`
- suffix noise: `Chinook` vs `Chinook Salmon`
- subspecies: `Coastal Rainbow Trout` (*O. m. irideus*)
- run-timing baked into the name: `Fall Chinook` / `Spring Chinook`, `Summer/Winter Steelhead`

`curated_species_photos` is keyed per raw name, so admins re-upload one photo per variant.

## Decision

A **global canonicalization layer** in the gold-serving path. Names are unreliable
and `scientific_name` can't be the key, so we use a deterministic normalizer +
(Phase 2) a small curated override table — not a full taxonomy backbone (YAGNI at
this scale).

**Product decision (confirmed):** Steelhead and Rainbow Trout stay **separate**
canonical entries (anadromous vs resident *O. mykiss* — anglers treat them as
different fish). Collapse only the noise *within* a form. Kokanee stays separate
from Sockeye by the same rule.

## Phase 1 (implemented)

`app/lib/species_canonical.py` — `canonicalize(common_name, scientific_name) ->
Canon(key, label, run)`:
- strips one leading run-timing word (`spring/fall/summer/winter`) → `run`
- strips one leading descriptor (`coastal/redband/westslope/interior`)
- fixes spacing nicknames (`small mouth`→`smallmouth`)
- maps the base to a canonical label via a small dict (`chinook`→`Chinook Salmon`,
  `redband`→`Rainbow Trout`, `steelhead`→`Steelhead`, …); unknown → Title Case
- `key` = lowercased canonical label (the dedup + curation key)

`app/routers/fishing.py::fishing_species` now groups by `canon.key`, displays
`canon.label`, and aggregates `runs` (e.g. `["spring","fall"]`) + `aliases` (raw
names covered). Because `app/routers/admin.py::list_watershed_fish` **reuses**
`fishing_species`, the admin list dedupes for free and its `species_key` becomes
canonical — so a photo set on the canonical entry covers all variants.

Verified on John Day: 8 salmonid rows → Chinook Salmon (spring+fall), Steelhead
(summer+winter), Rainbow Trout (redband+rainbow) as three entries; Steelhead ≠
Rainbow Trout. Unit tests in `tests/test_species_canonical.py`.

## Phase 2

✅ **Cross-surface parity** (PR #71): `canonicalize` applied to catch-probability so
it agrees with Fish Present. (species-spotter is the insect/prey surface — not fish —
so it's out of scope.)

✅ **Re-key migration** (`sk20a1b2c3d4`): existing `curated_species_photos` rows
re-keyed raw → canonical so no curated photo is orphaned and the admin "curated"
badge matches the deduped list. Collisions (several raw rows → one canonical key in a
watershed) keep the row already at the canonical key, else the most-recently-updated,
and delete the rest (one photo per canonical species). The migration inlines a frozen
copy of the canonicalization so its result is stable. Downgrade is a no-op.

✅ **UI run/form badges** (PR #76): Fish Present shows "Spring & Fall runs" etc.;
`/admin/photos` shows "one photo covers: …".

✅ **Long-tail override mechanism** (`sa30a1b2c3d4` + admin endpoints): table
`gold.species_aliases` (raw_name → canonical_label); `canonicalize()` consults it
first; Fish Present + catch-probability load + pass overrides (global, applies to
every watershed). Admin CRUD: `GET/POST/DELETE /admin/species-aliases`. Verified:
mapping "Columbia River Redband Trout" → Rainbow Trout merges it across surfaces.

Still specified (convenience, optional):

1. **In-app override management UI** — a small `/admin` surface (or affordance on
   the fish list) to add/list/remove `species_aliases` without hitting the API
   directly, plus an optional "these look like the same fish — merge?" suggestion.
   The mechanism is fully functional + admin-operable via the endpoints today.
   keys, so no curated photo is orphaned by the canonical-key switch. (Phase 1 is
   non-destructive: existing photos still resolve via the gallery/alias fallback in
   `find_photo`, but the "curated" badge can read stale until this runs.)
3. **Cross-surface parity**: apply `canonicalize` to catch-probability and
   species-spotter so all fish surfaces agree (today they keep their own alias dicts).
4. **UI run/form badges**: render `runs` as "spring & fall runs" and show `aliases`
   as "covers …" in `/admin/photos`.

## Alternatives

| Option | Verdict |
|---|---|
| Group by `scientific_name` | Rejected: unreliable (common-name strings / NULL) |
| Full GBIF/iNat taxonomy backbone | Rejected (YAGNI): heavy; subspecies + forms still need product rules |
| **Deterministic normalizer + curated override** | **Selected**: fixes ~80% automatically, global, extensible, no re-ingestion |

## Verification

- Unit: `tests/test_species_canonical.py` (chinook collapse; steelhead≠rainbow;
  case/spacing; kokanee≠sockeye).
- Integration: `/sites/johnday/fishing/species` returns one Chinook/Steelhead/Rainbow
  with `runs`/`aliases`.
- Regression: existing RiverPath suite (Fish Present rendering) stays green.
