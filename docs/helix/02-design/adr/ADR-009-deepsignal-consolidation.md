---
dun:
  id: ADR-009
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-009: Consolidate DeepSignal (B2B geology) into RiverSignal as a layer

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-05-08 | Accepted | Founder | FEAT-008, FEAT-011 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | The platform launched as **four** products: RiverSignal (B2B ecology), DeepSignal (B2B geology), RiverPath (B2C river), DeepTrail (B2C geology). DeepSignal and RiverSignal shared the same B2B desktop audience (restoration professionals, researchers, land managers) and the same warehouse; running them as separate product surfaces duplicated navigation and split a single buyer's attention without a distinct buyer or pricing story. |
| Current State (pre-ADR) | A standalone `/deepsignal` surface existed alongside `/riversignal`. Geology data (Macrostrat, MRDS, NGMDB, fossils) was already in the shared warehouse and consumable by both. |
| Requirements | One B2B desktop product for professionals; geology must remain a first-class capability (not dropped); no data migration (warehouse is shared); B2C geology (DeepTrail) is unaffected. |

## Decision

Remove DeepSignal as a separate product and **consolidate its B2B geology
functionality into RiverSignal as an integrated layer**. The platform is now
**three products**: RiverSignal (B2B, with geology layer), RiverPath (B2C river),
DeepTrail (B2C geology). DeepSignal was removed from the landing page on
2026-05-08. The `/deepsignal` route may persist as a thin alias/redirect into the
RiverSignal geology layer but is not marketed as a product.

**Key Points**: Three products, one platform (principle #2) | Geology is a *layer*
of RiverSignal, not a product | No warehouse changes — geology data already shared
| DeepTrail (B2C geology) is untouched.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Keep four products | Clear geology brand | Duplicate B2B nav; split one buyer's attention; double surface to maintain | Rejected: no distinct B2B buyer |
| Drop geology from B2B entirely | Simplest | Loses a real differentiator ("geology IS the foundation of watershed ecology") | Rejected: geology is core to the thesis |
| **Consolidate geology into RiverSignal as a layer** | One B2B product; geology retained; no data migration | Requires removing the DeepSignal surface + redirect | **Selected: matches the one-platform principle** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | One B2B product to sell, document, and maintain; geology presented in ecological context |
| Negative | Marketing/docs that referenced four products must be updated (this ADR + PRD + vision + feature-registry) |
| Neutral | `/deepsignal` route retained as alias; FEAT-008 (Geologic Context) now scoped under RiverSignal |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| Stale "four product" references linger in docs | M | L | feature-registry FEAT-011 note + AR-2026-06-06 tracked update of vision/PRD |
| Existing `/deepsignal` links break | L | L | Keep route as redirect/alias into RiverSignal geology layer |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| Landing page shows three products | On release (done 2026-05-08) |
| No "DeepSignal product" framing in vision/PRD | This ADR + AR-2026-06-06 doc-gap remediation |

## Concern Impact

- Reinforces principle #2 ("Three apps, one platform"). No new concern selected;
  consolidates surface area under existing `managed-cloud-platform-only` infra.

## References

- `00-discover/product-vision.md` (3-product platform; forward-reference to this ADR)
- `01-frame/feature-registry.md` (FEAT-011 Three-Product UI: "was 4 — DeepSignal consolidated 2026-05-08")
- `02-design/plan-2026-04-10-four-product-platform.md` (superseded title; original 4-product plan)
