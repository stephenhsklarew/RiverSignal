# Design Plan: Curated Aquatic-Insect Photos (extend `/admin/photos`)

**Date**: 2026-05-18
**Status**: DRAFT — pending decision on migration deploy path
**Scope**: Extend the existing fish-photo admin tool at `/admin/photos` so the same console can curate photos for the aquatic insects shown in `/path/now`'s "What Fish Are Eating Now" section. One unified admin page with a **Fish | Fish Food** type selector. Touches schema, four backend endpoints, the public `species-spotter` endpoint, and one frontend page.

---

## Problem

`/admin/photos` today curates only fish (`gold.curated_species_photos`, taxonomic group implicitly `Actinopterygii`). Its consumer `fishing_species` (`app/routers/fishing.py:18–204`) reads curated rows with this precedence: `gold.species_gallery` → curated global (`watershed='*'`) → curated watershed-specific.

The peer section on `/path/now`, "What Fish Are Eating Now" (`RiverNowPage.tsx:542–580`, backed by `species-spotter` in `app/routers/ai_features.py:327–451`), has **no curation path at all** — every insect photo is pulled live from `gold.species_gallery`, which is iNat-only and watershed-scoped via materialized view. We get no editorial control: bad iNat photos, no Wikimedia/manual overrides, no per-watershed specialisation. The fish flow already has all of that.

## Goal

A single `/admin/photos` console where the curator picks **Fish** or **Fish Food** at the top. Switching the type changes nothing about the workflow — list / iNat search / per-watershed scope / audit log all work identically. The public `species-spotter` endpoint starts honouring curated insect photos with the same precedence chain `fishing_species` uses.

## Non-goals

- Coverage of taxa beyond aquatic invertebrates that already appear in "What Fish Are Eating Now" (currently `iconic_taxon IN ('Insecta', 'Arachnida', 'Mollusca')` plus pattern-matched amphipods/worms/leeches/springtails per `ai_features.py:350–363`). No mammals, no birds.
- Backfilling iNat-source insect photos into curated rows. Curation is opt-in; uncurated species continue to use the gallery.
- A separate `/admin/insects` route. One console, one URL.

---

## Schema

**Decision**: Extend `gold.curated_species_photos` in place. Don't create a parallel `curated_insect_photos` table. Rationale: same audit table, same endpoints, same admin component, one source of truth. The cost is a small migration; the alternative duplicates ~600 lines of Python and React.

New alembic migration `<next_rev>_curated_photos_taxonomic_group.py`:

```python
def upgrade():
    op.add_column(
        "curated_species_photos",
        sa.Column("taxonomic_group", sa.String(40), nullable=True),
        schema="gold",
    )
    op.execute(
        "UPDATE gold.curated_species_photos "
        "SET taxonomic_group = 'Actinopterygii' WHERE taxonomic_group IS NULL"
    )
    op.alter_column(
        "curated_species_photos", "taxonomic_group",
        nullable=False, server_default="Actinopterygii", schema="gold",
    )
    # Replace PK so the same species_key+watershed can coexist as fish + insect
    # (rare in practice — generic common names like "yellow drake" — but
    # eliminates a class of insertion failures).
    op.drop_constraint(
        "curated_species_photos_pkey", "curated_species_photos", schema="gold",
    )
    op.create_primary_key(
        "curated_species_photos_pkey", "curated_species_photos",
        ["species_key", "watershed", "taxonomic_group"], schema="gold",
    )
    # Audit log mirrors the new dimension so history queries can filter.
    op.add_column(
        "curated_species_photos_log",
        sa.Column("taxonomic_group", sa.String(40), nullable=True),
        schema="audit",
    )
    op.execute(
        "UPDATE audit.curated_species_photos_log "
        "SET taxonomic_group = 'Actinopterygii' WHERE taxonomic_group IS NULL"
    )
```

`downgrade()` is the inverse: drop the new PK, drop columns. Safe because pre-migration data only contained fish anyway.

**Note on values**: store the iNat `iconic_taxon` string (`Actinopterygii`, `Insecta`, `Arachnida`, `Mollusca`). Keep insects as one bucket `Insecta` in the admin tool — Arachnida/Mollusca and the pattern-matched leeches/amphipods/etc. can also be curated under `Insecta` for now; if the granularity ever matters we add a second column.

---

## Backend

### `app/routers/admin.py` — five endpoints to extend

Each gains `taxonomic_group` as a query param defaulting to `Actinopterygii` (backwards-compatible — existing UI calls work unchanged).

| Endpoint | Change |
|---|---|
| `GET /admin/curated-photos` | `?taxonomic_group=` filters the list. |
| `GET /admin/curated-photos/{species_key}` | `?taxonomic_group=` selects which row to return. `global_fallback` lookup also filtered by group so we don't pre-seed a fish photo into an insect editor. |
| `PUT /admin/curated-photos/{species_key}` | Body or query param includes `taxonomic_group`. UPSERT key becomes `(species_key, watershed, taxonomic_group)`. Audit row carries it. |
| `DELETE /admin/curated-photos/{species_key}` | `?taxonomic_group=` narrows. Audit row carries it. |
| `GET /admin/curated-photos/{species_key}/history` | Optional `?taxonomic_group=` filter. |
| `GET /admin/inat/photos` | New `?taxonomic_group=Insecta` (or whatever) passes through to iNat as `iconic_taxa=Insecta`, narrowing search so "Ephemerella" doesn't return moths or unrelated lookalikes. Cache key extended to `(scientific_name, watershed, taxonomic_group)`. |

