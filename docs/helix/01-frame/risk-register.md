# Risk Register

**Status**: Draft
**Last Updated**: 2026-05-10
**Risk Owner**: Stephen Sklarew

## Summary

- **Critical Risks**: 1
- **High Risks**: 4
- **Medium Risks**: 5
- **Low Risks**: 2
- **Overall Risk Level**: Medium-High (single-engineer team magnifies all categories)

## Risk Scoring

**Probability**: Very High (5) >80% | High (4) 60-80% | Medium (3) 40-60% | Low (2) 20-40% | Very Low (1) <20%
**Impact**: Critical (5) >30% overrun | High (4) 20-30% | Medium (3) 10-20% | Low (2) 5-10% | Negligible (1) <5%
**Risk Score** = Probability x Impact

## Active Risks

### RISK-001: Single-engineer bus factor
**Category**: Resource
**Status**: Open
**Owner**: Founder

**Description**: All architectural knowledge, deploy access, and ongoing development depend on one person. Illness, burnout, or departure halts the project.

**Assessment**:
- **Probability**: 4 (any 12-month period for a solo founder)
- **Impact**: 5 (project stops; production keeps running but degrades over weeks)
- **Risk Score**: 20 (Critical)

**Triggers**: Founder unavailable >2 weeks; production fire with no responder.

**Mitigation**:
- **Preventive**: Comprehensive HELIX docs (this set); Terraform IaC; reproducible local dev; CI/CD on push; runbooks in `05-deploy/`.
- **Contingency**: Pre-identified contractor with codebase familiarity; rotating quarterly retainer arrangement.
- **Fallback**: Production self-stable for ~30 days without intervention thanks to managed services (Cloud Run, Cloud SQL, scheduled jobs); freeze-and-handoff procedure documented.

**Review**: Quarterly | **Next Review**: 2026-08-10

---

### RISK-002: AI API cost runaway
**Category**: Business / Operational
**Status**: Mitigating
**Owner**: Founder

**Description**: Per-request costs to Anthropic (narrative) and OpenAI (TTS) scale linearly with users. A viral spike or runaway loop could produce a $5k+ surprise bill.

**Assessment**:
- **Probability**: 3 (no real spike yet, but possible)
- **Impact**: 3 (recoverable but stressful)
- **Risk Score**: 9 (Medium)

**Triggers**: Daily Anthropic cost >$30; daily OpenAI cost >$10; uncached cache-miss rate >40%.

**Mitigation**:
- **Preventive**: Aggressive prompt caching; pre-generated narratives in `gold.deep_time_story`; per-IP rate limits on TTS; audio caching to GCS.
- **Contingency**: Daily billing alert at $50; circuit breaker that disables narrative endpoints if daily cost exceeds threshold.
- **Fallback**: Browser `speechSynthesis` fallback for TTS; static cached narratives served if Claude API down or capped.

**Review**: Monthly | **Next Review**: 2026-06-10

---

### RISK-003: Data source license drift / compliance breach
**Category**: Compliance
**Status**: Open
**Owner**: Founder

**Description**: We ingest 30+ sources with varying licenses (Public Domain, CC BY 4.0, CC BY-NC, Public Records, Varies). A B2B paid feature surfacing CC BY-NC data, or a redistribution of an agency dataset beyond its terms, creates legal exposure.

**Assessment**:
- **Probability**: 3 (easy to slip when adding features)
- **Impact**: 4 (cease-and-desist + brand damage)
- **Risk Score**: 12 (High)

**Triggers**: New B2B feature; new data source ingestion; license change upstream.

**Mitigation**:
- **Preventive**: License field tracked per source in `app/routers/status.py` SOURCE_META; `commercial: true/false` flag gates B2B features; new ingestion adapters require license review checkbox in PR.
- **Contingency**: Audit script to detect non-commercial data leaking into commercial paths; ability to flip a feature flag to remove a source from a tier.
- **Fallback**: Take feature offline; renegotiate or replace data source.

**Review**: On every new data source | **Next Review**: 2026-06-10

---

