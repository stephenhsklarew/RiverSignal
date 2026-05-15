# Design Plan: SMS Alerts for Trip Quality Score Thresholds

**Date**: 2026-05-15
**Status**: DRAFT (pre-collaborative review)
**Refinement Rounds**: 3 (solo)
**Supersedes**: `plan-2026-05-14-push-notifications.md`
**Scope**: Send time-sensitive SMS alerts to opted-in users when the Trip Quality Score for one of their explicitly-watched watersheds is forecast to cross a "fishable" threshold within the next 3 days. Includes per-watershed opt-in, anti-spam dispatch rules, and prepaid-budget caps.

## Problem Statement

RiverSignal's TripQualityCard reports the current TQS for a watershed and exposes a 14-day forecast modal. Users planning weekend trips need to know when conditions will be *good* without having to open the app — but the prior plan's choice of Web Push runs into two hard ceilings:

1. **iOS Safari requires PWA install** before any push notifications work — most iOS users don't know this exists. Realistically blocks 60–80% of the iPhone audience.
2. **Web Push opt-in rates** sit at 5–15% of users prompted in industry data. Once blocked, users rarely re-enable.

SMS solves both:
- Universal reach: every smartphone with cell service, no install
- ~95% open rates, often within 5 minutes
- Phone-number entry conveys intent and durability in a way "Allow notifications?" does not
- Two-factor verification flow is well-understood by users

Cost is the only meaningful tradeoff vs. Web Push, and at RiverSignal's likely scale (hundreds-to-low-thousands of opted-in users), it stays under a few hundred dollars per month.

A separate concern: **a Virginia user shouldn't get alerts about Washington watersheds unless they explicitly opt in to those**. The watch model must be per-watershed, not per-account.

## Requirements

### Functional

#### F1. Per-watershed opt-in flow
1. User taps the `🔔 Alerts` chip on the TQS card for any watershed.
2. If they haven't yet verified a phone number, prompt for one + 6-digit OTP verification (Telnyx Verify).
3. After verification, present the current watershed pre-selected plus a multi-select list of all other supported watersheds the user can add. Default: only the current watershed is checked.
4. User confirms; subscriptions are persisted as `(user_id, watershed)` rows.
5. From any other watershed's TQS card, tapping `🔔 Alerts` opens the same sheet — phone already verified, just lets them check/uncheck additional watersheds.
6. Settings page at `/path/settings/alerts` shows all current subscriptions with toggle to disable per-watershed or globally.

#### F2. Contextual nudge in the forecast modal
7. When the 14-day forecast modal opens and *any* day within the next 7 days has `tqs >= 80` (Excellent), display a one-line banner at the modal header: *"Want a heads-up when conditions hit Excellent? Get a text →"*
8. Tapping the banner opens the same opt-in flow as F1, pre-checking the watershed in view.
9. Banner doesn't appear if user already has an active subscription for that watershed.
10. PostHog event tracks contextual-nudge impressions vs. click-throughs.

#### F3. Alert dispatcher
11. Daily Cloud Run Job runs at **06:00 PT** (single batch).
12. For every active subscription `(user, watershed)`, query the next 3 days of forecast rows in `gold.trip_quality_daily`.
13. Match conditions: a forecast day has `tqs >= 80` (excellent threshold) AND `confidence != 'low'`.
14. Per-(user, watershed, target_date) cooldown of **48 hours** — once we've alerted user X about watershed Y's Saturday forecast, we won't alert them again about that specific target_date for 48h, even if subsequent forecasts continue to match.
15. Per-user weekly cap: **maximum 3 SMS per rolling 7 days** regardless of how many subscriptions match.
16. Quiet hours: no SMS dispatched if user's local time is between **9 PM and 8 AM**. Held messages are dropped, not queued.
17. Digest mode: when a single dispatcher run matches multiple watersheds for one user, combine into a single SMS body (counts as one alert toward the weekly cap):
    - Single match: *"Deschutes is forecast Excellent for Saturday (TQS 85). Open RiverSignal: <short link>"*
    - Multi-match: *"Excellent conditions this weekend: Deschutes Sat (85), Metolius Sun (82). Open RiverSignal: <short link>"*

#### F4. Reply handling
18. STOP / STOPALL → globally unsubscribe the phone number from all RiverSignal SMS. Required by carrier regulations.
19. HELP → respond with the support URL and a one-line description.
20. Any other inbound text is logged but not auto-responded.

