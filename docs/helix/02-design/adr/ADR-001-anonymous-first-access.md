---
dun:
  id: ADR-001
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-001: Anonymous-first access for all read endpoints

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-04-15 | Accepted | Founder | FEAT-019 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | Most "useful river/geology data" apps gate the entire experience behind sign-up walls. This is a friction tax on first-time users and contradicts the public-domain nature of most of our source data. |
| Current State | All federal datasets we ingest are open. iNaturalist research-grade observations are CC BY-NC. None of the read paths legally require auth. |
| Requirements | The platform must work for an anonymous user who lands on the site for the first time and just wants to know whether their fishing trip will be productive. Sign-in is purely additive. |

## Decision

We will design every read endpoint to work for anonymous users by default. Authentication is optional and adds: cross-device sync of saved items, persistence of photo observations, and account-level personalization. No read endpoint will return a 401 for a missing token.

**Key Points**: Optional-auth dependency injection (`get_optional_user`) | Anonymous browsers identified by client-generated `rs_anonymous_id` (UX only, not a security boundary) | Sign-in via OAuth (Google, Apple) is offered but never required.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Sign-in required for all endpoints | Simpler auth model; richer per-user analytics | Massive friction; tanks B2C distribution; legally unjustified | Rejected: violates "make the data reach people" goal |
| Sign-in required for "premium" features only | Pay-wall lever for monetization | Confusing — what counts as premium?; arbitrary boundary | Rejected: unnecessary complexity for a platform whose moat is data, not access control |
| **Anonymous-first; auth as additive** | Lowest friction; matches data licenses; aligns with iNaturalist culture | Per-user analytics requires anonymous_id workarounds | **Selected: maximizes reach; trivial to layer auth-required features later if needed** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | Maximum first-visit conversion; aligns with public-domain ethos; simpler legal posture (we're not gating public data) |
| Negative | Per-user analytics rely on `rs_anonymous_id` which resets when users clear cookies; harder to contact pre-auth users for research |
| Neutral | Sign-up rate becomes a metric to track (anonymous → authed conversion) rather than a baseline assumption |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Cost-based abuse via expensive anonymous endpoints (e.g., AI narrative) | M | M | Aggressive caching; per-IP rate limit on AI endpoints; circuit breaker on daily LLM cost |
| Difficulty re-engaging anonymous users | M | L | In-app nudges to sign in for cross-device sync; saved-items prompts |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| Anonymous → authed conversion ≥ 8% | Quarterly or if conversion < 4% |
| <1% of read traffic returns 401 | Continuous (any 401 is a regression) |

## Concern Impact

- **Concern selection**: Selects `anonymous-first-access` (privacy) — see `01-frame/concerns.md`.
- **Practice override**: None; this is the project default for all read endpoints.

## References

- `01-frame/principles.md` (Principle #1)
- `01-frame/concerns.md`
- `app/routers/auth.py:67–88` (`get_current_user`, `get_optional_user`)