### RISK-004: Production database loss / corruption
**Category**: Technical
**Status**: Mitigating
**Owner**: Founder

**Description**: 8.4M time-series rows + 1.3M observations + user-generated photo observations live in a single Cloud SQL instance. Loss = significant re-ingestion cost and lost user data.

**Assessment**:
- **Probability**: 2 (managed Postgres is reliable)
- **Impact**: 5 (catastrophic for users; weeks to re-ingest)
- **Risk Score**: 10 (Medium)

**Triggers**: Bad migration; bad query truncating data; instance corruption; accidental Terraform replacement.

**Mitigation**:
- **Preventive**: Cloud SQL automated backups (14-day retention via `db_backup_retention_days`); point-in-time recovery enabled; user_observations writes to bronze with full data_payload preserved; `terraform apply` requires plan review.
- **Contingency**: Restore from latest automated backup; bronze data re-ingestible from sources within 24–72h.
- **Fallback**: Documented restore procedure in `05-deploy/`; tested quarterly.

**Review**: Quarterly | **Next Review**: 2026-08-10

---

### RISK-005: Authentication compromise
**Category**: Technical / Compliance
**Status**: Open
**Owner**: Founder

**Description**: JWT signing key leak, OAuth secret rotation failure, or session token theft.

**Assessment**:
- **Probability**: 2
- **Impact**: 4 (account takeover; user trust damage)
- **Risk Score**: 8 (Medium)

**Triggers**: Suspicious sign-in patterns; secret-manager access alerts; OAuth provider compromise notification.

**Mitigation**:
- **Preventive**: Secrets in Google Secret Manager (not env files); JWT cookies are httpOnly + samesite=lax; OAuth redirect URIs locked to production hostname; Apple/Google client secrets rotated annually.
- **Contingency**: Rotate `AUTH_SECRET_KEY` (invalidates all sessions); force re-auth.
- **Fallback**: Disable OAuth login routes; revert to anonymous-only mode.

**Review**: Quarterly | **Next Review**: 2026-08-10

---

### RISK-006: B2C distribution failure (no users)
**Category**: Business
**Status**: Open
**Owner**: Founder

**Description**: We ship great mobile apps that nobody finds. Without organic discovery (App Store, search, partnerships), MAU stays in the hundreds.

**Assessment**:
- **Probability**: 4 (default outcome for indie apps)
- **Impact**: 4 (kills the B2C revenue path)
- **Risk Score**: 16 (High)

**Triggers**: <500 MAU at end of Q1 Y2; <2% landing-page → app conversion.

**Mitigation**:
- **Preventive**: SEO-friendly landing page with `/status` data dashboards; partnerships with watershed councils for co-distribution; cross-app links (RiverPath users see DeepTrail and vice versa).
- **Contingency**: Pivot focus to B2B if B2C doesn't take after 18 months.
- **Fallback**: Open-source the consumer apps as community projects; keep B2B closed.

**Review**: Quarterly | **Next Review**: 2026-08-10

---

### RISK-007: Apple/Google App Store policy mismatch
**Category**: Compliance
**Status**: Monitoring
**Owner**: Founder

**Description**: Apps are currently web-served PWAs. If we wrap into native iOS/Android, App Store review may flag privacy disclosure, sign-in mechanisms, or content policy.

**Assessment**:
- **Probability**: 3
- **Impact**: 3
- **Risk Score**: 9 (Medium)

**Triggers**: First native build submission; policy update from Apple/Google.

**Mitigation**:
- **Preventive**: Privacy policy in place; Apple Sign-In implemented (required if Google sign-in present in iOS app); Hide-My-Email forwarding endpoint registered.
- **Contingency**: Address review feedback; resubmit.
- **Fallback**: Stay PWA-only.

**Review**: Before any native submission

---

### RISK-008: Photo observation abuse (CSAM, doxxing, copyright)
**Category**: Compliance / Brand
**Status**: Open
**Owner**: Founder

**Description**: User-uploaded photos could include illegal content, sensitive locations (e.g., archaeological sites), or copyright-infringing material.