#### F5. Budget caps (defense in depth)
21. **Carrier prepay**: Telnyx account holds a prepaid balance. When it hits zero, sends fail at the carrier layer. No auto-recharge.
22. **App-level daily cap**: configurable `MAX_SMS_PER_DAY` env var (default 500). Dispatcher checks remaining day-budget before each send; stops dispatching when exhausted.
23. **App-level monthly cap**: `MAX_SMS_PER_MONTH` env var (default 5000). Same enforcement pattern.
24. Both caps are tracked in a small `sms_send_log` table with cheap aggregation queries.

### Non-Functional

- **Dispatcher latency**: alerts delivered within 5 minutes of the 06:00 PT trigger.
- **Verification UX**: OTP code delivered within 30 seconds of phone-number entry.
- **Idempotency**: re-running the dispatcher for the same date is a no-op (cooldown table prevents re-sends).
- **PII**: phone numbers encrypted at rest (Postgres `pgcrypto` or app-level AES); never logged in plain text.
- **Compliance**: A2P 10DLC campaign registered with Telnyx; HELP/STOP/STOPALL implemented; consent record stored.

### Constraints

- SMS via **Telnyx** (chosen over Twilio on cost + dashboard for prepay UX).
- One-shot dispatcher (no per-event push). Once-per-day batch is sufficient for trip planning.
- US phone numbers only at MVP. International is a separate plan if/when needed.

## Architecture Decisions

### AD-1: Channel selection — SMS only

- **Question**: SMS only, or SMS + optional Web Push?
- **Chosen**: **SMS only for MVP.** Drop Web Push entirely. Reconsider later if a measurable cohort of users explicitly asks for desktop browser badging.
- **Rationale**: Each additional channel multiplies dispatcher complexity (per-channel rate limits, per-channel preferences, per-channel failure handling) for marginal incremental reach. SMS alone covers ≥95% of the smartphone audience. The 5–15% of users who'd opt into both is small enough that the simplification pays for itself.

### AD-2: Per-watershed opt-in — explicit subscription list

- **Question**: Should opting in to alerts default to all watersheds, the current watershed only, or require explicit per-watershed selection?
- **Chosen**: **Explicit per-watershed.** New opt-in flow defaults to checking only the current-context watershed. User must actively check additional ones.
- **Rationale**: A Virginia user planning a Pacific Northwest trip should not receive ambient alerts about Washington conditions they never asked for. Geographically distant alerts feel like spam regardless of how good the science is. Default-narrow respects user intent.

### AD-3: Dispatcher cadence — once-daily 06:00 PT batch

- **Question**: Continuous dispatcher (fires as new forecast rows arrive) vs. scheduled batch.
- **Chosen**: **06:00 PT daily batch.** Matches the natural "checking conditions for the week" moment for anglers in the Pacific time zone.
- **Rationale**: Continuous dispatch creates two problems: (a) firing alerts at 2 PM Tuesday for Saturday feels random; (b) tracking "did we already alert this user today" requires more careful state. Daily batch makes the user experience predictable ("the alert always comes Tuesday morning before work") and the implementation deterministic.

### AD-4: Verification provider — Telnyx Verify

- **Chosen**: Telnyx Verify SDK for the OTP flow.
- **Rationale**: Same vendor as our SMS dispatch. Single dashboard for cost/balance/logs. Cheaper than Twilio Verify (~$0.03 vs ~$0.05 per verification). Auto-fill on iOS works in Safari via the standard `<input autocomplete="one-time-code">` attribute — vendor-agnostic.

### AD-5: Phone-number storage — encrypted at rest

- **Chosen**: Application-level encryption (AES-GCM, key in Secret Manager) of `users.phone_number_e164`. Stored in a separate column from the rest of the user record.
- **Rationale**: Phone numbers are PII with regulatory implications. App-level encryption defends against accidental log leakage and DB-dump exposure. The encrypted column never appears in API responses or analytics.

### AD-6: Budget enforcement — defense in depth

- **Carrier prepay** (Telnyx): outer safety net. Balance hits $0 → carrier rejects sends. No surprise bills, ever.
- **App-level caps** (daily, monthly): inner safety net. A bug that tries to re-fire 10,000 SMS hits the daily cap (500) and stops at our layer before the carrier even notices.
- Both layered: removes any single point of failure for cost runaway.

## Interface Contracts

### REST endpoints

