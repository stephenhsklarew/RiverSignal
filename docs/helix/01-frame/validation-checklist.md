# Frame Phase Validation Checklist

**Status**: [x] Complete (retroactive — frame artifacts written 2026-05-10 against an already-deployed production system)
**Validated By**: Stephen Sklarew
**Date**: 2026-05-10
**Result**: [x] Pass

## Go / No-Go Gates

- [x] Problem, goals, and success metrics are clear enough to judge outcomes.
  - See `prd.md` and `00-discover/opportunity-canvas.md`. North-star metric: sessions where user saved a finding.
- [x] P0 scope is identified, prioritized, and separated from non-goals.
  - 20 features in `feature-registry.md` with priorities. Non-goals: hunting, marine, climbing, social/community features, national-scale coverage. Documented in `00-discover/opportunity-canvas.md`.
- [x] Features and stories are traceable through IDs and links.
  - FEAT-001 through FEAT-020 with categorization and dependencies.
- [x] Acceptance criteria are testable.
  - Each feature spec under `features/FEAT-*.md` includes acceptance criteria. Test coverage is partial (see `03-test/test-plan.md`).
- [x] Major risks, dependencies, and external constraints are explicit.
  - 12 risks in `risk-register.md`; threat model in `threat-model.md`; compliance requirements documented.
- [x] Frame artifacts do not contradict each other.
  - PRD, feature registry, and stakeholder map cross-checked during this writing pass.
- [x] Required stakeholders have reviewed the plan.
  - Solo-engineer project; founder is the sole stakeholder for technical decisions. B2B council reviewers will be added in research-plan Phase 2.

## Result

- [x] **PASS**: Ready for Design phase

**Conditions/Notes**:
This is a retroactive frame validation. The platform is already live in production and most features are deployed. The frame artifacts now exist to anchor future change management — the next time someone proposes a new feature, it has a defined home in the registry and the relevant frame docs.

Outstanding from this pass (does not block):
- Privacy policy page must ship before the first user data subject request
- Self-service data export + delete endpoints before EU launch announcement
- Server-side EXIF stripping before promoting public photo observations to landing page
- Annual review of source-data licenses and commercial flags

These flow into the next Design + Build cycle, not into a re-Frame.
