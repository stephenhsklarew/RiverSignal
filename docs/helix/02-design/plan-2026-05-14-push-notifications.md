# Design Plan: Push Notifications for Watershed Conditions

**Date**: 2026-05-14
**Status**: SUPERSEDED 2026-05-15 by `plan-2026-05-15-sms-alerts.md`
**Refinement Rounds**: 3 (solo)
**Scope**: Deliver phone-level push notifications and home-screen badges to RiverPath users when a metric (initially Trip Quality Score) crosses a configurable threshold for one of their watched watersheds.

> **Supersession note (2026-05-15)**: After working through opt-in friction and iOS install-cliff concerns, this plan was retired in favor of an SMS-first alert channel. Web Push adoption is fundamentally capped by permission-grant rates (5–15%) and iOS PWA-install friction; SMS via Telnyx delivers the same outcome at meaningful cost but vastly higher reach (95%+ open rates) and intuitive UX (phone-number opt-in matches what consumers expect). See `plan-2026-05-15-sms-alerts.md` for the replacement design.

> Sections marked **OPEN FORK** are decision points to work through collaboratively, mirroring the trip-share and metric-history plans. The "Recommendation" inside each fork is my current lean — not a locked decision.

## Problem Statement

Trip Quality Score is RiverPath's headline composite metric: it summarizes fishing conditions per watershed and shifts daily with water temp, flow, hatch activity, and stocking. Users today learn about a great-conditions day only when they open the app. The window between "conditions are great" and "user notices conditions are great" is the window we're paid in if the app is the trip-planning surface.

Two adjacent constraints make push the right channel rather than email/SMS:

- **Phone-top placement is the moment of intent**. An angler picking up their phone Friday morning is in trip-planning headspace; an email in their inbox isn't.
- **Already-mobile-first**. RiverPath is mobile-first; users are already on the phones we want to ping. iOS 16.4+ and all modern Android browsers support Web Push from PWAs.

Today: there's no out-of-app notification channel at all. The `/alerts` endpoint surfaces in-app badges via `BottomNav` polling every 60 seconds when the app is open. We want **out-of-app** delivery — phone-top banner, lockscreen, home-screen badge — so users don't have to be in the app to know.

## Requirements

### Functional

#### F1. User opt-in & subscription management
1. From any RiverPath surface (probably `/path/saved` or a new `/path/settings`), authenticated users can tap "Get alerts on my phone."
2. Browser prompts for notification permission. If granted, frontend registers a `PushSubscription` via `navigator.serviceWorker.ready.then(reg => reg.pushManager.subscribe(...))`.
3. Frontend POSTs the subscription (endpoint + p256dh + auth keys) to the backend `POST /api/v1/push/subscriptions` along with the watersheds the user wants notifications for.
4. User can view their active subscriptions across devices ("iPhone — Safari", "MacBook — Chrome") and revoke any individually.
5. User can pause notifications globally (mute) without removing subscriptions.
6. Browser-side unsubscribe (user revokes notification permission outside the app) is detected on next app open and the corresponding subscription is marked inactive.

