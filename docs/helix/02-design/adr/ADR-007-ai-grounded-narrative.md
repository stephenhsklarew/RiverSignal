---
dun:
  id: ADR-007
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-007: AI narrative must be grounded in our warehouse, never raw LLM

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-04-22 | Accepted | Founder | FEAT-010, FEAT-017 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | LLMs hallucinate confidently. A wrong species, wrong age, or fictional restoration outcome in a user-facing narrative tarnishes the brand and erodes trust in our data. We invest heavily in unifying public scientific data — that investment is wasted if we then ask the LLM to make stuff up about a place. |
| Current State | We have rich warehouse data per (lat, lon): geologic units, fossil occurrences, species observations, water quality, restoration projects. |
| Requirements | Every user-facing narrative ("Deep Time Story", AI Q&A) must reference verifiable facts from the warehouse. Reading levels and tone are LLM choices; facts are not. |

## Decision

All narrative-generating AI calls follow a retrieval-augmented pattern:

1. Compute a context bundle from the warehouse for the target location (e.g., nearest geologic units from Macrostrat, fossil occurrences within 50 km from PBDB+iDigBio+GBIF, species observations at site, ecological tier for cross-domain links).
2. Pass that context bundle as structured input to Anthropic Claude with a system prompt that instructs the model to ground its narrative in those facts.
3. Cache the result in `gold.deep_time_story` (or equivalent) with a key including data-freshness timestamps so it auto-invalidates on warehouse refresh.

**Key Points**: Context-first, not LLM-first | Cache aggressively (per (lat, lon, reading_level)) | Reading-level controls (adult / kid / expert) are tone settings, not fact toggles | TTS audio is generated only against the cached narrative.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Raw LLM (no retrieval) | Simplest integration; cheapest dev | Hallucination risk; brand destroyer | Rejected: not viable for a science-first product |
| Hand-written narratives | Highest accuracy | Doesn't scale to thousands of locations; not a story per place | Rejected: doesn't deliver the "story for any place" promise |
| Retrieval but no cache | Always fresh | Cost-prohibitive; latency spikes | Rejected: caching is mandatory at our cost ceiling |
| **Retrieval + cache + reading-level tone control** | Grounded; affordable; engaging | Cache invalidation needs care; context bundle prompt design is iterative | **Selected: only viable path for production** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | Brand trust; cost stays bounded; supports kid/adult/expert tone variation; audio TTS layer fits cleanly |
| Negative | Context bundle pipeline is now a critical dependency for every narrative endpoint; new data sources need to be integrated into the bundle to be reachable by AI |
| Neutral | Narrative review remains a quality concern (RISK-010) — grounding doesn't eliminate misinterpretation risk |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Context bundle missing relevant data (model fills gap with hallucination) | M | M | Domain-expert review (research-plan); user-flagging UI; iterative prompt tightening |
| Cache key doesn't include all freshness signals → stale narrative served | L | M | Include `MAX(updated_at)` per relevant table in cache key |
| LLM cost growth | M | M | See ADR-005 (RISK-002); circuit breaker on daily cost |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| Domain-expert accuracy score ≥ 4/5 average | Quarterly review per domain (geology, fishing, restoration) |
| AI cost per MAU ≤ $0.05 | Monthly |
| Cache hit rate ≥ 90% | Monthly |

## Concern Impact

- **Concern selection**: Selects `ai-grounded-narrative` (quality) — see `01-frame/concerns.md`.

## References

- `app/routers/reasoning.py` (narrative + Q&A endpoints)
- `app/routers/deep_time.py` (story endpoint)
- `pipeline/medallion.py` (`gold.deep_time_story` + `gold.river_story_timeline`)
