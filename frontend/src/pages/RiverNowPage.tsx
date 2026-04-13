import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import { tempF } from '../utils/temp'
import './RiverNowPage.css'

const API = 'http://localhost:8001/api/v1'

const TYPE_ICONS: Record<string, string> = {
  campground: '⛺', trailhead: '🥾', boat_ramp: '🚣', day_use: '☀',
  fishing_access: '🎣', swim_area: '🏊', waterfall: '💧',
}

export default function RiverNowPage() {
  const watershed = useWatershed('/path/now')

  if (!watershed) {
    return <RiverNowDefault />
  }

  return <RiverNowDetail watershed={watershed} />
}

// ════════════════════════════════════════════
// DEFAULT: Same content as /path homepage
// ════════════════════════════════════════════

import logo from '../assets/riverpath-logo.svg'

const WATERSHED_ORDER = ['mckenzie', 'deschutes', 'metolius', 'klamath', 'johnday']
const WATERSHED_LABELS: Record<string, string> = {
  mckenzie: 'McKenzie', deschutes: 'Deschutes', metolius: 'Metolius',
  klamath: 'Klamath', johnday: 'John Day',
}
const PHOTOS: Record<string, string> = {
  mckenzie: 'https://images.unsplash.com/photo-1660806739398-0f0627930230?w=900&h=600&fit=crop',
  deschutes: 'https://images.unsplash.com/photo-1528672903139-6a4496639a68?w=900&h=600&fit=crop',
  metolius: 'https://images.unsplash.com/photo-1657215223750-c4988d4a2635?w=900&h=600&fit=crop',
  klamath: 'https://images.unsplash.com/photo-1566126157268-bd7167924841?w=900&h=600&fit=crop',
  johnday: 'https://images.unsplash.com/photo-1559867243-edf5915deaa7?w=900&h=600&fit=crop',
}
const TAGLINES: Record<string, string> = {
  mckenzie: 'Fire, recovery, and the return of salmon',
  deschutes: '111 miles of canyon ecology and steelhead runs',
  metolius: "Spring-fed sanctuary — Oregon's purest river",
  klamath: 'The largest dam removal in American history',
  johnday: 'Wild & Scenic through ancient fossil beds',
}

