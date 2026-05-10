# Feasibility Study: Liquid Marble Platform

**Decision Deadline**: N/A (project already in production)
**Status**: Retroactive — confirms feasibility of continued investment

## Executive Summary

### Project Overview

A unified data platform powering three connected apps (RiverSignal B2B, RiverPath B2C, DeepTrail B2C) over 30+ public scientific data sources. Already deployed to production on GCP since 2026-04. This document confirms continued feasibility for the next 12-month roadmap.

### Recommendation

**Overall Assessment**: FEASIBLE
**Decision**: GO — continue investment
**Rationale**: Production stack is live and stable; per-user variable costs are bounded; the 30-source medallion warehouse is a real moat; three orthogonal monetization paths reduce single-channel risk. The dominant risk (single-engineer bus factor) is mitigation-tractable via documentation and contractor retainer.

## Feasibility Assessment

### Technical
- **Assessment**: FEASIBLE
- **Key requirements**: FastAPI + Cloud Run (proven; running today); Cloud SQL Postgres ≤ db-custom-2-4096 ($50/mo) suffices for current load; React + Vite SPA (no SSR complexity); medallion view refresh on cron (working)
- **Main risks**: Bronze schema drift from upstream public APIs; AI cost growth; private VPC means we can't `cloud-sql-proxy` from a laptop without setup overhead

### Business
- **Assessment**: FEASIBLE
- **Market opportunity**: ~3M licensed PNW anglers + ~200 watershed councils + ~50k regional rockhounds. SAM ~$180M. SOM at 3 years ~$3M is achievable with 30k installs + 30 B2B accounts.
- **Value proposition**: Unified data + AI narrative + cross-domain (water × geology) is differentiated. No single competitor covers all three.

### Operational
- **Assessment**: FEASIBLE
- **Support and deployment needs**: Single founder operates the stack via GitHub Actions auto-deploy + Cloud Run. Runbooks are being formalized in `05-deploy/`. Monthly maintenance is light because most services are managed.
- **Regulatory requirements**: GDPR, CCPA, Apple/Google App Store policies, COPPA. None block; all are addressable with privacy policy + self-service deletion endpoint.

### Resource
- **Assessment**: FEASIBLE
- **Budget**: $316k Y1 / $583k Y2 / $906k Y3 (per `business-case.md`); breakeven Q3 Y3
- **Team and timeline**: 1.5 FTE through Y2; expand to 2.5 FTE in Y3. Solo-engineer bus factor mitigated via documentation + contractor retainer.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Single-engineer bus factor | High | High | HELIX docs + Terraform IaC + contractor retainer |
| AI cost runaway | Medium | Medium | Aggressive caching; daily budget alerts; circuit breaker |
| Public-data license drift | Medium | High | License flag per source; PR audit checklist |
| B2C distribution failure | High | Medium | Watershed council partnerships; SEO via `/status` |
| Production DB loss | Low | Critical | Cloud SQL automated backups + tested restore procedure |

## Alternatives

### Alternative: Single mobile app instead of three differentiated surfaces
- **Pros**: Lower UX complexity; single codepath
- **Cons**: Loses audience differentiation; B2B desktop ≠ B2C mobile UX; can't cross-promote
- **Feasibility**: Possible but inferior — would lose the "one platform, three apps" leverage

### Alternative: Stop AI narrative; revert to static text
- **Pros**: Eliminates Anthropic + OpenAI API costs entirely
- **Cons**: Loses primary differentiator; loses kid-engagement audio stories
- **Feasibility**: Technically trivial; product-wise a regression. Not recommended.

### Alternative: Open-source the platform; consulting business
- **Pros**: Distribution via OSS community; lower revenue ceiling but lower CAC
- **Cons**: Doesn't capture B2C subscription value; hard to monetize OSS
- **Feasibility**: Possible Plan B if B2C/B2B both fail to land in 18 months

## Next Steps

1. Continue current roadmap (Y1 deliverables in `prd.md`)
2. Address top operational risks: auto-EXIF strip (TM-I-002), AI rate limit (TM-D-001), self-service data deletion (compliance)
3. Begin B2B partnerships in Q3 (watershed councils as design partners)
4. Re-evaluate at end of Q1 Y2 against MAU + B2B-pipeline targets in `business-case.md`
