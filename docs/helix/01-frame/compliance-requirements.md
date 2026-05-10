# Compliance Requirements

**Project**: Liquid Marble (RiverSignal / RiverPath / DeepTrail)
**Compliance Risk Level**: Medium
**Date**: 2026-05-10

## Executive Summary

**Applicable Regulations**: GDPR (EU users via web), CCPA/CPRA (California users), Apple App Store Privacy, Google Play Privacy, COPPA (since the product targets families/kids in DeepTrail), CC BY-NC (iNaturalist photos).

**Compliance Scope**: Authentication and user accounts (FEAT-019), photo observations (FEAT-020), saved favorites (FEAT-016), AI narrative caching with user inputs, and any data we redistribute via the API or B2B reports.

**Key Requirements**:
1. Anonymous-first usage (no PII collected without sign-in).
2. CC BY-NC content (primarily iNaturalist photos) is excluded from B2B paid features.
3. User photo observations honor public/private visibility throughout the data plane.
4. Apple Sign-In is offered on platforms where Google Sign-In is offered (Apple App Store policy 4.8).
5. Privacy policy + data subject rights endpoints.

## Applicable Regulations

### GDPR (General Data Protection Regulation, EU)
- **Jurisdiction**: EU and EEA users accessing the public web app
- **Applicability**: We collect email/name/avatar via OAuth and store user-generated photo observations. Even with EU traffic anonymous, sign-in collects PII.
- **Key Requirements**: Lawful basis for processing (Art. 6); transparency (Art. 13); data subject rights — access, rectification, erasure, portability (Art. 15–20); breach notification within 72h (Art. 33); records of processing (Art. 30).
- **Penalties**: Up to €20M or 4% of global turnover.
- **Timeline**: Continuous.

