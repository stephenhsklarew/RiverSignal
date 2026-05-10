---
dun:
  id: ADR-006
  depends_on:
    - helix.prd
    - helix.architecture
---
# ADR-006: Federated OAuth only; never store passwords

| Date | Status | Deciders | Related | Confidence |
|------|--------|----------|---------|------------|
| 2026-05-08 | Accepted | Founder | FEAT-019 | High |

## Context

| Aspect | Description |
|--------|-------------|
| Problem | We need to identify users to enable cross-device sync of saved items and photo observations. Building and maintaining a password store is a major liability — credential stuffing, reset flows, breach notification, etc. |
| Current State | OAuth providers (Google, Apple) handle billions of authentications safely. Apple Sign-In is required by the App Store if Google sign-in is offered in iOS apps. |
| Requirements | Sign-up must be one tap. We must never see or store a user's password. We must support both Google and Apple to satisfy Apple's iOS requirement and to give Apple-ecosystem users a privacy-preserving option (Hide-My-Email). |

## Decision

We support two sign-in methods only: Google OAuth 2.0 and Apple Sign-In. Both flows return us an issuer-signed identity claim, from which we extract a stable `provider_id` + email + display name. We issue our own JWT cookie (`rs_token`) for session management.

**Key Points**: No password fields anywhere | Apple Sign-In with optional email-relay (Hide-My-Email) supported | Stable `provider + provider_id` is the canonical user key, not email (which can change) | JWT signed with HS256 + secret in Secret Manager.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Email + password | Universal; no provider dependency | Credential management liability; reset flows; stuffing attacks; 2FA implementation | Rejected: too much surface for solo engineer |
| Email-only "magic links" | No passwords; common in 2024+ apps | Email deliverability flakiness; phishing-look-alike risk; no Apple App Store benefit | Rejected: extra infra (email service) for marginal UX |
| Single OAuth provider (Google only) | Simpler integration | App Store rejection if iOS app uses Google sign-in without Apple | Rejected: blocks iOS path |
| **Google + Apple OAuth** | One-tap sign-up; no passwords; Apple-ecosystem privacy; satisfies App Store rules | Two integrations to maintain; Apple's quirks (form_post callback, ES256 client_secret JWT) | **Selected: minimum viable identity surface** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | Zero password-related incident exposure; one-tap sign-up; Apple ecosystem users feel respected |
| Negative | Users without a Google or Apple account cannot sign in (estimated <2% of target audience); Apple's flow has unique quirks (form_post, client-secret JWT generation, Hide-My-Email forwarding) |
| Neutral | If we ever need to add a third provider (e.g., GitHub for B2B), the OAuth pattern is reusable |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| OAuth client secret leak | L | C | Stored in Secret Manager (ADR-003); rotated annually |
| Apple flow quirks break silently after Apple policy update | M | M | Pre-launch + quarterly verification; Apple developer portal email alerts |
| User loses access to their Google/Apple account | L | M | Document recovery procedure; not our problem to solve at scale |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| Sign-up completion rate ≥ 80% (drops at OAuth screen tracked) | Continuous |
| Zero password incidents (because there are no passwords) | Continuous |

## Concern Impact

- **Concern selection**: Selects `federated-auth-only` (security) — see `01-frame/concerns.md`.

## References

- `app/routers/auth.py` (OAuth implementations)
- `01-frame/security-requirements.md`
- `01-frame/threat-model.md` (TM-S-001, TM-S-003, TM-I-003)