function RiverNowDefault() {
  const navigate = useNavigate()
  const [sites, setSites] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all(
      WATERSHED_ORDER.map(ws =>
        fetch(`${API}/sites/${ws}`).then(r => r.json()).then(data => ({ ...data, watershed: ws }))
      )
    ).then(data => { setSites(data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const handleAsk = (ws: string, question: string) => {
    if (question.trim()) {
      navigate(`/path/now/${ws}?q=${encodeURIComponent(question.trim())}`)
    }
  }

  return (
    <div className="rnow-default">
      {/* Logo + nav */}
      <nav className="rnow-default-nav">
        <img src={logo} alt="RiverPath" className="rnow-default-logo" />
      </nav>
      <div className="rnow-default-links">
        {WATERSHED_ORDER.map(ws => (
          <Link key={ws} to={`/path/now/${ws}`} className="rnow-default-link">{WATERSHED_LABELS[ws]}</Link>
        ))}
      </div>

      {/* Watershed cards */}
      <div className="rnow-default-list">
        {loading ? (
          <div className="rnow-loading">Loading rivers...</div>
        ) : (
          sites.map(site => (
            <RiverCard
              key={site.watershed}
              site={site}
              photo={PHOTOS[site.watershed]}
              tagline={TAGLINES[site.watershed]}
              onNavigate={() => navigate(`/path/now/${site.watershed}`)}
              onAsk={(q) => handleAsk(site.watershed, q)}
            />
          ))
        )}
      </div>
    </div>
  )
}

function RiverCard({ site, photo, tagline, onNavigate, onAsk }: {
  site: any; photo: string; tagline: string;
  onNavigate: () => void; onAsk: (q: string) => void
}) {
  const [askInput, setAskInput] = useState('')
  const health = site.health || {}
  const sc = site.scorecard || {}
  const healthClass = (health.score || 0) >= 70 ? 'good' : (health.score || 0) >= 50 ? 'moderate' : 'poor'

  return (
    <div className="river-card">
      <div className="river-card-image" onClick={onNavigate}>
        <img src={photo} alt={site.name} loading="lazy" />
        {health.score != null && (
          <div className="river-card-score-orb">
            <div className={`river-card-score ${healthClass}`}>{health.score}</div>
            <div className="river-card-score-label">health</div>
          </div>
        )}
      </div>
      <div className="river-card-body">
        <h2 className="river-card-name" onClick={onNavigate}>{site.name}</h2>
        <div className="river-card-tagline">{tagline}</div>
        <div className="river-card-pills">
          <span className="river-pill">{sc.total_species?.toLocaleString() || '—'} species</span>
          {health.water_temp_c != null && <span className="river-pill">{tempF(health.water_temp_c)}</span>}
          {sc.total_interventions > 0 && <span className="river-pill">{sc.total_interventions} projects</span>}
        </div>
        <div className="river-card-ask">
          <input
            type="text"
            value={askInput}
            onChange={e => setAskInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && askInput.trim()) onAsk(askInput) }}
            placeholder="How's the fly fishing today?"
          />
          <button onClick={() => { if (askInput.trim()) onAsk(askInput) }}>Ask</button>
        </div>
      </div>
    </div>
  )
}

// ════════════════════════════════════════════
// DETAIL: Full River Now for a specific watershed
// ════════════════════════════════════════════

function RiverNowDetail({ watershed }: { watershed: string }) {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const pendingQuestion = searchParams.get('q')

  const [site, setSite] = useState<any>(null)
  const [siteLoading, setSiteLoading] = useState(true)
  const [conditions, setConditions] = useState<any[]>([])
  const [hatch, setHatch] = useState<any>(null)
  const [refuges, setRefuges] = useState<any[]>([])
  const [fishSpecies, setFishSpecies] = useState<any[]>([])
  const [accessPoints, setAccessPoints] = useState<any[]>([])
  const [whatsAlive, setWhatsAlive] = useState<any[]>([])

  // Inline chat state
  const [askInput, setAskInput] = useState('')
  const [chatQuestion, setChatQuestion] = useState<string | null>(null)
  const [chatAnswer, setChatAnswer] = useState<string | null>(null)
  const [chatLoading, setChatLoading] = useState(false)

  // Load data
  useEffect(() => {
    setSiteLoading(true)
    fetch(`${API}/sites/${watershed}`).then(r => r.json()).then(d => { setSite(d); setSiteLoading(false) }).catch(() => setSiteLoading(false))
    fetch(`${API}/sites/${watershed}/fishing/conditions`).then(r => r.json()).then(setConditions)
    fetch(`${API}/sites/${watershed}/fishing/hatch-confidence`).then(r => r.json()).then(setHatch)
    fetch(`${API}/sites/${watershed}/cold-water-refuges`).then(r => r.json()).then(setRefuges)
    fetch(`${API}/sites/${watershed}/species?taxonomic_group=Actinopterygii&limit=5`).then(r => r.json()).then(setFishSpecies)
    fetch(`${API}/sites/${watershed}/recreation`).then(r => r.json()).then(d => setAccessPoints((d || []).slice(0, 8)))
    fetch(`${API}/sites/${watershed}/species?limit=6`).then(r => r.json()).then(setWhatsAlive)
  }, [watershed])

  // Handle pending question from URL
  useEffect(() => {
    if (!pendingQuestion || chatLoading || chatQuestion) return
    submitQuestion(pendingQuestion)
    setSearchParams({}, { replace: true })
  }, [pendingQuestion])

  const submitQuestion = (question: string) => {
    setChatQuestion(question)
    setChatLoading(true)
    setChatAnswer(null)
    fetch(`${API}/sites/${watershed}/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
      .then(r => r.json())
      .then(data => setChatAnswer(data.answer || data.detail || 'Unable to answer.'))
      .catch(() => setChatAnswer('Set ANTHROPIC_API_KEY to enable AI answers.'))
      .finally(() => setChatLoading(false))
  }

  const handleAsk = () => {
    if (askInput.trim()) {
      submitQuestion(askInput.trim())
      setAskInput('')
    }
  }

  const health = site?.health || {}
  const latest = conditions?.[0]
  const topInsects = (hatch?.insects || []).filter((i: any) => i.month === hatch?.current_month).slice(0, 3)
  const coldRefuges = refuges.filter((r: any) => r.thermal_class === 'cold_water_refuge' || r.thermal_class === 'cool_water')
  const fishActive = fishSpecies.filter((s: any) => s.photo_url).slice(0, 3)
  const flowTrend = conditions.length >= 2
    ? (conditions[0]?.discharge_cfs > conditions[1]?.discharge_cfs ? 'Rising ↑' : conditions[0]?.discharge_cfs < conditions[1]?.discharge_cfs ? 'Falling ↓' : 'Stable →')
    : null
  const hatchConfidence = topInsects[0]?.confidence || null

  return (
    <div className="rnow">
      <WatershedHeader watershed={watershed} basePath="/path/now" />

      {siteLoading && !site && (
        <div className="rnow-loading">Loading {watershed} river data...</div>
      )}

      {site && (
        <>
          {/* ── Hero Card ── */}
          <div className="rnow-hero">
            <h2 className="rnow-hero-title">{site.name}</h2>
            <div className="rnow-hero-metrics">
              {health.water_temp_c != null && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{tempF(health.water_temp_c)}</span>
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

          {/* ── Ask Box + Inline Chat (below hero) ── */}
          <div className="rnow-ask-section">
            <div className="rnow-ask-row">
              <input
                type="text"
                value={askInput}
                onChange={e => setAskInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleAsk() }}
                placeholder={`Ask about the ${site.name.replace('Upper ', '').replace(' River', '')}...`}
                className="rnow-ask-input"
              />
              <button onClick={handleAsk} className="rnow-ask-btn">Ask</button>
            </div>
            {(chatQuestion || chatLoading) && (
              <div className="rnow-chat-response">
                <div className="rnow-chat-question">{chatQuestion}</div>
                {chatLoading ? (
                  <div className="rnow-chat-loading">Thinking...</div>
                ) : chatAnswer ? (
                  <div className="rnow-chat-answer"><Markdown>{chatAnswer}</Markdown></div>
                ) : null}
              </div>
            )}
          </div>

          {/* ── Swipeable Condition Cards ── */}
          <div className="rnow-cards-label">Current Activity</div>
          <div className="rnow-cards">
            <div className="rnow-card" onClick={() => navigate(`/path/fish/${watershed}`)}>
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
              </div>
              <div className="rnow-card-action">View Fish + Refuges →</div>
            </div>

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

            <div className="rnow-card" onClick={() => navigate(`/path/fish/${watershed}`)}>
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
                          <span className="refuge-dot" style={{ background: r.thermal_class === 'cold_water_refuge' ? '#2563eb' : '#0d9488' }} />
                          {r.station} — {r.avg_summer_temp_c != null ? tempF(r.avg_summer_temp_c) : '—'}
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
                      watershed,
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
