---
dun:
  id: helix.implementation-plan
  depends_on:
    - helix.test-plan
---
# Build Plan

## Scope

This is a retroactive implementation plan reflecting how the platform has been built. It captures the build sequencing that has shipped and the next-up backlog. Future stories (FEAT-021+) will be sequenced through this same document.

**Governing Artifacts**:
- `docs/helix/01-frame/prd.md`
- `docs/helix/01-frame/feature-registry.md`
- `docs/helix/02-design/architecture.md`
- `docs/helix/02-design/adr/ADR-*.md`
- `docs/helix/03-test/test-plan.md`

## Shared Constraints

- **Anonymous-first** (ADR-001): every read endpoint must work without auth.
- **Medallion warehouse** (ADR-002): UI queries must hit gold; new ingestion populates bronze first.
- **Secrets in Secret Manager** (ADR-003): no .env in production code paths.
- **Visibility-aware obs** (ADR-004): every new public endpoint joining `user_observations` adds the filter and a regression test.
- **Managed cloud only** (ADR-005): no new self-hosted services.
- **Federated auth only** (ADR-006): no password fields.
- **AI grounded** (ADR-007): every LLM/AI call grounded in warehouse context.
- **License-tagged sources** (ADR-008): every new ingestion adapter populates SOURCE_META.
- **TypeScript strict** (`tsc -p tsconfig.app.json --noEmit`): build blocks on type errors. `noUnusedLocals` + `noUnusedParameters` are on.
- **Mobile-first B2C, desktop-first B2B**: don't apologize for the inverse.

## Build Sequencing — shipped (retroactive)

| Order | Story / Area | Governing Artifacts | Depends On | Notes |
|------|---------------|---------------------|------------|-------|
| 1 | Postgres schema + bronze tables | PRD; FEAT-005 | — | Foundation; alembic `1479f57b36fb_initial_schema` |
| 2 | First ingestion adapters (USGS, iNat) | FEAT-005 | (1) | Get bronze populated end-to-end |
| 3 | Silver views + first gold view | FEAT-005, ADR-002 | (1) | Validate medallion pattern |
| 4 | FastAPI server scaffold + first read endpoints | FEAT-006 | (3) | Prove the data path |
| 5 | RiverSignal desktop UI (FEAT-006) | FEAT-006, FEAT-011 | (4) | First user-visible product |
| 6 | Predictive models v1 (FEAT-017) | FEAT-017, ADR-007 | (5) | 5 models in `gold.predictions` |
| 7 | RiverPath mobile B2C (FEAT-012) | FEAT-012, FEAT-014 | (5), (6) | Bottom-nav tab pattern |
| 8 | DeepTrail mobile B2C (FEAT-013) | FEAT-013, FEAT-014 | (7) | Geology + fossils + AI narrative |
| 9 | Authentication (FEAT-019) | FEAT-019, ADR-006 | (4) | OAuth + JWT |
| 10 | Photo observations (FEAT-020) | FEAT-020, ADR-004 | (9) | Public/private toggle + visibility filtering across surfaces |
| 11 | Liquid Marble landing + `/status` rebrand | (per recent commits) | (5)–(10) | Brand consolidation; sticky `/status` header; gold.snowpack_current view fix |
| 12 | Unified RiverPath header across all screens | (recent commits) | (7) | Single `.ws-header` element; settings inside |

## Build Sequencing — next up (backlog)

| Order | Story / Area | Governing Artifacts | Depends On | Notes |
|------|---------------|---------------------|------------|-------|
| 13 | Server-side EXIF GPS strip on public photo obs | FEAT-020, threat-model TM-I-002 | (10) | Highest-priority security gap |
| 14 | Privacy policy + self-service data export/delete | compliance-requirements.md | — | Highest-priority compliance gap |
| 15 | AI cost circuit breaker + per-IP rate limit | threat-model TM-D-001, ADR-007 | (6) | Operational guardrail before broad B2C launch |
| 16 | Auth flow integration test suite | test-plan.md | (9) | Highest-priority test gap |
| 17 | CI test workflow (separate from deploy) | test-plan.md | — | Block merges on test failure |
| 18 | SNOTEL historical normals ingestion → fill `pct_of_normal` | FEAT-005 | (11) | Completes snowpack card UX |
| 19 | Funder report generation (FEAT-004) | FEAT-004 | (5) | First B2B paid surface |
| 20 | Management recommendations (FEAT-003) | FEAT-003 | (5), (6) | Second B2B value prop |

## Issue Decomposition

Story-level work is tracked via `ddx bead` in `.ddx/issues.jsonl` (when issues are created via the HELIX workflow). For now (solo engineer) the build sequencing list above is the working backlog.

**Per-issue requirements** (when adopted):
- Labels: `helix`, `phase:build`, `kind:build`, `story:US-{story-id}`
- References: user story, technical design, story test plan, this build plan
- `spec-id` pointing at the nearest governing artifact
- Blockers as dependency links

## Quality Gates

- [x] Failing tests exist before implementation starts (TDD-style for new features; retroactive for prior work)
- [x] All required tests pass before deploying (CI runs `pytest`; type check pre-flight)
- [x] Behavior changes update canonical documents (HELIX docs, including this build plan, kept current)
- [x] Code review complete before phase exit (solo engineer = self-review against checklist; future contractor handoff via PR)

## Risks

| Risk | Impact | Response |
|------|--------|----------|
| Solo-engineer bus factor | High | Comprehensive HELIX docs (this set); contractor retainer (per RISK-001) |
| Build-without-test for older code | Medium | Backfill the auth + AI grounding test suites in next two sprints |
| New endpoint forgets visibility filter | Critical | Mandatory regression test entry; PR review checklist; consider migration to a `silver.public_user_observations` view as the only joinable surface |
| Build breaks on TypeScript noUnusedLocals after a refactor | Low | Pre-flight `npx tsc --noEmit` before push; deploys fail loudly when this regresses |

## Exit Criteria

- [x] Build issue set is defined with sequence and dependencies
- [x] Shared constraints are documented (above)
- [x] Verification expectations are explicit (test-plan + per-feature test references)
- [ ] All ADR-mandated practices have automated enforcement (in-progress: visibility test gate exists; license test gate is manual)

## Review Checklist

- [x] Governing artifacts listed and exist on disk
- [x] Shared constraints trace back to PRD/ADRs
- [x] Build sequence has justified ordering (shipped order is historical fact; backlog ordering reflects risk-first)
- [x] Dependencies between build steps are explicit
- [x] Each story references its governing artifact (FEAT spec or ADR)
- [ ] Quality gates are automated, not aspirational (CI test workflow is the next infrastructure beat)
