# Design Plan: Trip Plans & Share-Saved-Items

**Date**: 2026-05-10
**Status**: CONVERGED (post-collaborative-review)
**Refinement Rounds**: 4 + 8 collaborative forks resolved with product owner
**Scope**: Two new features on the Saved screen for `/path` and `/trail`:
1. **Share Saved Items** — generate a read-only link recipients can open without an account, including selectively shared private observations.
2. **Trip Plan Generation** — given a date range and an item subset (or interests for discovery mode), produce a saved AAA-TripTik-style itinerary (directions, lodging, daily plan); trip plans are themselves saveable and shareable.

## Collaborative Review Outcomes (2026-05-10)

Eight forks worked through with the product owner, resolving the highest-leverage open questions in the original draft:

| Fork | Decision | Key implication |
|---|---|---|
| 1. Form factor | In-app dashboard first; print stylesheet Phase 3 | Structured `TripPlan` JSON drives both presentations |
| 2. Lodging | Use existing `recreation_sites` (campgrounds, RV parks, cabins) only | **No new `lodging_options` table.** Hotels/motels deferred. AD-7 collapses; one risk class removed |
| 3. Privacy | Private obs included in shares get full precision | **No fuzzed-coord code path.** AD-8 simplifies; one less branch in snapshot serializer |
| 4. Discovery | Wizard accepts saved items OR empty start with interests + watersheds | New `propose_candidate_items` backend function; ~2 days extra work |
| 5. Generation | Async via FastAPI BackgroundTasks; client polls | **New `status` column on `trip_plans`**; "navigate away" UX works naturally |
| 6. Recipients | View-only; no save-a-copy in MVP | No new `shared_observation` saved type; trims plan from 14 → 12 issues |
| 7. Watershed default | Current watershed only; "+ Add" for others | Wizard step shows active watershed pre-selected, others as opt-in chips |
| 8. /path vs /trail | Same model, product-aware defaults | Single `product` field drives wizard defaults, interest catalog, prompt tone |

## Problem Statement

RiverPath and DeepTrail already let users bookmark reaches, species, fly patterns, recreation sites, restoration projects, fossils, minerals, rock sites, and (for /path users) their own observations. Today a user's "trip" lives in their head — they have a Saved tab with disconnected items, and no way to:

- Hand the list to a friend ("here's what we're hitting next weekend") without screenshots or copy/paste.
- Show others their private observations in a controlled way (private observations are intentionally hidden from public maps; today the only way to "show" one is to make it public, which loses the privacy boundary forever).
- Convert the list into something operationally useful — a sequenced itinerary with drive times, lodging that fits the route, "park here, walk this trail, rocks are 200m off the loop" detail.

Two user personas pull this hard:

- **Trip-planning angler/family** (RiverPath): "We're doing 4 days on the Deschutes Aug 8–11, two adults two kids, here's our saved fly shops and access points. Can the app produce a printable plan with motels, campgrounds, and a rough day-by-day?"
- **Rock/fossil collector** (DeepTrail): "I've got 12 rockhounding sites saved across 3 counties. I want a 3-day route, where to stay, and to share the plan with my collecting partner."

Today: neither happens in-app.

Desired outcome: the Saved screen grows two affordances — a Share button that mints a link, and a "Plan a Trip" button that opens a date+selection sheet and produces a structured, persisted, shareable plan.

## Requirements

### Functional

#### F1. Share Saved Items
1. From `/path/saved` and `/trail/saved`, user can tap a "Share" action that opens a sheet listing every saved item, defaulting to all selected.
2. User toggles which items to include (multiselect with "All" / "None" shortcuts).
3. For observations marked `visibility='private'`, the share sheet shows a clear visual indicator and a per-item confirmation that they will be visible to anyone with the link.
4. Tapping "Create Share Link" calls `POST /api/v1/shares` and returns a short URL like `https://riversignal.app/s/AbCd1234` (8-char URL-safe slug).
5. Anyone opening the URL — without authentication — sees a read-only `SharedView` page with the included items, presented in the same visual language as Saved (cards, photos, coordinates, map).
6. The share URL is the **only** way to view the shared private observations; they remain `visibility='private'` and are still excluded from public observation queries (search, map, leaderboards).
7. The share owner (creator) can revoke the link from `/path/saved/shares` (a new sub-page); revoking returns 410 Gone for subsequent visits.
8. Shares default to no expiration, but creator can set 24h, 7d, 30d, or "never" at creation.
9. Each share has a viewer counter (visible only to creator) so they can see if it's been opened.
10. Trip Plans (FR F2) are first-class share targets — selecting a saved trip plan automatically also includes its referenced items.
11. Recipients can save a *copy* of the share to their own Saved list if they're authenticated; this clones the item references but does not transfer ownership of private observations (those remain view-only inside the share).

