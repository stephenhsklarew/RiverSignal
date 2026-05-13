# Design Plan: Persona Self-Selection at Sign-up

**Date**: 2026-05-13
**Status**: DECISIONS RESOLVED — ready for polish/decomposition
**Governing artifacts**:
- `01-frame/features/FEAT-019-authentication.md` (auth flow this extends)
- `01-frame/prd.md` (canonical persona list)
- `00-discover/riverpath-vision.md`, `deeptrail-vision.md`
- `02-design/adr/ADR-001-anonymous-first-access.md` (anonymous-first principle, which this must not violate)
- `02-design/plan-2026-05-11-trip-quality-score.md` (TQS uses persona to gate guide-only features)

## 1. Problem Statement and User Impact

The platform serves multiple personas with meaningfully different feature needs (Professional Guides vs Self-Guided Anglers, Families, Rockhounds, Educators, Watershed Pros — see `prd.md` §Personas). Today every user sees every feature regardless of fit. As we ship persona-specific surfaces — the guide-tier client-planning view, the family kid-mode story tone, the rockhound legal-collecting badges, the watershed-pro funnel into RiverSignal — we need to know which persona(s) a user identifies with.

We need a lightweight, optional self-selection step that:
1. Doesn't break anonymous-first access (ADR-001) — the platform must keep working for unauthenticated users with no tailoring.
2. Doesn't tank sign-up conversion — never block account creation on persona selection.
3. Captures enough signal to tailor surfaces and unlock paid features (guide tier).
4. Survives evolution — we'll add and rename personas; user data shouldn't have to migrate.

## 2. Recommended Approach

**Optional, skippable, multi-select, post-signup.** Sign-up itself stays one-tap OAuth (Google or Apple). After the OAuth callback completes, the user lands on a friendly prompt:

> "Help us tailor what you see. How will you use Liquid Marble? (Pick any that apply, or skip)"

Multi-select because a guide who also hikes with family is both. A teacher who also fly-fishes is both. Forcing one is wrong for ~20% of users.

Skippable because gating completion harms anonymous-first ethos and reduces sign-up rate. Skipped users see the generic experience; they can set personas any time from settings.

### User-facing persona options (≤6)

| User-facing label | Internal persona | What it unlocks |
|---|---|---|
| 🎣 I fish — for myself | `angler_self_guided` | Catch probability emphasis on `/path/now`, TQS watchlist on home rivers, hatch tools, on-water reference |
| 🪝 I guide for clients | `guide_professional` | Client-trip planning view, late-cancellation alerts, multi-reach client briefings, $200–500/yr pricing tier |
| 👨‍👩‍👧 I visit rivers with family | `family_outdoor` | Story-mode UI tone, kid-friendly narrative reading level by default, swim safety prominence, photo identification |
| 🪨 I look for rocks and fossils | `rockhound` | DeepTrail surfaces, legal-collecting badges, mineral / rockhounding site cards |
| 🌲 I hike, camp, or explore generally | `outdoor_general` | Recreation tab emphasis, access points, scenic stops, less fishing-centric copy |
| 🔬 I teach, study, or steward watersheds | `watershed_pro` | Photo observations CTA, restoration outcomes section, watershed-council links, RiverSignal cross-product recommendation |

Ordering on the prompt matches our internal Primary→Tertiary ranking but the user picks what's true, not what we prioritize.

### When the prompt fires

- **New users**: on first authed page load after OAuth (existing `/auth/success` redirect is the hook).
- **Existing users post-rollout**: one-time soft prompt on next authed visit; dismissible permanently. The dismissal still records `personas_set_at` so we know they were asked.
- **Re-prompt**: only when `personas_version < CURRENT_VERSION` — i.e., we added a meaningful new persona that existing users couldn't have chosen. Most version bumps don't trigger re-prompt (renames, copy tweaks). Only structural additions do.

### What "skip" means

