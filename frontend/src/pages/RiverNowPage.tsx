import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import { tempF } from '../utils/temp'
const dtMark = '/favicon-deeptrail.svg'
import './RiverNowPage.css'

const API = 'http://localhost:8001/api/v1'

const TYPE_ICONS: Record<string, string> = {
  campground: '⛺', trailhead: '🥾', boat_ramp: '🚣', day_use: '☀',
  fishing_access: '🎣', swim_area: '🏊', waterfall: '💧',
}

const WS_CENTERS: Record<string, [number, number]> = {
  mckenzie: [-122.3, 44.08],
  deschutes: [-121.22, 44.33],
  metolius: [-121.57, 44.50],
  klamath: [-121.55, 42.65],
  johnday: [-119.15, 44.60],
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
  const [geology, setGeology] = useState<any[]>([])
  const [fossils, setFossils] = useState<any[]>([])
  const [weather, setWeather] = useState<any>(null)
  const [liveConditions, setLiveConditions] = useState<any>(null)
  const [stocking, setStocking] = useState<any[]>([])
  const [snowpack, setSnowpack] = useState<any>(null)
  const [harvest, setHarvest] = useState<any[]>([])
  const [speciesByReach, setSpeciesByReach] = useState<any[]>([])
  const [barriers, setBarriers] = useState<any[]>([])
  const [catchProb, setCatchProb] = useState<any>(null)
  const [spotter, setSpotter] = useState<any>(null)
  const [replay, setReplay] = useState<any>(null)
  const [campfireStory, setCampfireStory] = useState<string | null>(null)
  const [campfireLoading, setCampfireLoading] = useState(false)
  const [campfireAudio, setCampfireAudio] = useState<HTMLAudioElement | null>(null)
  const [campfirePlaying, setCampfirePlaying] = useState(false)

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
    // Live conditions + weather + stocking
    fetch(`${API}/sites/${watershed}/weather`).then(r => r.json()).then(setWeather).catch(() => {})
    fetch(`${API}/sites/${watershed}/conditions/live`).then(r => r.json()).then(setLiveConditions).catch(() => {})
    fetch(`${API}/sites/${watershed}/fishing/stocking`).then(r => r.json()).then(setStocking).catch(() => {})
    fetch(`${API}/sites/${watershed}/snowpack`).then(r => r.json()).then(setSnowpack).catch(() => {})
    fetch(`${API}/sites/${watershed}/fishing/harvest`).then(r => r.json()).then(setHarvest).catch(() => {})
    fetch(`${API}/sites/${watershed}/fishing/species`).then(r => r.json()).then(setSpeciesByReach).catch(() => {})
    fetch(`${API}/sites/${watershed}/fishing/barriers`).then(r => r.json()).then(setBarriers).catch(() => {})
    fetch(`${API}/sites/${watershed}/catch-probability`).then(r => r.json()).then(setCatchProb).catch(() => {})
    fetch(`${API}/sites/${watershed}/species-spotter`).then(r => r.json()).then(setSpotter).catch(() => {})
    fetch(`${API}/sites/${watershed}/replay?days_ago=30`).then(r => r.json()).then(setReplay).catch(() => {})
    // Geology + fossils for Deep Time card
    const center = WS_CENTERS[watershed]
    if (center) {
      fetch(`${API}/geology/at/${center[1]}/${center[0]}`).then(r => r.json()).then(d => setGeology(d.units || [])).catch(() => {})
      fetch(`${API}/fossils/near/${center[1]}/${center[0]}`).then(r => r.json()).then(d => setFossils(d.fossils || [])).catch(() => {})
    }
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
  const hatchConfidence = topInsects[0]?.confidence || null

  // Prefer live USGS readings over monthly averages
  const liveTemp = liveConditions?.readings?.find((r: any) => r.parameter === 'water_temp_c')
  const liveFlow = liveConditions?.readings?.find((r: any) => r.parameter === 'discharge_cfs')
  const liveDO = liveConditions?.readings?.find((r: any) => r.parameter === 'dissolved_oxygen_mg_l')
  const displayTemp = liveTemp ? `${liveTemp.display_value}°F` : health.water_temp_c != null ? tempF(health.water_temp_c) : null
  const displayFlow = liveFlow ? Math.round(liveFlow.value).toLocaleString() : latest?.discharge_cfs != null ? Math.round(latest.discharge_cfs).toLocaleString() : null
  const displayDO = liveDO ? liveDO.value.toFixed(1) : health.dissolved_oxygen_mg_l
  const isLive = !!(liveTemp || liveFlow)

  const playCampfireStory = async () => {
    if (campfirePlaying && campfireAudio) { campfireAudio.pause(); setCampfirePlaying(false); return }
    setCampfireLoading(true)
    try {
      // Get or generate story (server caches both text + audio)
      const r = await fetch(`${API}/sites/${watershed}/campfire-story`)
      const d = await r.json()
      setCampfireStory(d.story)

      // Play cached audio if available, otherwise fall back to TTS endpoint
      let audioUrl: string
      if (d.audio_url) {
        audioUrl = `http://localhost:8001${d.audio_url}`
      } else {
        const ttsResp = await fetch(`${API}/tts`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: d.story, voice: 'nova' }),
        })
        const blob = await ttsResp.blob()
        audioUrl = URL.createObjectURL(blob)
      }

      const audio = new Audio(audioUrl)
      audio.onended = () => setCampfirePlaying(false)
      setCampfireAudio(audio)
      setCampfirePlaying(true)
      setCampfireLoading(false)
      audio.play()
    } catch { setCampfireLoading(false) }
  }

  // Harvest trend — latest year vs prior
  const latestHarvest = harvest[0]
  const priorHarvest = harvest[1]
  const harvestDelta = latestHarvest && priorHarvest
    ? Math.round(((latestHarvest.harvest - priorHarvest.harvest) / priorHarvest.harvest) * 100)
    : null

  // Deduplicate species by reach for carousel
  const uniqueFishByReach: any[] = []
  const seenFish = new Set<string>()
  for (const s of speciesByReach) {
    const key = s.common_name || s.species
    if (!seenFish.has(key)) {
      seenFish.add(key)
      uniqueFishByReach.push(s)
    }
  }

  // Upcoming stocking
  const upcomingStocking = stocking.filter((s: any) => new Date(s.date) > new Date()).slice(0, 3)
  const recentStocking = stocking.filter((s: any) => new Date(s.date) <= new Date()).slice(0, 3)

  // Weather
  const todayWeather = weather?.periods?.[0]

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
            <div className="rnow-hero-top">
              <h2 className="rnow-hero-title">{site.name}</h2>
              {isLive && <span className="rnow-live-badge">LIVE</span>}
            </div>
            <div className="rnow-hero-metrics">
              {displayTemp && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{displayTemp}</span>
                  <span className="rnow-metric-label">Water Temp</span>
                </div>
              )}
              {displayFlow && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{displayFlow}</span>
                  <span className="rnow-metric-label">Flow (cfs)</span>
                </div>
              )}
              {displayDO != null && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{displayDO}</span>
                  <span className="rnow-metric-label">DO (mg/L)</span>
                </div>
              )}
              {latestHarvest && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">
                    {latestHarvest.harvest?.toLocaleString()}
                    {harvestDelta != null && (
                      <span className={`rnow-delta ${harvestDelta >= 0 ? 'up' : 'down'}`}>
                        {harvestDelta >= 0 ? '↑' : '↓'}{Math.abs(harvestDelta)}%
                      </span>
                    )}
                  </span>
                  <span className="rnow-metric-label">{latestHarvest.species} '{String(latestHarvest.year).slice(2)}</span>
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
              {todayWeather && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{todayWeather.temperature}°F</span>
                  <span className="rnow-metric-label">{todayWeather.forecast}</span>
                </div>
              )}
            </div>
            {health.score != null && (
              <div className="rnow-hero-score">Health Score: <strong>{health.score}</strong>/100</div>
            )}
            {liveTemp && (
              <div className="rnow-hero-station">{liveTemp.station} · {new Date(liveTemp.timestamp).toLocaleTimeString()}</div>
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

          {/* ── River Replay (what changed) ── */}
          {replay && replay.changes?.length > 0 && (
            <div className="rnow-replay">
              <div className="rnow-replay-title">📋 What Changed (Last 30 Days)</div>
              {replay.changes.map((c: any, i: number) => (
                <div key={i} className={`rnow-replay-item ${c.delta > 0 ? 'positive' : c.delta < 0 ? 'negative' : ''}`}>
                  {c.label}
                </div>
              ))}
            </div>
          )}

          {/* ── Catch Probability ── */}
          {catchProb && (
            <div className="rnow-catch-prob">
              <div className="rnow-catch-header">
                <span className="rnow-catch-title">🎣 Catch Probability</span>
                <span className={`rnow-catch-score ${catchProb.overall_level}`}>{catchProb.overall_score}</span>
              </div>
              <div className="rnow-catch-species">
                {catchProb.species?.slice(0, 4).map((s: any, i: number) => (
                  <div key={i} className="rnow-catch-row">
                    <span className="rnow-catch-name">{s.species}</span>
                    <div className="rnow-catch-bar-bg">
                      <div className={`rnow-catch-bar-fill ${s.level}`} style={{ width: `${s.score}%` }}></div>
                    </div>
                    <span className={`rnow-catch-pct ${s.level}`}>{s.score}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Species Spotter ── */}
          {spotter && spotter.species?.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">👀 Likely Sightings Today</div>
              <div className="rnow-spotter-grid">
                {spotter.species.slice(0, 6).map((s: any, i: number) => (
                  <div key={i} className="rnow-spotter-card">
                    {s.photo_url && <img src={s.photo_url} alt={s.common_name} className="rnow-spotter-img" loading="lazy" />}
                    <div className="rnow-spotter-name">{s.common_name}</div>
                    <div className="rnow-spotter-prob">{s.probability}% likely</div>
                    <div className="rnow-spotter-group">{s.group}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ── Campfire Story ── */}
          <section className="rnow-section">
            <button className={`rnow-campfire-btn${campfirePlaying ? ' playing' : ''}`} onClick={playCampfireStory} disabled={campfireLoading}>
              {campfireLoading ? '⏳ Generating story...' : campfirePlaying ? '⏹ Stop Story' : '🔥 Campfire Story'}
            </button>
            {campfireStory && !campfirePlaying && (
              <div className="rnow-campfire-text">{campfireStory}</div>
            )}
          </section>

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

            <div className="rnow-card" onClick={() => navigate(`/path/fish/${watershed}?section=refuges`)}>
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

            {/* Deep Time Card */}
            {geology.length > 0 && (
              <DeepTimeCard geology={geology} fossils={fossils} watershed={watershed} />
            )}
          </div>

          {/* ── Fish Near You (Species by Reach) ── */}
          {uniqueFishByReach.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">🐟 Fish Near You</div>
              <div className="rnow-fish-carousel">
                {uniqueFishByReach.slice(0, 10).map((s: any, i: number) => (
                  <div key={i} className="rnow-fish-card">
                    <div className="rnow-fish-name">{s.common_name || s.species}</div>
                    <div className="rnow-fish-stream">{s.stream}</div>
                    <div className="rnow-fish-use">{s.use_type}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ── Fish Passage Barriers ── */}
          {barriers.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">⚠ Fish Passage Barriers ({barriers.length})</div>
              <div className="rnow-barriers">
                {barriers.slice(0, 5).map((b: any, i: number) => (
                  <div key={i} className="rnow-barrier-item">
                    <span className={`rnow-barrier-dot ${b.passage_status === 'Passable' ? 'pass' : 'block'}`}></span>
                    <span className="rnow-barrier-stream">{b.stream_name || b.barrier_name || '—'}</span>
                    <span className="rnow-barrier-status">{b.passage_status || '—'}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ── Weather Forecast ── */}
          {weather?.periods?.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">Weather Forecast</div>
              <div className="rnow-weather-grid">
                {weather.periods.slice(0, 6).map((p: any, i: number) => (
                  <div key={i} className={`rnow-weather-item${p.is_daytime ? '' : ' night'}`}>
                    <div className="rnow-weather-name">{p.name}</div>
                    <div className="rnow-weather-temp">{p.temperature}°{p.unit}</div>
                    <div className="rnow-weather-desc">{p.forecast}</div>
                    <div className="rnow-weather-wind">{p.wind_speed} {p.wind_direction}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ── Snowpack Card ── */}
          {snowpack && (snowpack.stations_with_snow > 0 || snowpack.station_count > 0) && (
            <section className="rnow-section">
              <div className="rnow-section-title">Snowpack & Mountain Conditions</div>
              <div className="rnow-snowpack-card">
                <div className="rnow-snow-metrics">
                  {snowpack.avg_swe_in != null && (
                    <div className="rnow-snow-metric">
                      <span className="rnow-snow-value">{snowpack.avg_swe_in}"</span>
                      <span className="rnow-snow-label">Avg SWE</span>
                    </div>
                  )}
                  {snowpack.avg_pct_normal != null && (
                    <div className="rnow-snow-metric">
                      <span className={`rnow-snow-value ${snowpack.avg_pct_normal > 90 ? 'good' : snowpack.avg_pct_normal > 50 ? 'moderate' : 'low'}`}>
                        {snowpack.avg_pct_normal}%
                      </span>
                      <span className="rnow-snow-label">of Normal</span>
                    </div>
                  )}
                  <div className="rnow-snow-metric">
                    <span className="rnow-snow-value">{snowpack.stations_with_snow}/{snowpack.station_count}</span>
                    <span className="rnow-snow-label">Stations w/ Snow</span>
                  </div>
                </div>
                {snowpack.stations?.[0]?.swe_7day_change != null && (
                  <div className="rnow-snow-trend">
                    7-day trend: {snowpack.stations[0].swe_7day_change > 0 ? '↑ Building' : snowpack.stations[0].swe_7day_change < -0.3 ? '↓ Melting' : '→ Stable'}
                    {snowpack.stations[0].swe_7day_change !== 0 && ` (${snowpack.stations[0].swe_7day_change > 0 ? '+' : ''}${snowpack.stations[0].swe_7day_change}")`}
                  </div>
                )}
                {snowpack.insight && (
                  <div className="rnow-snow-insight">{snowpack.insight}</div>
                )}
                {snowpack.stations?.[0] && (
                  <div className="rnow-snow-station">
                    Station {snowpack.stations[0].station_id} · {snowpack.stations[0].latest_timestamp ? new Date(snowpack.stations[0].latest_timestamp).toLocaleDateString() : ''}
                  </div>
                )}
              </div>
            </section>
          )}

          {/* ── Stocking Alerts ── */}
          {(upcomingStocking.length > 0 || recentStocking.length > 0) && (
            <section className="rnow-section">
              <div className="rnow-section-title">Fish Stocking</div>
              {upcomingStocking.length > 0 && (
                <div className="rnow-stocking-upcoming">
                  {upcomingStocking.map((s: any, i: number) => (
                    <div key={i} className="rnow-stocking-item upcoming">
                      <span className="rnow-stocking-icon">🐟</span>
                      <div className="rnow-stocking-info">
                        <div className="rnow-stocking-name">{s.waterbody}</div>
                        <div className="rnow-stocking-detail">{s.fish?.toLocaleString()} fish · {s.date}</div>
                      </div>
                      <span className="rnow-stocking-badge">Upcoming</span>
                    </div>
                  ))}
                </div>
              )}
              {recentStocking.length > 0 && (
                <div className="rnow-stocking-recent">
                  {recentStocking.map((s: any, i: number) => (
                    <div key={i} className="rnow-stocking-item">
                      <span className="rnow-stocking-icon">🐟</span>
                      <div className="rnow-stocking-info">
                        <div className="rnow-stocking-name">{s.waterbody}</div>
                        <div className="rnow-stocking-detail">{s.fish?.toLocaleString()} fish · {s.date}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* ── What's Here Now ── */}
          {whatsAlive.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title-row">
                <span className="rnow-section-title">What's Here Now</span>
                <button className="rnow-view-map-btn" onClick={() => navigate(`/path/map/${watershed}`)}>View Map</button>
              </div>
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

// ════════════════════════════════════════════
// Deep Time Card — geology + fossils teaser
// ════════════════════════════════════════════

function DeepTimeCard({ geology, fossils, watershed }: { geology: any[]; fossils: any[]; watershed: string }) {
  // Find the oldest and most interesting geologic unit
  const sorted = [...geology].sort((a, b) => (b.age_max_ma || 0) - (a.age_max_ma || 0))
  const oldest = sorted[0]
  // Find a unit with a formation name for more interesting display
  const named = sorted.find(u => u.formation && u.formation.trim()) || oldest

  const ageDisplay = oldest?.age_max_ma
    ? oldest.age_max_ma >= 1000 ? `${(oldest.age_max_ma / 1000).toFixed(1)} billion` : `${Math.round(oldest.age_max_ma)} million`
    : null

  const fossilCount = fossils.length
  const oldestFossil = fossils.length > 0
    ? fossils.reduce((a, b) => ((a.age_max_ma || 0) > (b.age_max_ma || 0) ? a : b))
    : null

  // Build a story hook
  const rockDesc = oldest?.lithology || oldest?.rock_type || 'ancient rock'
  const period = oldest?.period || ''
  const center = WS_CENTERS[watershed]
  const trailUrl = center ? `/trail?lat=${center[1]}&lon=${center[0]}&from=path` : '/trail'

  return (
    <div className="rnow-card rnow-card-deeptime">
      <div className="deeptime-header">
        <img src={dtMark} alt="DeepTrail" className="deeptime-mark" />
        <span className="deeptime-label">Deep Time</span>
      </div>
      <div className="rnow-card-body">
        {ageDisplay && (
          <div className="deeptime-age">
            <span className="deeptime-age-number">{ageDisplay}</span>
            <span className="deeptime-age-unit"> years old</span>
          </div>
        )}
        <div className="deeptime-description">
          This river flows over {period ? `${period}-era ` : ''}{rockDesc}
          {named?.formation ? ` — the ${named.formation}` : ''}.
        </div>
        {fossilCount > 0 && (
          <div className="deeptime-fossils">
            {fossilCount} fossil{fossilCount !== 1 ? 's' : ''} found nearby
            {oldestFossil?.age_max_ma ? `, oldest: ${Math.round(oldestFossil.age_max_ma)} Ma` : ''}
            {oldestFossil?.taxon_name ? ` (${oldestFossil.taxon_name})` : ''}
          </div>
        )}
      </div>
      <a href={trailUrl} target="_blank" rel="noopener noreferrer" className="rnow-card-action deeptime-link">
        Explore in DeepTrail ↗
      </a>
    </div>
  )
}
