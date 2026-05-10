# Stakeholder Map

**Status**: Draft
**Last Updated**: 2026-05-10

## Primary Stakeholders (High Influence, High Interest)

### Founder / Solo Engineer (Stephen Sklarew, Synaptiq)
- **Role**: Builder, owner, sole decision-maker on technical and product direction
- **Interest**: Ship a useful, defensible platform; monetize via three orthogonal channels (B2C, B2B, dataset)
- **Influence**: Total — controls scope, design, deploy
- **Concerns**: Time/budget runway; AI cost runaway; bus factor; finding non-engineering channels (sales, partnerships)
- **Success Criteria**: Production stays up; B2B revenue arrives by Q3 Y3; the data moat compounds
- **Communication**: Direct (this document)

### End Users — RiverPath (anglers, families)
- **Role**: Primary B2C audience for `/path` mobile app
- **Interest**: Better fishing trips; reliable real-time conditions; engaging stories for kids
- **Influence**: Voting with their feet — installs, retention, word-of-mouth
- **Concerns**: Battery drain; data accuracy; offline use; iOS/Android parity
- **Success Criteria**: Open the app at the river, get a useful answer in under 30 seconds

### End Users — DeepTrail (rockhounds, geo-curious families)
- **Role**: Primary B2C audience for `/trail` mobile app
- **Interest**: Find legal collecting sites; understand what they're looking at; engaging audio stories on hikes
- **Influence**: Niche but vocal; rockhounding clubs are tight-knit
- **Concerns**: Site legality accuracy (digging on BLM vs private vs designated wilderness); image quality of fossils
- **Success Criteria**: Discover a site they didn't know about; understand the geology they're standing on

### B2B Customers — Watershed Councils, Restoration NGOs, State/Tribal Agencies
- **Role**: Primary B2B audience for RiverSignal
- **Interest**: Integrated analytics; defensible decisions; funder reporting
- **Influence**: Direct revenue; reference accounts shape product
- **Concerns**: Data trustworthiness; legal/redistribution constraints; long procurement cycles
- **Success Criteria**: Replace 2–3 internal tools; produce funder reports faster

## Secondary Stakeholders (Variable Influence/Interest)

### Data Source Providers (USGS, NOAA, iNaturalist, Macrostrat, etc.)
- **Role**: Origin of all bronze-layer data
- **Interest**: Their data being used and credited; not being abused (rate limits, redistribution)
- **Influence**: Could rate-limit or restrict; legal exposure if licenses violated
- **Engagement Level**: Inform (we cite them; we comply with TOS)

### iNaturalist Community
- **Role**: Largest single source of citizen-science species observations (CC BY-NC)
- **Interest**: Their photos and observations being credited; non-commercial use respected
- **Influence**: Brand-level — disrespecting their license tarnishes trust
- **Engagement Level**: Inform (license badges visible; commercial features won't surface CC BY-NC data)

### Apple / Google (Sign-in providers)
- **Role**: Identity gateway
- **Interest**: Compliance with their auth/privacy policies
- **Influence**: Could revoke OAuth client access
- **Engagement Level**: Inform (compliant configuration; respond to policy updates)

### GCP (Google Cloud)
- **Role**: All infrastructure
- **Interest**: Account in good standing
- **Influence**: Could suspend service for billing/policy issues
- **Engagement Level**: Inform (billing alerts, IAM hygiene)

### Anthropic / OpenAI (AI providers)
- **Role**: LLM and TTS API
- **Interest**: Account in good standing; usage limits
- **Influence**: Cost per token / per minute of audio; rate limits
- **Engagement Level**: Inform (cache aggressively; monitor cost)

## RACI Matrix

| Activity / Decision | Founder | Users (B2C) | Customers (B2B) | Data Sources | Cloud / AI Vendors |
|---------------------|---------|-------------|-----------------|--------------|--------------------|
| Project Vision | A/R | C (signal) | C (signal) | I | I |
| Feature Prioritization | A/R | C (feedback) | C (deals) | I | I |
| Technical Architecture | A/R | I | I | I | I |
| Schema / Data Model | A/R | I | C (B2B reporting) | I | I |
| Release Decision | A/R | I | I | I | I |
| Pricing | A/R | C | C | I | I |
| Compliance Posture | A/R | I | C | C | C |

**R** = Responsible | **A** = Accountable | **C** = Consulted | **I** = Informed

## Power/Interest Grid

```
High Power  | Keep Satisfied         | Manage Closely
            | - GCP                  | - Founder
            | - Apple/Google         | - B2B Customers
            |------------------------|---------------------
Low Power   | Monitor                | Keep Informed
            | - Anthropic/OpenAI     | - B2C Users
            | - Data Source Provs    | - iNat Community
            Low Interest             High Interest
```

## Communication Plan

| Stakeholder Group | Channel | Frequency | Content | Owner |
|-------------------|---------|-----------|---------|-------|
| Founder | Self / planning docs | Continuous | Roadmap, costs, decisions | Founder |
| B2C Users | In-app / blog / `/status` | On launch + monthly | New features, data freshness | Founder |
| B2B Customers | Email / Slack | Weekly during pilot, monthly steady | Status, issues, releases | Founder |
| Data Source Providers | TOS compliance + attribution in product | Continuous | License badges, source citations | Founder |
| Apple / Google | Developer console + email | When required | Privacy disclosures, OAuth changes | Founder |
| GCP | Billing dashboard + alerts | Continuous | Cost guardrails | Founder |

### Escalation Path
Bus-factor mitigation: solo engineer. Mitigation is documentation (HELIX docs, ADRs) and reproducible infra (Terraform, Docker). No internal escalation chain; external escalation goes through Synaptiq legal/billing for vendor disputes.
