/**
 * /path/where — ranking page (plan §7 pull surface).
 *
 * Inputs: home location (geolocate or manual lat/lon), max miles.
 * Output: watersheds sorted by best-reach TQS, with drive distance,
 * primary factor, reach_spread indicator. Tap row → expand to show
 * all reaches in that watershed.
 */
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useSWR from 'swr'
import { API_BASE } from '../config'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import './WherePage.css'

const FIVE_MIN = 5 * 60 * 1000

const todayIso = () => new Date().toISOString().slice(0, 10)
const fetcher = (url: string) => fetch(url).then(r => r.json())

interface RankRow {
  watershed: string
  best_reach_id: string
  best_reach_name: string
  watershed_tqs: number
  confidence: number
  primary_factor: string
  miles_from_user: number
  unfavorable_count: number
  total_reaches: number
  reach_spread: number
}

function bandLabel(tqs: number): { label: string; cls: string } {
  if (tqs >= 90) return { label: 'Excellent', cls: 'excellent' }
  if (tqs >= 70) return { label: 'Strong', cls: 'strong' }
  if (tqs >= 50) return { label: 'Mixed', cls: 'mixed' }
  if (tqs >= 30) return { label: 'Marginal', cls: 'marginal' }
  return            { label: 'Unfavorable', cls: 'unfavorable' }
}

const FACTOR_LABEL: Record<string, string> = {
  catch: 'catch outlook', water_temp: 'water temperature', flow: 'flow',
  weather: 'weather', hatch: 'hatch alignment', access: 'access',
}

export default function WherePage() {
  const navigate = useNavigate()
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null)
  const [maxMiles, setMaxMiles] = useState(150)
  const [onlyStrong, setOnlyStrong] = useState(false)
  const [geoError, setGeoError] = useState<string | null>(null)

  useEffect(() => {
    // Read last-used location from localStorage; otherwise geolocate on mount
    try {
      const saved = localStorage.getItem('rs_where_home')
      if (saved) {
        const p = JSON.parse(saved)
        if (typeof p.lat === 'number' && typeof p.lon === 'number') {
          setCoords(p)
          return
        }
      }
    } catch { /* ignore */ }
    if (typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          const c = { lat: pos.coords.latitude, lon: pos.coords.longitude }
          setCoords(c)
          try { localStorage.setItem('rs_where_home', JSON.stringify(c)) } catch { /* ignore */ }
        },
        err => setGeoError(err.message),
        { timeout: 5000 }
      )
    }
  }, [])

  const url = coords
    ? `${API_BASE}/trip-quality/ranking?date=${todayIso()}&user_lat=${coords.lat}&user_lon=${coords.lon}&max_miles=${maxMiles}`
    : null
  const { data, error, isLoading } = useSWR<{ date: string; results: RankRow[] }>(
    url, fetcher, { dedupingInterval: FIVE_MIN }
  )

  const [expanded, setExpanded] = useState<string | null>(null)

  const filtered = (data?.results || []).filter(r => !onlyStrong || r.watershed_tqs >= 70)

  const ws = getSelectedWatershed() || 'mckenzie'

  return (
    <>
      <WatershedHeader watershed={ws} basePath="/path/where" />
      <div className="where-page">
        <div className="where-header">
          <Link to={`/path/now/${ws}`} className="where-back">← {ws.replace(/_/g, ' ')}</Link>
          <h1 className="where-title">Where should I fish?</h1>
          <p className="where-sub">Best Go Score within drive distance, today.</p>
        </div>

      <div className="where-controls">
        <label className="where-control">
          <span>Max miles</span>
          <input
            type="range" min={25} max={400} step={25}
            value={maxMiles} onChange={e => setMaxMiles(parseInt(e.target.value))}
          />
          <span className="where-value">{maxMiles} mi</span>
        </label>
        <label className="where-control where-control-checkbox">
          <input type="checkbox" checked={onlyStrong} onChange={e => setOnlyStrong(e.target.checked)} />
          <span>Only Strong (≥ 70)</span>
        </label>
        {coords && (
          <div className="where-coords">
            from {coords.lat.toFixed(2)}, {coords.lon.toFixed(2)}{' '}
            <button
              className="where-relocate"
              onClick={() => { localStorage.removeItem('rs_where_home'); setCoords(null) }}
            >
              relocate
            </button>
          </div>
        )}
      </div>

      {!coords && !geoError && (
        <div className="where-empty">Locating you…</div>
      )}
      {geoError && (
        <div className="where-error">
          Couldn't read your location ({geoError}). Try again, or enter coordinates manually.
        </div>
      )}
      {isLoading && coords && <div className="where-empty">Loading rankings…</div>}
      {error && <div className="where-error">Couldn't load rankings.</div>}

      {filtered.length === 0 && coords && !isLoading && !error && (
        <div className="where-empty">No watersheds within {maxMiles} miles.</div>
      )}

      <ol className="where-list">
        {filtered.map(r => {
          const band = bandLabel(r.watershed_tqs)
          const open = expanded === r.watershed
          return (
            <li key={r.watershed} className="where-row">
              <button
                type="button"
                className="where-row-main"
                onClick={() => setExpanded(open ? null : r.watershed)}
              >
                <span className={`where-score ${band.cls}`}>{r.watershed_tqs}</span>
                <span className="where-row-body">
                  <span className="where-row-name">
                    {r.watershed.replace(/_/g, ' ')}
                    <span className="where-row-reach"> · {r.best_reach_name}</span>
                  </span>
                  <span className="where-row-meta">
                    {Math.round(r.miles_from_user)} mi · {band.label}
                    {r.reach_spread >= 0.5 && (
                      <span className="where-row-spread"> · {r.unfavorable_count}/{r.total_reaches} reaches unfavorable</span>
                    )}
                  </span>
                  <span className="where-row-factor">
                    biggest factor: {FACTOR_LABEL[r.primary_factor] || r.primary_factor}
                  </span>
                </span>
                <span className="where-row-chevron">{open ? '−' : '+'}</span>
              </button>
              {open && (
                <WatershedExpansion
                  watershed={r.watershed}
                  bestReachId={r.best_reach_id}
                  onJump={(reachId) => navigate(`/path/now/${r.watershed}`, { state: { reachId } })}
                />
              )}
            </li>
          )
        })}
      </ol>
      </div>
    </>
  )
}