**Assessment**:
- **Probability**: 3 (any UGC platform)
- **Impact**: 4 (legal + brand)
- **Risk Score**: 12 (High)

**Triggers**: First user report; abuse pattern detection.

**Mitigation**:
- **Preventive**: Default-public posts but private option (FEAT-020); EXIF stripping before public display; ToS prohibits illegal/abusive content.
- **Contingency**: Manual takedown procedure; temporary suspension of new uploads.
- **Fallback**: Disable photo upload until automated moderation is in place.

**Review**: Monthly during early rollout | **Next Review**: 2026-06-10

---

### RISK-009: Cloud Run / Cloud SQL cost growth
**Category**: Operational
**Status**: Monitoring
**Owner**: Founder

**Description**: Cloud SQL is on `db-custom-2-4096` ($~$50/mo); Cloud Run min instances = 1 ($~$30/mo); plus VPC connector, GCS, scheduled jobs. Growth could push costs.

**Assessment**:
- **Probability**: 3
- **Impact**: 2
- **Risk Score**: 6 (Medium)

**Triggers**: Monthly bill >$200.

**Mitigation**:
- **Preventive**: Min instances tuned to traffic; Cloud SQL autoscaling within budget; cache headers on static assets; gold view materialization keeps queries cheap.
- **Contingency**: Right-size DB tier downward if utilization low.
- **Fallback**: Aggressive cost cuts, accept latency degradation.

**Review**: Monthly

---

### RISK-010: AI hallucination in user-facing narratives
**Category**: Brand / Quality
**Status**: Mitigating
**Owner**: Founder

**Description**: LLM-generated story or Q&A invents facts (wrong species, wrong dates, fictional restoration outcomes), eroding trust.

**Assessment**:
- **Probability**: 3
- **Impact**: 3
- **Risk Score**: 9 (Medium)

**Triggers**: First user-reported error; periodic spot-check finds inaccuracy.

**Mitigation**:
- **Preventive**: Retrieval-augmented prompts grounded in our warehouse; reading-level controls; quiz-and-review pattern for new content.
- **Contingency**: Add citations / "based on" attribution per story; user-flagging UI.
- **Fallback**: Take narrative card offline for affected watershed; review prompt template.

**Review**: Monthly

---

### RISK-011: Material schema change in upstream public data source
**Category**: Technical
**Status**: Open
**Owner**: Founder

**Description**: USGS, iNaturalist, etc. change API schemas — silently breaks our adapters, gold views go stale.

**Assessment**:
- **Probability**: 3
- **Impact**: 2
- **Risk Score**: 6 (Medium)

**Triggers**: Daily ingestion job failure; row-count drop alert.

**Mitigation**:
- **Preventive**: Each adapter has integration test against live API; schema-validation in adapters; daily cron failure alerts.
- **Contingency**: Patch adapter; backfill missed window from upstream history if available.
- **Fallback**: Mark source unhealthy on `/status`; notify users via in-app banner.

**Review**: Per ingestion failure

---

### RISK-012: Browser/device fragmentation breaks PWA
**Category**: Technical
**Status**: Monitoring
**Owner**: Founder

**Description**: iOS Safari quirks, Android Chrome differences, sticky-header behavior on mobile, EXIF read in iOS Safari.

**Assessment**:
- **Probability**: 4
- **Impact**: 1
- **Risk Score**: 4 (Low)

**Triggers**: User-reported visual bug; Playwright failure on mobile profile.

**Mitigation**:
- **Preventive**: Playwright tests on mobile viewports; manual QA on real iPhone/Android before each release.
- **Contingency**: Hotfix with rollback option.
- **Fallback**: Show message recommending different browser.

**Review**: Per release

## Closed Risks

| ID | Risk | Resolution | Date | Lessons Learned |
|----|------|------------|------|-----------------|
| (none yet) | — | — | — | — |

## Escalation Criteria

Escalate (= founder decision + investor/contractor consultation) when:
- Risk score reaches Critical (20+) — currently RISK-001 only.
- Mitigation fails — preventive controls bypassed.
- Risk impacts the production stability or compliance posture for >24h.
