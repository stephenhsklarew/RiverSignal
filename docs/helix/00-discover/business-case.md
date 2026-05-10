# Business Case

## Executive Summary

Liquid Marble is a single data platform that powers three differentiated apps — RiverSignal (B2B watershed analytics), RiverPath (B2C river field companion), and DeepTrail (B2C rockhound adventure guide) — built on 30+ public scientific data sources unified via a medallion (bronze/silver/gold) Postgres warehouse. The investment ask covers continued development on a small-team basis (1–2 engineers) plus low-six-figures GCP and AI-API operating costs. Expected return is multi-tier: B2C mobile-app subscription/ads + B2B watershed-management SaaS licenses + dataset/API licensing to academic and agency partners.

## Opportunity Sizing

| Market Tier | Size | Calculation | Source |
|-------------|------|-------------|--------|
| TAM (Total) | ~$2.5B | US outdoor-recreation tech ($1.4B) + watershed-management SaaS ($600M) + geo-edutainment ($500M) | IBISWorld 2025; SAMHSA outdoor rec; market reports |
| SAM (Serviceable) | ~$180M | PNW + Utah anglers (~3M licensed) + 200 watershed councils + ~50 rockhounding orgs | ODFW/WDFW license counts; Pacific NW Watershed Council registry |
| SOM (Obtainable) | ~$3M @ 3y | 30k B2C users × $25/yr + 30 B2B accts × $25k/yr + 5 dataset licenses × $50k | Comparable freemium-mobile + agency-SaaS conversion |

**Key Assumptions**: Free tier drives 100k installs/yr; 5% paid conversion; B2B watershed councils and tribal/state agencies budget $10–50k/yr for analytics; AI-narrative cost ≤ $0.05/user/yr at scale (Anthropic prompt caching).

## Investment Required

| Category | Year 1 | Year 2 | Year 3 |
|----------|--------|--------|--------|
| Development (1.5 FTE) | $250k | $400k | $500k |
| Infrastructure (GCP) | $24k | $48k | $96k |
| AI APIs (Anthropic + OpenAI) | $12k | $30k | $60k |
| Go-to-Market | $20k | $80k | $200k |
| Operations / Compliance | $10k | $25k | $50k |
| **Total** | **$316k** | **$583k** | **$906k** |

## Expected ROI

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Revenue/Value | $40k | $400k | $1.6M |
| Costs | $316k | $583k | $906k |
| Net | -$276k | -$183k | +$694k |

**Breakeven**: ~Q3 Year 3 | **3-Year ROI**: ~25% on cumulative investment, with continuing recurring revenue tail and monetizable proprietary dataset.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Public data-source license restrictions (CC BY-NC, agency redistribution caps) | M | H | Provenance tracking per row; isolate non-commercial tiers; legal review of redistribution before B2B paid features |
| AI API cost runaway as audio/narrative usage grows | M | M | Aggressive prompt caching, narrative pre-generation in `gold.deep_time_story`, per-user rate limits |
| Single-engineer bus factor | H | H | Full Terraform infra, CI/CD on push, comprehensive HELIX docs, reproducible local dev |
| Data quality / hallucination in AI summaries | M | M | Verifiable citations; human-graded sample reviews each release; quiz-and-review pattern |
| Slow B2C consumer-app discovery without ad spend | H | M | SEO via `/status` data dashboards; cross-app linkages; partnership with watershed councils for distribution |

## Strategic Alignment

| Strategic Goal | How This Contributes |
|----------------|---------------------|
| Bring scientific watershed/geology data to non-experts | RiverPath + DeepTrail translate raw 8M-record datasets into stories, hatch charts, and rockhounding guides |
| Provide tools for restoration ecologists and conservation agencies | RiverSignal's analytics, predictive models (FEAT-017), and restoration outcomes pipeline |
| Build a defensible data moat | Curated unified medallion warehouse across 30+ sources is hard to replicate; predictive models trained on combined dataset are unique |

**Opportunity Cost**: Pursuing this means *not* pivoting the team into general-purpose ML consulting (the founder's day-job alternative). Estimated forgone consulting revenue ≈ $300k/yr at solo rate.

## Recommendation

**Decision**: Go

**Rationale**: The platform is already deployed to production with paying-pipeline-ready B2B prospects. Per-user variable costs are bounded by aggressive caching. The medallion data warehouse is the durable moat — competitors would need to re-ingest and reconcile 30+ sources to match. Three orthogonal monetization paths (B2C subscription, B2B SaaS, dataset licensing) reduce single-channel risk.

**Conditions**: None. Proceed with current scope; revisit if AI-API costs exceed $5/MAU or if Apple/Google compliance becomes a material blocker.