#### F2. Watched-watersheds & thresholds
7. A user can mark any of the supported watersheds as "watched" — independent from saved items (see fork OF-3).
8. For each watched watershed × metric combo, a notification rule defines:
   - threshold (e.g., `>= 80` for Trip Quality "good and above")
   - direction (`crossing_up`, `crossing_down`, or `at_or_above`)
   - active days / hours of day (so notifications don't fire at 2 AM unless user opted in)
9. MVP metric: **Trip Quality Score only**. Extensible to: Hatch Confidence, Snowpack changes, Fire perimeter near saved spot, Stocking event near a watched watershed (see OF-7).

#### F3. Dispatch pipeline
10. After each daily snapshot job (from the metric-history plan), a new "notification dispatcher" job:
    - Queries `notification_rules` for matches against today's new snapshots.
    - Applies dedup: don't fire the same rule again within `notification_rules.cooldown_hours` (default 24h).
    - Posts a VAPID-signed push message to each user's active `push_subscriptions` for the matched watershed.
11. Push payload includes a deep link (`/path/now/<watershed>?n=<rule_id>`) so taps open straight to the relevant content with notification provenance.
12. Failed pushes (410 Gone, 404 Not Found from the push service) mark the subscription inactive and stop retrying it.
13. Each fired notification is logged to `notification_events` for observability and to enable "notification history" in the UI.

#### F4. iOS install nudge
14. iOS Safari only supports Web Push for **installed** PWAs ("Add to Home Screen"). When a user on iOS Safari tries to enable notifications and the app isn't installed, show a sheet explaining how to add to home screen, with a screenshot/animation.
15. Track install-prompt → install completion with PostHog to size the iOS friction.
16. Don't show the prompt more than once per 7 days unless user explicitly tries to enable again.

#### F5. App-icon badge (App Badging API)
17. In addition to push, set the home-screen badge count (`navigator.setAppBadge(unseenAlertCount)`) so the icon shows a numeric badge when there are unread alerts.
18. Clear badge (`navigator.clearAppBadge()`) when user opens the app or reads alerts.

### Non-Functional

- **Dispatch latency**: a snapshot completing at 03:05 PT should result in pushes delivered by 03:10 PT (within 5 minutes).
- **Dispatch throughput**: support 10,000 subscribers per metric snapshot without timing out the dispatcher job (Cloud Run Job, 30-min timeout).
- **Push delivery reliability**: 99% of pushes to active subscriptions delivered within 1 minute of dispatch (we don't control the push services themselves; this is a delivery-to-push-service SLO, not delivery-to-device).
- **Subscription churn handling**: stale subscriptions are pruned within 24h of first 410 response.
- **Cost**: zero ongoing third-party cost (DIY Web Push); only Cloud Run dispatcher runtime.

### Constraints

- Service worker is already in place (`public/sw.js` v3, network-first for HTML, cache-first for assets, stale-while-revalidate for API).
- Add a `push` event handler to `sw.js`; no architectural rewrite required.
- VAPID keys stored as Secret Manager secrets (`vapid-public-key`, `vapid-private-key`); generated once via a one-off script.
- All push delivery uses standard Web Push protocol — no Firebase SDK, no OneSignal SDK, no third-party tags in the page.
- iOS support is **PWA-installed only**. We accept the cliff and instrument it.

## Architecture Decisions

### AD-1: Build vs. buy — DIY Web Push vs. third-party

- **Question**: Use a third-party push provider (OneSignal, FCM, Pusher Beams) or implement Web Push ourselves?
- **Alternatives**:
  - **A1: DIY Web Push** — generate VAPID keys, store subscriptions ourselves, use `pywebpush` to dispatch.
    - Pros: zero third-party data sharing; matches platform ethos of owned data; no additional bundle weight; no per-subscriber cost; single billing surface (GCP only).
    - Cons: more code; we own retry/backoff/key-rotation logic; pruning stale subscriptions is on us.
  - **A2: OneSignal** — drop in their SDK on frontend, store opaque user-handle, call their REST API for dispatch.
    - Pros: ships in 1–2 days; handles SDK, retries, segmentation; free up to 10k subs.
    - Cons: bundle weight (~30 KB); third-party JS in our page (analytics, cookies); subscriber data lives on their infra; lock-in to their data model.
  - **A3: Firebase Cloud Messaging (FCM)** — Google's push relay, free.
    - Pros: free, robust, well-documented; on iOS works just like Web Push.
    - Cons: requires Firebase SDK + GCP project setup; another auth surface; somewhat-deprecated in favor of newer Web Push (FCM v1 API is still recommended).
- **Chosen (provisional)**: **A1 (DIY Web Push)** behind a clean dispatcher interface that could be swapped to A2/A3 later.
- **Rationale**: DIY is roughly a week of focused work and gives full data ownership, which matches the platform's strong preference (curated data sources, owned AI integration, no third-party scripts). The dispatcher pattern is simple enough that "build it" is not a hidden trap.

### AD-2: How are watched watersheds modeled?

- **OPEN FORK (OF-3).**
- **Question**: What defines a user's "watched" watershed?
- **Alternatives**:
  - **B1: Explicit watch-list** — user adds watersheds to a watch list separately from saved items.
    - Pros: clean separation; user controls notification scope precisely; supports "watch but don't save anything specific."
    - Cons: another UI surface to maintain; users have to remember to add watersheds.
  - **B2: Inferred from saved items** — if you've saved anything in a watershed, you're watching it.
    - Pros: zero extra UI; auto-discoverable; "you saved a fly here = you care about here."
    - Cons: doesn't support "I'm planning a trip to a new river" before saving anything; harder to mute one watershed while keeping its saved items.
  - **B3: Hybrid** — saved items implicitly opt-in, plus an explicit "Also watch [other watershed]" option in settings.
    - Pros: best of both; default works for engaged users, manual control for explicit cases.
    - Cons: two truth sources.
- **My recommendation**: **B3** with B2 as the strong default. Most users will never touch the "also watch" surface and that's fine; the rare power user gets the affordance.

### AD-3: Threshold UX — system bands vs. user-defined

- **OPEN FORK (OF-4).**
- **Question**: Does the user pick the threshold value or do we offer named bands?
- **Alternatives**:
  - **C1: Named bands** — `Excellent (≥80)`, `Good and up (≥60)`, `Any change`. User picks one of three.
    - Pros: simple UX; bounded surface; aligns with existing "level" categorization (excellent/good/fair/poor) shown on Catch Probability.
    - Cons: less precision.
  - **C2: Free-form threshold** — user picks any number 0–100.
    - Pros: maximum precision.
    - Cons: power-user feature; most users don't know what number to pick.
  - **C3: Smart default with override** — system default is `≥80` (Excellent); a small "Customize" affordance reveals a slider.
    - Pros: zero-friction for the common case; power-users have an escape.
    - Cons: slightly more UI.
- **My recommendation**: **C1 (named bands)** for MVP. Slider can come later.

### AD-4: Cooldown window per rule

- **Question**: How long do we wait before firing the same rule again?
- **Alternatives**:
  - 24 hours: most natural; one notification per day per rule per watershed.
  - 7 days: very conservative; risks missing real changes for a week.
  - User-configurable: extra UI for marginal benefit.
- **Chosen**: **24h default, user can extend to 7d** if they find it noisy. Configurable per rule, not just globally.

### AD-5: Notification fatigue protection

- We deliberately *limit* concurrent rules per user: max **5 active rules** per user across all watersheds and metrics. If they want to enable a 6th, prompt to disable one first.
- We dedup at the **(user, rule, day)** level — multiple matches for the same rule in one day collapse to one notification.
- A "quiet hours" window (default 9 PM – 7 AM local) suppresses all pushes; held messages are dropped, not queued, to avoid morning floods.
- Each notification includes a one-tap "Mute this rule for 30 days" link.

### AD-6: Multi-device handling

- A user with iPhone + iPad + desktop Chrome registers three subscriptions; all three get notified. No deduplication at the device level — that's the user's job (and most platforms handle "I'm online here, dismiss elsewhere" themselves via OS-level sync).
- A subscription that returns 410 Gone is marked inactive immediately; deleted after 30 days.
- Browser-side "this subscription expired" is detected next time the user opens the app via the existing service worker `pushsubscriptionchange` event; we re-subscribe and POST the new subscription to backend, transparently to the user.

### AD-7: Notification surface in-app

- Each fired notification is also written to the existing `/alerts` surface (the `AlertsPage` shown in `BottomNav`).
- This gives a *history* view: "you missed these 4 notifications while your phone was off / offline / muted."
- It also gives users a way to **review** what they were pushed without digging through their notification shade.

### AD-8: Should we support notification *types* beyond Trip Quality?

- **OPEN FORK (OF-7).**
- **Question**: MVP launches with Trip Quality only. Which metrics get added next, and is there a phasing decision worth making now?
- **Possible types**:
  - Trip Quality Score crossing threshold (MVP, Phase 1)
  - Hatch Confidence rising for a watched watershed
  - Stocking event scheduled for a watched watershed in next 7 days
  - Live USGS gauge data: dramatic flow spike (>30% in 24h), temperature crossing fishing-comfort thresholds
  - Wildfire perimeter expanding near a saved location
  - Restoration project status change near a watched watershed
- **My recommendation**: **Trip Quality only in Phase 1**. The dispatcher architecture is metric-agnostic; new types are pure backend additions (rule type + scoring function + payload template). Hatch Confidence and Live Conditions are obvious Phase 2 candidates because they hook into existing surfaces. Fire and Restoration deserve their own scope discussion.

## Interface Contracts

### REST endpoints

```
POST   /api/v1/push/subscriptions
  Body: { endpoint, keys: { p256dh, auth }, user_agent, watersheds: [...] }
  Auth: required
  Returns: { id, created_at }
  201 on new, 200 on existing endpoint (refresh keys)

GET    /api/v1/push/subscriptions
  Auth: required
  Returns: [{ id, user_agent, created_at, last_used_at, active }]

DELETE /api/v1/push/subscriptions/:id
  Auth: required, owner only

GET    /api/v1/push/rules
PUT    /api/v1/push/rules/:id
POST   /api/v1/push/rules
DELETE /api/v1/push/rules/:id
  Auth: required
  Rule body: { watershed, metric_type, threshold, direction, cooldown_hours, quiet_hours_start, quiet_hours_end, active }

POST   /api/v1/push/test
  Auth: required
  Sends a test notification to user's most-recent subscription.
  Useful for debugging "did I actually grant permission?"

GET    /api/v1/alerts (existing)
  Extended: now also returns push-fired notifications, not just in-app ones.
```

### Frontend types (TS)

```ts
type PushSubscriptionInfo = {
  id: string
  user_agent: string        // truncated, e.g. "iPhone — Safari"
  created_at: string
  last_used_at: string | null
  active: boolean
}

type NotificationRule = {
  id: string
  watershed: string
  metric_type: 'trip_quality_score' | 'hatch_confidence' | ...
  threshold: number
  direction: 'crossing_up' | 'crossing_down' | 'at_or_above'
  cooldown_hours: number    // default 24
  quiet_hours_start: number // hour-of-day, 0-23, default 21
  quiet_hours_end: number   // default 7
  active: boolean
}

type NotificationPayload = {
  title: string         // "Deschutes is excellent today"
  body: string          // "Trip Quality Score reached 85 (Excellent)"
  watershed: string
  rule_id: string
  url: string           // "/path/now/deschutes?n=<rule_id>"
  tag: string           // "rule:<rule_id>" — replaces older notifications for same rule
}
```

### Service worker (`sw.js`) additions

```js
self.addEventListener('push', (event) => {
  if (!event.data) return
  const payload = event.data.json()
  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      tag: payload.tag,
      icon: '/favicon-riverpath.svg',
      badge: '/favicon-riverpath.svg',
      data: { url: payload.url, rule_id: payload.rule_id },
    }).then(() => {
      // Update home-screen badge count too.
      if ('setAppBadge' in self.navigator) {
        // Increment is fiddly without state; fetch fresh count from server instead.
        return fetch('/api/v1/alerts/unseen-count', { credentials: 'include' })
          .then(r => r.json())
          .then(d => self.navigator.setAppBadge?.(d.count))
          .catch(() => {})
      }
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/path/now'
  event.waitUntil(self.clients.openWindow(url))
})

self.addEventListener('pushsubscriptionchange', (event) => {
  // Re-subscribe and POST new subscription to backend.
  event.waitUntil(/* re-subscribe + POST */)
})
```

## Data Model

```sql
CREATE TABLE push_subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint        TEXT NOT NULL,
    p256dh_key      TEXT NOT NULL,
    auth_key        TEXT NOT NULL,
    user_agent      TEXT,
    active          BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at    TIMESTAMPTZ,
    UNIQUE (user_id, endpoint)
);
CREATE INDEX ix_push_subscriptions_user ON push_subscriptions(user_id) WHERE active;
CREATE INDEX ix_push_subscriptions_active ON push_subscriptions(active);

CREATE TABLE notification_rules (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    watershed         VARCHAR(32) NOT NULL,
    metric_type       VARCHAR(64) NOT NULL,
    threshold         NUMERIC NOT NULL,
    direction         VARCHAR(16) NOT NULL DEFAULT 'at_or_above',
    cooldown_hours    INTEGER NOT NULL DEFAULT 24,
    quiet_hours_start INTEGER NOT NULL DEFAULT 21,
    quiet_hours_end   INTEGER NOT NULL DEFAULT 7,
    active            BOOLEAN NOT NULL DEFAULT true,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_fired_at     TIMESTAMPTZ,
    UNIQUE (user_id, watershed, metric_type, threshold, direction)
);
CREATE INDEX ix_notification_rules_lookup
  ON notification_rules(watershed, metric_type, active);
-- Enforce per-user cap (max 5 active rules) at app level, not DB.

CREATE TABLE notification_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rule_id         UUID NOT NULL REFERENCES notification_rules(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES push_subscriptions(id) ON DELETE SET NULL,
    watershed       VARCHAR(32) NOT NULL,
    metric_type     VARCHAR(64) NOT NULL,
    metric_value    NUMERIC,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivery_status VARCHAR(16) NOT NULL,  -- 'sent' | 'failed' | 'gone' (410) | 'unauthorized' (403)
    seen_in_app_at  TIMESTAMPTZ
);
CREATE INDEX ix_notification_events_user_recent
  ON notification_events(user_id, sent_at DESC);
```

## Error Handling

| Class | Examples | Strategy |
|---|---|---|
| Push service returns 410 Gone | subscription expired / user revoked permission | mark subscription inactive immediately; do not retry |
| Push service returns 404 / 403 | endpoint URL invalid or unauthorized | same — mark inactive; alert if many in burst (key rotation needed?) |
| Push service 5xx | transient push-service outage | retry with exponential backoff up to 3 attempts; if all fail, log and move on; do NOT mark inactive |
| VAPID signing failure | misconfig or key rotation issue | dispatcher fails fast; alerts ops; nothing sent that hour |
| Rule fired during quiet hours | matched but in 9 PM–7 AM window | record event with status='suppressed_quiet_hours'; don't push |
| User over 5-rule cap creates 6th | UI should prevent, backend enforces | return 422 with `"max_rules_exceeded"` |
| Subscription POST has invalid keys | malformed crypto material | return 422; don't store |

## Security

- **VAPID private key** lives in Secret Manager (`vapid-private-key`); read by the dispatcher at startup. Public key is bundled in the frontend.
- **Subscription endpoint URLs are sensitive** — they grant the bearer the ability to send pushes to the user's device. Treat like a credential: serve over HTTPS only, never log raw, never expose to non-owner.
- **Rule changes require auth** — same session cookie as the rest of the app.
- **Test endpoint** (`POST /api/v1/push/test`) is rate-limited to 3 per minute per user.
- **No tracking pixels or third-party scripts** — DIY architecture means no analytics SDKs in our push path.
- **Privacy footer in subscription UI**: "We send notifications to your phone using your browser's standard push service (FCM, APNS, Mozilla autopush). We never share your subscription with third parties."

## Test Strategy

### Unit
- VAPID signing: given a fixed payload + private key, signature matches expected.
- Rule matching: given a snapshot and a list of rules, returns the expected matches; cooldown filter works; quiet-hours filter works.
- Dispatcher: dry-run mode produces correct payloads without calling out.

### Integration
- End-to-end subscription: register → POST → row stored; service worker receives push (use `web-push-cli` in CI to send to a test endpoint).
- 410 handling: simulate a 410 from a mock push endpoint; verify subscription marked inactive.
- Dedup: rule fires once for a given day even when multiple snapshots match.
- Quiet hours: rule fires at 8 AM but suppressed at 11 PM.

### Manual / E2E
- Real-device test on iPhone (PWA-installed) and Android Chrome.
- Verify app-icon badge appears and clears.
- Verify deep link routing from notification tap.

## Implementation Plan

### Dependency graph

```
Phase 0 (foundation)
├── VAPID keypair generation script + Secret Manager seeding
├── Alembic migration: push_subscriptions + notification_rules + notification_events
└── Service worker push event handler + push event tests

Phase 1 (subscription flow)
├── Frontend: opt-in UI on /path/settings or /path/saved
├── Frontend: iOS "Add to Home Screen" sheet
├── POST /push/subscriptions endpoint
├── GET / DELETE /push/subscriptions endpoints
└── Per-device list view ("iPhone — Safari", revoke buttons)

Phase 2 (rule configuration UI)
├── Rule CRUD endpoints
├── Frontend: "Notify me when..." sheet with watershed picker + metric picker + threshold band
├── Per-user 5-rule cap enforcement
└── Quiet hours selector

Phase 3 (dispatcher + delivery)
├── Background job triggered after metric_snapshots run
├── Rule-matching query
├── Dispatcher service: pywebpush + retry logic
├── notification_events recording
├── Stale subscription pruning
└── Cloud Run Job + Cloud Scheduler

Phase 4 (in-app surfacing)
├── /alerts: include push-fired events
├── App Badging API integration
├── "Mark all seen" affordance
└── PostHog events: subscription_created, notification_sent, notification_clicked
```

### Suggested HELIX issues

1. **Schema migration**: 3 tables + indexes. AC: alembic upgrade head succeeds.
2. **VAPID key generation script**: one-off `pipeline/scripts/generate_vapid_keys.py`. AC: outputs to Secret Manager; public key documented for frontend.
3. **Service worker push handler**: extend `sw.js` for `push`, `notificationclick`, `pushsubscriptionchange`. AC: showNotification fires; tap opens deep link.
4. **Subscription API + frontend opt-in flow**. AC: end-to-end test from "Enable notifications" tap → subscription stored.
5. **iOS install nudge component**. AC: detects iOS Safari + non-installed PWA; shows AddToHomeScreen sheet; tracked in PostHog.
6. **Notification rule CRUD + UI sheet**. AC: max 5 rules enforced; quiet hours configurable.
7. **Dispatcher job** (`pipeline/notification_dispatcher.py`). AC: runs after snapshot job; sends pushes; records events; prunes stale subs.
8. **Cloud Run Job + scheduler wiring** (terraform). AC: scheduled, runs daily after snapshot.
9. **App Badging API integration**. AC: badge appears on PWA icon when there are unread alerts; clears when read.
10. **Notification history in /alerts page**. AC: shows push-fired events alongside in-app alerts.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| iOS users won't install PWA → push feels broken | H | M | Install nudge sheet; track install completion rate; document the constraint clearly in UI copy |
| Stale subscriptions accumulate, slow down dispatcher | M | L | Mark inactive on 410; delete after 30 days; daily prune in dispatcher itself |
| VAPID key rotation accident | L | H | Rotate key only deliberately; new subs use new key; old subs continue with old key during 30d transition window |
| Notification fatigue → user disables permission | M | M | 5-rule cap; 24h cooldown; quiet hours; per-rule mute affordance in notification |
| Dispatcher takes longer than 30min as user count grows | L (now), M (later) | M | Batch push calls (sendAsync, parallel HTTP); migrate to Cloud Run service with queue if dispatcher exceeds job timeout |
| Push service URL leak | L | M | TLS everywhere; never log raw endpoints; rate-limit subscription endpoint to prevent enumeration |

## Observability

- **PostHog events**:
  - `push.subscription.created` (platform, browser, watersheds_count)
  - `push.subscription.revoked` (age_days)
  - `push.permission.requested` / `push.permission.granted` / `push.permission.denied`
  - `push.ios.install_prompt_shown` / `push.ios.install_completed`
  - `push.notification.sent` (rule_id_hash, latency_ms)
  - `push.notification.clicked` (rule_id_hash)
  - `push.rule.created` / `push.rule.muted`
- **Cloud Logging**: structured JSON with notification_id, rule_id, delivery_status.
- **Cloud Monitoring alert**: dispatcher job failure rate > 10% over 1 hour.
- **Weekly cost report**: dispatcher job runtime + push service requests (free but useful to track).

## Open Forks (for collaborative review)

1. **OF-1 Build vs. buy** (AD-1): provisional DIY, recommend confirming before committing to ~1 week of build.
2. **OF-2 iOS install nudge** (F4): how aggressive — modal blocker, in-context tooltip, or background banner?
3. **OF-3 Watched-watershed model** (AD-2): explicit watch-list, inferred from saves, or hybrid?
4. **OF-4 Threshold UX** (AD-3): named bands or slider?
5. **OF-5 Cooldown window** (AD-4): 24h is my lean; could be 12h, 48h, or fully user-controlled.
6. **OF-6 Notification fatigue** (AD-5): 5-rule cap is arbitrary; could be 3 or 10.
7. **OF-7 Phase 2 metric types** (AD-8): which metrics are next after Trip Quality?
8. **OF-8 Watered-down preview mode**: should users be able to "test" a rule by simulating a snapshot crossing the threshold, to verify the notification works without waiting for real conditions?

## Governing Artifacts

- **PRD**: `docs/helix/01-frame/prd.md`
- **FEAT-007 Fishing Intelligence**: Trip Quality Score is the headline metric this feature alerts on.
- **FEAT-016 Saved & Favorites**: AD-2 references the saved-items model for inferred watching.
- **plan-2026-05-10-metric-history.md**: snapshot pipeline is the upstream that this design's dispatcher hooks into. Phases here assume that plan's Phase 1 ships first.
- **plan-2026-05-10-trip-share.md**: independent; both touch user preferences UI surface.
- **Architecture**: `docs/helix/02-design/architecture.md` — adds a "Notifications & Push" subsection.

## Refinement Log

- **Round 1** (initial): the four-table data model, dispatcher architecture, service worker extensions.
- **Round 2**: iOS install constraint surfaced as a primary risk; added install-nudge UX as F4; added App Badging API; added quiet hours + cooldown semantics.
- **Round 3**: added Open Forks section; integrated metric-history plan as the upstream dependency; observability + cost section; risk register; added test endpoint for self-service debugging.