```
POST /api/v1/sms/phone/start-verification
  Body: { phone: "+15555550123" }
  Returns: { verification_id, expires_at }
  Sends OTP via Telnyx Verify. Rate-limited 3/min/IP.

POST /api/v1/sms/phone/confirm-verification
  Body: { verification_id, code: "123456" }
  Returns: { verified: true }
  Stores phone_number_e164 + phone_verified_at on the user.

GET /api/v1/sms/subscriptions
  Returns: [{ watershed, threshold, created_at, muted_until }]

POST /api/v1/sms/subscriptions
  Body: { watersheds: ["deschutes", "metolius"], threshold: 80 }
  Idempotent — upserts subscriptions for the listed watersheds.

DELETE /api/v1/sms/subscriptions/:watershed
  Removes a single subscription. Phone remains verified.

POST /api/v1/sms/inbound  (Telnyx webhook)
  Telnyx posts inbound SMS here. Handles STOP / STOPALL / HELP.
```

### Telnyx webhook signature verification

Telnyx signs inbound webhooks. Verify the `Telnyx-Signature-ed25519-Signature` header against the public key before processing.

### Frontend additions

- **`<AlertsChip watershed={ws} />`** — small button on the TQS pill row. Hidden when user already has an active subscription for that watershed.
- **`<AlertsOptInSheet />`** — opt-in flow: phone input → OTP → watershed multi-select → confirm.
- **`<ForecastModalNudge />`** — banner inside `TripQualityForecastModal` shown when ≥1 forecast day in the next 7d has `tqs >= 80` AND user has no subscription for the watershed in view.
- **`/path/settings/alerts`** — list of current subscriptions with per-watershed toggle and a global "Pause all alerts" switch.

## Data Model

```sql
-- Users table extensions
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS phone_number_e164_encrypted bytea,
  ADD COLUMN IF NOT EXISTS phone_verified_at timestamptz,
  ADD COLUMN IF NOT EXISTS sms_paused boolean NOT NULL DEFAULT false;

-- Per-watershed subscriptions
CREATE TABLE sms_alert_subscriptions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    watershed    VARCHAR(32) NOT NULL,
    threshold    INTEGER NOT NULL DEFAULT 80,
    muted_until  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, watershed)
);
CREATE INDEX ix_sms_subs_watershed ON sms_alert_subscriptions(watershed)
  WHERE muted_until IS NULL OR muted_until < now();

-- Per-(user, watershed, target_date) cooldown record
CREATE TABLE sms_alert_history (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    watershed        VARCHAR(32) NOT NULL,
    target_date      DATE NOT NULL,
    tqs_at_send      INTEGER NOT NULL,
    forecast_source  VARCHAR(32),
    sent_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    telnyx_message_id TEXT,
    delivery_status  VARCHAR(16) NOT NULL DEFAULT 'queued',
    UNIQUE (user_id, watershed, target_date)
);
CREATE INDEX ix_sms_history_user_recent ON sms_alert_history(user_id, sent_at DESC);

-- Budget tracking (cheap aggregation)
CREATE TABLE sms_send_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    cost_cents  NUMERIC(8,4),
    success     BOOLEAN NOT NULL
);
CREATE INDEX ix_sms_send_log_day ON sms_send_log((sent_at::date));
```

## Dispatcher Algorithm

```python
def dispatch_daily():
    # 1. Compute today's caps
    today_count   = SELECT count(*) FROM sms_send_log WHERE sent_at::date = today;
    month_count   = SELECT count(*) FROM sms_send_log WHERE sent_at >= first_of_month;
    if today_count >= MAX_SMS_PER_DAY: log + abort
    if month_count >= MAX_SMS_PER_MONTH: log + abort

    # 2. Find candidate matches
    matches = SELECT user_id, watershed, target_date, tqs, confidence
              FROM sms_alert_subscriptions sub
              JOIN gold.trip_quality_watershed_daily d
                ON d.watershed = sub.watershed
              WHERE d.target_date BETWEEN today AND today+3
                AND d.watershed_tqs >= sub.threshold
                AND d.confidence != 'low'
                AND (sub.muted_until IS NULL OR sub.muted_until < now())
                AND user.sms_paused IS NOT TRUE
                AND NOT EXISTS (
                    SELECT 1 FROM sms_alert_history h
                    WHERE h.user_id = sub.user_id
                      AND h.watershed = sub.watershed
                      AND h.target_date = d.target_date
                      AND h.sent_at >= now() - interval '48 hours'
                );

    # 3. Group by user → digest
    for user_id, user_matches in groupby(matches, by=user_id):
        # Weekly cap check
        if weekly_count(user_id) >= 3: continue

        # Quiet hours
        if now_in_user_tz(user_id) is between (21:00, 08:00): continue

        # Compose body (single vs multi-match)
        body = compose_digest(user_matches)
        send_telnyx(user_id, body)
        record_history(user_id, user_matches)
        record_send_log(cost=estimate_cents)
```

