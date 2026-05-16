# Runbook: SMS Alerts — Telnyx setup & first deploy

| | |
|---|---|
| **Date** | 2026-05-15 |
| **Status** | Active — first deploy not yet executed |
| **Audience** | Operator with Telnyx console access + `gcloud` + `terraform` access |
| **Related artifacts** | `docs/helix/02-design/plan-2026-05-15-sms-alerts.md`, `app/routers/sms.py`, `pipeline/sms/dispatcher.py`, `terraform/cloud_run_jobs.tf`, `terraform/cloud_scheduler.tf`, `terraform/secrets.tf` |

**Goal:** stand up SMS alerts end-to-end: Telnyx account → A2P 10DLC registration → secret population → first dispatcher run.

---

## 1. Telnyx account setup

### 1.1 Create account & fund

1. Sign up at https://telnyx.com.
2. Add a payment method and fund the account. Estimated MVP cost: ~$10/month at <500 alerts/day (Telnyx outbound SMS US ≈ $0.004 / segment, inbound free).
3. Note the **Account/Organization ID** from Account → Settings.

### 1.2 Buy a phone number

1. Numbers → Buy Numbers → **Local number** (long code) in any US area code.
   - Toll-free is also fine but requires separate verification; long code + A2P 10DLC is the cheaper, faster path.
2. After purchase, copy the E.164 form (e.g. `+15035551234`) — this becomes `TELNYX_FROM_NUMBER`.

### 1.3 Register A2P 10DLC campaign

Carriers in the US require A2P 10DLC registration for any number sending SMS to consumers. Without it, deliverability drops to ~30% and you'll be filtered as spam.

1. Messaging → 10DLC → Brand Registration. Use the business legal name and EIN (or Sole Proprietor if applicable). Approval is usually 1–2 business days.
2. Once the brand is approved, create a **Campaign**:
   - **Use case**: Account Notification (sub-type: "Conditions Alerts")
   - **Sample messages**: paste 2–3 of the templates produced by `pipeline/sms/dispatcher.py::compose_body()`, e.g.
     - `Deschutes is forecast Excellent for Sat (TQS 85). Open RiverPath: https://riversignal.app/path/now/deschutes`
     - `Excellent conditions: Deschutes Sat (85), Metolius Sun (82). Open RiverPath: https://riversignal.app/path/now`
   - **Opt-in description**: "Users opt in via the RiverPath app by entering their phone number and verifying a one-time code, then selecting which watersheds and a quality threshold."
   - **Opt-out keywords**: `STOP, STOPALL, UNSUBSCRIBE, QUIT, CANCEL, END` (Telnyx auto-handles these regardless; listing them appeases the registrar).
   - **Help keywords**: `HELP, INFO`
3. Wait for campaign approval (typically same-day after brand approval).
4. Assign the purchased number to the approved campaign.

---

## 2. Telnyx profiles

### 2.1 Messaging Profile

Messaging → Messaging Profiles → Create.

- **Name**: `riversignal-prod`
- **Number(s)**: attach the number purchased in §1.2.
- **Inbound Settings → Webhook URL**: `https://riversignal-api-x6ka75yaxa-uw.a.run.app/api/v1/sms/inbound`
  - Once a custom domain is in front of Cloud Run (e.g. `api.riversignal.app`), update this.
- **Webhook Failover URL**: leave blank. A second endpoint would only help if Cloud Run itself were down, and it wouldn't reach different infra anyway.
- **Webhook API Version**: v2
- **Webhook Signing**: enable ed25519. Copy the **public key** shown — this is `TELNYX_PUBLIC_KEY` (§3).
- **Outbound → Number pool**: long-code, default rate limit.

Copy the **Messaging Profile ID** — this is `TELNYX_MESSAGING_PROFILE_ID`.

### 2.2 Verify Profile

Verify → Verify Profiles → Create.

- **Name**: `riversignal-otp`
- **Channel**: SMS
- **Message template**: leave default ("Your RiverSignal verification code is {{code}}") or customize.
- **Code length**: 6 digits
- **Code expiry**: 10 minutes (matches `timeout_secs=600` in `app/lib/telnyx.py::start_verification`).

No webhook needed — we poll `confirm_verification` synchronously.

Copy the **Verify Profile ID** — this is `TELNYX_VERIFY_PROFILE_ID`.

### 2.3 API key

