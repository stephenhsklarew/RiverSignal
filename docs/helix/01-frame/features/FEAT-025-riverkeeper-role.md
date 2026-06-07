---
dun:
  id: FEAT-025
  depends_on:
    - helix.prd
    - FEAT-019
    - FEAT-023
    - FEAT-024
---
# Feature Specification: FEAT-025 -- Riverkeeper Role (per-watershed content stewardship)

**Feature ID**: FEAT-025
**Status**: Specified
**Priority**: P2
**Owner**: Core Engineering
**Date**: 2026-06-07

## Overview

A **Riverkeeper** is a scoped content-admin role: a signed-in user assigned to one or
more watersheds who can curate **only those watersheds'** content (splash card, river
story, fish photos, insect photos), and is accountable for the quality and accuracy of
that content. It sits between the anonymous/regular user (read + own observations) and
the global `is_admin` (edit anything). Access-control design of record:
`02-design/plan-2026-06-07-riverkeeper-access-control.md`. Role concept + rationale:
`00-discover/riverkeeper-role.md`.

## Problem Statement

- **Current situation**: The `/admin` content tools (FEAT-023/024) are gated by a single
  global `is_admin` flag — all-or-nothing. There is no way to let a trusted local steward
  edit *their* watershed without granting platform-wide admin.
- **Desired outcome**: Grant a person edit rights to specific watersheds only, so content
  quality scales to many watersheds via the people closest to each river, with least
  privilege and a clear per-watershed accountability owner.

## Requirements

### Functional Requirements

#### FR-01: Per-watershed assignment
- A Riverkeeper is assigned ≥1 watershed; a watershed may have ≥1 Riverkeeper
  (many-to-many). Assignments are revocable and effective immediately (checked live, not
  baked into the JWT).
- Acceptance criteria: granting `(user, watershed)` lets that user edit that watershed's
  content within one request; revoking removes the ability immediately.

#### FR-02: Scoped authorization on content endpoints
- The watershed-scoped admin writes — `PUT/DELETE /admin/watershed-splash/{ws}` (+ `/image`),
  `PUT /admin/river-stories/{ws}/{level}` (+ regenerate-audio), `PUT/DELETE
  /admin/curated-photos/{species_key}?watershed=<ws>`, and the insect equivalents —
  succeed when the caller is a global admin **or** a Riverkeeper of that watershed; else 403.
- Acceptance criteria: a Riverkeeper of `clinch_river_va` can edit Clinch content and gets
  403 editing `deschutes`; a global admin can edit both.

#### FR-03: Global defaults stay admin-only
- Curating the global default photo set (`watershed='*'`) and any cross-watershed/list or
  search endpoints remain `is_admin`-only.
- Acceptance criteria: a Riverkeeper editing `watershed='*'` gets 403.

#### FR-04: Grant / revoke (admin-only)
- `POST /admin/riverkeepers` (assign `{user_id|email, watershed}`) and `DELETE
  /admin/riverkeepers/{id}` (revoke); `GET /admin/riverkeepers` lists assignments. All
  `is_admin`-only. Riverkeepers cannot grant other Riverkeepers.
- Acceptance criteria: only `is_admin` can grant/revoke; the action is audit-logged with actor.

#### FR-05: Frontend gating
- `/auth/me` returns the caller's `is_admin` + `riverkeeper_watersheds[]`. `AdminRoute`
  admits global admins and users with ≥1 assignment. The `/admin/photos` watershed picker
  shows **all** watersheds for a global admin and **only assigned** watersheds for a
  Riverkeeper; non-assigned watersheds are not editable.
- Acceptance criteria: a Riverkeeper sees only their watershed(s) in `/admin/photos`; a
  non-admin, non-keeper is redirected as today.

#### FR-06: Attribution + audit
- Every content write records the acting user (existing `*_log` audit tables already carry
  `changed_by_user_id`); no change loses the actor.
- Acceptance criteria: an audit row exists per write naming the Riverkeeper who made it.

### Non-Functional Requirements

- **Least privilege**: a Riverkeeper can do nothing outside their assigned watersheds.
- **Immediate revocation**: authorization is checked live per request (like `is_admin`),
  never cached in the JWT.
- **No new product surface**: reuses the existing `/admin` UI (FEAT-023/024); only the
  visible/editable set narrows.

## Implementation Evidence

*(Specified — not yet built.)* Will touch: a `riverkeeper_assignments` table (new
migration), `app/lib/admin_auth.py` (new scoped dependency + `assert_can_edit_watershed`),
the watershed-scoped handlers in `app/routers/admin.py`, `/auth/me` in `app/routers/auth.py`,
and `frontend/src/components/AdminRoute.tsx` + `AdminPhotosPage.tsx` + `AuthContext.tsx`.

## Dependencies

- **Features**: FEAT-019 (auth/identity), FEAT-023 + FEAT-024 (the content tools being scoped)
- **Concerns/ADRs**: ADR-006 (federated auth — Riverkeepers sign in via OAuth); proposes a
  new authorization decision (recommend promoting the design to ADR-010 on acceptance)

## Out of Scope

- Capabilities beyond content curation (fish/stocking verification, observation moderation,
  stewardship posts, dashboard) — see `00-discover/riverkeeper-role.md` roadmap; future FEATs
- Self-service Riverkeeper application/onboarding flow (invitation-only for early adopters)
- A general RBAC system (this is one scoped role, intentionally minimal — extensible later)
- Riverkeepers editing global defaults or other watersheds

## Review Checklist

- [x] Overview connects to a PRD requirement (content quality at scale; trust-the-user)
- [x] Every functional requirement is testable
- [x] Non-functional requirements stated (least privilege, immediate revocation)
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes reasonable assumptions (future capabilities, RBAC, self-serve)