function WatershedExpansion({
  watershed, bestReachId, onJump,
}: { watershed: string; bestReachId: string; onJump: (reachId: string) => void }) {
  const { data } = useSWR<{ reaches: Array<{
    reach_id: string; tqs: number; is_hard_closed: boolean; primary_factor: string;
  }> }>(
    `${API_BASE}/trip-quality?date=${todayIso()}&watershed=${watershed}`,
    fetcher,
    { dedupingInterval: FIVE_MIN }
  )
  const { data: reachMeta } = useSWR<{ reaches: Array<{ id: string; short_label?: string; name: string }> }>(
    `${API_BASE}/reaches?watershed=${watershed}`,
    fetcher,
    { dedupingInterval: 86400000 }
  )
  if (!data) return <div className="where-expand-loading">…</div>
  const labels: Record<string, string> = {}
  for (const m of reachMeta?.reaches || []) labels[m.id] = m.short_label || m.name
  return (
    <ul className="where-expand">
      {data.reaches.map(r => {
        const band = bandLabel(r.tqs)
        return (
          <li key={r.reach_id}>
            <button
              className={`where-expand-row ${r.reach_id === bestReachId ? 'best' : ''} ${r.is_hard_closed ? 'closed' : ''}`}
              onClick={() => onJump(r.reach_id)}
            >
              <span className={`where-expand-score ${band.cls}`}>{r.is_hard_closed ? '✕' : r.tqs}</span>
              <span className="where-expand-name">{labels[r.reach_id] || r.reach_id}</span>
              <span className="where-expand-band">{r.is_hard_closed ? 'closed' : band.label}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
