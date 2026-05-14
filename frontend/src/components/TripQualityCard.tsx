/**
 * Trip Quality Score (TQS) card for /path/now.
 *
 * Renders three layers from plan §7:
 *  - Pill: "Trip Quality: 82 · Strong · Lower stretch" + reach_spread caveat
 *  - Reach chips: Upper · Middle · Lower (when watershed has ≥2 reaches)
 *  - Why-panel (modal): 6 sub-scores with weighted primary factor highlighted
 *
 * Default reach selection: location.state.reachId → localStorage → best-scoring.
 */
import { useEffect, useMemo, useState } from 'react'
import useSWR, { mutate } from 'swr'
import { useLocation } from 'react-router-dom'
import { API_BASE } from '../config'
import { useAuth } from './AuthContext'
import InfoTooltip from './InfoTooltip'
import LoginModal from './LoginModal'
import './TripQualityCard.css'

// Canonical source IDs that match app/routers/data_status.py freshness keys.
// 'fishing' is the project-wide identifier for ODFW (rendered as "ODFW fishing").
const TQS_SOURCES = ['usgs', 'snotel', 'mtbs', 'fishing', 'prism']
const TQS_TOOLTIP =
  'A 0–100 score blending six things into one number for this stretch of river: ' +
  'catch outlook, water temperature, flow, weather, hatch alignment with the season, ' +
  'and access (closures or active fires). When a reach is closed for a reason, ' +
  'the score is forced into the bottom band and we show a closed badge instead. ' +
  'Tap the pill for a breakdown of each sub-score.'

const DAY_MS = 86_400_000

const SCORE_KEYS = ['catch', 'water_temp', 'flow', 'weather', 'hatch', 'access'] as const
const SCORE_LABELS: Record<string, string> = {
  catch: 'Catch', water_temp: 'Water Temp', flow: 'Flow',
  weather: 'Weather', hatch: 'Hatch', access: 'Access',
}

function bandLabel(tqs: number): { label: string; copy: string; cls: string } {
  if (tqs >= 90) return { label: 'Excellent', copy: 'All indicators favorable', cls: 'excellent' }
  if (tqs >= 70) return { label: 'Strong',     copy: 'Conditions look strong', cls: 'strong' }
  if (tqs >= 50) return { label: 'Mixed',      copy: 'Conditions are mixed — manage expectations', cls: 'mixed' }
  if (tqs >= 30) return { label: 'Marginal',   copy: 'Several indicators weak — better options likely nearby', cls: 'marginal' }
  return            { label: 'Unfavorable', copy: 'Conditions unfavorable', cls: 'unfavorable' }
}

const todayIso = () => new Date().toISOString().slice(0, 10)

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then(r => r.json())

interface ReachScore {
  reach_id: string
  watershed: string
  tqs: number
  confidence: number
  is_hard_closed: boolean
  catch_score: number
  water_temp_score: number
  flow_score: number
  weather_score: number
  hatch_score: number
  access_score: number
  primary_factor: string
  partial_access_flag: boolean
  horizon_days: number
  forecast_source: string
}

interface WatershedRollup extends ReachScore {
  watershed_tqs: number
  best_reach_id: string
  unfavorable_count: number
  total_reaches: number
  reach_spread: number
  reaches: ReachScore[]
}

