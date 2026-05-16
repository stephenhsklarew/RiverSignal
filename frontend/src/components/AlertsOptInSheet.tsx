/**
 * SMS alerts opt-in sheet.
 *
 * Multi-step flow:
 *   1. Phone entry (+1 only, US + Canada)
 *   2. OTP verification (Telnyx Verify, 6-digit code)
 *   3. Watershed multi-select (one or more)
 *   4. Threshold band (Excellent ≥80 default / Good+ ≥70)
 *
 * On success → subscriptions are created and onClose(true) fires.
 * If the user already has a verified phone, steps 1–2 are skipped.
 */
import { useEffect, useMemo, useState } from 'react'
import useSWR from 'swr'
import { API_BASE } from '../config'
import './AlertsOptInSheet.css'

const WATERSHEDS = [
  { id: 'mckenzie',    name: 'McKenzie' },
  { id: 'deschutes',   name: 'Deschutes' },
  { id: 'metolius',    name: 'Metolius' },
  { id: 'klamath',     name: 'Klamath' },
  { id: 'johnday',     name: 'John Day' },
  { id: 'shenandoah',  name: 'Shenandoah' },
  { id: 'skagit',      name: 'Skagit' },
  { id: 'green_river', name: 'Green River' },
]

type Step = 'phone' | 'otp' | 'watersheds' | 'threshold' | 'done'

interface SubscriptionsResponse {
  phone_verified: boolean
  sms_paused: boolean
  subscriptions: Array<{
    watershed: string
    threshold: number
    muted_until: string | null
    created_at: string
  }>
}

interface Props {
  open: boolean
  onClose: (created: boolean) => void
  /** Optional preselected watershed (e.g., when opened from a watershed page). */
  preselectWatershed?: string
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then(r => {
    if (r.status === 401) return null
    return r.json()
  })

function formatPhoneDisplay(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 10)
  if (digits.length < 4) return digits
  if (digits.length < 7) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
}