### CCPA / CPRA (California Consumer Privacy Act)
- **Jurisdiction**: California residents
- **Applicability**: Same as GDPR for our use case (collect email, photos, saved items).
- **Key Requirements**: Privacy notice; right to know, delete, opt-out of sale (we don't sell), correct, limit use of sensitive PI; equal service regardless of opt-out.
- **Penalties**: $2,500 per violation; $7,500 per intentional/minor violation.
- **Timeline**: Continuous.

### Apple App Store Review Guidelines (when published as iOS app)
- **Jurisdiction**: Anywhere we publish to App Store
- **Applicability**: Required if we ship a native iOS app wrapping the PWA.
- **Key Requirements**: Privacy nutrition labels (Section 5.1); Apple Sign-In equality (4.8); Hide-My-Email forwarding domain registration; data minimization.
- **Penalties**: App rejection; account termination.
- **Timeline**: Pre-launch + each submission.

### Google Play Developer Program Policies
- **Jurisdiction**: Anywhere we publish to Play Store
- **Applicability**: Required if we ship a native Android app.
- **Key Requirements**: Data Safety section disclosures; sensitive permissions justification; minor protection.
- **Penalties**: Listing removal; account termination.
- **Timeline**: Pre-launch + each submission.

### COPPA (Children's Online Privacy Protection Act)
- **Jurisdiction**: US users under 13
- **Applicability**: DeepTrail explicitly targets families with kids (kid reading-level narratives). RiverPath similarly.
- **Key Requirements**: Don't knowingly collect PII from children under 13 without verifiable parental consent. Currently we don't ask for age — anonymous-first protects us, but we should add an age gate before any kid-explicit data collection.
- **Penalties**: Up to $51,744 per violation.
- **Timeline**: Continuous.

### Industry Standards

#### CC BY-NC 4.0 (iNaturalist research-grade observations)
- **Scope**: All images and observation records sourced from iNaturalist
- **Certification Required**: No, but compliance expected
- **Key Controls**: Attribution to iNaturalist + observer; non-commercial use only; share-alike for derivatives

#### Public Domain (USGS, NOAA, BLM, MTBS, NHDPlus, etc.)
- **Scope**: Most federal datasets
- **Certification Required**: No
- **Key Controls**: Attribution recommended, no use restrictions

#### CC BY 4.0 (Macrostrat, PBDB)
- **Scope**: Geologic units, fossil occurrences
- **Certification Required**: No
- **Key Controls**: Attribution required

## Compliance Requirements Matrix

| Requirement | Reference | Description | Implementation | Owner | Status |
|-------------|-----------|-------------|----------------|-------|--------|
| Lawful basis for processing PII | GDPR Art. 6 | Identify and document basis for each data processing activity | OAuth-driven user accounts: consent (Art. 6(1)(a)). Photo observations: contract performance (Art. 6(1)(b)). | Founder | Documented here; needs privacy policy page on site |
| Transparency | GDPR Art. 13 | Inform users at collection time | Privacy policy linked from sign-up modal | Founder | TODO |
| Data subject access right | GDPR Art. 15 | Users can request copy of their data | `/auth/me` returns user record; need full export endpoint | Founder | Partial — endpoint TODO |
| Data subject erasure right | GDPR Art. 17 | Users can request deletion | Need DELETE /auth/me endpoint that removes user, observations, saved items | Founder | TODO |
| Data subject portability | GDPR Art. 20 | Export in machine-readable format | JSON export of user data | Founder | TODO |
| Breach notification | GDPR Art. 33 | 72h notification to supervisory authority | Incident response runbook | Founder | TODO (see 05-deploy) |
| Records of processing | GDPR Art. 30 | Maintain records of processing activities | This document + data inventory in `01-frame/` | Founder | Initial draft (this doc) |
| iNaturalist attribution | CC BY-NC | Every iNat photo must show observer + license | License tag in observation responses (`license: "CC BY-NC"`); UI badge | Founder | Implemented |
| iNaturalist non-commercial | CC BY-NC | Don't surface CC BY-NC data in paid B2B features | `commercial: false` flag in source meta gates paid surfaces | Founder | Partial — needs B2B feature audit |
| Apple Sign-In parity | App Store 4.8 | Required if Google sign-in present in iOS app | Both Google and Apple OAuth are implemented | Founder | Implemented |
| COPPA — no PII from <13 without consent | COPPA | Default-anonymous; if we add age, require verified parental consent | Currently anonymous-first by default | Founder | Compliant by design |
| Privacy nutrition labels (App Store) | App Store 5.1 | Disclose categories of data collected | Required pre-iOS-launch | Founder | TODO |

## Data Classification and Handling

| Data Type | Classification | Regulations | Handling Requirements |
|-----------|----------------|-------------|----------------------|
| User email | PII (identifying) | GDPR, CCPA | Encrypted at rest (Cloud SQL default); not logged; not surfaced to other users |
| OAuth provider_id | PII | GDPR, CCPA | Same as email |
| User display name + avatar URL | PII (low) | GDPR, CCPA | Visible in UI; minimization not required |
| User photo observation (public) | UGC | Platform terms | Public by default with opt-out; EXIF GPS stripped before public display |
| User photo observation (private) | UGC + sensitivity | GDPR, CCPA | Filtered out of all public surfaces; never indexed |
| Anonymous_id (localStorage) | Pseudonymous identifier | GDPR | Not PII unless linked; deletable by clearing browser data |
| iNat observation photos | Third-party PII (observer) | CC BY-NC, GDPR | Always credited; never modified; non-commercial gate |
| Stream gauge / SNOTEL data | Public domain | None | No restrictions |
| Restoration project data | Public records | None | No restrictions |

### Data Retention

| Data Type | Retention Period | Legal Basis | Disposal Method |
|-----------|------------------|-------------|-----------------|
| User account | Until deletion request or 3 years inactivity | Consent | Hard delete from `users`, soft from `user_observations` (anonymize) |
| Photo observations | Until user deletes or account deleted | Consent | Hard delete from GCS + DB row |
| Anonymous_id | 1 year (browser localStorage) | Legitimate interest | Auto-expires, user can clear |
| Audit logs (sign-in events) | 90 days | Legitimate interest (security) | Cloud Logging retention |
| AI narrative cache | Indefinite (regenerated when underlying data changes) | Operational | Cache invalidation on data refresh |
| Cloud SQL backups | 14 days | Operational | Cloud SQL automated retention |

## Privacy Requirements

### Data Subject Rights

| Right | Implementation | Response Time |
|-------|----------------|---------------|
| Access | `/auth/me` returns user record; full export endpoint TODO | 30 days |
| Rectification | Editable username via `/auth/username`; full edit endpoint TODO | 30 days |
| Erasure | Manual delete via founder; self-service endpoint TODO | 30 days |
| Portability | JSON export via API; UI button TODO | 30 days |
| Restriction | TODO — need a "freeze" flag on user record | 30 days |
| Object | TODO — need opt-out from non-essential processing | 30 days |
| Withdraw consent | Sign out clears session; full data delete via Erasure | Immediate / 30 days |

### Privacy Impact Assessment

| Activity | Data | Purpose | Legal Basis | Risk Level |
|----------|------|---------|-------------|------------|
| OAuth sign-in | Email, name, provider_id | Account identification | Consent | Low |
| Photo observation upload (public) | Image, EXIF (location optional) | UGC platform feature | Contract | Medium (if GPS not stripped) |
| Photo observation upload (private) | Image, full EXIF | Personal use | Contract | Low (filtered from public) |
| AI narrative generation | Lat/lon (anonymous, no user link) | Feature delivery | Legitimate interest | Low |
| Saved items (anonymous) | localStorage only | Personalization | Legitimate interest | Low |
| Saved items (authenticated) | DB row linked to user | Cross-device sync | Contract | Low |

## Incident Response and Reporting

### Breach Notification Requirements

| Regulation | Authority Notification | Individual Notification | Timeline |
|------------|----------------------|------------------------|----------|
| GDPR | Yes — to supervisory authority | If "high risk" to rights | 72h to authority; without undue delay to users |
| CCPA | None to authority (but California AG enforcement); | Yes if unencrypted PI compromised | "Most expedient time possible" |
| Apple Sign-In | Apple Developer email if their auth flow is affected | n/a | Immediate |

See `05-deploy/incident-response-runbook.md` for procedure.

## Compliance Risk Assessment

| Risk | Impact | Likelihood | Risk Level | Mitigation |
|------|--------|------------|------------|------------|
| CC BY-NC content surfaced in paid B2B feature | High | Medium | High | Source meta `commercial: false` gates B2B surfaces; pre-release audit |
| Missing privacy policy at sign-up | Medium | Currently true | High | Write + publish privacy policy page; link from auth modal |
| Photo observation EXIF GPS leak | High | Medium | High | Server-side EXIF strip before public display |
| User asks for data deletion, no self-service | Medium | Medium | Medium | Manual delete works; build self-service endpoint within 90 days |
| iOS App Store rejection on privacy disclosure | Medium | Possible | Medium | Privacy nutrition labels prepared before submission |
| Children under 13 sign in | Medium | Possible | Medium | Anonymous-first means we don't collect PII without sign-in. Pre-iOS, add age gate or assert "13+" in ToS |

## Implementation Plan

- [x] Document regulatory applicability (this file)
- [x] Source license metadata in `app/routers/status.py`
- [x] Apple Sign-In implemented alongside Google
- [x] Anonymous-first default (FEAT-019)
- [ ] Publish privacy policy page (e.g., `/privacy`)
- [ ] Self-service data export endpoint (`GET /auth/export`)
- [ ] Self-service account deletion endpoint (`DELETE /auth/me`)
- [ ] EXIF GPS stripping for public photo observations
- [ ] Audit B2B paid surfaces for CC BY-NC content
- [ ] Privacy nutrition labels for iOS submission
- [ ] Incident response runbook in `05-deploy/`
- [ ] Annual review of source license terms