export default function TripQualityCard({ watershed }: { watershed: string }) {
  const location = useLocation() as { state?: { reachId?: string } }
  const dateIso = todayIso()
  const { data: rollupData, error } = useSWR<WatershedRollup>(
    `${API_BASE}/trip-quality?date=${dateIso}&watershed=${watershed}`,
    fetcher,
    { dedupingInterval: DAY_MS / 4 }
  )
  const { data: reachesData } = useSWR<{ reaches: Array<{ id: string; short_label?: string; name: string }> }>(
    `${API_BASE}/reaches?watershed=${watershed}`,
    fetcher,
    { dedupingInterval: DAY_MS }
  )

  const reachLabels: Record<string, string> = useMemo(() => {
    const out: Record<string, string> = {}
    for (const r of reachesData?.reaches || []) {
      out[r.id] = r.short_label || r.name
    }
    return out
  }, [reachesData])

  const reaches = rollupData?.reaches || []
  const lsKey = `rs_tqs_reach:${watershed}`

  const [selectedReachId, setSelectedReachId] = useState<string | null>(null)
  const [showWhy, setShowWhy] = useState(false)

  // Default reach selection: nav-state > localStorage > best
  useEffect(() => {
    if (!rollupData) return
    const fromNav = location.state?.reachId
    const fromLS = typeof localStorage !== 'undefined' ? localStorage.getItem(lsKey) : null
    const validIds = new Set(reaches.map(r => r.reach_id))
    const pick =
      (fromNav && validIds.has(fromNav)) ? fromNav :
      (fromLS && validIds.has(fromLS)) ? fromLS :
      rollupData.best_reach_id
    setSelectedReachId(pick)
  }, [rollupData, location.state, lsKey, reaches.length])

  const selectedReach = useMemo(
    () => reaches.find(r => r.reach_id === selectedReachId) || null,
    [reaches, selectedReachId]
  )

  function pickReach(id: string) {
    setSelectedReachId(id)
    try { localStorage.setItem(lsKey, id) } catch { /* localStorage may be unavailable */ }
    // Open the why-panel so the user can see the breakdown + add to watchlist.
    setShowWhy(true)
  }

  if (error) return null
  if (!rollupData) {
    return <div className="tqs-card tqs-loading">Loading trip quality…</div>
  }

  const showing: ReachScore | WatershedRollup = selectedReach || rollupData
  const tqs = selectedReach ? selectedReach.tqs : rollupData.watershed_tqs
  const band = bandLabel(tqs)
  const closed = showing.is_hard_closed
  const spread = rollupData.reach_spread || 0
  const showSpreadCaveat = spread >= 0.5 && !selectedReach
  const reachName = selectedReach
    ? (reachLabels[selectedReach.reach_id] || selectedReach.reach_id)
    : (reachLabels[rollupData.best_reach_id] || rollupData.best_reach_id)
  const confidence = showing.confidence

  return (
    <div className="tqs-card">
      <div className="tqs-pill-row">
        <button type="button" className="tqs-pill" onClick={() => setShowWhy(true)} aria-label="Show trip-quality details">
          {closed ? (
            <span className="tqs-closed-badge">Reach closed today</span>
          ) : (
            <>
              <span className="tqs-pill-label">Trip Quality</span>
              <span className={`tqs-pill-score ${band.cls}`}>{tqs}</span>
              <span className="tqs-pill-band">{band.label}</span>
              <span className="tqs-pill-reach">· {reachName}</span>
              {confidence < 90 && (
                <span className="tqs-pill-confidence">±{Math.round(100 - confidence)}</span>
              )}
            </>
          )}
        </button>
        <InfoTooltip text={TQS_TOOLTIP} sources={TQS_SOURCES} />
      </div>

      {showSpreadCaveat && !closed && (
        <div className="tqs-spread-caveat">
          {reachName} only — {rollupData.unfavorable_count} of {rollupData.total_reaches} reaches unfavorable
        </div>
      )}

      {reaches.length >= 2 && (
        <div className="tqs-reach-chips">
          {reaches.map(r => (
            <button
              key={r.reach_id}
              type="button"
              className={`tqs-reach-chip ${r.reach_id === selectedReachId ? 'on' : ''} ${r.is_hard_closed ? 'closed' : ''}`}
              onClick={() => pickReach(r.reach_id)}
            >
              <span className="tqs-chip-label">{reachLabels[r.reach_id] || r.reach_id}</span>
              <span className="tqs-chip-score">{r.is_hard_closed ? '✕' : r.tqs}</span>
            </button>
          ))}
        </div>
      )}

      {showWhy && (
        <WhyPanel
          reach={showing as ReachScore}
          band={band}
          reachName={reachName}
          onClose={() => setShowWhy(false)}
        />
      )}
    </div>
  )
}