- `personas` stays empty array `'{}'`
- `personas_set_at` is set to `now()` (so we don't re-prompt them next session — they actively chose not to answer)
- User sees the generic / un-tailored experience, same as anonymous

## 3. Schema Additions

Smallest viable schema. Three new columns on existing `users`, plus a small reference table for the persona catalog.

```sql
-- Catalog so we can rename / add personas without rewriting user rows.
CREATE TABLE IF NOT EXISTS user_personas_catalog (
    key             varchar(40) PRIMARY KEY,        -- 'angler_self_guided', 'guide_professional', ...
    display_label   varchar(80) NOT NULL,
    description     text,
    icon            varchar(20),                    -- emoji or icon name
    sort_order      int NOT NULL DEFAULT 0,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);

-- Extend users.
ALTER TABLE users ADD COLUMN IF NOT EXISTS personas varchar[] NOT NULL DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS personas_set_at timestamptz;
ALTER TABLE users ADD COLUMN IF NOT EXISTS personas_version smallint NOT NULL DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_users_personas ON users USING GIN (personas);
```

### Why an array column, not a join table

- Max ~6 personas per user; realistic v1 user count ≤ 25k → array is simpler with no real downside.
- GIN index on the array supports fast `'guide_professional' = ANY(personas)` checks at the row scan rate.
- Join-table migration is cheap to do later if we ever exceed ~20 personas.

### Why the catalog table

- Lets us rename a display label without touching user rows (rows reference stable `key`, not display label).
- `is_active=false` deprecates without deleting — existing rows that reference it still resolve.
- `sort_order` controls UI ordering centrally.

### Seed data

A migration seeds the six personas with stable keys. Display labels and descriptions are editable post-migration without code changes.

```sql
INSERT INTO user_personas_catalog (key, display_label, description, icon, sort_order) VALUES
  ('angler_self_guided',   'I fish — for myself',
   'Personal trips, no clients. Watchlist your home rivers and get pinged when conditions are good.',
   '🎣', 10),
  ('guide_professional',   'I guide for clients',
   'Run paid trips. Get a client-ready morning briefing, multi-reach planning, and late-cancellation alerts.',
   '🪝', 20),
  ('family_outdoor',       'I visit rivers with family',
   'Make every river stop feel alive. Stories, kid-friendly mode, swim safety, species photos.',
   '👨‍👩‍👧', 30),
  ('rockhound',            'I look for rocks and fossils',
   'Find legal collecting sites and learn what others have found nearby.',
   '🪨', 40),
  ('outdoor_general',      'I hike, camp, or explore generally',
   'Access points, trailheads, scenic stops, and what to look for at each river.',
   '🌲', 50),
  ('watershed_pro',        'I teach, study, or steward watersheds',
   'Restoration data, citizen-science contribution, watershed-council links, professional analytics.',
   '🔬', 60)
ON CONFLICT (key) DO NOTHING;
```

## 4. UX Flow

```
[OAuth tap]
  │
  ▼
[/auth/success — provider callback]
  │
  ▼
needsUsername == true  ──► [Username setup page] ──► (after username set)
                                                            │
                                                            ▼
needsUsername == false ──────────────────────────────► [Persona prompt modal]
                                                        │   │
                                                  Picks │   │ Skip
                                                        │   │
                                                        ▼   ▼
                                                  [POST /auth/personas]
                                                        │   │
                                                        ▼   ▼
                                                  [Land on intended page,
                                                   tailored to selections]
```

### Modal copy (draft)

```
🌊 Welcome to Liquid Marble

Pick any that describe how you'll use it — we'll tailor what you see.
You can change this any time in settings.

[ ] 🎣 I fish — for myself
[ ] 🪝 I guide for clients
[ ] 👨‍👩‍👧 I visit rivers with family
[ ] 🪨 I look for rocks and fossils
[ ] 🌲 I hike, camp, or explore generally
[ ] 🔬 I teach, study, or steward watersheds

   [ Skip — show me everything ]   [ Save and continue ]
```

Visual: same modal styling as the existing username-setup page (`UsernameSetupPage.tsx`); single primary action; clear skip; no scrolling on mobile.

### Settings page

A "Your interests" section on the existing user settings panel:
- Current selections shown as chips
- "Edit" button reopens the same modal pre-populated
- Save updates `personas` + `personas_set_at = now()`

## 5. API Surface

```
GET /api/v1/personas/catalog
   → [ { key, display_label, description, icon, sort_order }, ... ]   # only is_active=true

GET /api/v1/auth/me
   → existing response + { personas: [...], personas_set_at, personas_version }
   # so the client knows whether to show the prompt

POST /api/v1/auth/personas
   body: { personas: ["angler_self_guided", "family_outdoor"] }   # multi-select; empty = skip
   → 200 { personas, personas_set_at, personas_version }
   # auth required; updates the row, returns new state
```

### Validation rules

- All persona keys in the request must exist in `user_personas_catalog` with `is_active=true`. Unknown keys reject the whole request with 400.
- Empty array is valid (the skip case) — sets `personas='{}'` and `personas_set_at=now()`.
- Re-submission is allowed (user changed their mind) — overwrites the array, updates `personas_set_at`.

## 6. Feature gating

Most features key off persona via boolean helpers exposed by `AuthContext`:

```ts
// frontend/src/components/AuthContext.tsx (extension)
const hasPersona = (key: string): boolean => user?.personas?.includes(key) ?? false
const hasAnyPersona = (...keys: string[]): boolean => keys.some(hasPersona)
const isUnsetOrSkipped = (): boolean => !user || user.personas?.length === 0
```

Usage examples:

- **Default landing page** after sign-in:
  ```
  if hasPersona('guide_professional')  → /path/where  (multi-reach ranking is the main affordance)
  if hasPersona('angler_self_guided')  → /path/now    (today's snapshot)
  if hasPersona('family_outdoor')      → /path        (story cards homepage)
  if hasPersona('rockhound')           → /trail       (DeepTrail picker)
  if isUnsetOrSkipped() or multiple    → /            (Liquid Marble landing)
  ```
- **TQS watchlist nav item**: visible only for `angler_self_guided` or `guide_professional`.
- **Guide-tier features** (client-trip view, late-cancellation alerts, premium pricing pill): gated on `guide_professional`.
- **AI narrative reading level**: defaults to "kid-friendly" when `family_outdoor` is the only RiverPath-relevant persona.
- **Cross-product surfacing**: `watershed_pro` users see a RiverSignal cross-link in their nav; `rockhound` users see a DeepTrail cross-link.

Server-side enforcement uses the same `personas` array on writes that require persona scope (e.g., guide-tier subscription creation requires `guide_professional`).

## 7. Phasing

| Phase | Scope | Unblocks |
|-------|-------|----------|
| **A** (~2 days) | DB migration (catalog table + 3 new columns on users + seed); `GET /personas/catalog`; extend `GET /auth/me` to return persona fields; `POST /auth/personas` endpoint with validation; unit + integration tests | Persona data plane ready; no UI yet |
| **B** (~3 days) | Persona-prompt modal component; wire into post-signup flow after username setup; settings-page "Your interests" section; persona-skip cookie to prevent prompt loop within a session | Users self-select; data accumulates |
| **C** (~2 days) | Feature-gating helpers in `AuthContext`; first three gates wired (default landing page redirect, TQS watchlist nav, family kid-mode default) | Persona starts changing the product |
| **D** (later) | Guide-tier features (client-trip view, late-cancellation alerts) gated on `guide_professional`; pricing pill | Monetization path active |
| **E** (later) | Re-prompt logic for `personas_version` bumps; analytics on selection rates per persona; A/B on modal copy and ordering | Iterate based on data |

Total v1 (A + B + C) ≈ 1 week of one engineer.

## 8. Risks and Counter-Plans

| Risk | Likelihood | Impact | Counter |
|------|-----------|--------|---------|
| Sign-up funnel drops if modal feels heavy | Med | High | Make skip extremely visible; cap at 6 options; test in Phase A.5 hallway test (borrow the TQS plan's hallway-test pattern) |
| Users select all 6 ("just check everything") → no signal | Med | Med | Limit display to top 6; "Save and continue" button counter shows when ≥4 selected with a soft "we'll tailor better with a focused list" hint; accept it as long-tail noise otherwise |
| User picks `guide_professional` to unlock features without actually being a guide | Low | Low | Guide tier is paid — they're gating themselves out of free use; if pricing isn't live yet, no harm. When pricing launches, payment is the real verification. |
| We rename a persona display label and users feel surveilled ("did they change my answer?") | Low | Low | Display label can change freely; underlying `key` is stable; surface a "we updated the options" toast if `personas_version` bumps |
| Personas drift from the canonical PRD list | Med | Med | The catalog seed is authored from the PRD persona list. Any new persona requires both a PRD update and a catalog seed migration. Cross-check is part of the FEAT spec checklist |
| Account-takeover replay of personas POST leaks signal about a user | Low | Low | Endpoint requires the same auth cookie as every other write; no PII in the payload |

## 9. Decision Points — resolved 2026-05-13

All decisions resolved. Plan is ready for `helix polish` to decompose into tracker beads.

| # | Decision | Resolution | Rationale |
|---|----------|------------|-----------|
| 1 | Multi-select vs single-select | **Multi-select** | ~20% of users fit multiple personas (guide who also fishes with family). Single-select forces them to lie. |
| 2 | Skippable vs required | **Skippable** | Preserves anonymous-first (ADR-001); protects sign-up conversion. Skipped users see the generic experience. |
| 3 | Six options vs more granular | **Six** at launch | Past 6, modal UX degrades. Angler sub-personas (warmwater vs coldwater, tenkara, etc.) come in v2 as an optional second-level question. |
| 4 | Default landing page logic | **Persona-based redirect in Phase C** | Biggest tailoring win in v1. Single rule: `guide_professional` → `/path/where`; `angler_self_guided` → `/path/now`; `family_outdoor` → `/path`; `rockhound` → `/trail`; skipped / multi-select / `watershed_pro` → `/` (Liquid Marble landing). |
| 5 | Re-prompt cadence | **Only on `personas_version` bumps** | Yearly re-prompts feel noisy and rarely catch real life changes. Version bumps only fire when we add a new persona existing users couldn't have selected. |
| 6 | Prompt before or after username setup | **After username** | Two cleaner steps than one crowded screen. Username has higher conversion criticality (goes first); persona is optional (goes second). |
| 7 | Anonymous users prompt? | **No** | Asking unauthenticated users "what brings you here?" is invasive without an account behind it. localStorage tailoring without identity is creepy more than useful. Anonymous-first remains intact. |

Implementation order: 3 → 4 → 5 (schema → API → UX) in Phase A and B; feature gates in Phase C only after data accumulates.

Next step: `helix polish 02-design/plan-2026-05-13-persona-self-selection.md` to decompose into tracker beads.