Account → API Keys → Create. Scope: full access (Telnyx doesn't offer fine-grained scopes on v2 keys). Copy the key — this is `TELNYX_API_KEY`.

---

## 3. Secret Manager population

Six secrets are declared in `terraform/secrets.tf`. After `terraform apply`, populate versions:

```bash
PROJECT=riversignal-prod   # adjust to your project id

# Telnyx credentials from §1–2
echo -n "<api_key_from_2.3>"          | gcloud secrets versions add telnyx-api-key              --data-file=- --project=$PROJECT
echo -n "<verify_profile_id_2.2>"     | gcloud secrets versions add telnyx-verify-profile-id    --data-file=- --project=$PROJECT
echo -n "<messaging_profile_id_2.1>"  | gcloud secrets versions add telnyx-messaging-profile-id --data-file=- --project=$PROJECT
echo -n "+15035551234"                | gcloud secrets versions add telnyx-from-number          --data-file=- --project=$PROJECT
echo -n "<public_key_from_2.1>"       | gcloud secrets versions add telnyx-public-key           --data-file=- --project=$PROJECT

# Symmetric key for AES-GCM phone encryption. Generate ONCE, then save.
python -c "import secrets; print(secrets.token_hex(32))" | gcloud secrets versions add sms-encryption-key --data-file=- --project=$PROJECT
```

**Critical:** `sms-encryption-key` must never change once phones are encrypted in prod — rotating it would render all stored phone numbers unrecoverable. Back up the value to a password manager.

---

## 4. Deploy

```bash
# 1. Apply terraform — creates the dispatcher job, the scheduler, and the secret IDs
cd terraform && terraform apply

# 2. Build + push the image (handled by GitHub Actions on push to main)
git push origin main

# 3. Update the new job to use the freshly built image
gcloud run jobs update riversignal-sms-dispatcher \
  --image us-west1-docker.pkg.dev/$PROJECT/riversignal/api:latest \
  --region us-west1 --project=$PROJECT

# 4. Run the migration once (adds users.phone_* columns + the 3 SMS tables)
gcloud run jobs execute riversignal-migrate --region us-west1 --project=$PROJECT
```

---

## 5. Smoke test

### 5.1 Phone verification flow

1. In dev or staging, sign in as yourself.
2. Open `/path/alerts` → "SMS" tab → "Set up SMS alerts".
3. Enter your real mobile number. You should receive a 6-digit code within ~5 seconds.
4. Enter the code; the sheet advances to the watershed selector.
5. Pick one watershed and a threshold; save.
6. Verify the row in DB:
   ```sql
   SELECT user_id, watershed, threshold, created_at FROM sms_alert_subscriptions WHERE user_id = '<your-uid>';
   SELECT id, phone_verified_at, sms_paused FROM users WHERE id = '<your-uid>';
   ```

### 5.2 Dispatcher dry run

The dispatcher is idempotent — running it twice on the same day is a no-op (history dedup). Trigger an off-cycle run:

```bash
gcloud run jobs execute riversignal-sms-dispatcher --region us-west1 --project=$PROJECT
```

Check logs:

```bash
gcloud logging read 'resource.labels.job_name=riversignal-sms-dispatcher' --limit 20 --project=$PROJECT
```

Expected outputs: `Found N candidate matches` → `SMS dispatcher complete: sent=N skipped_cap=… …`. If `sent=0` with no matches found, that's fine — you may need to wait until a watershed actually forecasts ≥ threshold in the next 3 days.

### 5.3 Inbound STOP test

1. Reply `STOP` to the dispatcher's SMS.
2. Within seconds, Telnyx auto-marks the number opted-out at the messaging-profile level (defense in depth).
3. Our `/api/v1/sms/inbound` handler also flips `users.sms_paused = true`. Confirm:
   ```sql
   SELECT sms_paused FROM users WHERE id = '<your-uid>';   -- should be true
   ```
4. The "SMS" tab in `/path/alerts` should now show "⏸ Paused".

---

## 6. Going live

### 6.1 Pre-flight checklist

- [ ] A2P 10DLC campaign **approved** (not just submitted). Sending before approval results in low deliverability and possible carrier complaints.
- [ ] All six secrets populated with `latest` versions visible in `gcloud secrets versions list <name>`.
- [ ] `terraform apply` completed without diff on `cloud_run_jobs.tf`, `cloud_scheduler.tf`, `secrets.tf`.
- [ ] Cloud Scheduler `riversignal-sms-dispatcher` exists and shows next-run time at 9:00 PT.
- [ ] At least one staff phone verified and subscribed end-to-end (§5.1).
- [ ] Outbound STOP works (§5.3).
- [ ] API service `min_instances` ≥ 1 so inbound webhooks don't hit cold-start (else accept occasional 5s timeouts → Telnyx retries).

### 6.2 First production day

The scheduler fires daily at 09:00 `America/Los_Angeles`. Watch:

- **Cost**: `SELECT count(*), sum(cost_cents) FROM sms_send_log WHERE sent_at::date = current_date AND success;`
- **Bounces / failures**: `SELECT delivery_status, count(*) FROM sms_alert_history WHERE sent_at::date = current_date GROUP BY 1;`
- **Cloud Logging**: `resource.labels.job_name=riversignal-sms-dispatcher AND severity>=ERROR`

### 6.3 Budget caps

Defaults (set via env in the job):

| Env var | Default | Notes |
|---|---|---|
| `MAX_SMS_PER_DAY` | 500 | Aborts if `sms_send_log` for today already at this count |
| `MAX_SMS_PER_MONTH` | 5000 | Same, month-to-date |
| `SMS_WEEKLY_CAP_PER_USER` | 3 | Per-user cap in addition to app-level budgets |
| `SMS_COOLDOWN_HOURS` | 48 | Suppresses re-alerts for the same (user, watershed, target_date) |
| `SMS_FORECAST_HORIZON_DAYS` | 3 | How far ahead to look in `gold.trip_quality_watershed_daily` |

Tighter caps for the first week (e.g. `MAX_SMS_PER_DAY=100`) are a good idea — bump the env on the Cloud Run Job:

```bash
gcloud run jobs update riversignal-sms-dispatcher \
  --set-env-vars MAX_SMS_PER_DAY=100,MAX_SMS_PER_MONTH=1000 \
  --region us-west1 --project=$PROJECT
```

---

## 7. Common operations

### Pause all sending app-wide (kill switch)

Don't disable the scheduler — that risks forgetting to re-enable. Set the daily cap to 0:

```bash
gcloud run jobs update riversignal-sms-dispatcher \
  --set-env-vars MAX_SMS_PER_DAY=0 \
  --region us-west1 --project=$PROJECT
```

### Rotate Telnyx API key

1. Telnyx → API Keys → create new, copy the value.
2. `echo -n "<new_key>" | gcloud secrets versions add telnyx-api-key --data-file=-`
3. Cloud Run picks up `latest` on the next job execution — no redeploy needed.
4. Telnyx → API Keys → delete the old key.

### Investigate a missed alert

```sql
-- Was the candidate eligible at all?
SELECT * FROM gold.trip_quality_watershed_daily
WHERE watershed = '<ws>' AND target_date = '<date>';

-- Did the user have a matching subscription and a verified phone?
SELECT s.*, u.phone_verified_at, u.sms_paused
FROM sms_alert_subscriptions s JOIN users u ON u.id = s.user_id
WHERE s.user_id = '<uid>' AND s.watershed = '<ws>';

-- Was a send recorded?
SELECT * FROM sms_alert_history
WHERE user_id = '<uid>' AND watershed = '<ws>' AND target_date = '<date>';

-- Was the user already at their weekly cap?
SELECT count(*) FROM sms_alert_history
WHERE user_id = '<uid>' AND sent_at >= now() - INTERVAL '7 days';
```

---

## 8. Open follow-ups (deferred from plan)

- **PostHog event instrumentation** on the SMS funnel. Requires `npm i posthog-js` + `VITE_POSTHOG_KEY` wiring in `main.tsx` first. Events: `sms_chip_clicked`, `sms_phone_submitted`, `sms_otp_verified`, `sms_watersheds_selected`, `sms_subscription_created`, `sms_paused`, `sms_resumed`.
- **Phone-hash lookup for STOP webhook**. Today the inbound handler falls back on Telnyx's profile-level opt-out enforcement. To flip our own `sms_paused` deterministically, add a `phone_hash` column on `users` populated by `hash_phone_for_lookup()` at confirm-verification time, and update the WHERE clause in `app/routers/sms.py::inbound_webhook`.
- **Cloud Monitoring alert** on dispatcher failure rate (>10% failed sends in a 10-minute window).
- **Weekly cost report cron** summarizing `sms_send_log` to a Slack webhook.