function GuideDivergenceNote({ reachId, tqs }: { reachId: string; tqs: number }) {
  const dateIso = todayIso()
  const { data } = useSWR<{ median_availability_pct: number | null; guide_count: number }>(
    `${API_BASE}/guide-availability/${reachId}?date=${dateIso}`,
    (u: string) => fetch(u).then(r => r.json())
  )
  // Surface only when TQS ≥ 75 AND guides have unusual availability ≥ 60%
  if (!data?.median_availability_pct || data.guide_count < 1) return null
  if (tqs < 75) return null
  if (data.median_availability_pct < 60) return null
  return (
    <div className="tqs-why-note">
      Local guides have unusual availability for this date
      (median {Math.round(data.median_availability_pct)}% open across {data.guide_count} {data.guide_count === 1 ? 'guide' : 'guides'}).
    </div>
  )
}

function WatchButton({ reachId }: { reachId: string }) {
  const { isLoggedIn } = useAuth()
  const watchlistUrl = `${API_BASE}/watchlist`
  const { data, mutate: refetch } = useSWR<{ watches: Array<{ reach_id: string }> }>(
    isLoggedIn ? watchlistUrl : null,
    (u: string) => fetch(u, { credentials: 'include' }).then(r => r.json())
  )
  const watching = !!data?.watches?.find(w => w.reach_id === reachId)
  const [busy, setBusy] = useState(false)
  const [showLogin, setShowLogin] = useState(false)

  async function toggle() {
    if (!isLoggedIn) { setShowLogin(true); return }
    setBusy(true)
    try {
      if (watching) {
        await fetch(`${watchlistUrl}/${reachId}`, { method: 'DELETE', credentials: 'include' })
      } else {
        await fetch(watchlistUrl, {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reach_id: reachId }),
        })
      }
      refetch()
      mutate(watchlistUrl)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <button
        type="button"
        className={`tqs-watch ${watching ? 'on' : ''}`}
        onClick={toggle}
        disabled={busy}
        aria-pressed={watching}
      >
        {watching ? '★ Watching' : '☆ Watch this reach'}
      </button>
      {showLogin && (
        <LoginModal onClose={() => setShowLogin(false)} mode="signup" />
      )}
    </>
  )
}

function WhyPanel({
  reach, band, reachName, onClose,
}: {
  reach: ReachScore
  band: ReturnType<typeof bandLabel>
  reachName: string
  onClose: () => void
}) {
  const scores: Record<string, number> = {
    catch: reach.catch_score, water_temp: reach.water_temp_score,
    flow: reach.flow_score, weather: reach.weather_score,
    hatch: reach.hatch_score, access: reach.access_score,
  }
  return (
    <div className="tqs-why-overlay" onClick={onClose}>
      <div className="tqs-why-card" onClick={e => e.stopPropagation()}>
        <button className="tqs-why-close" onClick={onClose}>✕</button>
        <div className="tqs-why-header">
          <div className="tqs-why-reach">{reachName}</div>
          <div className="tqs-why-title">
            <span className={`tqs-why-score ${band.cls}`}>{reach.tqs}</span>
            <span className="tqs-why-band">{band.label}</span>
          </div>
          <div className="tqs-why-copy">{band.copy}</div>
          {reach.partial_access_flag && (
            <div className="tqs-why-warning">⚠ Partial access concern — see access score</div>
          )}
          <GuideDivergenceNote reachId={reach.reach_id} tqs={reach.tqs} />
        </div>

        <ul className="tqs-why-list">
          {SCORE_KEYS.map(k => {
            const v = scores[k]
            const isPrimary = k === reach.primary_factor
            // Hide weather while v0.5 ships with weather_score = 0
            if (k === 'weather' && v === 0) return null
            return (
              <li key={k} className={`tqs-why-row ${isPrimary ? 'primary' : ''}`}>
                <span className="tqs-why-row-label">
                  {SCORE_LABELS[k]}{isPrimary && <span className="tqs-why-primary-tag"> · biggest factor</span>}
                </span>
                <span className="tqs-why-row-bar">
                  <span className="tqs-why-row-fill" style={{ width: `${v}%` }} />
                </span>
                <span className="tqs-why-row-value">{v}</span>
              </li>
            )
          })}
        </ul>

        <WatchButton reachId={reach.reach_id} />

        <div className="tqs-why-meta">
          Confidence ±{Math.round(100 - reach.confidence)} ·
          source: {reach.forecast_source} ·
          horizon: {reach.horizon_days}d
        </div>
      </div>
    </div>
  )
}
