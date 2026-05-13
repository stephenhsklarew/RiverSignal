/**
 * /path/alerts — Watchlist + Notifications + Digest tabs (plan §7 push).
 *
 * Auth-gated: anonymous → login modal, no content.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useSWR, { mutate } from 'swr'
import { API_BASE } from '../config'
import { useAuth } from '../components/AuthContext'
import LoginModal from '../components/LoginModal'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import './AlertsPage.css'

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then(r => r.json())

type Tab = 'watchlist' | 'notifications' | 'digest'

function bandLabel(tqs: number): { label: string; cls: string } {
  if (tqs >= 90) return { label: 'Excellent', cls: 'excellent' }
  if (tqs >= 70) return { label: 'Strong',     cls: 'strong' }
  if (tqs >= 50) return { label: 'Mixed',      cls: 'mixed' }
  if (tqs >= 30) return { label: 'Marginal',   cls: 'marginal' }
  return            { label: 'Unfavorable', cls: 'unfavorable' }
}

export default function AlertsPage() {
  const { isLoggedIn } = useAuth()
  const [tab, setTab] = useState<Tab>('notifications')
  const watershed = getSelectedWatershed() || 'mckenzie'

  return (
    <>
      <WatershedHeader watershed={watershed} basePath="/path/alerts" />
      <div className="alerts-page">
        <Link to={`/path/now/${watershed}`} className="alerts-back">← {watershed.replace(/_/g, ' ')}</Link>
        {!isLoggedIn ? (
          <NotLoggedInInner />
        ) : (
          <>
            <h1 className="alerts-title">Alerts</h1>
            <div className="alerts-tabs" role="tablist">
              {(['notifications', 'watchlist', 'digest'] as Tab[]).map(t => (
                <button
                  key={t}
                  role="tab"
                  className={`alerts-tab ${tab === t ? 'on' : ''}`}
                  onClick={() => setTab(t)}
                >{t === 'notifications' ? 'Notifications' : t === 'watchlist' ? 'Watchlist' : 'Digest'}</button>
              ))}
            </div>
            {tab === 'notifications' && <NotificationsTab />}
            {tab === 'watchlist' && <WatchlistTab />}
            {tab === 'digest' && <DigestTab />}
          </>
        )}
      </div>
    </>
  )
}

function NotLoggedInInner() {
  const [showLogin, setShowLogin] = useState(false)
  return (
    <>
      <div className="alerts-empty">
        <p>Sign in to view your alerts and watchlist.</p>
        <button className="alerts-cta" onClick={() => setShowLogin(true)}>Sign in</button>
      </div>
      {showLogin && <LoginModal onClose={() => setShowLogin(false)} mode="signin" />}
    </>
  )
}

// ── Notifications tab ───────────────────────────────────────────────────────

interface Alert {
  id: string
  reach_id: string
  reach_name: string
  watershed: string
  alert_type: string
  target_date: string
  tqs_at_alert: number
  narrative: string | null
  delivered_at: string | null
  seen_at: string | null
}

function NotificationsTab() {
  const navigate = useNavigate()
  const url = `${API_BASE}/alerts`
  const { data, isLoading } = useSWR<{ alerts: Alert[] }>(url, fetcher)

  async function markSeen(id: string) {
    await fetch(`${API_BASE}/alerts/${id}/seen`, { method: 'POST', credentials: 'include' })
    mutate(url)
    mutate(`${API_BASE}/alerts?seen=false`)
  }

  if (isLoading) return <div className="alerts-empty">Loading…</div>
  const alerts = data?.alerts || []
  if (!alerts.length) return <div className="alerts-empty">No alerts yet. Add reaches to your watchlist and we'll ping you when conditions cross your threshold.</div>

  return (
    <ul className="alerts-list">
      {alerts.map(a => {
        const band = bandLabel(a.tqs_at_alert)
        const unseen = !a.seen_at
        return (
          <li key={a.id} className={`alert-card ${unseen ? 'unseen' : ''}`}>
            <div className="alert-card-top">
              <span className={`alert-card-score ${band.cls}`}>{a.tqs_at_alert}</span>
              <div className="alert-card-headline">
                <div className="alert-card-title">{a.reach_name} · {a.target_date}</div>
                <div className="alert-card-sub">
                  {a.alert_type === 'band_cross_up' ? '↑ Crossed threshold' :
                   a.alert_type === 'trend_rising' ? '↗ Rising trend' :
                   a.alert_type}
                </div>
              </div>
              {unseen && <span className="alert-card-dot" aria-label="unseen" />}
            </div>
            {a.narrative && <p className="alert-card-narrative">{a.narrative}</p>}
            <div className="alert-card-actions">
              <button
                className="alert-card-action"
                onClick={() => navigate(`/path/now/${a.watershed}`, {
                  state: { reachId: a.reach_id },
                })}
              >Plan this trip</button>
              {unseen && (
                <button className="alert-card-action secondary" onClick={() => markSeen(a.id)}>
                  Mark seen
                </button>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}

// ── Watchlist tab ───────────────────────────────────────────────────────────

interface Watch {
  reach_id: string
  name: string
  short_label?: string
  watershed: string
  alert_threshold: number
  alert_trend: boolean
  muted_until: string | null
  current_tqs: number | null
  trend_7d: number
}

function WatchlistTab() {
  const url = `${API_BASE}/watchlist`
  const { data, isLoading } = useSWR<{ watches: Watch[] }>(url, fetcher)
  if (isLoading) return <div className="alerts-empty">Loading…</div>
  const watches = data?.watches || []
  if (!watches.length) {
    return (
      <div className="alerts-empty">
        Your watchlist is empty. Open a reach's why-panel on /path/now to start watching.
      </div>
    )
  }
  return (
    <ul className="watchlist-list">
      {watches.map(w => (
        <WatchRow key={w.reach_id} watch={w} onRefresh={() => mutate(url)} />
      ))}
    </ul>
  )
}

function WatchRow({ watch, onRefresh }: { watch: Watch; onRefresh: () => void }) {
  const [threshold, setThreshold] = useState(watch.alert_threshold)
  const [busy, setBusy] = useState(false)
  const muted = watch.muted_until && new Date(watch.muted_until) > new Date()

  async function update(patch: object) {
    setBusy(true)
    try {
      await fetch(`${API_BASE}/watchlist/${watch.reach_id}`, {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      })
      onRefresh()
    } finally { setBusy(false) }
  }

  async function remove() {
    setBusy(true)
    try {
      await fetch(`${API_BASE}/watchlist/${watch.reach_id}`, {
        method: 'DELETE', credentials: 'include',
      })
      onRefresh()
    } finally { setBusy(false) }
  }

  const trendArrow = watch.trend_7d > 4 ? '↑' : watch.trend_7d < -4 ? '↓' : '→'
  return (
    <li className="watch-row">
      <div className="watch-row-top">
        <div className="watch-row-name">
          {watch.short_label || watch.name}{' '}
          <span className="watch-row-ws">· {watch.watershed.replace(/_/g, ' ')}</span>
        </div>
        <div className="watch-row-tqs">
          {watch.current_tqs ?? '—'}
          <span className="watch-row-trend">{trendArrow} {Math.abs(watch.trend_7d)}</span>
        </div>
      </div>
      <div className="watch-row-controls">
        <label className="watch-control">
          Alert at
          <input
            type="number" min={0} max={100} value={threshold}
            onChange={e => setThreshold(parseInt(e.target.value || '0'))}
            onBlur={() => threshold !== watch.alert_threshold && update({ alert_threshold: threshold })}
            disabled={busy}
          />
        </label>
        <button
          className={`watch-mute ${muted ? 'on' : ''}`}
          disabled={busy}
          onClick={() => update({
            muted_until: muted ? null : new Date(Date.now() + 7 * 86400_000).toISOString(),
          })}
        >{muted ? 'Unmute' : 'Mute 7d'}</button>
        <button className="watch-remove" disabled={busy} onClick={remove}>Remove</button>
      </div>
    </li>
  )
}

// ── Digest tab ──────────────────────────────────────────────────────────────

interface DigestPayload {
  issued_at: string
  week_of: string
  watershed_summaries: Array<{
    reach_id: string
    name: string
    watershed: string
    threshold: number
    peak: { date: string; tqs: number; band: string } | null
    daily: Array<{ date: string; tqs: number; band: string; is_hard_closed: boolean; band_crossing: boolean }>
  }>
}

function DigestTab() {
  const url = `${API_BASE}/digest/weekly`
  const { data, isLoading } = useSWR<{ digest: DigestPayload | null; week_of?: string }>(url, fetcher)
  if (isLoading) return <div className="alerts-empty">Loading…</div>
  if (!data?.digest) return <div className="alerts-empty">No digest yet — your first weekly outlook arrives Friday morning.</div>

  const d = data.digest
  return (
    <div className="digest-pane">
      <div className="digest-header">
        <div className="digest-week">Week of {d.week_of}</div>
        <div className="digest-issued">Issued {new Date(d.issued_at).toLocaleString()}</div>
      </div>
      {d.watershed_summaries.map(s => (
        <div key={s.reach_id} className="digest-reach">
          <div className="digest-reach-top">
            <div className="digest-reach-name">{s.name}</div>
            {s.peak && (
              <div className="digest-reach-peak">
                Peak: <span className={`digest-peak-score ${bandLabel(s.peak.tqs).cls}`}>{s.peak.tqs}</span> on {s.peak.date}
              </div>
            )}
          </div>
          <div className="digest-strip" role="list">
            {s.daily.map(day => (
              <div
                key={day.date}
                role="listitem"
                className={`digest-day ${bandLabel(day.tqs).cls} ${day.band_crossing ? 'cross' : ''} ${day.is_hard_closed ? 'closed' : ''}`}
                title={`${day.date}: ${day.is_hard_closed ? 'closed' : `${day.tqs} (${day.band})`}`}
              >
                <span className="digest-day-label">{new Date(day.date).toLocaleDateString(undefined, { weekday: 'narrow' })}</span>
                <span className="digest-day-score">{day.is_hard_closed ? '✕' : day.tqs}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
