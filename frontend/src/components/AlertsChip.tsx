/**
 * Small SMS-alerts chip surfaced on the Go Score card.
 *
 *   - If user has a subscription for this watershed: "🔔 Alerts on" (manage link).
 *   - Otherwise: "🔔 Get alerts" → opens AlertsOptInSheet with watershed preselected.
 */
import { useState } from 'react'
import useSWR from 'swr'
import { API_BASE } from '../config'
import AlertsOptInSheet from './AlertsOptInSheet'
import { useAuth } from './AuthContext'
import LoginModal from './LoginModal'
import './AlertsChip.css'

interface SubscriptionsResponse {
  phone_verified: boolean
  sms_paused: boolean
  subscriptions: Array<{ watershed: string; threshold: number; muted_until: string | null }>
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then(r => {
    if (r.status === 401) return null
    return r.json()
  })

export default function AlertsChip({ watershed }: { watershed: string }) {
  const { isLoggedIn } = useAuth()
  const { data, mutate } = useSWR<SubscriptionsResponse | null>(
    isLoggedIn ? `${API_BASE}/sms/subscriptions` : null,
    fetcher,
  )
  const [showSheet, setShowSheet] = useState(false)
  const [showLogin, setShowLogin] = useState(false)

  const subscribed = !!data?.subscriptions?.find(
    s => s.watershed === watershed && !s.muted_until,
  )
  const paused = !!data?.sms_paused

  function onClick() {
    if (!isLoggedIn) { setShowLogin(true); return }
    setShowSheet(true)
  }

  const label = subscribed
    ? (paused ? 'Paused' : 'Following')
    : 'Follow'

  return (
    <>
      <button
        type="button"
        className={`alerts-chip ${subscribed ? 'on' : ''} ${paused ? 'paused' : ''}`}
        onClick={onClick}
        aria-label={subscribed ? 'Manage SMS alerts' : 'Follow this watershed for SMS alerts'}
      >
        <svg className="alerts-chip-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 3.5a5.5 5.5 0 0 0-5.5 5.5v3.2L4.9 15a.9.9 0 0 0 .8 1.4h12.6a.9.9 0 0 0 .8-1.4l-1.6-2.8V9A5.5 5.5 0 0 0 12 3.5Z" strokeLinejoin="round" />
          <path d="M9.7 18.5a2.5 2.5 0 0 0 4.6 0" strokeLinecap="round" />
        </svg>
        {label}
      </button>
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
