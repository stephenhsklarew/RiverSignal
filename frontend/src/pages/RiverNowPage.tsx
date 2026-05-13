import { useEffect, useState } from 'react'
import useSWR from 'swr'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { CardSettingsPanel, loadCardSettings, type CardConfig } from '../components/CardSettings'
import { useWatershed } from '../hooks/useWatershed'
import { tempF } from '../utils/temp'
import PhotoObservation from '../components/PhotoObservation'
import InfoTooltip from '../components/InfoTooltip'
import TripQualityCard from '../components/TripQualityCard'
import { useAuth } from '../components/AuthContext'
const dtMark = '/favicon-deeptrail.svg'
import { API_BASE } from '../config'
import './RiverNowPage.css'

const API = API_BASE

const TYPE_ICONS: Record<string, string> = {
  campground: '⛺', trailhead: '🥾', boat_ramp: '🚣', day_use: '☀',
  fishing_access: '🎣', swim_area: '🏊', waterfall: '💧',
}

const WS_CENTERS: Record<string, [number, number]> = {
  deschutes: [-121.22, 44.33],
  green_river: [-110.15, 38.99],
  johnday: [-119.15, 44.60],
  klamath: [-121.55, 42.65],
  mckenzie: [-122.3, 44.08],
  metolius: [-121.57, 44.50],
  skagit: [-121.50, 48.45],
}

export default function RiverNowPage() {
  const watershed = useWatershed('/path/now')

  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])

  if (!watershed) {
    return <RiverNowDefault />
  }

  return <RiverNowDetail watershed={watershed} />
}

// ════════════════════════════════════════════
// DEFAULT: Same content as /path homepage
// ════════════════════════════════════════════

import logo from '../assets/riverpath-logo.svg'

