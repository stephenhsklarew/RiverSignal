# Project Principles

These principles guide judgment calls across all HELIX phases. They are not workflow rules — they are the lenses we apply when choosing between two valid options.

## Principles

1. **Anonymous-first.** Every read endpoint works without authentication. Sign-in is for sync and persistence, never for access. New features that require sign-in must justify the cost in the spec.

2. **Three apps, one platform.** Code paths and data live on one backend, one warehouse, one Cloud Run service. Apps differentiate at the React route level, not by duplicating infrastructure.

3. **Bronze, silver, gold — in that order.** Ingestion writes raw to bronze. Silver normalizes and deduplicates. Gold pre-aggregates for the API. Don't query bronze from a UI endpoint; if there's no view, write one.

4. **Data has provenance.** Every record traces to its source (`source_type`, `source_id`, license). New ingestion adapters must populate provenance before merging.

5. **Cache aggressively.** API responses, gold view materialization, AI narratives, and TTS audio all get cached at the appropriate layer. Cost-per-request matters.

6. **Mobile-first for B2C, desktop-first for B2B.** Don't apologize for the inverse. Optimize each surface for its actual use context — RiverPath at the river bank, RiverSignal at a desk.

7. **Story over schema.** Users don't care that we joined ten tables. They care that we told them when to fish or what fossil they're standing on. Write the narrative, then build the schema to support it.

8. **Trust the user with their own data.** Photo observations, saved items, sign-in tokens — store with privacy by default, share with explicit opt-in.

9. **Reversible decisions over reversible-looking decisions.** Schema migrations, secret rotations, third-party integrations — pick the path that's actually easy to undo, not the one that *feels* easy. Document the rollback in the same PR.

10. **Make intent explicit in the artifact.** PRD says what; ADR says why. Code says what; commit message says why. When the why is non-obvious, write it down — usually as a comment, occasionally as a `principles.md` entry.

11. **Production parity locally.** Anyone can run the full stack on their laptop with `docker compose` (bronze + silver + gold + API + frontend). If they can't, that's a bug.

12. **Validate before claiming.** A type check is not a test. A passing test is not a feature shipping. A feature shipping is not a feature working. Each gate is a separate claim.

## Tension Resolution

When principles pull in opposite directions, document the resolution strategy here.

### "Anonymous-first" vs "Trust the user with their own data"
**When**: Photo observations were added with private/public visibility. Anonymous-first says any user can post; the trust principle says private posts shouldn't leak.
**Resolution**: Anonymous users can post *public* observations. Private observations require auth (so we can ACL them). Public/private filtering is enforced at the silver/gold view level, not just the API.

### "Cache aggressively" vs "Make intent explicit"
**When**: Cached AI narratives might serve outdated context after an underlying data refresh.
**Resolution**: Cache keys include the data-source freshness signal (e.g., `source_max_updated_at`). Stale narratives are auto-invalidated, never silently served.

### "Three apps, one platform" vs "Mobile-first for B2C, desktop-first for B2B"
**When**: Shared components (e.g., `WatershedHeader`) need to look right on both desktop B2B and mobile B2C surfaces.
**Resolution**: Components default to mobile, with desktop overrides via media queries. B2B desktop pages use composition (not subclassing) to swap in heavier desktop layouts.