## Error Handling

| Class | Examples | Strategy |
|---|---|---|
| OTP delivery fails | bad number, carrier issue | User sees "couldn't send — check the number"; verification_id is invalidated |
| Telnyx 4xx on send | invalid number, opted-out number | Log; mark phone as `sms_undeliverable`; never retry |
| Telnyx 5xx on send | transient carrier issue | Retry once after 30s; if still failing, log + skip; user gets alert tomorrow |
| Budget cap exceeded | dispatcher hits daily/monthly limit | Log explicit warning; abort with status `'budget_capped'`; alert ops via Cloud Monitoring |
| Phone marked STOP'd | inbound STOP received | Set `users.sms_paused=true`; webhook returns 200; never send again until user re-verifies |
| Webhook signature mismatch | malformed or spoofed payload | Return 401; log; do not process |
| User without subscriptions | dispatcher finds no matches | No-op; log "0 candidates" |

## Security

- Phone numbers encrypted at rest (AES-GCM, key in Secret Manager).
- Plain-text phone numbers never logged. Cloud Logging filters scrub `phone` keys.
- Telnyx webhook signature validation mandatory.
- OTP codes hashed before storage; never logged. Codes expire after 10 minutes.
- Rate limits: phone-verification start endpoint limited to 3/min/IP, 10/hr/user-account.
- A2P 10DLC compliance: campaign registered with Telnyx; brand verified; consent flow auditable.

## Test Strategy

### Unit
- Cooldown SQL: given fixture rows, the candidate query returns expected set.
- Digest composer: 1, 2, 3 matches produce correctly-formatted SMS bodies.
- Quiet hours: 21:00 / 22:00 / 07:59 in user TZ all suppress; 08:00 fires.
- Phone encryption round-trip.

### Integration
- Full opt-in flow: start verification → OTP delivered (mocked) → confirm → subscription saved.
- Dispatcher dry-run with fixture forecast rows.
- STOP handler updates `users.sms_paused`.

### Manual / E2E
- Real OTP delivery to a test phone.
- Webhook delivery from Telnyx sandbox.
- 48h cooldown across two dispatcher runs.

## Implementation Plan

```
Phase 0 — Foundation (1–2 days)
├── Alembic migration: phone columns + subscriptions + history + send_log tables
├── Telnyx account setup, A2P 10DLC campaign registration
├── Secret Manager: telnyx-api-key, sms-encryption-key
└── pyverify wrapper module (phone encrypt/decrypt utilities)

Phase 1 — Verification + subscription API (2 days)
├── POST /sms/phone/start-verification
├── POST /sms/phone/confirm-verification
├── GET/POST/DELETE /sms/subscriptions
├── Rate limiting on verification endpoint
└── Tests

Phase 2 — Frontend opt-in (2 days)
├── <AlertsChip> on TripQualityCard
├── <AlertsOptInSheet> (phone input, OTP, watershed multi-select)
├── <ForecastModalNudge> in TripQualityForecastModal
├── /path/settings/alerts page

Phase 3 — Dispatcher + Telnyx integration (2–3 days)
├── pipeline/sms/dispatcher.py
├── Telnyx HTTP client wrapper with signature verification
├── Daily Cloud Run Job + Cloud Scheduler cron at 06:00 PT
├── Webhook endpoint POST /sms/inbound for STOP/HELP
└── Budget cap enforcement

Phase 4 — Polish + observability (1 day)
├── PostHog events (verification_started/completed, subscription_added,
│   nudge_shown, nudge_clicked, sms_sent, sms_clicked)
├── Cloud Monitoring alert on dispatcher failure rate
├── Weekly cost report cron
└── Tighten copy on opt-in flow + nudge banner
```

### Suggested HELIX issues

