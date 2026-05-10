---
dun:
  id: ADR-008
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-008: Every ingestion adapter tags rows with license + commercial flag

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-04-25 | Accepted | Founder | FEAT-005 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | We ingest 30+ data sources with mixed licenses: Public Domain, CC BY 4.0, CC BY-NC, Public Records, Varies, Academic Free. A B2B paid feature surfacing CC BY-NC content (notably iNaturalist photos) creates legal exposure. We need to know per-source what's commercially safe to surface. |
| Current State | License + `commercial: true/false` is tracked in `app/routers/data_status.py` SOURCE_META, but not on individual rows. |
| Requirements | Any row served by the API must be queryable by license. B2B/paid features must filter by `commercial=true` sources only. New ingestion adapters must declare their license at adapter registration time. |

## Decision

Every ingestion adapter populates two fields on every row written: `source_type` (free-text identifier of the upstream source) and a side-table `source_metadata` that maps `source_type → {license, commercial, upstream_frequency, refresh_schedule, description}`. The status page (`app/routers/data_status.py`) is the canonical source for the metadata, mirrored to the runtime via `SOURCE_META` Python dict for easy code-side gating.

**Key Points**: License is per-source, not per-row | `commercial` flag is the gate for B2B paid features | New adapter PRs must add a SOURCE_META entry — pre-commit lint enforces.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Per-row license column | Maximum granularity | Bloat for the 99% case where source-level granularity is sufficient | Rejected: source-level is right granularity |
| External license-management service | Industry-standard | Overkill for our scale; adds an integration | Rejected: complexity not justified |
| No license tracking; ToS gate by manual audit | Simplest | Auditing is the bottleneck; mistakes leak | Rejected: not safe |
| **Per-source metadata; commercial flag gates paid features** | Right granularity; runtime-checkable; PR-enforceable | Requires discipline in adapter PRs | **Selected: matches data shape and our scale** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | B2B feature reviews can run a simple SQL filter to verify no non-commercial leak; new adapter PRs have explicit license review |
| Negative | If an upstream provider changes their license, we need to update SOURCE_META and audit downstream usage — manual process |
| Neutral | License badges visible on user-facing data (e.g., iNat photos) — supports compliance + transparency |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Upstream license changes silently | L | H | Annual review of source TOS; subscribe to provider mailing lists |
| New adapter merged without SOURCE_META | M | M | Pre-commit lint on adapter directory; PR template checkbox |
| Commercial flag misset (true when should be false) | L | H | Annual external audit if B2B paid revenue exists |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| 100% of bronze tables have valid source_type | Daily — `/status` endpoint shows |
| Zero CC BY-NC content in B2B paid surfaces | Pre-release audit per B2B feature |

## Concern Impact

- **Concern selection**: Selects `license-tagged-source-data` (compliance) — see `01-frame/concerns.md`.

## References

- `app/routers/data_status.py` (SOURCE_META)
- `pipeline/ingest/*.py` (adapters)
- `01-frame/compliance-requirements.md` (data classification table)
