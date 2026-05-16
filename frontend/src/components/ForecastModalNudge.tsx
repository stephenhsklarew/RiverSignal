/**
 * 1-line banner inside TripQualityForecastModal nudging the user toward SMS alerts.
 *
 * Suppressed for 7 days once dismissed (localStorage). Hidden entirely once the
 * user has any subscription. Opens AlertsOptInSheet with the current watershed
 * preselected.
 */
import { useState } from 'react'
import useSWR from 'swr'
import { API_BASE } from '../config'
import AlertsOptInSheet from './AlertsOptInSheet'
import { useAuth } from './AuthContext'
import LoginModal from './LoginModal'
import './ForecastModalNudge.css'

const SUPPRESS_KEY = 'rs_alerts_nudge_dismissed_at'
const SUPPRESS_DAYS = 7

interface SubscriptionsResponse {
  phone_verified: boolean
  subscriptions: Array<{ watershed: string }>
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then(r => {
    if (r.status === 401) return null
    return r.json()
  })

function isSuppressed(): boolean {
  try {
    const raw = localStorage.getItem(SUPPRESS_KEY)
    if (!raw) return false
    const at = parseInt(raw, 10)
    return Number.isFinite(at) && Date.now() - at < SUPPRESS_DAYS * 86_400_000
  } catch {
    return false
  }
}

export default function ForecastModalNudge({ watershed }: { watershed: string }) {
  const { isLoggedIn } = useAuth()
  const { data, mutate } = useSWR<SubscriptionsResponse | null>(
    isLoggedIn ? `${API_BASE}/sms/subscriptions` : null,
    fetcher,
  )
  const [showSheet, setShowSheet] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [hidden, setHidden] = useState(isSuppressed())

  // If they already subscribed to this watershed, don't nudge.
  const hasAny = (data?.subscriptions?.length || 0) > 0
  if (hidden || hasAny) return null

  function dismiss() {
    try { localStorage.setItem(SUPPRESS_KEY, String(Date.now())) } catch { /* ok */ }
    setHidden(true)
  }

  function openOptIn() {
    if (!isLoggedIn) { setShowLogin(true); return }
    setShowSheet(true)
  }

  return (
    <>
      <div className="fc-nudge">
        <button type="button" className="fc-nudge-cta" onClick={openOptIn}>
          🔔 Get a text when Excellent days are coming
        </button>
        <button
          type="button"
          className="fc-nudge-dismiss"
          onClick={dismiss}
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
      {showSheet && (
        <AlertsOptInSheet
          open={showSheet}
          onClose={(created) => {
            setShowSheet(false)
            if (created) mutate()
          }}
          preselectWatershed={watershed}
        />
      )}
      {showLogin && <LoginModal onClose={() => setShowLogin(false)} mode="signup" />}
    </>
  )
}