1. Schema migration (phone columns + 3 new tables). AC: alembic upgrade head succeeds.
2. Phone encryption utility module. AC: round-trip encrypt/decrypt with key from Secret Manager.
3. Telnyx Verify integration + verification API endpoints. AC: real OTP delivers in <30s; rate limit enforced.
4. Subscriptions CRUD API. AC: per-watershed upsert/delete; idempotent.
5. AlertsChip + AlertsOptInSheet UI. AC: phone-verification → multi-select → save persists.
6. ForecastModalNudge banner. AC: shows only when ≥1 day-7d forecast ≥80 AND user has no sub for that watershed; click opens opt-in pre-checked.
7. /path/settings/alerts page. AC: lists subscriptions; toggle per-watershed; global pause.
8. SMS dispatcher (Phase 3 core). AC: 06:00 PT batch finds matches, dedupes, batches digests, applies cooldown + weekly cap + quiet hours + budget cap; writes history rows.
9. Telnyx webhook handler. AC: STOP sets sms_paused; signature verification enforced.
10. Budget caps + monitoring. AC: daily/monthly caps abort dispatcher; Cloud Monitoring alert fires on cap hit.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A2P 10DLC registration rejected by carrier | M | H | Submit brand + campaign details early; use Telnyx's pre-vetted templates; fallback to "non-marketing transactional" framing |
| Bug fires duplicate SMS to same user | M | M | sms_alert_history unique constraint on (user_id, watershed, target_date); daily cap as belt-and-braces |
| User OTP doesn't arrive | M | L | Verification page surfaces "didn't get it?" link → resend after 60s; logs help diagnose carrier issues |
| Phone number leak via logs | L | H | App-level encryption; log filter scrubs `phone` keys; quarterly log audit |
| Budget runaway | L | H | Telnyx prepay (outer); app-level daily/monthly cap (inner); cost monitoring |
| User says they STOP'd but kept receiving | L | H | Inbound STOP handler sets sms_paused atomically; dispatcher pre-flight check enforces sms_paused |
| Per-user weekly cap edge case (timezone) | L | L | Compute weekly cap in UTC; users won't notice |
| Telnyx outage | L | M | Dispatcher retries 5xx once; persistent failures logged; missed alerts not catastrophic since users can still open app |

## Observability

- **PostHog events**:
  - `sms.alerts_chip.shown` / `sms.alerts_chip.clicked`
  - `sms.nudge.shown` / `sms.nudge.clicked` (forecast modal contextual)
  - `sms.verification.started` / `.completed` / `.failed`
  - `sms.subscription.created` (per watershed) / `.deleted`
  - `sms.dispatcher.run` (candidates_found, sends_completed, capped_count, duration_ms)
  - `sms.delivery.completed` / `.failed` (via Telnyx webhook delivery receipts)
- **Cloud Monitoring alerts**:
  - Dispatcher exit ≠ 0
  - Daily cap hit (proactive — means we sized wrong or there's a bug)
  - Telnyx 5xx rate > 5% in 1h
- **Cost tracking**: weekly cron aggregates `sms_send_log` and writes a markdown report to GCS.

## Open Forks (collaborative review pending)

1. **OF-1 Threshold default** — 80 (Excellent) is the proposed default. Could be 70 (Good and up) for more frequent alerts, or user-configurable. Lean: 80 default, allow override later.
2. **OF-2 Contextual nudge frequency** — currently shows every time the forecast modal opens with a qualifying day. Could be "show once per week if dismissed." Lean: show every time the user actually opens the modal; if they're looking at a good-conditions day they're interested.
3. **OF-3 Weekly cap value** — 3 is the proposed cap. Could be 2 (more conservative) or 5 (let users get more during peak season). Lean: 3.
4. **OF-4 Dispatcher time zone** — fixed at 06:00 PT or per-user local 06:00? Per-user requires storing user TZ, which we don't have. Lean: fixed PT for MVP (most users are in PT/MT), per-user TZ later.
5. **OF-5 International phone numbers** — US-only at MVP. Adding international raises A2P compliance complexity (each country has its own regime). Lean: US-only until international demand surfaces.
6. **OF-6 Account-required vs. anonymous opt-in** — current plan ties subscriptions to authenticated user. Could allow anonymous phone-only opt-in. Lean: account-required; aligns with existing auth model and supports settings page.

## Governing Artifacts

- **`plan-2026-05-14-tqs-forecast-history.md`** — provides `gold.trip_quality_watershed_daily` and forecast confidence values the dispatcher reads.
- **`plan-2026-05-14-push-notifications.md`** — superseded by this plan; retained for context on the alternative considered.
- **FEAT-007 Fishing Intelligence** — TQS is the metric this alerts on.
- **FEAT-019 Authentication** — phone verification builds on existing user auth.

## Refinement Log

- **Round 1**: initial structure — SMS-only, per-watershed opt-in, dispatcher rules.
- **Round 2**: added contextual nudge in forecast modal; budget caps as defense in depth (carrier prepay + app cap); STOP/HELP webhook.
- **Round 3**: tightened anti-spam logic (cooldown by target_date, not by rule; digest mode; 06:00 PT batch); phone encryption; A2P risk surfaced.
