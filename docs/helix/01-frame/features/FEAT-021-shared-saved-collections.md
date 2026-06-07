---
dun:
  id: FEAT-021
  depends_on:
    - helix.prd
    - FEAT-016
    - FEAT-019
---
# Feature Specification: FEAT-021 -- Shared Saved Collections

**Feature ID**: FEAT-021
**Status**: Implemented (spec retroactive)
**Priority**: P1
**Owner**: Core Engineering
**Date**: 2026-06-05

## Overview

A RiverPath user can share their Saved items for a watershed via a link that
anyone can open for 24 hours. The recipient sees the shared items land in their
own Saved area (client-side, expiring) until they sign in to keep them
permanently. Backed by a `shared_collections` table (migration `sc01a1b2c3d4`)
with a random token and a 24h TTL.

## Problem Statement

- **Current situation**: Saved items (FEAT-016) lived only on one device with no
  way to share a curated set (species, flies, reaches, recreation, observations)
  with a friend or trip group.
- **Desired outcome**: A one-tap share link lets a sender hand a curated Saved set
  to a recipient, who can preview it and optionally keep it.

## Requirements

### Functional Requirements

#### FR-01: Create a share link
- `POST /saved/share` snapshots the chosen items + sections into a row with a
  `secrets.token_urlsafe` token and `expires_at = now + 24h`; returns
  `{token, url: /path/shared/<token>, expires_at, item_count}`.
- Anonymous users can share (owner_user_id nullable).
- Acceptance criteria: posting a non-empty item set returns a token + URL; an
  empty set returns 400; the row carries a 24h expiry.

#### FR-02: Resolve a share link (public)
- `GET /saved/shared/{token}` returns the snapshot if `expires_at > now()`, else
  404 (the message does not distinguish "expired" from "never existed").
- Acceptance criteria: a valid token returns watershed + items; a bogus or expired
  token returns 404 with a friendly message.

#### FR-03: Recipient ingest + banner
- `SharedCollectionPage` (`/path/shared/:token`) fetches the snapshot, drops the
  items into the recipient's Saved flagged `shared` + `expiresAt` (24h), sets the
  selected watershed, and redirects to `/path/saved?shared=1`.
- A banner shows "📬 N shared items added to your Saved" with a **sign in** link
  to keep them; signing in runs `keepShared()` (see FEAT-022).
- Acceptance criteria: opening the link lands the items in Saved with the banner;
  the sign-in link opens the login modal and returns the user to Saved.

#### FR-04: Observation sharing with privacy warning
- Shared observations carry the original photographer + visibility (see FEAT-022).
- If the link includes private observations, the share modal warns the sender
  before they copy it.
- Acceptance criteria: a link containing a private observation surfaces a warning
  in the modal.

### Non-Functional Requirements

- **TTL**: links expire exactly 24h after creation; expired rows resolve to 404.
- **Cap**: at most 500 items per share (400 otherwise).

## Implementation Evidence

- `app/routers/saved_share.py` — POST /saved/share, GET /saved/shared/{token}
- `alembic/versions/sc01a1b2c3d4_shared_saved_collections.py` — `shared_collections` table
- `frontend/src/pages/SharedCollectionPage.tsx`, `frontend/src/pages/SavedPage.tsx`,
  `frontend/src/components/SavedContext.tsx` (`addShared`, `keepShared`)
- Tests: `tests/test_riverpath_fixes.py`, `tests/riverpath-fixes.spec.ts` (#6/#6b/#6c)

## Dependencies

- **Features**: FEAT-016 (Saved Favorites), FEAT-019 (auth for "keep permanently"),
  FEAT-022 (account sync persists kept items)
- **Data**: `shared_collections` table

## Out of Scope

- Editing a shared collection after creation (links are immutable snapshots)
- Re-sharing a received collection
- Notifying the sender when a recipient opens the link

## Review Checklist

- [x] Overview connects to a PRD requirement (B2C sharing / story over schema)
- [x] Every functional requirement is testable
- [x] Non-functional requirements have numeric targets (24h, 500 items)
- [x] Dependencies reference real artifact IDs
- [x] Out of scope excludes reasonable assumptions