### `app/routers/ai_features.py:327` — `species-spotter` consumes curated photos

Insert a curated-photo lookup pass before the existing `gold.species_gallery` fallback. Use the same precedence chain `fishing_species` already implements:

1. `curated_species_photos WHERE watershed = :ws AND taxonomic_group IN ('Insecta','Arachnida','Mollusca')` — watershed-specific override
2. `curated_species_photos WHERE watershed = '*' AND taxonomic_group IN (...)` — global override
3. `gold.species_gallery` by genus prefix — current behaviour, unchanged

Build a `photo_map` dict identical in shape to `fishing.py:46–84`. Apply via `find_photo(common_name, scientific_name)` to each insect row before returning.

No new endpoints. No response-shape change. Frontend `RiverNowPage` renders whatever `photo_url` comes back, same as today.

---

## Frontend

### `frontend/src/pages/AdminPhotosPage.tsx`

Add a `type` parameter driven by `?type=fish|insect` (defaults to `fish`). Hold it in `useSearchParams`. Pass it everywhere the page currently makes an admin API call.

UX touches:

1. **Top of page** — a two-button pill toggle right under the page heading:
   ```
   Curating: [ 🐟 Fish ] [ 🦟 Fish Food ]
   ```
   Toggling updates the URL and re-fetches. Visual style matches the existing `species-map-cat` pill (radius 20px, active = accent).

2. **Heading text** — "Fish photos" vs "Fish food photos".

3. **Placeholders** — when type=insect, scientific_name placeholder changes from `Salmo trutta` to `Ephemerella subvaria`; common_name placeholder from `Brown Trout` to `Hendrickson`.

4. **iNat search** — `taxonomic_group` threaded into the proxy call. No UI change to the candidate grid.

5. **Add scope / Specialize for watershed dropdowns** — work unchanged; URLs they construct now carry `?type=`.

6. **History page** — `AdminPhotoHistoryPage` reads `?type=` too, passes through to the history endpoint.

### `frontend/src/main.tsx`

No route changes. The existing three routes work with the new query param.

### `frontend/src/components/AdminRoute.tsx`

No change.

---

## Migration / Deploy

**Open**: deploy path for the schema change. Three options, ranked:

1. **(Recommended)** Land the migration file in the same PR as the code change. Existing Cloud Run `migrate` job (per `terraform/cloud_run_jobs.tf`) runs it on the next deploy. Zero out-of-band schema edits.
2. Run `alembic upgrade head` locally against the prod Cloud SQL proxy as soon as the migration file lands. Tool ships immediately; risk is prod schema diverges from any in-flight feature branch until their deploy catches up.
3. Stand up a local Postgres mirror to test against. Slowest. Contradicts the current "point local at prod DB" setup unless the user wants to change that for sensitive schema work.

The PR description should include a one-line revert: `alembic downgrade -1`.

---

## Acceptance Criteria

1. `/admin/photos?type=insect` renders the same list/edit UX as `/admin/photos`, populated with curated insect rows (initially empty).
2. Saving an insect photo writes a row with `taxonomic_group='Insecta'` and a matching audit-log entry. Deleting removes it.
3. iNat search on the insect editor returns research-grade observations narrowed to `Insecta`/`Arachnida`/`Mollusca` and the configured watershed bbox.
4. After saving a curated insect photo for watershed X, `/path/now/X`'s "What Fish Are Eating Now" card for that species shows the curated photo within one SWR cycle (or hard refresh — same caveat the fish flow already documents).
5. Existing `/admin/photos` flow (no `?type=` or `?type=fish`) is bit-for-bit unchanged.
6. `alembic downgrade -1` cleanly reverses the migration; `gold.curated_species_photos` returns to its previous PK and column set, and existing fish rows are preserved.

---

## Risks

- **Schema migration on prod**: ALTER TABLE + UPDATE on a small table (current row count is dozens). Low blast radius but not zero — pre-deploy backup is the existing nightly Cloud SQL backup; no extra mitigation needed.
- **PK collision on downgrade**: if any insect rows exist at the time of downgrade, the migration must refuse (or delete-then-downgrade). The downgrade should `DELETE FROM gold.curated_species_photos WHERE taxonomic_group <> 'Actinopterygii'` first, with an explicit log line.
- **`species-spotter` regression**: the new curated lookup pass adds 1-2 SQL queries on every call. The endpoint already executes 4 source queries; adding two more is acceptable but should be measured. Add to the post-deploy smoke check.

---

## Out of scope / follow-ups

- Bulk import of curated insect photos (e.g., from a Wikimedia hatch chart). Today's curator adds one at a time; bulk is a future plan.
- A "missing photos" report listing insects in `gold.species_gallery` that have no curated row and no acceptable iNat fallback.
- Same model for amphibians, reptiles, mammals on the (currently nonexistent) "What's Alive Right Now" surface — same migration, just more `taxonomic_group` values.
