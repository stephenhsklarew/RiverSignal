---
dun:
  id: FEAT-019
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-019 -- Authentication & User Accounts

**Feature ID**: FEAT-019
**Status**: Implemented (spec retroactive)
**Priority**: P0
**Owner**: Core Engineering
**Date**: 2026-05-08

## Overview

Authentication system supporting Google and Apple OAuth2 login with JWT session cookies, anonymous-first architecture, and user profile management. Enables user-owned observations and personalized experiences while keeping all read endpoints accessible without authentication.

## Problem Statement

- **Current situation**: PRD FR-19/20/21 described email/password auth with multi-tenancy. The platform needed auth for photo observation ownership and user-specific features without blocking anonymous read access.
- **Desired outcome**: Frictionless OAuth2 login (Google/Apple), anonymous-first browsing, and user identity for write operations.

## Requirements

### Functional Requirements

#### FR-01: Google OAuth2 Login
- Google OAuth2 flow with redirect callback
- User record created in `users` table on first login
- Acceptance criteria: User clicks "Sign in with Google", completes OAuth flow, and is redirected back to the app with an active session

#### FR-02: Apple OAuth2 Login
- Apple OAuth2 flow with redirect callback
- Handles Apple's privacy relay email
- Acceptance criteria: User clicks "Sign in with Apple", completes OAuth flow, and is redirected back with an active session

#### FR-03: JWT Session Cookies
- JWT tokens stored in httpOnly cookies with 30-day expiry
- Tokens include user ID, email, and provider
- `/auth/me` endpoint returns current user profile
- `/auth/logout` clears the session cookie
- Acceptance criteria: Session persists across browser restarts for 30 days; logout clears all session state

#### FR-04: Anonymous User Tracking (rs_anonymous_id)
- Anonymous users receive a persistent anonymous ID (`rs_anonymous_id`) for client-side state
- All read API endpoints work without authentication
- Auth required only for write operations (photo submissions, future features)
- Acceptance criteria: Anonymous users can browse all content, view predictions, use chat; write endpoints return 401 without valid session

#### FR-05: Username Setup Flow
- Post-login flow for setting a display username
- `UsernameSetupPage` at `/setup-username`
- Username uniqueness validation
- Acceptance criteria: New users are prompted to choose a username after first OAuth login; username is displayed in UserMenu

#### FR-06: User Observation Ownership
- Photo observations are linked to the authenticated user's ID
- `/observations/mine` returns only the current user's observations
- Acceptance criteria: Submitted observations are attributed to the logged-in user; anonymous submissions are rejected

## Implementation Evidence

- `app/routers/auth.py` — Google/Apple OAuth2 endpoints, JWT cookie management
- `frontend/src/components/AuthContext.tsx` — React context for auth state
- `frontend/src/components/LoginModal.tsx` — OAuth login modal
- `frontend/src/components/UserMenu.tsx` — Authenticated user menu
- `frontend/src/pages/UsernameSetupPage.tsx` — Username setup flow

## Dependencies

- **External services**: Google OAuth2 API, Apple OAuth2 API
- **Other features**: FEAT-020 (photo observations require auth for ownership)
- **Infrastructure**: FEAT-018 (Secret Manager stores OAuth client secrets)

## Out of Scope

- Email/password authentication
- Multi-tenancy with organization workspaces (PRD FR-20/21 deferred)
- Role-based access control (viewer/analyst/manager/admin)
- Social features (following, profiles, activity feeds)
- Two-factor authentication

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Every functional requirement is testable
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes things someone might reasonably assume are in scope
