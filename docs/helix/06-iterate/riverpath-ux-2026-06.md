# Iterate log: RiverPath UX batch — June 2026

**Date**: 2026-06-05
**Surface**: RiverPath B2C (`/path`) — FEAT-012, FEAT-016, FEAT-020, FEAT-021, FEAT-022
**Status**: Shipped to production (GCP Cloud Run, single image serving API + SPA)

Backfill record for a run of RiverPath fixes/enhancements that shipped without individual
Helix design notes. Captures what shipped, the PRs, and verification so 02-design / 06-iterate
reflect production. Design detail for the account-sync work is in
`02-design/plan-2026-06-05-saved-items-account-sync.md`; shared collections extend
`02-design/plan-2026-05-10-trip-share.md`.

## What shipped

| PR | Summary |
|----|---------|
| **#38** | RiverPath batch #1–#6: Notifications subscribed-state (vs "no alerts"); all UI temps °C→°F; "# species" → "Species observed" + tooltip; Time Machine renders when enabled (graceful "needs more history"); river-story OpenAI TTS audio (39 mp3s); **shared Saved collections** (24h link, `shared_collections` table `sc01a1b2c3d4`, recipient banner). |
| **#39** | River-story audio mismatch fix — audited all 39 mp3s (Whisper transcription vs narrative), 24/39 were stale; regenerated all from canonical narratives. °C compare-table fix reached users via SW cache bump `v4→v5`. Share observations (with private-warning). Removed hardcoded `/path` watershed nav. |
| **#40** | Shared observations render on the Saved map (recipient, even logged-out). River-story scroll-to-top on page turn (first attempt — window scroll). |
| **#41** | Real story page-turn fix: reset the **inner** `.rnow-story-text` scroll box to top (the prior window-scroll did nothing visible). SW cache `v5→v6`. |
| **#42** | Shared-items banner "sign in" is a clickable link → opens `LoginModal`; OAuth returns to `/path/saved` where `keepShared()` makes items permanent. |
| **this PR** | Saved **account sync** (cross-device `saved_items` table `sv01a1b2c3d4`); shared observations keep original **photographer + source + observed + visibility**, shown on the detail screen. SW cache `v6→v7`. |

## Key decisions
- **°C → °F deltas** convert with the scale factor only (×9/5, no +32 offset) — the "What Changed" card delta was a server-built string in `/replay` (`ai_features.py`).
- **PWA staleness**: behavior-changing deploys bump `frontend/public/sw.js` `CACHE_NAME` to force-evict active clients (documented in that file).
- **Shared observations are bookmarks, not ownership** — never written to `user_observations`; attribution + privacy travel in the snapshot payload.
- **Private observations**: shareable per the owner's choice ("all, but warn on private"); the recipient's copy keeps `private` visibility and shows it on the detail screen.

## Verification
- `tests/test_riverpath_fixes.py` (pytest) — share create/resolve/expire, audio_url present, saved-items 401 + authed round-trip + attribution.
- `tests/riverpath-fixes.spec.ts` + `tests/riverpath-story-scroll.spec.ts` (Playwright) — °F, species label, Time Machine, shared link/observation lands + renders, photographer + private visibility on detail, story inner-scroll reset.
- River-story audio re-audited post-fix: 39/39 transcript-vs-narrative match.

## Follow-ups
- Cross-device logged-in merge verified manually on staging (OAuth session can't run headless).
- Logout does not clear local saved items (existing behavior).
