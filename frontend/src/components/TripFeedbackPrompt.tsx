/**
 * One-tap "How was it?" feedback prompt (plan §5 Phase B + §3.0c).
 *
 * Trigger: on /path/now/<watershed> visits ≥1 day after a planned trip
 * (a watched reach the user opened the why-panel for, or one navigated
 * to from the ranking page in the last 3 days).
 *
 * Dismiss without submit → hidden 24h via localStorage.
 */
import { useEffect, useState } from 'react'
import { API_BASE } from '../config'
import './TripFeedbackPrompt.css'

const DAY_MS = 86_400_000

export interface FeedbackTarget {
  reach_id: string
  reach_label: string
  trip_date: string  // YYYY-MM-DD
  tqs_at_view?: number
}

export default function TripFeedbackPrompt({ target }: { target: FeedbackTarget | null }) {
  const lsKey = target ? `rs_feedback_dismissed:${target.reach_id}:${target.trip_date}` : ''
  const [dismissed, setDismissed] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [pendingRating, setPendingRating] = useState<number | null>(null)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!target) return
    setDismissed(false)
    setSubmitted(false)
    setPendingRating(null)
    setNotes('')
    setError(null)
    try {
      const ts = localStorage.getItem(lsKey)
      if (ts && Date.now() - parseInt(ts) < DAY_MS) setDismissed(true)
    } catch { /* ignore */ }
  }, [target?.reach_id, target?.trip_date])

  if (!target || dismissed || submitted) return null
  const t = target

  function dismiss() {
    try { localStorage.setItem(lsKey, String(Date.now())) } catch { /* ignore */ }
    setDismissed(true)
  }

  async function submit(rating: number) {
    setPendingRating(rating)
    setSubmitting(true)
    setError(null)
    try {
      const r = await fetch(`${API_BASE}/trip-feedback`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reach_id: t.reach_id,
          trip_date: t.trip_date,
          rating,
          notes: notes.trim() || undefined,
          tqs_at_view: t.tqs_at_view,
        }),
      })
      if (!r.ok) {
        setError((await r.json()).detail || 'Failed to submit')
        setSubmitting(false)
        setPendingRating(null)
        return
      }
      setSubmitted(true)
    } catch {
      setError('Network error')
      setSubmitting(false)
      setPendingRating(null)
    }
  }

  return (
    <div className="tfp-card">
      <button className="tfp-close" onClick={dismiss} aria-label="Dismiss">✕</button>
      <div className="tfp-question">
        How was {t.reach_label} on {t.trip_date}?
      </div>
      <div className="tfp-rating-row">
        {[1, 2, 3, 4, 5].map(n => (
          <button
            key={n}
            className={`tfp-rating ${pendingRating === n ? 'on' : ''}`}
            disabled={submitting}
            onClick={() => submit(n)}
          >
            {['😞', '😐', '🙂', '😀', '🤩'][n - 1]}
          </button>
        ))}
      </div>
      <input
        type="text"
        className="tfp-notes"
        placeholder="Optional note (catches, conditions, anything)…"
        value={notes}
        onChange={e => setNotes(e.target.value)}
        maxLength={500}
        disabled={submitting}
      />
      {error && <div className="tfp-error">{error}</div>}
    </div>
  )
}