#### F2. Trip Plan Generation
1. From `/path/saved` and `/trail/saved`, user can tap "Plan a Trip" to open a multi-step sheet:
   - Step 1: date range (start, end) — required.
   - Step 2: item selection — defaults to all saved items in the current watershed; user can deselect or add items from other watersheds the user has saved.
   - Step 3: trip preferences — number of travelers (default 2), lodging style (`camping`, `lodge`, `mixed`, `none`), vehicle type (`car`, `4wd`, `rv`), pace (`relaxed`, `balanced`, `intense`).
2. Tapping "Generate" calls `POST /api/v1/trip-plans` (async) and shows a loading state with progress chips.
3. Generation produces a structured trip plan with:
   - **Header**: title (auto-generated, editable post-hoc), date range, participants, overview paragraph.
   - **Daily itinerary**: for each calendar day inside the range, an ordered list of stops with start time estimate, drive time from previous stop, "what's here" narrative, photo (if any from the saved item), and parking/access notes if available.
   - **Routing**: for each transition between stops, a polyline + summary (total miles, drive time, primary route).
   - **Lodging recommendations**: 1–3 suggestions per overnight, drawn from a new `lodging_options` table seeded with curated regional listings (similar to existing `fly_shops_guides`, `mineral_shops`).
   - **Conditions & gear**: per-day weather forecast (NWS), water/flow conditions for any river stops (USGS), recommended fly patterns / collecting gear for the season.
   - **Provenance footer**: data sources used + a "Trip plan generated by AI; verify reservations and access rules before traveling" disclaimer.
4. The generated plan is saved as a `SavedItem` with `type='trip_plan'`, persisted in the new server-side `trip_plans` table (because plans contain too much data for localStorage and need to be shareable across devices and users).
5. Trip plan detail view at `/path/trip/{slug}` and `/trail/trip/{slug}` renders the structured plan.
6. Plan can be re-generated (regenerates content, keeps the same id and slug) and edited (title only, MVP).
7. Plans can be shared via FR F1 — selecting a plan in the Share sheet auto-includes all items the plan references (including private observations).

#### Cross-cutting
8. Both features show a clear "Sign in to share / plan trips" interstitial when user is not authenticated.
9. Both features are surfaced in `/path/saved` and `/trail/saved` with consistent UI; the share/plan output adapts to the calling product (different chrome and accent color but identical underlying data model).

### Non-Functional

- **Latency**: trip plan generation must complete within 60 s for plans up to 10 stops over 7 days. Share creation must complete within 1 s.
- **Privacy**: shared private observations leak only to viewers of the specific share URL. No enumeration vector. No reverse lookup from observation id back to share without the share id.
- **Durability**: shares and trip plans persist indefinitely until explicitly revoked or for the configured TTL. Database-backed, included in standard backups.
- **Cost**: trip plan generation involves one Anthropic call (~10–25k input tokens, ~5–8k output tokens). Cap one in-progress plan per user; cap 10 plans per user per day to prevent abuse.
- **Accessibility**: share view and trip plan page render correctly on mobile portrait at 360 px wide; print stylesheet for trip plans (the "AAA TripTik" framing implies users will print or PDF).

### Constraints

- Backend: FastAPI + PostgreSQL + SQLAlchemy already in place. Do not introduce a new datastore.
- Frontend: React + Vite + react-router-dom + SWR. No new global libraries beyond what's installed.
- Auth: existing cookie-based auth for owner-restricted endpoints. Anonymous access for share URLs only.
- AI: Anthropic API already wired (`anthropic-api-key` in Secret Manager). Reuse the same client and connection-reuse pattern as `river-story` and `time-machine`.
- Routing: avoid Google Directions (license cost). Use **OSRM** public server for MVP (`https://router.project-osrm.org`), with a stubbed adapter so we can swap to a paid provider later.
- Lodging: no scraping. Curated `lodging_options` table seeded by a one-off CSV import; admin script to expand. Initial coverage: the 7 supported watersheds (Pacific NW + Green River basin).

## Architecture Decisions

### AD-1: Share storage model — denormalized snapshot vs. live references

- **Question**: When a user shares saved items, should the share record store a snapshot of the items as they were at share time, or live references that re-resolve every view?
- **Alternatives**:
  - **A1: Snapshot** — share row contains the full item payload as JSONB at creation time. Recipients see what was shared even if the source item changes.
    - Pros: viewer experience is stable; private observations don't accidentally leak deletion-recovered data; simpler authorization (no per-item check at view time); recipient can save a copy that's an exact archive.
    - Cons: source-of-truth drift (if the user updates an observation photo, the share keeps the old one); duplicate storage.
  - **A2: Live references** — share row stores `[{type, id}, ...]` and view re-fetches each item on access.
    - Pros: edits flow through; less storage.
    - Cons: per-view N+1 reads; deleted items become 404s mid-share; private observation visibility check has to special-case the share context (who is allowed to see this private obs? answer: anyone holding *this share id*).
  - **A3: Hybrid** — references for owner-mutable items (their own observations) + snapshot for everything else.
    - Pros: edit flow-through where it matters most; performance OK.
    - Cons: complex authorization, two code paths for view rendering.
