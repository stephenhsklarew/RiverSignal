# Research Plan: Liquid Marble user discovery + technical validation

**Research Lead**: Stephen Sklarew
**Time Budget**: 8 weeks (rolling, parallelized with development)
**Created**: 2026-05-10
**Status**: Draft

## Research Objectives

### Primary Research Questions

1. **Question**: Do PNW anglers find RiverPath useful enough to use weekly during fishing season?
   - **Why Important**: B2C subscription path depends on weekly engagement, not occasional use
   - **Success Criteria**: ≥3 sessions/week per active user during May–September 2026 from 20+ recruited testers

2. **Question**: Do watershed councils trust the RiverSignal restoration outcomes data enough to use it in funder reports?
   - **Why Important**: B2B revenue depends on trust in the data; replacing internal Excel is the wedge
   - **Success Criteria**: 3+ pilot councils incorporate RiverSignal output in at least one Q3 funder report

3. **Question**: Do families with kids (8–14) find DeepTrail's audio narratives engaging on real road trips?
   - **Why Important**: Kid engagement is the unique angle; if it doesn't land, audio TTS investment isn't justified
   - **Success Criteria**: ≥4/5 average kid-engagement rating from 10 family observation sessions

4. **Question**: What is our actual per-MAU AI cost at scale?
   - **Why Important**: Determines pricing floor and circuit-breaker thresholds
   - **Success Criteria**: Cost-per-MAU stays below $0.05 with current caching strategy at 1k MAU

### Knowledge Gaps

| Gap | Impact | Current Confidence |
|-----|--------|--------------------|
| Real-world weekly engagement curve for B2C anglers | High | Low (no production users yet) |
| Watershed-council willingness to pay for RiverSignal | High | Low (no formal sales calls) |
| iNaturalist data freshness vs user expectations | Medium | Medium (we ingest daily but don't measure perception) |
| AI narrative perceived accuracy by domain experts | High | Medium (founder QA only) |
| Mobile network performance on backcountry data | Medium | Low (works on wifi; untested 3G/no-signal) |
| iOS app review path for Liquid Marble | Medium | Low |

## Scope

**In Scope**:
- User interviews and observation sessions (RiverPath, DeepTrail)
- B2B prospect calls with 5+ watershed councils
- Cost telemetry from production (Cloud Run logs, Anthropic/OpenAI billing)
- Hallway-test usability sessions for landing page and `/status`
- Domain-expert review of AI narratives (geologist, fly-fishing guide, restoration ecologist)

**Out of Scope**:
- Quantitative survey of national outdoor-rec market (deferred to Y2 if we expand beyond PNW)
- A/B testing of pricing tiers (premature — first need product-market fit signal)
- Native iOS/Android performance research (PWA is the current ship)

**Assumptions**:
- We can recruit 20 anglers via PNW fly-fishing forums and personal network
- We have warm intros to ≥3 watershed councils
- Founder time is the limiting factor, not budget

## Research Methods

### B2C user diary (RiverPath, RiverPath Saturday)
- **Objective**: Q1 (weekly engagement)
- **Approach**: Recruit 20 anglers, give them the app, ask for a weekly photo + 1-paragraph note for 12 weeks
- **Participants/Sources**: PNW fly-fishing forums, Reddit r/flyfishing, personal network
- **Duration**: 12 weeks (May 15 – Aug 15)
- **Deliverable**: Synthesis report with weekly engagement curve, retention drop-off, top feature requests

### B2B discovery interviews (Restoration Councils)
- **Objective**: Q2 (B2B trust)
- **Approach**: 30-min calls with watershed council staff; demo + 5 open-ended questions
- **Participants/Sources**: 5 PNW councils (intro via personal network)
- **Duration**: 4 weeks
- **Deliverable**: Customer-development findings, willingness-to-pay benchmarks, top objections

### Family observation sessions (DeepTrail)
- **Objective**: Q3 (kid engagement)
- **Approach**: 10 in-person sessions: family takes a 1-hour hike with the app; observe + post-interview
- **Participants/Sources**: Personal network of friends with kids 8–14
- **Duration**: 6 weeks
- **Deliverable**: Engagement scoring, story-quality feedback, audio length preferences

### Production cost telemetry
- **Objective**: Q4 (AI cost-per-MAU)
- **Approach**: Daily roll-up of Cloud Run logs + Anthropic/OpenAI billing into a spreadsheet; correlate with MAU from `auth_events` (TODO)
- **Participants/Sources**: Production usage
- **Duration**: Continuous
- **Deliverable**: Monthly cost-per-MAU dashboard; circuit-breaker threshold proposal

### Domain-expert AI narrative review
- **Objective**: Validate AI-grounded narrative accuracy
- **Approach**: Recruit 1 geologist (PNW Cascades), 1 fly-fishing guide (McKenzie), 1 restoration ecologist; have each review 20 random narratives + Q&A flows
- **Participants/Sources**: Personal network + paid honoraria ($300/expert)
- **Duration**: 2 weeks
- **Deliverable**: Accuracy scoring (1–5 per narrative); list of common error categories; prompt improvement backlog

### Hallway tests
- **Objective**: Surface obvious UX/copy issues
- **Approach**: 20-min sessions with 5 random outdoor-curious people; think-aloud through landing → app
- **Participants/Sources**: Personal network
- **Duration**: 2 weeks
- **Deliverable**: Top 10 friction points

## Timeline

| Phase | Duration | Activities | Deliverables |
|-------|----------|------------|--------------|
| Planning | Week 1 | Recruit testers; finalize interview scripts; set up cost dashboard | Tester list, scripts, dashboard URL |
| Investigation | Weeks 2–10 | Run all six methods in parallel | Raw data per method |
| Analysis | Weeks 9–11 (overlap) | Synthesize per question | Per-question findings |
| Validation | Week 12 | Stakeholder review (founder + advisors); update PRD/roadmap | Updated roadmap |

**Total Duration**: 12 weeks

## Research Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low recruit response (B2C anglers) | Medium | Medium | Offer Amazon gift card for completion; tap multiple forums |
| Watershed councils don't return calls | Medium | High | Use warm intros; shift to async written feedback if needed |
| Domain experts disagree on accuracy criteria | Low | Low | Standardize rubric upfront; founder reconciles |
| Cost telemetry blocked by missing instrumentation | Medium | Medium | Add `request.user_id` + `cost_estimate` log fields before research start |

## Completion Criteria
- [ ] All four research questions answered with evidence
- [ ] Findings documented and reviewed by founder
- [ ] Recommendations actionable (concrete PRD/roadmap changes)
- [ ] Updated `prd.md` and `feature-registry.md` reflect findings
