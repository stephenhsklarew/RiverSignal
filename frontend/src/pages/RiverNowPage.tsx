import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import SaveButton from '../components/SaveButton'
import './RiverNowPage.css'

const API = 'http://localhost:8001/api/v1'
const WATERSHEDS = [
  { key: 'mckenzie', label: 'McKenzie' },
  { key: 'deschutes', label: 'Deschutes' },
  { key: 'metolius', label: 'Metolius' },
  { key: 'klamath', label: 'Klamath' },
  { key: 'johnday', label: 'John Day' },
]

const TYPE_ICONS: Record<string, string> = {
  campground: '⛺', trailhead: '🥾', boat_ramp: '🚣', day_use: '☀',
  fishing_access: '🎣', swim_area: '🏊', waterfall: '💧',
}

export default function RiverNowPage() {
  const navigate = useNavigate()
  const [ws, setWs] = useState<string | null>(null)
  const [locating, setLocating] = useState(false)
  const [site, setSite] = useState<any>(null)
  const [conditions, setConditions] = useState<any[]>([])
  const [hatch, setHatch] = useState<any>(null)
  const [refuges, setRefuges] = useState<any[]>([])
  const [species, setSpecies] = useState<any[]>([])
  const [accessPoints, setAccessPoints] = useState<any[]>([])
  const [whatsAlive, setWhatsAlive] = useState<any[]>([])

  // Try GPS on mount
  useEffect(() => {
    if (!navigator.geolocation) return
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        fetch(`${API}/sites/nearest?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`)
          .then(r => r.ok ? r.json() : null)
          .then(data => { if (data) setWs(data.watershed); setLocating(false) })
          .catch(() => setLocating(false))
      },
      () => setLocating(false),
      { timeout: 5000 }
    )
  }, [])

  // Load all data when watershed selected
  useEffect(() => {
    if (!ws) return
    fetch(`${API}/sites/${ws}`).then(r => r.json()).then(setSite)
    fetch(`${API}/sites/${ws}/fishing/conditions`).then(r => r.json()).then(setConditions)
    fetch(`${API}/sites/${ws}/fishing/hatch-confidence`).then(r => r.json()).then(setHatch)
    fetch(`${API}/sites/${ws}/cold-water-refuges`).then(r => r.json()).then(setRefuges)
    fetch(`${API}/sites/${ws}/species?taxonomic_group=Actinopterygii&limit=5`).then(r => r.json()).then(setSpecies)
    fetch(`${API}/sites/${ws}/recreation`).then(r => r.json()).then(d => setAccessPoints(d.slice(0, 8)))
    fetch(`${API}/sites/${ws}/species?limit=6`).then(r => r.json()).then(setWhatsAlive)
  }, [ws])

  const health = site?.health || {}
  const latest = conditions?.[0]
  const topInsects = (hatch?.insects || []).filter((i: any) => i.month === hatch?.current_month).slice(0, 3)
  const coldRefuges = refuges.filter((r: any) => r.thermal_class === 'cold_water_refuge' || r.thermal_class === 'cool_water')
  const fishActive = species.filter((s: any) => s.photo_url).slice(0, 3)

  // Flow trend from last 2 months
  const flowTrend = conditions.length >= 2
    ? (conditions[0]?.discharge_cfs > conditions[1]?.discharge_cfs ? 'Rising ↑' : conditions[0]?.discharge_cfs < conditions[1]?.discharge_cfs ? 'Falling ↓' : 'Stable →')
    : null

  const hatchConfidence = topInsects[0]?.confidence || null

  return (
    <div className="rnow">
      {/* GPS / Watershed picker */}
      <div className="rnow-header">
        {locating ? (
          <div className="rnow-locating">Finding your river...</div>
        ) : !ws ? (
          <div className="rnow-picker">
            <div className="rnow-picker-label">Choose a river</div>
            <div className="rnow-picker-chips">
              {WATERSHEDS.map(w => (
                <button key={w.key} className="rnow-chip" onClick={() => setWs(w.key)}>{w.label}</button>
              ))}
            </div>
          </div>
        ) : (
          <div className="rnow-location">
            <span className="rnow-location-icon">📍</span>
            <span className="rnow-location-name">{site?.name || ws}</span>
            <button className="rnow-change" onClick={() => { setWs(null); setSite(null) }}>Change</button>
          </div>
        )}
      </div>

      {ws && site && (
        <>
          {/* ── Hero Card ── */}
          <div className="rnow-hero">
            <h2 className="rnow-hero-title">{site.name}</h2>
            <div className="rnow-hero-metrics">
              {health.water_temp_c != null && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{health.water_temp_c}°C</span>
                  <span className="rnow-metric-label">Water Temp</span>
                </div>
              )}
              {latest?.discharge_cfs != null && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{Math.round(latest.discharge_cfs).toLocaleString()}</span>
                  <span className="rnow-metric-label">Flow (cfs)</span>
                </div>
              )}
              {flowTrend && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{flowTrend}</span>
                  <span className="rnow-metric-label">Trend</span>
                </div>
              )}
              {health.dissolved_oxygen_mg_l != null && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{health.dissolved_oxygen_mg_l}</span>
                  <span className="rnow-metric-label">DO (mg/L)</span>
                </div>
              )}
              {hatchConfidence && (
                <div className="rnow-metric">
                  <span className={`rnow-metric-value confidence-${hatchConfidence}`}>
                    {hatchConfidence.charAt(0).toUpperCase() + hatchConfidence.slice(1)}
                  </span>
                  <span className="rnow-metric-label">Hatch</span>
                </div>
              )}
            </div>
            {health.score != null && (
              <div className="rnow-hero-score">Health Score: <strong>{health.score}</strong>/100</div>
            )}
          </div>

          {/* ── Swipeable Condition Cards ── */}
          <div className="rnow-cards-label">Current Activity</div>
          <div className="rnow-cards">
            {/* Fish Activity Card */}
            <div className="rnow-card" onClick={() => navigate(`/path/fish/${ws}`)}>
              <div className="rnow-card-header">
                <span className="rnow-card-icon">🐟</span>
                <span className="rnow-card-title">Fish Activity</span>
              </div>
              <div className="rnow-card-body">
                {fishActive.length > 0 ? (
                  <div className="rnow-card-species">
                    {fishActive.map((s: any, i: number) => (
                      <div key={i} className="rnow-mini-species">
                        {s.photo_url && <img src={s.photo_url} alt="" className="rnow-mini-img" />}
                        <span>{s.common_name || s.taxon_name}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span>{site.scorecard?.fish_species || 0} fish species tracked</span>
                )}
                {latest?.steelhead_harvest ? <div className="rnow-card-stat">{latest.steelhead_harvest} steelhead harvested this period</div> : null}
              </div>
              <div className="rnow-card-action">View Fish + Refuges →</div>
            </div>

            {/* Insect Activity Card */}
            <div className="rnow-card" onClick={() => navigate('/path/hatch')}>
              <div className="rnow-card-header">
                <span className="rnow-card-icon">🪰</span>
                <span className="rnow-card-title">Insect Activity</span>
              </div>
              <div className="rnow-card-body">
                {topInsects.length > 0 ? (
                  <div className="rnow-card-species">
                    {topInsects.map((ins: any, i: number) => (
                      <div key={i} className="rnow-mini-species">
                        {ins.photo_url && <img src={ins.photo_url} alt="" className="rnow-mini-img" />}
                        <span>{ins.common_name || ins.taxon_name}</span>
                        <span className={`rnow-conf confidence-${ins.confidence}`}>{ins.confidence}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span>No hatch data this month</span>
                )}
              </div>
              <div className="rnow-card-action">View Hatch Chart →</div>
            </div>

            {/* Refuge Status Card */}
            <div className="rnow-card" onClick={() => navigate(`/path/fish/${ws}`)}>
              <div className="rnow-card-header">
                <span className="rnow-card-icon">❄</span>
                <span className="rnow-card-title">Cold-Water Refuges</span>
              </div>
              <div className="rnow-card-body">
                {coldRefuges.length > 0 ? (
                  <>
                    <div className="rnow-card-stat">{coldRefuges.length} cold/cool refuge stations</div>
                    <div className="rnow-card-detail">
                      {coldRefuges.slice(0, 2).map((r: any, i: number) => (
                        <div key={i} className="rnow-mini-refuge">
                          <span className="refuge-dot" style={{ background: r.thermal_class === 'cold' ? '#2563eb' : '#0d9488' }} />
                          {r.station} — {r.avg_summer_temp_c?.toFixed(1)}°C
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <span>No thermal refuge data</span>
                )}
              </div>
              <div className="rnow-card-action">View Thermal Map →</div>
            </div>
          </div>

          {/* ── What's Here Now ── */}
          {whatsAlive.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">What's Here Now</div>
              <div className="rnow-alive-grid">
                {whatsAlive.map((s: any, i: number) => (
                  <div key={i} className="rnow-alive-item">
                    {s.photo_url && <img src={s.photo_url} alt={s.common_name} className="rnow-alive-img" />}
                    <div className="rnow-alive-name">{s.common_name || s.taxon_name}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ── Nearby Access Points ── */}
          {accessPoints.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">Nearby Access</div>
              <div className="rnow-access-list">
                {accessPoints.map((ap: any, i: number) => (
                  <div key={i} className="rnow-access-card">
                    <span className="rnow-access-icon">{TYPE_ICONS[ap.rec_type] || '📍'}</span>
                    <div className="rnow-access-info">
                      <div className="rnow-access-name">{ap.name}</div>
                      <div className="rnow-access-type">{ap.rec_type.replace('_', ' ')}</div>
                    </div>
                    <SaveButton item={{
                      type: 'recreation',
                      id: `${ap.rec_type}-${ap.id}`,
                      watershed: ws,
                      label: ap.name,
                      sublabel: ap.rec_type.replace('_', ' '),
                    }} size={16} />
                  </div>
                ))}
              </div>
              <Link to="/path/explore" className="rnow-more-link">View all in Explore →</Link>
            </section>
          )}
        </>
      )}
    </div>
  )
}