- **Chosen**: **A1 — snapshot**.
- **Rationale**: Trip Plans are themselves snapshots (a generated artifact frozen at creation time), so consistency suggests every share is a snapshot. Per-item authorization for private observations becomes a pure presence check ("is this id in the snapshot?"), eliminating an entire class of access-control bugs. Storage cost is trivial — even a 50-item share with photo URLs is well under 100 KB. Recipient copy-to-saved becomes trivial: snapshot is the copy.

### AD-2: Saved-items persistence — keep localStorage or migrate to API

- **Question**: Currently non-observation saved items live in localStorage (`SavedContext`). To share/plan them we need server access. Migrate everything?
- **Alternatives**:
  - **B1: Full migration** — every saved-item type moves to a `user_saved_items` table; localStorage becomes a write-through cache.
    - Pros: cross-device sync (a long-standing limitation called out in FEAT-016); single source of truth; trivial server-side share/plan flows.
    - Cons: migration of existing localStorage data; auth-required for every save action (today, anonymous users can save things and it works because it's local).
  - **B2: On-demand server materialization** — keep localStorage; when user shares or plans, serialize the local items into the server payload at that moment.
    - Pros: minimal change; anonymous users keep working as today.
    - Cons: share creation request body is large; "share my whole list" implies the client knows the whole list (it does, via localStorage); cross-device shares from a different device than where items were saved silently miss items.
  - **B3: Lazy migration** — write to server when authenticated; fall back to localStorage when not.
    - Pros: graceful for anonymous users; ports user data on first login.
    - Cons: dual code path lasts forever; merge conflicts when same email logs in across devices that each have local items.
- **Chosen**: **B2 for MVP**, with a flag to revisit B1 in a follow-up.
- **Rationale**: Migrating the saved-items model is its own significant change (FEAT-016 already accepted localStorage; cross-device sync is a separate request). For sharing/planning, the client always has the data we need at the moment of action, so the lift to send it server-side is minimal. We track a `saved_items_payload` JSONB in `share` and `trip_plan` rows. Defer B1 to a future cycle when cross-device sync is independently prioritized.

### AD-3: Trip plan generation — single LLM call vs. orchestrated pipeline

- **Question**: Is the plan one big Anthropic prompt that gets the whole result, or a multi-step process (cluster items by day → fetch routes → fetch lodging → compose)?
- **Alternatives**:
  - **C1: Single prompt** — feed the LLM all saved items, dates, prefs; get JSON back with the whole plan.
    - Pros: simplest code; LLM does the day-clustering and ordering naturally.
    - Cons: LLM hallucinates lodging that doesn't exist; LLM-generated routes have no real driving distances; plan quality depends entirely on prompt engineering.
  - **C2: Orchestrated** — Python clusters items by geographic proximity into days; OSRM computes drive times; SQL query selects lodging from `lodging_options` near each overnight; LLM only writes the narrative prose given the structured input.
    - Pros: no hallucinated lodging or routes; deterministic geographic clustering; LLM is doing what it's good at (writing naturally about real items).
    - Cons: more moving parts; needs a clustering algorithm.
  - **C3: Two-step** — Python pre-computes routes/lodging; LLM clusters and narrates given the structured menu.
    - Pros: middle ground; LLM still does sequencing.
    - Cons: clustering by LLM is non-deterministic and can be poor with many items.
- **Chosen**: **C2**.
- **Rationale**: The "AAA TripTik" framing demands accurate driving directions and real lodging. C1 is a non-starter for production credibility — users would catch invented motels immediately. C2 keeps Anthropic in its sweet spot (prose narration over structured input) and puts authoritative data (OSRM, curated lodging) in the deterministic path. Clustering is a 50-line k-means-by-day variant; not novel.

### AD-4: Routing provider

- **Question**: How to compute drive times and polylines between stops?
- **Alternatives**:
  - **D1: OSRM public server** — free, OpenStreetMap-based, hosted at `router.project-osrm.org`.
    - Pros: free; sufficient quality; no API key.
    - Cons: rate-limited (1 rps practical); no SLA; usage policy says "limited testing" not "production".
  - **D2: Self-hosted OSRM** — Cloud Run instance with prepared OSM extracts.
    - Pros: no rate limits; under our control.
    - Cons: ~25 GB region extracts to host; ops burden.
  - **D3: Mapbox Directions API** — free tier 100k req/mo, then paid.
    - Pros: production-grade SLA; great quality.
    - Cons: cost at scale; API key + rate-limit infrastructure.
  - **D4: Google Directions API** — paid, great quality.
    - Pros: best-in-class.
    - Cons: $5/1k requests, license restrictions on caching.
- **Chosen**: **D1 for MVP behind a `RoutingProvider` interface**, with **D3 (Mapbox) as the documented next step** when usage exceeds OSRM's polite-use bound.
- **Rationale**: A trip plan with 8 stops is 7 routing requests, cached on the trip-plan row. At 10 plans/user/day cap and ~100 active users, that's ~7000 requests/day on initial generation only — well within OSRM's tolerance and trivially within Mapbox's free tier. Wrapping in an interface lets us swap without touching call sites.

### AD-5: Trip plan storage shape

- **Question**: How structured is the persisted trip plan?
- **Alternatives**:
  - **E1: Free-form markdown** — store the LLM output as a string.
    - Pros: simplest; render with `Markdown` component (already used for river stories).
    - Cons: not addressable (can't link to "day 3"); regeneration replaces the whole document; no analytics on which stops were included.
  - **E2: Structured JSON** — store the plan as a typed object with days, stops, routes, lodging.
    - Pros: addressable, partially regenerable, analyzable; renderer can mix prose and structured widgets (a real map polyline next to the day's narrative).
    - Cons: schema work upfront.
- **Chosen**: **E2**.
- **Rationale**: AAA TripTik is inherently structured. Mixing real polylines (we have routing data) with prose narration is the differentiator vs. a wall of LLM text. JSONB storage in Postgres gives us flexibility with no migration cost per shape change.

### AD-6: Anonymous share viewing — auth model

- **Question**: How are share URLs authorized?
- **Alternatives**:
  - **F1: Bearer token in URL** — slug is a 64-bit random token; possession of slug = read access.
    - Pros: simple; standard pattern (Google Docs share-by-link, Dropbox).
    - Cons: leaks via referer headers and chat link previews.
  - **F2: Slug + secret** — short slug for the URL plus a `?k=` secret in the query for verification.
    - Pros: defense against guessing.
    - Cons: same leak vectors; UX worse.
  - **F3: Owner-listed allowlist** — share only viewable by listed email addresses, magic-link verified.
    - Pros: stronger authentication.
    - Cons: high friction; "show my friend my saved spots" demands frictionless paste-link.
- **Chosen**: **F1 with 8-char URL-safe slug from a 48-bit random source** (≥4 × 10¹⁴ search space; cryptographically random; not guessable in any reasonable timeframe).
- **Rationale**: This is "share with people I trust by giving them a link" — same pattern as Google Docs share-by-link. The privacy story remains: no public enumeration; revocation supported; shares are stable URLs. Add `referrer-policy: no-referrer` and `<meta name="robots" content="noindex">` to the share view to mitigate referer/indexing leaks.

### AD-7: Lodging data source (REVISED 2026-05-10)

- **Question**: Where do lodging recommendations come from?
- **Resolution (Fork 2 collaborative review)**: **No new lodging table or external API for MVP.** Lodging suggestions are sourced *exclusively* from the existing `recreation_sites` table, filtered to lodging-relevant `rec_type` values (`campground`, `rv_park`, `cabin`).
- **Implication**:
  - The `LodgingOption` type contract stays as a *projection* over `recreation_sites` — same shape, different source.
  - Wizard's lodging style choices simplify to `camping`, `mixed`, `none` (drop `lodge` until that data lands).
  - When a user picks `mixed`, the orchestrator picks campgrounds anyway and the prose acknowledges the gap: *"We don't yet have curated motel/lodge data for this watershed. For non-camping options, see [Booking.com search for {town}]."*
- **Future work**: a curated table for lodges/motels/B&Bs is a clean follow-up when there's product evidence users want it. Not blocking MVP.

### AD-8: How are private observations included in shares without leaking? (REVISED 2026-05-10)

- **Question**: A user can share a list that includes their own private observations. How does the snapshot keep them private to non-shared contexts?
- **Resolution (Fork 3 collaborative review)**: Private observations stay hidden from the public app, but when explicitly included in a share, the recipient sees them with **full precision**. The act of selecting a private observation in the share sheet *is* the consent — no per-share coordinate toggle, no fuzzing.
- **Mechanism**:
  1. The `shares` row stores a denormalized payload of items (AD-1). For private observations included in the share, the snapshot contains the full item record exactly as the owner sees it.
  2. The original `user_observations` row remains `visibility='private'`. Existing `GET /observations/user` queries continue to filter by user_id and exclude private observations from anyone else's queries.
  3. The share view endpoint reads only from the snapshot in the `shares` row. It never queries `user_observations` to render. So a recipient cannot enumerate a user's *other* private observations — they only see what was put into the snapshot.
  4. **UX requirement**: each item row in the share sheet shows a 🔒 chip if it's a private observation. The share creation summary states: *"This share includes 2 private observations only visible to people with this link."* No coordinate toggle.
- **Rationale**: User confirmed the priority is "keep private observations out of the public app," not "obfuscate within explicit shares." Selecting a private obs in the share sheet is an explicit choice with implicit consent to share its coordinates. The snapshot-only render path remains the primary defense — recipients cannot enumerate beyond what was packaged.

## Interface Contracts

### REST endpoints

#### Share

- `POST /api/v1/shares` — create a share. **Auth required.**
  - Body: `{ items: SavedItem[], trip_plan_id?: uuid, expires_at?: iso8601 | null, include_private_obs_coords: boolean, title?: string }`
  - Response: `{ id: uuid, slug: string, url: string, created_at, expires_at, view_count }`
  - Errors: 401 unauthorized; 429 if user has >50 active shares; 413 if items payload >1 MB.
- `GET /api/v1/shares/{slug}` — fetch a share for rendering. **No auth required.**
  - Response: `{ slug, title, owner_display_name, created_at, expires_at, items: SavedItem[], trip_plan?: TripPlan, view_count: never_returned }`
  - Errors: 404 if not found; 410 if revoked or expired.
  - Side effect: increments `view_count` on the share (deduped by IP+UA cookie hash for 1h to avoid refresh inflation).
- `GET /api/v1/shares` — list current user's shares. **Auth required.**
- `DELETE /api/v1/shares/{id}` — revoke a share. **Auth required, owner only.**

#### Trip Plan

- `POST /api/v1/trip-plans` — generate a plan. **Auth required.** Synchronous; expected ~30–60s.
  - Body: `{ start_date, end_date, items: SavedItem[], travelers: int, lodging_style: enum, vehicle_type: enum, pace: enum, watersheds: string[] }`
  - Response: `{ id: uuid, slug, title, plan: TripPlan }`
  - Errors: 401; 422 invalid dates (end<start, range >14 days); 429 daily limit; 503 if Anthropic unavailable.
- `GET /api/v1/trip-plans` — list user's plans.
- `GET /api/v1/trip-plans/{id_or_slug}` — fetch a plan. Auth required for owner; otherwise 404 (sharing is via `/shares`, not direct).
- `DELETE /api/v1/trip-plans/{id}` — delete a plan.
- `POST /api/v1/trip-plans/{id}/regenerate` — re-run generation with same inputs.
- `PATCH /api/v1/trip-plans/{id}` — title only for MVP.

### Frontend routes

- `/path/saved/share/{slug}` and `/trail/saved/share/{slug}` — branded share view (chrome adapts).
- `/s/{slug}` — short share URL (redirects to product-branded view based on a `product` field stored on the share row, defaulting to RiverPath).
- `/path/saved/shares` — list of user's outgoing shares with revoke controls.
- `/path/trip/{slug}` and `/trail/trip/{slug}` — trip plan detail view (owner-authenticated).

### Type contracts (TypeScript / Pydantic)

```ts
type SharedItem = SavedItem & {
  // For private observations in a snapshot, all fields are present but
  // coordinates may be fuzzed (latitude/longitude rounded to 0.01° = ~0.7 mi)
  // when the share was created with include_private_obs_coords=false.
  fuzzed_coords?: boolean
}

type TripPlan = {
  id: string; slug: string; title: string; overview: string
  start_date: string; end_date: string
  travelers: number; lodging_style: 'camping'|'lodge'|'mixed'|'none'
  vehicle_type: 'car'|'4wd'|'rv'; pace: 'relaxed'|'balanced'|'intense'
  days: TripDay[]
  generated_at: string; generation_model: string  // for provenance
}

type TripDay = {
  date: string; title: string; narrative: string
  stops: TripStop[]
  overnight?: LodgingOption  // null on last day if none needed
  weather?: { high_f: number; low_f: number; conditions: string }
  total_drive_minutes: number; total_drive_miles: number
}

type TripStop = {
  saved_item: SavedItem  // the source bookmark
  arrive_estimate?: string  // HH:MM
  duration_minutes: number
  parking_notes?: string
  route_from_previous?: { polyline: string; minutes: number; miles: number; summary: string }
  conditions?: { water_temp_c?: number; flow_cfs?: number; hatch?: string }
}

type LodgingOption = {
  id: string; name: string; type: 'campground'|'lodge'|'motel'|'inn'|'rv_park'|'cabin'
  latitude: number; longitude: number; address: string
  reservation_url?: string; phone?: string; price_band: '$'|'$$'|'$$$'
  notes: string  // curated, e.g. "Walk-in tent sites; first-come first-served"
  last_verified: string  // YYYY-MM-DD
}
```

### Anthropic prompt contract (trip plan narrator)

Single `messages.create` call, prompt-cached (system + tool-context cached for the day).

- **System** (cacheable): role, AAA-TripTik framing, output JSON schema, hallucination guardrails ("you must not invent lodging or routing; use only the provided lodging_menu and routes"), tone calibration ("conversational, mildly enthusiastic, never marketing-speak").
- **User**: structured JSON containing pre-clustered days, OSRM routes, lodging menu, weather forecasts, watershed context paragraphs, user prefs.
- **Output**: `TripPlan` JSON; we parse and validate against pydantic; on parse failure, retry once with stricter "respond with valid JSON only" preamble; on second failure, return 503 to the caller with a "regenerate" affordance.

## Data Model

### New tables

```sql
CREATE TABLE shares (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug          VARCHAR(16) UNIQUE NOT NULL,           -- 8-char URL-safe; index key
    owner_user_id UUID NOT NULL REFERENCES users(id),
    title         TEXT,
    items         JSONB NOT NULL,                        -- SavedItem[] snapshot
    trip_plan_id  UUID REFERENCES trip_plans(id),        -- optional, when share is a trip plan
    product       VARCHAR(8) NOT NULL,                   -- 'path' | 'trail' (controls render chrome)
    expires_at    TIMESTAMPTZ,                           -- NULL = no expiration
    revoked_at    TIMESTAMPTZ,                           -- NULL = active
    view_count    INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_shares_owner ON shares(owner_user_id, created_at DESC);
CREATE INDEX ix_shares_slug_active ON shares(slug) WHERE revoked_at IS NULL;

CREATE TABLE trip_plans (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug          VARCHAR(16) UNIQUE NOT NULL,
    owner_user_id UUID NOT NULL REFERENCES users(id),
    title         TEXT NOT NULL,
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    -- Async generation status (Fork 5: BackgroundTasks)
    status        VARCHAR(16) NOT NULL DEFAULT 'pending', -- pending|generating|completed|failed
    progress_step VARCHAR(32),                            -- e.g. 'clustering', 'routing', 'narrating'
    error_reason  TEXT,
    plan          JSONB,                                  -- TripPlan structured object; null until completed
    inputs        JSONB NOT NULL,                         -- preserved generation inputs for regenerate
    generation_model VARCHAR(64),
    generation_tokens INTEGER,                            -- for cost telemetry
    product       VARCHAR(8) NOT NULL,                    -- 'path' | 'trail' (Fork 8)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_trip_plans_owner ON trip_plans(owner_user_id, created_at DESC);
-- Enforce one-in-flight per user (Fork 5):
CREATE UNIQUE INDEX ix_trip_plans_one_inflight
    ON trip_plans(owner_user_id) WHERE status IN ('pending', 'generating');

-- NOTE: lodging_options table dropped from MVP per Fork 2.
-- Lodging recommendations sourced from existing recreation_sites
-- table filtered to rec_type IN ('campground', 'rv_park', 'cabin').
```

### Migration strategy

1. Alembic migration `e5f6a7b8c9d0_add_share_trip_lodging.py` creates all three tables.
2. One-off seed script `pipeline/seed_lodging.py` reads `seed/lodging_seed.csv` (one-time research pass, included in repo) and bulk-inserts entries.
3. No existing-data migration needed (greenfield tables).

### Backwards compatibility

Existing `SavedContext` localStorage shape unchanged. Adding a new `type='trip_plan'` to `SavedItem.type` is additive; older clients ignore it.

## Error Handling

| Class | Examples | Strategy |
|---|---|---|
| User input invalid | dates reversed, range too long, items missing | 422 with field-level message; frontend keeps the sheet open and highlights field |
| External API outage | OSRM down, NWS down, Anthropic 5xx | OSRM: degrade to straight-line distance + heuristic time; NWS: omit weather block; Anthropic: 503 with retry-after; UI offers "try again" |
| Rate limits | user exceeds 10 plans/day, 50 active shares | 429 with reset-time |
| Hallucination / invalid LLM output | malformed JSON, references unknown lodging | retry once; on second fail return 503; do not persist garbage |
| Share access | revoked, expired, never existed | 410 vs. 404; both render "this share isn't available" with a link to RiverPath |
| Private-obs leak prevention | snapshot tampering | snapshot is hash-stamped at creation; if someone DB-edits a snapshot, hash mismatch triggers 410 (defense in depth) |

## Security

- **Slug entropy**: 48-bit random; ≥10¹⁴ search space. Rate-limit share-fetch endpoint to 60 req/min per IP to prevent brute-force enumeration.
- **No-index, no-referer**: share view sets `<meta name="robots" content="noindex,nofollow">` and `Referrer-Policy: no-referrer`.
- **CSRF**: share/plan creation use existing session cookie; FastAPI same-site=lax cookie + `Origin` check (already present for observation endpoints).
- **PII in shares**: owner_display_name shown to recipients; user can opt to display a custom name per share (defaults to display_name).
- **Private observation coordinates**: default to fuzzed (rounded to 0.01°). Explicit opt-in per share for exact coords. Document in the share creation sheet with copy: "Exact GPS visible to anyone with the link — only enable for trusted recipients."
- **Trip plan PII**: trip plan stores no personal info beyond user_id; the rendered plan does not include user name or contact info unless explicitly added to the title.
- **Anthropic input sanitization**: user-provided title and item labels go into the prompt; we strip `\n\n----` style prompt-injection markers and apply a 200-char length cap per field.
- **OSRM URL crafting**: coords clamped to ±90/±180; query escaped via `httpx.params=`.
- **Reservation URLs**: stored as-given in `lodging_options`. Render with `rel="noopener noreferrer"` to prevent `window.opener` leaks.

## Test Strategy

### Unit
- `frontend/src/components/ShareSheet.tsx`: item selection, "all/none" toggles, private-obs warning visibility.
- `frontend/src/components/TripPlanWizard.tsx`: date validation, item de/select.
- `app.routers.shares.create_share`: snapshot integrity, hash stamping, item filtering.
- `app.routers.trip_plans.cluster_days`: k-means-by-day with 1, 5, 50 stops; 1-day, 7-day, 14-day ranges; pathological (all stops at same coords) doesn't crash.
- `app.lib.routing.osrm_route`: response parsing, error fallback to straight-line.
- `app.lib.lodging.suggest_overnight`: spatial query around a point with price-band and type filters.

### Integration
- End-to-end share creation → fetch by slug → revoke → 410.
- End-to-end trip plan generation with stubbed OSRM and stubbed Anthropic.
- Private observation in share is rendered with fuzzed coords by default; with exact coords when opt-in flag is set.
- Share with trip plan auto-includes the plan's referenced items.
- Recipient "save copy" creates SavedItems with type='shared_observation' that don't grant write access to original.

### E2E (Playwright)
- User saves 5 items → opens share sheet → creates share → opens link in incognito → sees content.
- User generates a 3-day trip plan → opens it → the route polyline is visible on day-2 map.

## Implementation Plan

### Dependency graph

```
Phase 0 (foundation, parallelizable)
├── Migration: shares, trip_plans, lodging_options tables
├── Lodging seed CSV (~350 entries) + import script
└── RoutingProvider interface + OSRM adapter

Phase 1 (share, no plans)
├── POST/GET/DELETE /shares endpoints
├── ShareSheet UI on /path/saved and /trail/saved
├── /s/{slug} short-link route + branded share view
└── /path/saved/shares management page

Phase 2 (trip plan generation)
├── Day clustering algorithm + tests
├── Anthropic prompt + JSON schema validator
├── POST /trip-plans endpoint (orchestrates clustering, OSRM, lodging, LLM)
├── TripPlanWizard UI
└── /path/trip/{slug} and /trail/trip/{slug} renderers

Phase 3 (integration)
├── Trip plans appear in Saved with type='trip_plan'
├── Share sheet recognizes trip-plan items and auto-includes referenced items
├── Saved-copy from share for recipients
└── Print stylesheet for trip plan
```

Each phase is independently shippable; Phase 1 ships before Phase 2 if Phase 2 hits scope risk.

### Issue breakdown (suggested HELIX issues, post-collaborative review)

1. **HELIX-#1** Migration & schema: `shares` + `trip_plans` tables (no `lodging_options`). AC: alembic upgrade head succeeds; one-inflight constraint on trip_plans verified.
2. **HELIX-#2** Routing provider abstraction + OSRM adapter. AC: `RoutingProvider.route([(lat,lon),...])` returns polyline + miles + minutes for known waypoints; falls back gracefully on 5xx; per-(origin,dest) cache.
3. **HELIX-#3** Share API endpoints (create / get / list / revoke). AC: integration tests pass; private observations included in snapshot are rendered with full precision; share view never queries `user_observations`.
4. **HELIX-#4** ShareSheet component + buttons on /path/saved and /trail/saved. AC: user can mint a share including private observations; 🔒 chip visible on private items in the sheet; summary text counts private items.
5. **HELIX-#5** Branded share view at `/s/{slug}`. AC: anonymous user can open link; sees items; map renders observations and recreation sites; expired/revoked shows 410 page; `<meta name="robots" content="noindex">` and `Referrer-Policy: no-referrer` set.
6. **HELIX-#6** Outgoing-shares management page at `/path/saved/shares`. AC: list view with revoke action; viewer count visible to owner.
7. **HELIX-#7** Day clustering algorithm + candidate-item proposer. AC: unit tests cover 1/5/50 items × 1/7/14-day ranges; `propose_candidate_items(watersheds, interests, dates)` returns geographically distributed stops; degenerate inputs handled.
8. **HELIX-#8** Trip plan generation orchestrator (async via BackgroundTasks). AC: status transitions `pending → generating → completed|failed` recorded; one-inflight constraint enforced; with stubbed Anthropic, produces valid `TripPlan` JSON; status row updated at each progress_step.
9. **HELIX-#9** TripPlanWizard UI — accepts saved items OR empty start with required interests + watersheds + dates (Fork 4c). AC: per-product defaults applied (Fork 8b); current watershed pre-selected with "+ Add" affordances for others (Fork 7a); submit fires `POST /trip-plans` and navigates immediately to `/path/trip/{slug}` for polling.
10. **HELIX-#10** Trip plan detail view at `/path/trip/{slug}` and `/trail/trip/{slug}`. AC: renders progress UI when status≠completed; renders header, daily breakdown, embedded route polylines on a static map per day, lodging cards (campground-only), weather chips, provenance footer when complete; product chrome adapts (Fork 8b).
11. **HELIX-#11** Trip plan as saved item / share target. AC: trip plans appear in Saved with type='trip_plan'; sharing a trip plan auto-includes referenced saved items.
12. **HELIX-#12** Print stylesheet for trip plans (Phase 3 polish, Fork 1c). AC: "Print" button on plan view produces print-ready output; cover page + day pages + lodging contacts.

**Phase scoping:**
- **Phase 0** (foundation, parallelizable): #1, #2, #7-clustering-algorithm.
- **Phase 1** (share, ships independently): #3, #4, #5, #6.
- **Phase 2** (trip plan generation): #7-proposer, #8, #9, #10.
- **Phase 3** (integration & polish): #11, #12.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Anthropic JSON output malformed → plan generation fails | M | M | Retry once with stricter system prompt; on second fail, return 503 with regenerate option; never persist garbage |
| OSRM rate limits hit → routes degraded | M | L | Cache per (origin, dest) for 30 days; switchable provider interface; document Mapbox path; keep-alive client connections |
| Lodging entries go stale (closed, renamed) | H over months | M | `last_verified` shown on each card; quarterly re-verification job; "report wrong" link mailto to ops |
| Private observation coords leak via share | L | H | Default fuzzed; explicit opt-in with copy warning; snapshot-only render path means no live join can leak; pen-test the share endpoint |
| Slug guessing | L | M | 48-bit entropy; rate-limit fetch to 60/min/IP; revocation supported |
| User generates 100+ plans by accident | M | L (cost) | Daily cap 10; one in-flight per user; monitor token spend per user weekly |
| LLM hallucinates lodging despite prompt | L | M | Lodging menu provided in prompt; output validation rejects any lodging name not in `lodging_options`; on rejection, regenerate |
| Trip plan inputs leak prompt injection | L | M | Sanitize titles/labels before prompting; system prompt instructs LLM to ignore "instructions" inside item labels |
| Share viewer count incremented by bots / refresh loops | M | L | Dedup by IP+UA cookie hash for 1 hour |
| Recipient "save copy" creates infinite chain | L | L | Disallow re-sharing of `type='shared_observation'`; copy depth tracked |

## Observability

- **Metrics** (PostHog event taxonomy):
  - `share.created` (item_count, includes_private_obs, has_trip_plan, ttl)
  - `share.viewed` (slug_hash, is_owner)
  - `share.revoked` (age_seconds_at_revoke)
  - `trip_plan.requested` (item_count, days, lodging_style, pace)
  - `trip_plan.generated` (latency_ms, tokens_used, cost_estimate)
  - `trip_plan.failed` (reason: anthropic_5xx | parse_fail | timeout)
  - `trip_plan.viewed`
  - `trip_plan.printed`
- **Logging**: structured JSON logs at INFO for share/plan creation; ERROR for LLM/OSRM/NWS failures with retry path.
- **Alerts**: Cloud Monitoring alert when `trip_plan.failed` rate exceeds 20% over 1 hour.
- **Cost tracking**: weekly Cloud Run report aggregates `generation_tokens` from `trip_plans` table; alert if 7-day cost exceeds $10.

## Open Questions

1. **Branded short URL**. Use `https://riversignal.app/s/{slug}` (current api domain) vs. a vanity domain? Decision deferred — sticking with current domain to avoid DNS/cert work.
2. **Email delivery of share links**? Out of scope for MVP. User copies the link manually.
3. **iCal export of trip plan?** Out of scope for MVP; documented as a fast follow.
4. **Recipient comments / collaboration on shares**? Explicitly out of scope; share is read-only.
5. **Trip plan editing beyond title** (reorder stops, swap lodging)? Out of scope for MVP; "regenerate" is the only edit affordance.
6. **Multi-watershed trip plans**: should the wizard span multiple watersheds in one plan? Yes — `inputs.watersheds` is an array; clustering handles cross-watershed. Lodging menu pulls from all involved watersheds.

## Governing Artifacts

- **PRD**: `docs/helix/01-frame/prd.md`
- **FEAT-016 Saved & Favorites**: persistence model that this work builds on.
- **FEAT-020 Photo Observations**: privacy/visibility model for observations included in shares.
- **FEAT-019 Authentication**: auth flow used to identify share owners and trip-plan owners.
- **Architecture**: `docs/helix/02-design/architecture.md` — adds `RoutingProvider` interface to the external-services section.
- **Anthropic SDK pattern**: same prompt-cache + structured-output approach used in `/sites/{ws}/river-story` and `/sites/{ws}/time-machine`.

## Refinement Log

- **Round 1** (initial draft): identified two features, sketched APIs, captured the localStorage tension. ~30 underspecified items.
- **Round 2**: pushed on the privacy model — added AD-8 (snapshot-only render path, fuzzed coords by default, explicit opt-in). Added LodgingOption schema. Added day clustering as its own design point. ~14 substantive changes.
- **Round 3**: stress-tested LLM hallucination (lodging menu validation in AD-7), error paths (table in §Error Handling), recipient flows (save-copy of `type='shared_observation'`). ~9 substantive changes.
- **Round 4**: tightened observability + risk register; resolved short-URL question; pinned routing provider with explicit migration path; added print stylesheet; added rate limits per user. **3 substantive changes** — convergence threshold met.