export default function AlertsOptInSheet({ open, onClose, preselectWatershed }: Props) {
  const { data: subs, mutate } = useSWR<SubscriptionsResponse | null>(
    open ? `${API_BASE}/sms/subscriptions` : null,
    fetcher,
  )

  const [step, setStep] = useState<Step>('phone')

  const [phoneDisplay, setPhoneDisplay] = useState('')
  const [verificationId, setVerificationId] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [threshold, setThreshold] = useState<70 | 80>(80)

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Seed step + preselected watershed when sheet opens / data loads.
  useEffect(() => {
    if (!open) return
    setStep(subs?.phone_verified ? 'watersheds' : 'phone')
    if (preselectWatershed) {
      setSelected(new Set([preselectWatershed]))
    }
  }, [open, subs?.phone_verified, preselectWatershed])

  const phoneE164 = useMemo(() => {
    const digits = phoneDisplay.replace(/\D/g, '')
    return digits.length === 10 ? `+1${digits}` : null
  }, [phoneDisplay])

  if (!open) return null

  async function startVerification() {
    if (!phoneE164) { setError('Enter a 10-digit US or Canadian number.'); return }
    setBusy(true); setError(null)
    try {
      const r = await fetch(`${API_BASE}/sms/phone/start-verification`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: phoneE164 }),
      })
      if (!r.ok) {
        const e = await r.json().catch(() => ({}))
        throw new Error(e.detail || `Verification failed (${r.status})`)
      }
      const data = await r.json()
      setVerificationId(data.verification_id)
      setStep('otp')
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function confirmVerification() {
    if (!verificationId || !phoneE164 || code.length < 4) {
      setError('Enter the code from your text message.'); return
    }
    setBusy(true); setError(null)
    try {
      const r = await fetch(`${API_BASE}/sms/phone/confirm-verification`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verification_id: verificationId, code, phone: phoneE164 }),
      })
      if (!r.ok) {
        const e = await r.json().catch(() => ({}))
        throw new Error(e.detail || 'Code is incorrect or expired.')
      }
      await mutate()
      setStep('watersheds')
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function saveSubscriptions() {
    if (selected.size === 0) {
      setError('Pick at least one watershed.'); return
    }
    setBusy(true); setError(null)
    try {
      const r = await fetch(`${API_BASE}/sms/subscriptions`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ watersheds: [...selected], threshold }),
      })
      if (!r.ok) {
        const e = await r.json().catch(() => ({}))
        throw new Error(e.detail || 'Could not save your alerts.')
      }
      await mutate()
      setStep('done')
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="alerts-overlay" onClick={() => onClose(false)}>
      <div className="alerts-sheet" onClick={e => e.stopPropagation()}>
        <button className="alerts-close" onClick={() => onClose(false)} aria-label="Close">✕</button>

        {step === 'phone' && (
          <>
            <h2>Get SMS alerts</h2>
            <p className="alerts-sub">
              We&apos;ll text you when conditions hit your bar for a watershed you care about.
              At most 3 messages per week. STOP anytime.
            </p>
            <label className="alerts-label">Mobile number</label>
            <input
              type="tel"
              value={phoneDisplay}
              onChange={e => setPhoneDisplay(formatPhoneDisplay(e.target.value))}
              placeholder="(555) 123-4567"
              inputMode="tel"
              autoFocus
            />
            <p className="alerts-fine">US and Canada only. Standard message rates may apply.</p>
            {error && <div className="alerts-error">{error}</div>}
            <button className="alerts-cta" onClick={startVerification} disabled={busy || !phoneE164}>
              {busy ? 'Sending code…' : 'Send code'}
            </button>
          </>
        )}

        {step === 'otp' && (
          <>
            <h2>Enter the code</h2>
            <p className="alerts-sub">
              We sent a 6-digit code to {phoneDisplay}.
            </p>
            <input
              type="text"
              value={code}
              onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 8))}
              placeholder="123456"
              inputMode="numeric"
              autoFocus
              className="alerts-otp"
            />
            {error && <div className="alerts-error">{error}</div>}
            <button className="alerts-cta" onClick={confirmVerification} disabled={busy || code.length < 4}>
              {busy ? 'Verifying…' : 'Verify'}
            </button>
            <button className="alerts-link" onClick={() => { setStep('phone'); setCode(''); setError(null) }}>
              ← Change number
            </button>
          </>
        )}

        {step === 'watersheds' && (
          <>
            <h2>Which watersheds?</h2>
            <p className="alerts-sub">
              We&apos;ll only text you about places you pick — no Virginia user getting Washington alerts.
            </p>
            <div className="alerts-watershed-list">
              {WATERSHEDS.map(ws => {
                const on = selected.has(ws.id)
                return (
                  <button
                    key={ws.id}
                    type="button"
                    className={`alerts-watershed ${on ? 'on' : ''}`}
                    onClick={() => {
                      const next = new Set(selected)
                      if (on) next.delete(ws.id); else next.add(ws.id)
                      setSelected(next)
                    }}
                  >
                    <span>{ws.name}</span>
                    <span className="alerts-check">{on ? '✓' : ''}</span>
                  </button>
                )
              })}
            </div>
            {error && <div className="alerts-error">{error}</div>}
            <button
              className="alerts-cta"
              onClick={() => setStep('threshold')}
              disabled={selected.size === 0}
            >
              Continue ({selected.size} selected)
            </button>
          </>
        )}

        {step === 'threshold' && (
          <>
            <h2>How picky?</h2>
            <p className="alerts-sub">
              Choose the bar that triggers a text. You can change this later.
            </p>
            <div className="alerts-threshold-list">
              <button
                type="button"
                className={`alerts-threshold ${threshold === 80 ? 'on' : ''}`}
                onClick={() => setThreshold(80)}
              >
                <div className="alerts-threshold-band excellent">Excellent only</div>
                <div className="alerts-threshold-meta">Go Score ≥ 80 · ~3–6 alerts/season</div>
              </button>
              <button
                type="button"
                className={`alerts-threshold ${threshold === 70 ? 'on' : ''}`}
                onClick={() => setThreshold(70)}
              >
                <div className="alerts-threshold-band strong">Good or better</div>
                <div className="alerts-threshold-meta">Go Score ≥ 70 · ~8–15 alerts/season</div>
              </button>
            </div>
            {error && <div className="alerts-error">{error}</div>}
            <button className="alerts-cta" onClick={saveSubscriptions} disabled={busy}>
              {busy ? 'Saving…' : 'Turn on alerts'}
            </button>
            <p className="alerts-fine">
              We cap at 3 texts per week with a 48-hour cooldown per watershed.
              Reply STOP to a text anytime to turn alerts off.
            </p>
          </>
        )}

        {step === 'done' && (
          <>
            <h2>You&apos;re set</h2>
            <p className="alerts-sub">
              We&apos;ll text {phoneDisplay || 'your verified number'} when one of your
              watersheds hits {threshold === 80 ? 'Excellent (≥80)' : 'Good or better (≥70)'} in the next 3 days.
            </p>
            <button className="alerts-cta" onClick={() => onClose(true)}>Done</button>
          </>
        )}
      </div>
    </div>
  )
}