const WATERSHED_ORDER = ['deschutes', 'green_river', 'johnday', 'klamath', 'mckenzie', 'metolius', 'skagit']
const PHOTOS: Record<string, string> = {
  deschutes: 'https://images.unsplash.com/photo-1528672903139-6a4496639a68?w=900&h=600&fit=crop',
  green_river: 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=900&h=600&fit=crop',
  johnday: 'https://images.unsplash.com/photo-1559867243-edf5915deaa7?w=900&h=600&fit=crop',
  klamath: 'https://images.unsplash.com/photo-1566126157268-bd7167924841?w=900&h=600&fit=crop',
  mckenzie: 'https://images.unsplash.com/photo-1660806739398-0f0627930230?w=900&h=600&fit=crop',
  metolius: 'https://images.unsplash.com/photo-1657215223750-c4988d4a2635?w=900&h=600&fit=crop',
  skagit: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900&h=600&fit=crop',
}
const TAGLINES: Record<string, string> = {
  deschutes: '111 miles of canyon ecology and steelhead runs',
  green_river: 'Desert canyons, ancient rock, and Colorado cutthroat',
  johnday: 'Wild & Scenic through ancient fossil beds',
  klamath: 'The largest dam removal in American history',
  mckenzie: 'Fire, recovery, and the return of salmon',
  metolius: "Spring-fed sanctuary — Oregon's purest river",
  skagit: 'All five salmon species in the shadow of the North Cascades',
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

// Watershed → state-specific source identifiers for tooltips.
// 'fishing' is the ODFW (Oregon) adapter; 'washington' and 'utah' are the
// state-bundle adapters that include stocking + parks + access points.
const WS_STATE_SOURCES: Record<string, { stocking: string[]; access: string[] }> = {
  skagit:      { stocking: ['washington'],         access: ['recreation', 'washington'] },
  green_river: { stocking: ['utah'],               access: ['recreation', 'utah'] },
}
const DEFAULT_STATE_SOURCES = { stocking: ['fishing'], access: ['recreation'] }

function RiverNowDetail({ watershed }: { watershed: string }) {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const pendingQuestion = searchParams.get('q')
  const stateSources = WS_STATE_SOURCES[watershed] || DEFAULT_STATE_SOURCES

  // ─── SWR-backed page data (stale-while-revalidate, cache survives navigation) ───
  // TTL bands:
  //   ~ 60 s   : "near-live" — live USGS gauges
  //   ~ 30 min : weather, fishing conditions, catch probability
  //   ~ 1 h    : hatch, snowpack, stocking, spotter, site basics
  //   ~ 6 h    : cold-water refuges, recreation access, what's alive
  //   ~ 24 h   : species lists, harvest, barriers, fly shops, time-machine, replay,
  //              river story, geology, fossils
  const MIN = 60_000
  const HOUR = 60 * MIN
  const DAY = 24 * HOUR

  const { data: site, isLoading: siteLoading } = useSWR<any>(`/sites/${watershed}`, { dedupingInterval: HOUR })
  const { data: conditions = [] } = useSWR<any[]>(`/sites/${watershed}/fishing/conditions`, { dedupingInterval: 30 * MIN })
  const { data: hatch } = useSWR<any>(`/sites/${watershed}/fishing/hatch-confidence`, { dedupingInterval: HOUR })
  const { data: refuges = [] } = useSWR<any[]>(`/sites/${watershed}/cold-water-refuges`, { dedupingInterval: 6 * HOUR })
  const { data: fishSpecies = [] } = useSWR<any[]>(`/sites/${watershed}/species?taxonomic_group=Actinopterygii&limit=5`, { dedupingInterval: DAY })
  const { data: recreationData } = useSWR<any[]>(`/sites/${watershed}/recreation`, { dedupingInterval: 6 * HOUR })
  const accessPoints = (recreationData || []).slice(0, 8)
  const { data: whatsAlive = [] } = useSWR<any[]>(`/sites/${watershed}/species?limit=6`, { dedupingInterval: 6 * HOUR })
  const { data: weather } = useSWR<any>(`/sites/${watershed}/weather`, { dedupingInterval: 30 * MIN })
  const { data: liveConditions } = useSWR<any>(`/sites/${watershed}/conditions/live`, { dedupingInterval: MIN })
  const { data: stocking = [] } = useSWR<any[]>(`/sites/${watershed}/fishing/stocking`, { dedupingInterval: HOUR })
  const { data: snowpack } = useSWR<any>(`/sites/${watershed}/snowpack`, { dedupingInterval: HOUR })
  const { data: harvest = [] } = useSWR<any[]>(`/sites/${watershed}/fishing/harvest`, { dedupingInterval: DAY })
  const { data: speciesByReach = [] } = useSWR<any[]>(`/sites/${watershed}/fishing/species`, { dedupingInterval: DAY })
  const { data: barriers = [] } = useSWR<any[]>(`/sites/${watershed}/fishing/barriers`, { dedupingInterval: DAY })
  const { data: flyShops = [] } = useSWR<any[]>(`/sites/${watershed}/fly-shops`, { dedupingInterval: DAY })
  const { data: catchProb } = useSWR<any>(`/sites/${watershed}/catch-probability`, { dedupingInterval: 30 * MIN })
  const { data: spotter } = useSWR<any>(`/sites/${watershed}/species-spotter`, { dedupingInterval: HOUR })
  const { data: replay } = useSWR<any>(`/sites/${watershed}/replay?days_ago=30`, { dedupingInterval: DAY })
  const { data: timeMachine } = useSWR<any>(`/sites/${watershed}/time-machine`, { dedupingInterval: DAY })

  // Conditional keys (skip the fetch when there's no watershed center).
  const center = WS_CENTERS[watershed]
  const { data: geologyData } = useSWR<any>(center ? `/geology/at/${center[1]}/${center[0]}` : null, { dedupingInterval: DAY })
  const { data: fossilsData } = useSWR<any>(center ? `/fossils/near/${center[1]}/${center[0]}` : null, { dedupingInterval: DAY })
  const geology = geologyData?.units || []
  const fossils = fossilsData?.fossils || []

  const { hasPersona } = useAuth()
  // family_outdoor persona defaults to Kids reading level (overridable by user)
  const [riverStoryLevel, setRiverStoryLevel] = useState<string>(() => hasPersona('family_outdoor') ? 'kids' : 'adult')
  const { data: riverStoryData, isLoading: riverStoryLoading } = useSWR<any>(
    `/sites/${watershed}/river-story?reading_level=${riverStoryLevel}`,
    { dedupingInterval: DAY }
  )
  const riverStory: string = riverStoryData?.narrative || ''
  const riverStoryAudioUrl: string | null = riverStoryData?.audio_url || null

  // Side effect: derive selected year from time-machine response.
  const [tmYear, setTmYear] = useState<number | null>(null)
  useEffect(() => {
    if (timeMachine?.years?.length) {
      setTmYear(timeMachine.years[timeMachine.years.length - 1].year)
    }
  }, [timeMachine])

  // User-triggered: comparison fetch fires on demand (not on mount), so plain fetch is fine.
  const [compareWs, setCompareWs] = useState<string | null>(null)
  const [compareData, setCompareData] = useState<any>(null)

  // Audio playback state for the river-story TTS.
  const [riverStorySpeaking, setRiverStorySpeaking] = useState(false)
  const [riverStoryAudioLoading, setRiverStoryAudioLoading] = useState(false)
  const [riverStoryAudioEl, setRiverStoryAudioEl] = useState<HTMLAudioElement | null>(null)

  // Card customization
  const [cardConfig, setCardConfig] = useState<CardConfig[]>(loadCardSettings)
  const [showSettings, setShowSettings] = useState(false)

  // Generate dynamic CSS to hide/reorder cards
  const cardStyle = cardConfig.map((c, i) => {
    const rules = [`[data-card="${c.id}"] { order: ${i}; }`]
    if (!c.visible) rules.push(`[data-card="${c.id}"] { display: none !important; }`)
    return rules.join('\n')
  }).join('\n')

  // Inline chat state
  const [askInput, setAskInput] = useState('')
  const [chatQuestion, setChatQuestion] = useState<string | null>(null)
  const [chatAnswer, setChatAnswer] = useState<string | null>(null)
  const [chatLoading, setChatLoading] = useState(false)

  // All page data is loaded declaratively via useSWR above — no imperative fetch effect.

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
    // Try River Oracle first, fall back to basic chat
    fetch(`${API}/river-oracle`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, watershed }),
    })
      .then(r => {
        if (!r.ok) throw new Error('oracle failed')
        return r.json()
      })
      .then(data => setChatAnswer(data.answer || data.detail || 'Unable to answer.'))
      .catch(() => {
        // Fallback to basic chat endpoint
        fetch(`${API}/sites/${watershed}/chat`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question }),
        })
          .then(r => r.json())
          .then(data => setChatAnswer(data.answer || data.detail || 'Unable to answer.'))
          .catch(() => setChatAnswer('Set ANTHROPIC_API_KEY to enable AI answers.'))
      })
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

  const handleRiverStoryLevelChange = (level: string) => {
    // Changing the level changes the SWR key, which triggers a refetch automatically.
    setRiverStoryLevel(level)
    if (riverStoryAudioEl) { riverStoryAudioEl.pause(); setRiverStorySpeaking(false) }
  }

  const speakRiverStory = () => {
    // Stop if already playing
    if (riverStorySpeaking) {
      if (riverStoryAudioEl) { riverStoryAudioEl.pause(); setRiverStoryAudioEl(null) }
      else window.speechSynthesis.cancel()
      setRiverStorySpeaking(false)
      return
    }
    if (!riverStory) return

    // Prefer cached OpenAI audio
    if (riverStoryAudioUrl) {
      setRiverStoryAudioLoading(true)
      const audioFetchUrl = riverStoryAudioUrl.startsWith('http') ? riverStoryAudioUrl : `${new URL(API_BASE).origin}${riverStoryAudioUrl}`
      fetch(audioFetchUrl)
        .then(r => r.blob())
        .then(blob => {
          const url = URL.createObjectURL(blob)
          const audio = new Audio(url)
          audio.onended = () => { setRiverStorySpeaking(false); setRiverStoryAudioEl(null) }
          setRiverStoryAudioEl(audio)
          setRiverStorySpeaking(true)
          setRiverStoryAudioLoading(false)
          audio.play()
        })
        .catch(() => { setRiverStoryAudioLoading(false) })
      return
    }

    // Fallback to browser speech synthesis
    setRiverStoryAudioLoading(true)
    const utterance = new SpeechSynthesisUtterance(riverStory)
    utterance.rate = 0.95
    utterance.onend = () => setRiverStorySpeaking(false)
    utterance.onerror = () => { setRiverStorySpeaking(false); setRiverStoryAudioLoading(false) }
    window.speechSynthesis.speak(utterance)
    setRiverStorySpeaking(true)
    setRiverStoryAudioLoading(false)
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
      <style dangerouslySetInnerHTML={{ __html: cardStyle }} />
      <WatershedHeader watershed={watershed} basePath="/path/now" onSettingsClick={() => setShowSettings(true)} />
      {showSettings && (
        <CardSettingsPanel cards={cardConfig} onChange={setCardConfig} onClose={() => setShowSettings(false)} />
      )}

      {siteLoading && !site && (
        <div className="rnow-loading">Loading {watershed} river data...</div>
      )}

      {site && (
        <>
          {/* ── TQS Card (above hero) ── */}
          <TripQualityCard watershed={watershed} />

          {/* ── Hero Card ── */}
          <div className="rnow-hero">
            {isLive && (
              <div className="rnow-hero-top">
                <span className="rnow-live-badge">LIVE</span>
              </div>
            )}
            <div className="rnow-hero-metrics">
              {displayTemp && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{displayTemp}</span>
                  <span className="rnow-metric-label">Water Temp <InfoTooltip text="Right-now water temperature from the closest USGS stream gauge to this river. The reading refreshes every 15 minutes." sources={['usgs']} /></span>
                </div>
              )}
              {displayFlow && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{displayFlow}</span>
                  <span className="rnow-metric-label">Flow (cfs) <InfoTooltip text="How much water the river is moving right now, in cubic feet per second, from the closest USGS gauge. Refreshes every 15 minutes. Higher flow means faster, deeper water." sources={['usgs']} /></span>
                </div>
              )}
              {displayDO != null && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{displayDO}</span>
                  <span className="rnow-metric-label">DO (mg/L) <InfoTooltip text="Dissolved oxygen — how much oxygen is in the water. Fish need it to breathe; trout do best above about 8 mg/L. Reading comes from the closest USGS gauge that measures oxygen (not every gauge does, so this may be a different station than the temperature reading)." sources={['usgs']} /></span>
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
                  <span className="rnow-metric-label">{latestHarvest.species} '{String(latestHarvest.year).slice(2)} <InfoTooltip text="How many of this species were caught and kept by anglers in the most recent year the state wildlife agency has published. The arrow shows whether the count went up or down from the year before." sources={stateSources.stocking} /></span>
                </div>
              )}
              {hatchConfidence && (
                <div className="rnow-metric">
                  <span className={`rnow-metric-value confidence-${hatchConfidence}`}>
                    {hatchConfidence.charAt(0).toUpperCase() + hatchConfidence.slice(1)}
                  </span>
                  <span className="rnow-metric-label">Hatch <InfoTooltip text="How likely the insects fish eat are hatching right now. We add up how warm the water has been over the season (warm water triggers emergence) and compare to the timing each insect typically needs. HIGH means peak hatch. MEDIUM means insects are active but not yet at peak." sources={['snotel', 'usgs']} /></span>
                </div>
              )}
              {todayWeather && (
                <div className="rnow-metric">
                  <span className="rnow-metric-value">{todayWeather.temperature}°F</span>
                  <span className="rnow-metric-label">{todayWeather.forecast} <InfoTooltip text="Today's air temperature and conditions from the National Weather Service for the center of this watershed. The forecast is fetched fresh and held for 30 minutes between requests." /></span>
                </div>
              )}
            </div>
            {health.score != null && (
              <div className="rnow-hero-score">Health Score: <strong>{health.score}</strong>/100 <InfoTooltip text="A 0–100 snapshot of how this river is doing right now. We look at how the current water temperature and oxygen level compare to historical averages for this time of year, plus how many different species have been observed lately — more variety generally means a healthier river." sources={['usgs', 'inaturalist']} /></div>
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

          <div className="rnow-card-container">
          <div data-card="river_replay">
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

          </div>
          <div data-card="catch_probability">
          {/* ── Catch Probability ── */}
          {catchProb && (
            <div className="rnow-catch-prob">
              <div className="rnow-catch-header">
                <span className="rnow-catch-title">🎣 Catch Probability <InfoTooltip text="How likely you are to catch each species today. We combine current water temperature versus what each species prefers, the season, what bugs are hatching, recent stocking, and whether there are cold-water hiding spots nearby." sources={['usgs', 'fishing', 'inaturalist']} /></span>
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

          </div>
          <div data-card="species_spotter">
          {/* ── What Fish Are Eating ── */}
          {spotter && spotter.species?.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title-row">
                <span className="rnow-section-title">🪰 What Fish Are Eating Now <InfoTooltip text="Which bugs and insects fish are eating right now. Each insect species emerges when the water has warmed up enough, not on a specific date. We combine those temperature signals with recent sightings by citizen scientists and expert hatch charts to rank the most likely active insects." sources={['usgs', 'wqp_bugs', 'inaturalist']} /></span>
                <button className="rnow-view-map-btn" onClick={() => navigate(`/path/map/${watershed}?filter=eating_now`)}>View Map</button>
              </div>
              <div className="rnow-spotter-grid">
                {spotter.species.slice(0, 6).map((s: any, i: number) => (
                  <div key={i} className="rnow-spotter-card">
                    {s.photo_url && <img src={s.photo_url} alt={s.common_name} className="rnow-spotter-img" loading="lazy" title={s.observer ? `📷 ${s.observer}` : undefined} />}
                    <div className="rnow-spotter-name">{s.common_name}</div>
                    <div className="rnow-spotter-prob">{s.probability}% likely</div>
                    <div className="rnow-spotter-group">{s.group}</div>
                    {s.note && <div className="rnow-spotter-note">{s.note}</div>}
                    {s.observer && <div className="rnow-photo-credit">📷 {s.observer}</div>}
                  </div>
                ))}
              </div>
            </section>
          )}

          </div>
          <div data-card="campfire_story">
          {/* ── River Story ── */}
          <RiverStoryCard
            narrative={riverStory}
            loading={riverStoryLoading}
            readingLevel={riverStoryLevel}
            onChangeLevel={handleRiverStoryLevelChange}
            speaking={riverStorySpeaking}
            audioLoading={riverStoryAudioLoading}
            onSpeak={speakRiverStory}
          />
          </div>
          <div data-card="current_activity">
          {/* ── Swipeable Condition Cards ── */}
          <div className="rnow-cards-label">Current Activity</div>
          <div className="rnow-cards">
            <div className="rnow-card" onClick={() => navigate(`/path/fish/${watershed}`)}>
              <div className="rnow-card-header">
                <span className="rnow-card-icon">🐟</span>
                <span className="rnow-card-title">Fish Activity <InfoTooltip text="Fish species people and biologists have seen recently in this watershed. Combines verified iNaturalist sightings from citizen scientists with USGS-led professional fish surveys." sources={['inaturalist', 'biodata']} /></span>
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
                <span className="rnow-card-title">Insect Activity <InfoTooltip text="Stream insects that have been spotted recently in this watershed — mayflies, caddis, stoneflies, etc. Pulled from citizen-science sightings (iNaturalist) and aquatic-insect surveys done for water-quality monitoring." sources={['inaturalist', 'wqp_bugs']} /></span>
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
                <span className="rnow-card-title">Cold-Water Refuges <InfoTooltip text="Spots within this watershed where the water stays cooler than the main river — usually spring-fed pools or shaded side channels. Fish, especially trout, gather here during heat waves. Identified by comparing temperatures across USGS monitoring stations." sources={['usgs']} /></span>
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

          </div>
          <div data-card="fish_present">
          {/* ── Fish Near You (Species by Reach) ── */}
          {uniqueFishByReach.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title-row">
                <span className="rnow-section-title">🐟 Fish Present <InfoTooltip text="Fish species documented in this watershed. Pulled from verified citizen-science sightings, professional fish surveys, museum specimen records, and (where the state publishes it) the salmon-distribution database. Duplicates are removed and species are grouped by river stretch." sources={['inaturalist', 'biodata', 'gbif']} /></span>
                <button className="rnow-view-map-btn" onClick={() => navigate(`/path/map/${watershed}?filter=fish_present`)}>View Map</button>
              </div>
              <div className="rnow-fish-carousel">
                {uniqueFishByReach.slice(0, 10).map((s: any, i: number) => (
                  <div key={i} className="rnow-fish-card">
                    {s.photo_url ? (
                      <img src={s.photo_url} alt={s.common_name || s.species} className="rnow-fish-photo" loading="lazy" />
                    ) : (
                      <div className="rnow-fish-photo-placeholder">🐟</div>
                    )}
                    <div className="rnow-fish-info">
                      <div className="rnow-fish-name">{s.common_name || s.species}</div>
                      <div className="rnow-fish-stream">{s.stream}</div>
                      <div className="rnow-fish-use">{s.use_type}</div>
                      {s.observer && <div className="rnow-photo-credit">📷 {s.observer}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          </div>
          <div data-card="barriers">
          {/* ── Fish Passage Barriers ── */}
            <section className="rnow-section">
              <div className="rnow-section-title">⚠ Fish Passage Barriers{barriers.length > 0 ? ` (${barriers.length})` : ''} <InfoTooltip text="Things in the river that fish can't easily swim past — dams, weirs, culverts, and waterfalls. Sourced from regional barrier inventories. Each barrier is marked as fully blocking, partially passable, or fully passable where that's been reported." sources={['fish_barrier']} /></div>
              {barriers.length > 0 ? (
              <div className="rnow-barriers">
                {barriers.slice(0, 5).map((b: any, i: number) => (
                  <div key={i} className="rnow-barrier-item">
                    <span className={`rnow-barrier-dot ${b.passage_status === 'Passable' ? 'pass' : 'block'}`}></span>
                    <span className="rnow-barrier-stream">{b.stream_name || b.barrier_name || '—'}</span>
                    <span className="rnow-barrier-status">{b.passage_status || '—'}</span>
                  </div>
                ))}
              </div>
              ) : (
                <div className="rnow-empty">No documented fish passage barriers in this watershed</div>
              )}
            </section>

          </div>
          <div data-card="fly_shops">
          {/* ── Fly Shops & Guides ── */}
          {flyShops.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">🏪 Fly Shops & Guides <InfoTooltip text="Local fly shops, outfitters, and guide services for this river. Hand-curated from in-person research and public business directories. If you know a shop that should be listed, reach out via the contact link." /></div>
              <div className="rnow-shops">
                {flyShops.map((s: any, i: number) => (
                  <div key={i} className="rnow-shop-card">
                    <div className="rnow-shop-type">{s.type === 'fly_shop' ? '🏪' : s.type === 'guide_service' ? '🚣' : '🏪🚣'}</div>
                    <div className="rnow-shop-info">
                      <div className="rnow-shop-name">{s.name}</div>
                      <div className="rnow-shop-city">{s.city}</div>
                      <div className="rnow-shop-desc">{s.description}</div>
                      <div className="rnow-shop-links">
                        {s.phone && <a href={`tel:${s.phone}`} className="rnow-shop-link">📞 {s.phone}</a>}
                        {s.website && <a href={s.website} target="_blank" rel="noopener noreferrer" className="rnow-shop-link">🌐 Website</a>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
          </div>
          <div data-card="time_machine">
          {/* ── Time Machine ── */}
          {timeMachine && timeMachine.years?.length > 2 && (() => {
            const years = timeMachine.years
            const selected = years.find((y: any) => y.year === tmYear) || years[years.length - 1]
            return (
              <section className="rnow-section">
                <div className="rnow-section-title">🕰️ Time Machine — Species Through the Years <InfoTooltip text="What people and biologists were finding in this watershed year by year. Drag the slider to see which species showed up in each year. Built from verified citizen-science sightings and agency surveys going back as far as the records exist." sources={['inaturalist', 'biodata']} /></div>
                <div className="rnow-tm-slider-row">
                  <span className="rnow-tm-year-label">{years[0].year}</span>
                  <input type="range" className="rnow-tm-slider"
                    min={years[0].year} max={years[years.length - 1].year} step={1}
                    value={tmYear || years[years.length - 1].year}
                    onChange={e => setTmYear(parseInt(e.target.value))} />
                  <span className="rnow-tm-year-label">{years[years.length - 1].year}</span>
                </div>
                <div className="rnow-tm-stat">
                  <span className="rnow-tm-stat-year">{selected.year}</span>
                  <span className="rnow-tm-stat-count">{selected.species_count} species</span>
                  <span className="rnow-tm-stat-obs">{selected.observations?.toLocaleString()} observations</span>
                </div>
                {selected.top_species?.length > 0 && (
                  <div className="rnow-tm-species">
                    {selected.top_species.map((s: any, i: number) => (
                      <div key={i} className="rnow-tm-species-item">
                        {s.photo && <img src={s.photo} alt="" className="rnow-tm-species-img" loading="lazy" />}
                        <div>
                          <div className="rnow-tm-species-name">{s.common || s.taxon}</div>
                          <div className="rnow-tm-species-count">{s.count} obs</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )
          })()}

          </div>
          <div data-card="compare_rivers">
          {/* ── Compare Rivers ── */}
          <section className="rnow-section">
            <div className="rnow-section-title">⚖️ Compare Rivers <InfoTooltip text="See how this river stacks up against another one side by side — health score, current water temperature, total species, and restoration project count. Pick another river to compare." sources={['usgs', 'inaturalist']} /></div>
            <div className="rnow-compare-picker">
              <span className="rnow-compare-label">Compare {site.name} with:</span>
              <div className="rnow-compare-btns">
                {['mckenzie', 'deschutes', 'metolius', 'klamath', 'johnday']
                  .filter(w => w !== watershed)
                  .map(w => (
                    <button key={w} className={`rnow-compare-btn${compareWs === w ? ' active' : ''}`}
                      onClick={() => {
                        setCompareWs(w)
                        setCompareData(null)
                        fetch(`${API}/compare?ws1=${watershed}&ws2=${w}`).then(r => r.json()).then(setCompareData)
                      }}>
                      {{ mckenzie: 'McKenzie', deschutes: 'Deschutes', metolius: 'Metolius', klamath: 'Klamath', johnday: 'John Day' }[w]}
                    </button>
                  ))}
              </div>
            </div>
            {compareData && (
              <div className="rnow-compare-table">
                <div className="rnow-compare-row header">
                  <span></span>
                  <span>{compareData.river1.name?.replace(' River', '')}</span>
                  <span>{compareData.river2.name?.replace(' River', '')}</span>
                </div>
                {[
                  ['Species', compareData.river1.species?.toLocaleString(), compareData.river2.species?.toLocaleString()],
                  ['Health', compareData.river1.health_score || '—', compareData.river2.health_score || '—'],
                  ['Water Temp', compareData.river1.water_temp_c ? `${compareData.river1.water_temp_c}°C` : '—', compareData.river2.water_temp_c ? `${compareData.river2.water_temp_c}°C` : '—'],
                  ['DO (mg/L)', compareData.river1.do_mg_l || '—', compareData.river2.do_mg_l || '—'],
                  ['Hatch Activity', compareData.river1.hatch_activity, compareData.river2.hatch_activity],
                  ['Projects', compareData.river1.projects?.toLocaleString(), compareData.river2.projects?.toLocaleString()],
                ].map(([label, v1, v2], i) => (
                  <div key={i} className="rnow-compare-row">
                    <span className="rnow-compare-label-cell">{label}</span>
                    <span className="rnow-compare-val">{v1}</span>
                    <span className="rnow-compare-val">{v2}</span>
                  </div>
                ))}
              </div>
            )}
          </section>

          </div>
          <div data-card="weather">
          {/* ── Weather Forecast ── */}
          {weather?.periods?.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">Weather Forecast <InfoTooltip text="7-day forecast for the center of this watershed from the National Weather Service. Fetched fresh and held for 30 minutes between requests." /></div>
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

          </div>
          <div data-card="snowpack">
          {/* ── Snowpack Card ── */}
          {snowpack && (snowpack.stations_with_snow > 0 || snowpack.station_count > 0) && (
            <section className="rnow-section">
              <div className="rnow-section-title">Snowpack & Mountain Conditions <InfoTooltip text="How much snow is up in the mountains around this watershed. SWE means 'snow water equivalent' — how many inches of water the snowpack would melt into. Readings come from the automated SNOTEL stations the NRCS runs in the high country, updated daily." sources={['snotel']} /></div>
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

          </div>
          <div data-card="stocking">
          {/* ── Stocking Alerts ── */}
          {(upcomingStocking.length > 0 || recentStocking.length > 0) && (
            <section className="rnow-section">
              <div className="rnow-section-title-row">
                <span className="rnow-section-title">Fish Stocking <InfoTooltip text="Upcoming and recent fish releases by the state wildlife agency for waters in this drainage. Pulled from the agency's public stocking schedule and refreshed weekly." sources={stateSources.stocking} /></span>
                <button className="rnow-view-map-btn" onClick={() => navigate(`/path/stocking/${watershed}`)}>View Map</button>
              </div>
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

          </div>
          <div data-card="whats_here">
          {/* ── What's Here Now ── */}
          {whatsAlive.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title-row">
                <span className="rnow-section-title">What's Here Now <InfoTooltip text="Wildlife and plants people have actually spotted in this watershed in the past few weeks — what you'd be most likely to encounter on a visit today. Drawn from verified citizen-science sightings on iNaturalist." sources={['inaturalist']} /></span>
                <button className="rnow-view-map-btn" onClick={() => navigate(`/path/map/${watershed}`)}>View Map</button>
              </div>
              <div className="rnow-alive-grid">
                {whatsAlive.map((s: any, i: number) => (
                  <div key={i} className="rnow-alive-item">
                    {s.photo_url && <img src={s.photo_url} alt={s.common_name} className="rnow-alive-img" title={s.observer ? `📷 ${s.observer}` : undefined} />}
                    <div className="rnow-alive-name">{s.common_name || s.taxon_name}</div>
                    {s.observer && <div className="rnow-photo-credit">📷 {s.observer}</div>}
                  </div>
                ))}
              </div>
            </section>
          )}

          </div>
          <div data-card="nearby_access">
          {/* ── Nearby Access Points ── */}
          {accessPoints.length > 0 && (
            <section className="rnow-section">
              <div className="rnow-section-title">Nearby Access <InfoTooltip text="Public places to get to the river near here — campgrounds, trailheads, day-use sites, boat ramps, fishing access points. Drawn from the Forest Service recreation database and the state's park / boat-ramp / fishing-access listings." sources={stateSources.access} /></div>
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
          </div>
          </div>{/* end rnow-card-container */}

          {/* ── Data Attribution ── */}
          <div className="rnow-attribution">
            Data: USGS · NOAA/NWS · USDA SNOTEL · ODFW · EPA · iNaturalist (CC BY-NC) · USFS · OSMB · Macrostrat · PBDB
          </div>
        </>
      )}

      <PhotoObservation app="riverpath" watershed={watershed} />
    </div>
  )
}

// ════════════════════════════════════════════
// River Story Card — pre-cached ecological narratives
// ════════════════════════════════════════════

function RiverStoryCard({ narrative, loading, readingLevel, onChangeLevel, speaking, audioLoading, onSpeak }: {
  narrative: string; loading: boolean; readingLevel: string;
  onChangeLevel: (level: string) => void;
  speaking: boolean; audioLoading: boolean; onSpeak: () => void;
}) {
  const [page, setPage] = useState(0)
  const SENTENCES_PER_PAGE = 5

  // Reset page when narrative changes
  useEffect(() => { setPage(0) }, [narrative])

  // Split into sentences for pagination
  const sentences = narrative
    .split(/(?<=[.!?])\s+/)
    .filter(s => s.trim().length > 10)
  const totalPages = Math.max(1, Math.ceil(sentences.length / SENTENCES_PER_PAGE))
  const pageSentences = sentences.slice(page * SENTENCES_PER_PAGE, (page + 1) * SENTENCES_PER_PAGE)

  return (
    <>
      <div className="rnow-story-label">River Story <InfoTooltip text="A narrative about this river, written by AI but grounded in real data — species counts, water quality, recent wildfires, restoration projects. Rewritten periodically as new data arrives. The audio version is read by a synthetic voice." sources={['inaturalist', 'usgs', 'restoration', 'mtbs']} /></div>
      <section className="rnow-story-card">
        {/* Reading level toggle + audio */}
        <div className="rnow-story-controls">
          <div className="rnow-story-toggle">
            {(['adult', 'kids', 'expert'] as const).map(level => (
              <button key={level} className={`rnow-story-level${readingLevel === level ? ' active' : ''}`}
                onClick={() => onChangeLevel(level)}>
                {level === 'kids' ? 'Kids' : level === 'expert' ? 'Expert' : 'Adult'}
              </button>
            ))}
          </div>
          <button className={`rnow-story-listen${speaking ? ' active' : ''}`} onClick={onSpeak} disabled={audioLoading || loading}>
            {audioLoading ? '...' : speaking ? '⏹' : '🔊'}
          </button>
        </div>

        {/* Story content */}
        {loading ? (
          <div className="rnow-story-loading">Loading story...</div>
        ) : (
          <div className="rnow-story-text">
            <Markdown>{pageSentences.join(' ')}</Markdown>
          </div>
        )}

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="rnow-story-pagination">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="rnow-story-page-btn">← Prev</button>
            <span className="rnow-story-page-info">{page + 1} / {totalPages}</span>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="rnow-story-page-btn">Next →</button>
          </div>
        )}
      </section>
    </>
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
