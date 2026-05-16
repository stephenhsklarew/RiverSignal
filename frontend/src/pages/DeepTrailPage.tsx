import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import Markdown from 'react-markdown'
import { CardSettingsPanel, loadDeepTrailCardSettings, DEEPTRAIL_DEFAULT_CARDS, type CardConfig } from '../components/CardSettings'
import logo from '../assets/deeptrail-logo.svg'
import { API_BASE } from '../config'
import './DeepTrailPage.css'

// Watershed centers as curated locations with landscape photos
const WATERSHEDS = [
  { id: 'klamath', name: 'Upper Klamath Basin', lat: 42.65, lon: -121.55,
    photo: 'https://images.unsplash.com/photo-1566126157268-bd7167924841?w=900&h=400&fit=crop',
    caption: 'Crater Lake & volcanic highlands' },
  { id: 'mckenzie', name: 'McKenzie River', lat: 44.075, lon: -122.3,
    photo: 'https://images.unsplash.com/photo-1660806739398-0f0627930230?w=900&h=400&fit=crop',
    caption: 'Tamolitch Blue Pool — lava tube hydrology' },
  { id: 'deschutes', name: 'Deschutes River', lat: 44.325, lon: -121.225,
    photo: 'https://images.unsplash.com/photo-1528672903139-6a4496639a68?w=900&h=400&fit=crop',
    caption: 'Smith Rock — 30 Ma welded tuff canyon' },
  { id: 'metolius', name: 'Metolius River', lat: 44.5, lon: -121.575,
    photo: 'https://images.unsplash.com/photo-1657215223750-c4988d4a2635?w=900&h=400&fit=crop',
    caption: 'Spring-fed from Cascade volcanic aquifer' },
  { id: 'johnday', name: 'John Day River', lat: 44.6, lon: -119.15,
    photo: 'https://images.unsplash.com/photo-1559867243-edf5915deaa7?w=900&h=400&fit=crop',
    caption: 'Painted Hills — 33 Ma volcanic ash layers' },
  { id: 'shenandoah', name: 'Shenandoah River', lat: 38.92, lon: -78.20,
    photo: 'https://images.unsplash.com/photo-1697028262529-74efa0627a02?w=900&h=400&fit=crop',
    caption: 'Blue Ridge limestone caves & Ordovician dolostones' },
  { id: 'skagit', name: 'Skagit River', lat: 48.45, lon: -121.50,
    photo: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900&h=600&fit=crop',
    caption: 'North Cascades glacial geology' },
]

interface Location { id: string; name: string; lat: number; lon: number; photo?: string; caption?: string }
interface Fossil {
  taxon_name: string; common_name: string | null; phylum: string; class_name: string; period: string;
  age_max_ma: number | null; distance_km: number | null; source_id: string | null;
  image_url: string | null; image_license: string | null; museum: string | null;
  latitude: number; longitude: number; morphosource_url?: string | null;
}
interface Mineral {
  site_name: string; commodity: string; dev_status: string;
  distance_km: number | null; latitude: number; longitude: number;
  image_url?: string | null; image_license?: string | null;
}
interface TimelineItem {
  type: string; name: string; period: string; age_max_ma: number | null;
  rock_type?: string; taxon_name?: string; phylum?: string;
}

const PHYLUM_ICONS: Record<string, string> = {
  'Mollusca': '🐚', 'Chordata': '🦴', 'Arthropoda': '🦐', 'Plantae': '🌿',
  'Tracheophyta': '🌿', 'Bryophyta': '🌱', 'Cnidaria': '🪸', 'Echinodermata': '⭐',
  'Brachiopoda': '🐚', 'Foraminifera': '🔬', 'Radiolaria': '🔬',
}

type Screen = 'pick' | 'detail' | 'fossils' | 'minerals' | 'rockhounding'

export default function DeepTrailPage() {
  const [screen, setScreen] = useState<Screen>('pick')
  const [loc, setLoc] = useState<Location | null>(null)
  const [customLat, setCustomLat] = useState('')

  // Card customization
  const [dtCardConfig, setDtCardConfig] = useState<CardConfig[]>(loadDeepTrailCardSettings)
  const [showDtSettings, setShowDtSettings] = useState(false)

  // Page title
  useEffect(() => {
    document.title = 'Deep Trail'
    return () => { document.title = 'River Signal' }
  }, [])
  const [customLon, setCustomLon] = useState('')
  const [gpsLoading, setGpsLoading] = useState(false)

  // Detail screen data
  const [fossils, setFossils] = useState<Fossil[]>([])
  const [minerals, setMinerals] = useState<Mineral[]>([])
  const [timeline, setTimeline] = useState<TimelineItem[]>([])
  const [landStatus, setLandStatus] = useState<any>(null)
  const [geoContext, setGeoContext] = useState<any>(null)
  const [riverData, setRiverData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [readingLevel, setReadingLevel] = useState('adult')
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState<{role: string; text: string}[]>([])
  const [chatLoading, setChatLoading] = useState(false)

  // Story narrative + audio
  const [storyNarrative, setStoryNarrative] = useState('')
  const [storyLoading, setStoryLoading] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [audioLoading, setAudioLoading] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const speakStory = async () => {
    // Stop if already playing
    if (speaking && audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setSpeaking(false)
      return
    }
    if (!storyNarrative || storyLoading) return

    setAudioLoading(true)
    try {
      const resp = await fetch(`${API_BASE}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: storyNarrative, voice: 'nova' }),
      })
      if (!resp.ok) throw new Error('TTS failed')
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)

      if (audioRef.current) { audioRef.current.pause(); URL.revokeObjectURL(audioRef.current.src) }
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => setSpeaking(false)
      audio.onerror = () => setSpeaking(false)
      setSpeaking(true)
      setAudioLoading(false)
      audio.play()
    } catch {
      setAudioLoading(false)
      // Fallback to browser speech synthesis
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(storyNarrative)
        utterance.rate = 0.95; utterance.lang = 'en-US'
        utterance.onend = () => setSpeaking(false)
        setSpeaking(true)
        speechSynthesis.speak(utterance)
      }
    }
  }

  // AI features state
  const [crossDomain, setCrossDomain] = useState<any>(null)
  const [quiz, setQuiz] = useState<any>(null)
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({})
  const [compareEra1, setCompareEra1] = useState('Eocene')
  const [compareEra2, setCompareEra2] = useState('Miocene')
  const [compareData, setCompareData] = useState<any>(null)
  const [mineralShops, setMineralShops] = useState<any[]>([])
  const [rockhoundingSites, setRockhoundingSites] = useState<any[]>([])
  const [selectedRocksite, setSelectedRocksite] = useState<any>(null)
  const [rarityScores, setRarityScores] = useState<Record<string, any>>({})

  // Fossil/mineral filters
  const [periodFilter, setPeriodFilter] = useState('')
  const [phylumFilter, setPhylumFilter] = useState('')
  const [mineralFilter, setMineralFilter] = useState('')

  const selectLocation = (l: Location) => {
    setLoc(l)
    setScreen('detail')
    setChatMessages([])
    setPeriodFilter('')
    setPhylumFilter('')
    setMineralFilter('')
  }

  const useMyLocation = () => {
    if (!navigator.geolocation) return
    setGpsLoading(true)
    navigator.geolocation.getCurrentPosition(
      pos => {
        setGpsLoading(false)
        selectLocation({
          id: 'gps', name: `${pos.coords.latitude.toFixed(4)}°N, ${Math.abs(pos.coords.longitude).toFixed(4)}°W`,
          lat: pos.coords.latitude, lon: pos.coords.longitude,
        })
      },
      () => setGpsLoading(false)
    )
  }

  const handleCustom = (e: React.FormEvent) => {
    e.preventDefault()
    const lat = parseFloat(customLat), lon = parseFloat(customLon)
    if (isNaN(lat) || isNaN(lon)) return
    selectLocation({ id: 'custom', name: `${lat.toFixed(4)}°N, ${Math.abs(lon).toFixed(4)}°W`, lat, lon })
  }

  // Fetch data when location selected
  useEffect(() => {
    if (!loc) return
    setLoading(true)
    Promise.all([
      fetch(`${API_BASE}/fossils/near/${loc.lat}/${loc.lon}?radius_km=50`).then(r => r.json()),
      fetch(`${API_BASE}/deep-time/timeline/${loc.lat}/${loc.lon}`).then(r => r.json()),
      fetch(`${API_BASE}/land/at/${loc.lat}/${loc.lon}`).then(r => r.json()),
      fetch(`${API_BASE}/minerals/near/${loc.lat}/${loc.lon}?radius_km=50`).then(r => r.json()),
      fetch(`${API_BASE}/geology/at/${loc.lat}/${loc.lon}`).then(r => r.json()),
    ]).then(([f, t, l, m, g]) => {
      setFossils(f.fossils || [])
      setTimeline(t.timeline || [])
      setLandStatus(l)
      setMinerals(m.minerals || [])
      setGeoContext(g)
      setLoading(false)
    }).catch(() => setLoading(false))

    // AI features
    fetch(`${API_BASE}/deep-time/geology-ecology/${loc.lat}/${loc.lon}`).then(r => r.json()).then(setCrossDomain).catch(() => {})
    fetch(`${API_BASE}/deep-time/quiz?lat=${loc.lat}&lon=${loc.lon}`).then(r => r.json()).then(setQuiz).catch(() => {})
    fetch(`${API_BASE}/deep-time/rarity`).then(r => r.json()).then(d => setRarityScores(d.scores || {})).catch(() => {})
    fetch(`${API_BASE}/deep-time/mineral-shops`).then(r => r.json()).then(setMineralShops).catch(() => {})
    fetch(`${API_BASE}/rockhounding/near/${loc.lat}/${loc.lon}?radius_km=150`).then(r => r.json()).then(d => setRockhoundingSites(d.sites || [])).catch(() => {})

    // Fetch nearest river data for Living River card
    setRiverData(null)
    fetch(`${API_BASE}/sites/nearest?lat=${loc.lat}&lon=${loc.lon}`)
      .then(r => r.ok ? r.json() : null)
      .then(nearest => {
        if (!nearest) return
        return fetch(`${API_BASE}/sites/${nearest.watershed}`).then(r => r.json()).then(site => {
          setRiverData({ ...nearest, ...site })
        })
      })
      .catch(() => {})
  }, [loc])

  // Fetch deep time narrative when location or reading level changes
  useEffect(() => {
    if (!loc) return
    if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0 }
    if ('speechSynthesis' in window) speechSynthesis.cancel()
    setSpeaking(false)
    setStoryLoading(true)
    setStoryNarrative('')
    fetch(`${API_BASE}/deep-time/story`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: loc.lat, lon: loc.lon, reading_level: readingLevel }),
    })
      .then(r => r.json())
      .then(data => {
        setStoryNarrative(data.narrative || 'No geologic data available for this location.')
        setStoryLoading(false)
      })
      .catch(() => { setStoryNarrative('Unable to load story.'); setStoryLoading(false) })
  }, [loc, readingLevel])

  const sendChat = () => {
    if (!chatInput.trim() || chatLoading || !loc) return
    const q = chatInput.trim()
    setChatMessages(prev => [...prev, { role: 'user', text: q }])
    setChatInput('')
    setChatLoading(true)
    fetch(`${API_BASE}/deep-time/story`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: loc.lat, lon: loc.lon, reading_level: readingLevel, question: q }),
    })
      .then(r => r.json())
      .then(data => {
        setChatMessages(prev => [...prev, { role: 'assistant', text: data.context_summary || data.narrative || 'No data available.' }])
        setChatLoading(false)
      })
      .catch(() => { setChatMessages(prev => [...prev, { role: 'assistant', text: 'Unable to answer right now.' }]); setChatLoading(false) })
  }

  const statusColor = landStatus?.collecting_status === 'permitted' ? '#4caf50'
    : landStatus?.collecting_status === 'prohibited' ? '#f44336' : '#ff9800'

  const filteredFossils = fossils.filter(f =>
    (!periodFilter || f.period === periodFilter) && (!phylumFilter || f.phylum === phylumFilter)
  )
  const filteredMinerals = mineralFilter ? minerals.filter(m => m.commodity?.includes(mineralFilter)) : minerals
  const fossilPeriods = [...new Set(fossils.map(f => f.period).filter(Boolean))].sort()
  const fossilPhyla = [...new Set(fossils.map(f => f.phylum).filter(Boolean))].sort()
  const mineralCommodities = [...new Set(minerals.flatMap(m => (m.commodity || '').split(', ')).filter(Boolean))].sort()

  // ═══════════════════════════════════════════════
  // SCREEN 1: PICK LOCATION
  // ═══════════════════════════════════════════════
  if (screen === 'pick') return (
    <div className="dt-app">
      <header className="dt-header">
        <div className="dt-header-top">
          <Link to="/" className="dt-logo-link"><img src={logo} alt="DeepTrail" className="dt-logo" /></Link>
        </div>
        <h1 className="dt-title">Discover the Ancient Worlds Beneath Your Feet</h1>
      </header>

      <main className="dt-pick-content">
        <button className="dt-gps-btn" onClick={useMyLocation} disabled={gpsLoading}>
          📍 {gpsLoading ? 'Getting location...' : 'Use My Location'}
        </button>

        <div className="dt-pick-divider">or enter coordinates</div>
        <form onSubmit={handleCustom} className="dt-coord-form">
          <input type="text" value={customLat} onChange={e => setCustomLat(e.target.value)}
            placeholder="Latitude" className="dt-coord-input" />
          <input type="text" value={customLon} onChange={e => setCustomLon(e.target.value)}
            placeholder="Longitude" className="dt-coord-input" />
          <button type="submit" className="dt-coord-btn">Explore →</button>
        </form>

        <div className="dt-pick-divider">or pick a watershed</div>
        <div className="dt-watershed-list">
          {WATERSHEDS.map(ws => (
            <button key={ws.id} className="dt-watershed-btn" onClick={() => selectLocation(ws)}>
              <img src={ws.photo} alt={ws.name} className="dt-ws-thumb" loading="lazy" />
              <div className="dt-ws-info">
                <span className="dt-ws-name">{ws.name}</span>
                <span className="dt-ws-caption">{ws.caption}</span>
              </div>
              <span className="dt-ws-arrow">→</span>
            </button>
          ))}
        </div>
      </main>
    </div>
  )

  // ═══════════════════════════════════════════════
  // SCREEN 2: LOCATION DETAIL
  // ═══════════════════════════════════════════════
  if (screen === 'detail') return (
    <div className="dt-app">
      <header className="dt-detail-header">
        <button className="dt-back" onClick={() => setScreen('pick')}>← Back</button>
        <img src={logo} alt="DeepTrail" className="dt-logo" />
      </header>

      {/* Card settings panel */}
      {showDtSettings && (
        <CardSettingsPanel
          cards={dtCardConfig}
          onChange={setDtCardConfig}
          onClose={() => setShowDtSettings(false)}
          storageKey="deeptrail-card-settings"
          defaults={DEEPTRAIL_DEFAULT_CARDS}
          title="Customize Deep Trail"
          dark
        />
      )}

      {loading ? <div className="dt-loading">Loading geology data...</div> : (
        <main className="dt-content">
          {/* Dynamic CSS for card ordering/visibility */}
          <style>{dtCardConfig.map((c, i) => {
            const rules = [`[data-dtcard="${c.id}"] { order: ${i}; }`]
            if (!c.visible) rules.push(`[data-dtcard="${c.id}"] { display: none !important; }`)
            return rules.join('\n')
          }).join('\n')}</style>

          <section className="dt-loc-hero">
            <div className="dt-hero-top-row">
              <h1>{loc!.name}</h1>
              <button className="dt-settings-btn" onClick={() => setShowDtSettings(true)} title="Customize sections">⚙</button>
            </div>
            <p className="dt-loc-coords">{loc!.lat.toFixed(4)}°N, {Math.abs(loc!.lon).toFixed(4)}°W</p>
            {loc!.photo && (
              <img src={loc!.photo} alt={loc!.name} className="dt-hero-img" />
            )}
          </section>

          <div className="dt-card-container" style={{ display: 'flex', flexDirection: 'column' }}>

          <div data-dtcard="deep_time_story">
          {/* Deep Time Story */}
          <StoryCard
            narrative={storyNarrative}
            loading={storyLoading}
            readingLevel={readingLevel}
            onChangeLevel={setReadingLevel}
            speaking={speaking}
            audioLoading={audioLoading}
            onSpeak={speakStory}
          />

          </div>
          <div data-dtcard="kid_quiz">
          {/* Kid Quiz Mode */}
          {quiz && quiz.questions?.length > 0 && (
            <section className="dt-quiz-section">
              <h3>🧩 Quiz Me!</h3>
              {quiz.questions.map((q: any, i: number) => (
                <div key={i} className="dt-quiz-q">
                  <div className="dt-quiz-question">{q.question}</div>
                  <div className="dt-quiz-choices">
                    {q.choices.map((c: string, j: number) => {
                      const answered = quizAnswers[i] !== undefined
                      const isCorrect = c === q.correct
                      const isChosen = quizAnswers[i] === c
                      return (
                        <button key={j}
                          className={`dt-quiz-choice${answered ? (isCorrect ? ' correct' : isChosen ? ' wrong' : '') : ''}`}
                          onClick={() => !answered && setQuizAnswers(prev => ({...prev, [i]: c}))}
                          disabled={answered}>
                          {c}
                        </button>
                      )
                    })}
                  </div>
                  {quizAnswers[i] !== undefined && (
                    <div className={`dt-quiz-hint ${quizAnswers[i] === q.correct ? 'right' : 'wrong-hint'}`}>
                      {quizAnswers[i] === q.correct ? '✅ Correct!' : `❌ The answer is: ${q.correct}`}
                      {q.hint && <span> — {q.hint}</span>}
                    </div>
                  )}
                </div>
              ))}
            </section>
          )}
          </div>
          <div data-dtcard="ask_place">
          {/* Ask About This Place */}
          <section className="dt-chat-section">
            <h3>Ask About This Place</h3>
            <div className="dt-chat-messages">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`dt-chat-msg ${msg.role}`}>
                  <div className="dt-chat-bubble">{msg.text}</div>
                </div>
              ))}
              {chatLoading && <div className="dt-chat-msg assistant"><div className="dt-chat-bubble">Thinking...</div></div>}
            </div>
            <div className="dt-chat-input-row">
              <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') sendChat() }}
                placeholder="What was this place like millions of years ago?"
                className="dt-chat-input" />
              <button onClick={sendChat} disabled={!chatInput.trim() || chatLoading} className="dt-chat-btn">Ask</button>
            </div>
          </section>

          </div>
          <div data-dtcard="geologic_context">
          {/* Geologic Context (deduplicated) */}
          {geoContext?.units?.length > 0 && (() => {
            const seen = new Set<string>()
            const unique = geoContext.units.filter((u: any) => {
              const key = `${u.unit_name}|${u.rock_type}|${u.period}|${u.lithology}`
              if (seen.has(key)) return false
              seen.add(key)
              return true
            })
            return unique.length > 0 ? (
            <section className="dt-geo-section">
              <h3>Geologic Context</h3>
              {unique.slice(0, 3).map((u: any, i: number) => (
                <div key={i} className="dt-geo-unit">
                  <span className={`rock-badge-dt ${u.rock_type || ''}`}>{u.rock_type || 'unknown'}</span>
                  <div>
                    <div className="dt-geo-name">{u.formation || u.unit_name}</div>
                    <div className="dt-geo-meta">{u.lithology ? `${u.lithology} · ` : ''}{u.period}{u.age_max_ma ? ` · ${u.age_max_ma}–${u.age_min_ma || '?'} Ma` : ''}</div>
                  </div>
                </div>
              ))}
            </section>
            ) : null
          })()}

          </div>
          <div data-dtcard="cross_domain">
          {/* Cross-Domain Connector */}
          {crossDomain && crossDomain.connections?.length > 0 && (
            <section className="dt-cross-section">
              <h3>🌋 Why This River?</h3>
              {crossDomain.connections.map((c: any, i: number) => (
                <div key={i} className="dt-cross-card">
                  <span className="dt-cross-icon">{c.icon}</span>
                  <div>
                    <div className="dt-cross-geo">{c.geology}</div>
                    <div className="dt-cross-text">{c.connection}</div>
                  </div>
                </div>
              ))}
              {crossDomain.ecology?.river_name && (
                <a href={`/path/now/${crossDomain.ecology.watershed}`} className="dt-cross-link">
                  See the {crossDomain.ecology.river_name} →
                </a>
              )}
            </section>
          )}
          </div>
          <div data-dtcard="formation_explorer">
          {/* Formation Explorer */}
          {geoContext?.units?.length > 0 && (
            <section className="dt-formation-section">
              <h3>🗺️ Formation Explorer</h3>
              <div className="dt-formation-list">
                {geoContext.units.slice(0, 3).map((u: any, i: number) => (
                  <button key={i} className="dt-formation-btn"
                    onClick={() => {
                      fetch(`${API_BASE}/deep-time/formation/${encodeURIComponent(u.formation || u.unit_name)}`)
                        .then(r => r.json())
                        .then(d => alert(`${d.formation}: ${d.fossil_count} fossils found\n\n${d.fossils.slice(0, 5).map((f: any) => `• ${f.common_name || f.taxon} (${f.period})`).join('\n')}`))
                    }}>
                    <span className="dt-formation-name">{u.formation || u.unit_name}</span>
                    <span className="dt-formation-period">{u.period}</span>
                  </button>
                ))}
              </div>
            </section>
          )}
          </div>
          <div data-dtcard="legal_collecting">
          {/* Legal Collecting */}
          {landStatus && (
            <section className="dt-legal-card">
              <div className="dt-legal-dot" style={{ background: statusColor }}></div>
              <div>
                <strong>Collecting: {landStatus.collecting_status || 'unknown'}</strong>
                <span className="dt-legal-agency"> — {landStatus.agency || 'Unknown'}</span>
                <p className="dt-legal-rules">{landStatus.collecting_rules}</p>
                <p className="dt-legal-disclaimer">{landStatus.disclaimer}</p>
              </div>
            </section>
          )}

          </div>
          <div data-dtcard="deep_time_timeline">
          {/* Deep Time Timeline */}
          {timeline.length > 0 && (
            <TimelineSection items={timeline} />
          )}

          </div>
          <div data-dtcard="compare_eras">
          {/* Compare Eras */}
          <section className="dt-compare-section">
            <h3>⚖️ Compare Eras</h3>
            <div className="dt-compare-pickers">
              <select className="dt-filter-select" value={compareEra1} onChange={e => setCompareEra1(e.target.value)}>
                {['Eocene', 'Oligocene', 'Miocene', 'Pliocene', 'Pleistocene', 'Holocene'].map(e => (
                  <option key={e} value={e}>{e}</option>
                ))}
              </select>
              <span className="dt-compare-vs">vs</span>
              <select className="dt-filter-select" value={compareEra2} onChange={e => setCompareEra2(e.target.value)}>
                {['Eocene', 'Oligocene', 'Miocene', 'Pliocene', 'Pleistocene', 'Holocene', 'Today'].map(e => (
                  <option key={e} value={e}>{e}</option>
                ))}
              </select>
              <button className="dt-compare-go" onClick={() => {
                fetch(`${API_BASE}/deep-time/compare-eras?lat=${loc!.lat}&lon=${loc!.lon}&era1=${compareEra1}&era2=${compareEra2}`)
                  .then(r => r.json()).then(setCompareData)
              }}>Compare</button>
            </div>
            {compareData && (
              <div className="dt-compare-results">
                <div className="dt-compare-col">
                  <div className="dt-compare-era-name">{compareData.era1.era}</div>
                  <div className="dt-compare-stat">{compareData.era1.fossil_count} fossils</div>
                  {compareData.era1.fossils?.slice(0, 3).map((f: any, i: number) => (
                    <div key={i} className="dt-compare-fossil">{f.name} ({f.phylum})</div>
                  ))}
                </div>
                <div className="dt-compare-col">
                  <div className="dt-compare-era-name">{compareData.era2.era}</div>
                  <div className="dt-compare-stat">{compareData.era2.fossil_count} fossils</div>
                  {compareData.era2.fossils?.slice(0, 3).map((f: any, i: number) => (
                    <div key={i} className="dt-compare-fossil">{f.name} ({f.phylum})</div>
                  ))}
                </div>
              </div>
            )}
          </section>
          </div>
          <div data-dtcard="fossils_nearby">
          {/* Fossils navigation */}
          <section className="dt-nav-cards">
            <button className="dt-nav-card" onClick={() => setScreen('fossils')}>
              <span className="dt-nav-card-icon">🦴</span>
              <span className="dt-nav-card-label">Fossils Found Nearby</span>
              <span className="dt-nav-card-count">{fossils.length}</span>
              <span className="dt-nav-card-arrow">→</span>
            </button>
          </section>
          </div>
          <div data-dtcard="minerals_nearby">
          {/* Minerals navigation */}
          <section className="dt-nav-cards">
            <button className="dt-nav-card" onClick={() => setScreen('minerals')}>
              <span className="dt-nav-card-icon">💎</span>
              <span className="dt-nav-card-label">Mineral Sites Nearby</span>
              <span className="dt-nav-card-count">{minerals.length}</span>
              <span className="dt-nav-card-arrow">→</span>
            </button>
          </section>
          </div>
          <div data-dtcard="rockhounding">
          {/* Rockhounding Sites */}
          {rockhoundingSites.length > 0 && (
            <section className="dt-rockhounding">
              <h3>🪨 Rockhounding Sites ({rockhoundingSites.length})</h3>
              {rockhoundingSites.map((s: any, i: number) => (
                <button key={i} className="dt-rocksite-row" onClick={() => { setSelectedRocksite(s); setScreen('rockhounding') }}>
                  {s.image_url && <img src={s.image_url} alt={s.rock_type} className="dt-rocksite-row-img" loading="lazy" />}
                  <div className="dt-rocksite-row-body">
                    <div className="dt-rocksite-name">{s.name}</div>
                    <div className="dt-rocksite-rocks">{s.rock_type}</div>
                  </div>
                  <div className="dt-rocksite-row-right">
                    <span className={`dt-rocksite-owner ${s.land_owner === 'BLM' ? 'public' : s.land_owner === 'Private' ? 'private' : 'other'}`}>
                      {s.land_owner}
                    </span>
                    {s.distance_km != null && <span className="dt-rocksite-dist">{s.distance_km} km</span>}
                  </div>
                  <span className="dt-rocksite-arrow">→</span>
                </button>
              ))}
            </section>
          )}
          </div>
          <div data-dtcard="mineral_shops">
          {/* Mineral Shops */}
          {mineralShops.length > 0 && (
            <section className="dt-mineral-shops">
              <h3>🏪 Mineral Shops Nearby</h3>
              {mineralShops.map((s: any, i: number) => (
                <div key={i} className="dt-shop-card">
                  <div className="dt-shop-name">{s.name}</div>
                  <div className="dt-shop-city">{s.city}</div>
                  <div className="dt-shop-desc">{s.description}</div>
                  <div className="dt-shop-links">
                    {s.phone && <a href={`tel:${s.phone}`} className="dt-shop-link">📞 {s.phone}</a>}
                    {s.website && <a href={s.website} target="_blank" rel="noopener noreferrer" className="dt-shop-link">🌐 Website</a>}
                  </div>
                </div>
              ))}
            </section>
          )}
          </div>
          <div data-dtcard="living_river">
          {/* Living River link */}
          {riverData && (
            <section className="dt-nav-cards">
              <a href={`/path/now/${riverData.watershed}`} target="_blank" rel="noopener noreferrer" className="dt-nav-card dt-nav-card-river">
                <span className="dt-nav-card-icon">🐟</span>
                <span className="dt-nav-card-label">
                  Living River
                  <span className="dt-nav-card-sub">{riverData.name}</span>
                </span>
                <span className="dt-nav-card-count">
                  {riverData.scorecard?.total_species?.toLocaleString() || '—'}
                  <span className="dt-nav-card-unit">species</span>
                </span>
                <span className="dt-nav-card-arrow">↗</span>
              </a>
            </section>
          )}
          </div>

          </div>{/* end dt-card-container */}
        </main>
      )}
    </div>
  )

  // ═══════════════════════════════════════════════
  // SCREEN 3a: FOSSIL LIST + MAP
  // ═══════════════════════════════════════════════
  if (screen === 'fossils') return (
    <div className="dt-app">
      <header className="dt-detail-header">
        <button className="dt-back" onClick={() => setScreen('detail')}>← {loc!.name}</button>
        <img src={logo} alt="DeepTrail" className="dt-logo" />
      </header>

      <MiniMap items={filteredFossils} center={loc!} color="#d4a96a"
        labels={filteredFossils.map(f => f.common_name || f.taxon_name)}
        extraItems={rockhoundingSites} extraColor="#4caf50"
        extraLabels={rockhoundingSites.map(s => s.name + ' — ' + s.rock_type)} />

      {/* Period selector + phylum chips */}
      <PeriodFilterModal periods={fossilPeriods} selected={periodFilter} onSelect={setPeriodFilter} />
      <div className="dt-filter-chips">
        <button className={`dt-chip${!phylumFilter ? ' active' : ''}`} onClick={() => setPhylumFilter('')}>All Types</button>
        {fossilPhyla.map(p => (
          <button key={p} className={`dt-chip${phylumFilter === p ? ' active' : ''}`} onClick={() => setPhylumFilter(phylumFilter === p ? '' : p)}>{PHYLUM_ICONS[p] || '🪨'} {p}</button>
        ))}
      </div>

      {/* Grouped by period */}
      <FossilGroupedList fossils={filteredFossils.map(f => ({
        ...f,
        rarity: rarityScores[f.taxon_name]?.rarity || null,
        rarity_count: rarityScores[f.taxon_name]?.occurrences || null,
      }))} />
    </div>
  )

  // ═══════════════════════════════════════════════
  // SCREEN 4: ROCKHOUNDING SITE DETAIL
  // ═══════════════════════════════════════════════
  if (screen === 'rockhounding' && selectedRocksite) {
    const s = selectedRocksite
    return (
      <div className="dt-app">
        <header className="dt-detail-header">
          <button className="dt-back" onClick={() => setScreen('detail')}>← {loc!.name}</button>
          <img src={logo} alt="DeepTrail" className="dt-logo" />
        </header>

        {s.image_url && (
          <div className="dt-rockdetail-hero">
            <img src={s.image_url} alt={s.rock_type} />
          </div>
        )}

        <div className="dt-rockdetail-content">
          <h2 className="dt-rockdetail-name">{s.name}</h2>
          <div className="dt-rockdetail-rocks">{s.rock_type}</div>

          <div className="dt-rockdetail-badges">
            <span className={`dt-rocksite-owner ${s.land_owner === 'BLM' ? 'public' : s.land_owner === 'Private' ? 'private' : 'other'}`}>
              {s.land_owner}
            </span>
            {s.nearest_town && <span className="dt-rockdetail-town">📍 {s.nearest_town}</span>}
            {s.distance_km != null && <span className="dt-rockdetail-dist">{s.distance_km} km away</span>}
          </div>

          <div className="dt-rockdetail-section">
            <h3>Description</h3>
            <p>{s.description}</p>
          </div>

          <div className="dt-rockdetail-section dt-rockdetail-rules-box">
            <h3>⚖️ Collecting Rules</h3>
            <p>{s.collecting_rules}</p>
          </div>

          <div className="dt-rockdetail-section">
            <h3>Location</h3>
            <p className="dt-rockdetail-coords">{s.latitude.toFixed(4)}°N, {Math.abs(s.longitude).toFixed(4)}°W</p>
          </div>

          <MiniMap
            items={[{ latitude: s.latitude, longitude: s.longitude }]}
            center={{ lat: s.latitude, lon: s.longitude }}
            color="#4caf50"
            labels={[s.name]}
          />
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════════════
  // SCREEN 3b: MINERAL LIST + MAP
  // ═══════════════════════════════════════════════
  return (
    <div className="dt-app">
      <header className="dt-detail-header">
        <button className="dt-back" onClick={() => setScreen('detail')}>← {loc!.name}</button>
        <img src={logo} alt="DeepTrail" className="dt-logo" />
      </header>

      <MiniMap items={filteredMinerals} center={loc!} color="#e65100"
        labels={filteredMinerals.map(m => m.site_name)}
        extraItems={rockhoundingSites} extraColor="#4caf50"
        extraLabels={rockhoundingSites.map(s => s.name + ' — ' + s.rock_type)} />

      {/* Filter chips */}
      <div className="dt-filter-chips">
        <button className={`dt-chip${!mineralFilter ? ' active' : ''}`} onClick={() => setMineralFilter('')}>All</button>
        {mineralCommodities.map(c => (
          <button key={c} className={`dt-chip${mineralFilter === c ? ' active' : ''}`} onClick={() => setMineralFilter(mineralFilter === c ? '' : c)}>{c}</button>
        ))}
      </div>

      {/* Grouped by commodity */}
      <MineralGroupedList minerals={filteredMinerals} />
    </div>
  )
}


// ═══════════════════════════════════════════════
// Compact MapLibre map for fossil/mineral lists
// ═══════════════════════════════════════════════
function MiniMap({ items, center, color, labels, extraItems, extraColor, extraLabels }: {
  items: { latitude: number; longitude: number }[];
  center: { lat: number; lon: number };
  color: string;
  labels?: string[];
  extraItems?: { latitude: number; longitude: number }[];
  extraColor?: string;
  extraLabels?: string[];
}) {
  const ref = useRef<HTMLDivElement>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)

  useEffect(() => {
    if (!ref.current) return
    const map = new maplibregl.Map({
      container: ref.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [center.lon, center.lat],
      zoom: 8,
      interactive: true,
    })

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      const features = items.filter(i => i.latitude && i.longitude).map((item, idx) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [item.longitude, item.latitude] },
        properties: { idx, label: labels?.[idx] || `Item ${idx + 1}` },
      }))

      map.addSource('items', { type: 'geojson', data: { type: 'FeatureCollection', features } })
      map.addLayer({
        id: 'item-points', type: 'circle', source: 'items',
        paint: { 'circle-radius': 7, 'circle-color': color, 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5 },
      })

      // Rockhounding sites as extra pins (green diamonds)
      if (extraItems && extraItems.length > 0) {
        const extraFeatures = extraItems.filter(i => i.latitude && i.longitude).map((item, idx) => ({
          type: 'Feature' as const,
          geometry: { type: 'Point' as const, coordinates: [item.longitude, item.latitude] },
          properties: { idx, label: extraLabels?.[idx] || `Site ${idx + 1}`, isExtra: true },
        }))
        map.addSource('extra-items', { type: 'geojson', data: { type: 'FeatureCollection', features: extraFeatures } })
        map.addLayer({
          id: 'extra-points', type: 'circle', source: 'extra-items',
          paint: {
            'circle-radius': 8, 'circle-color': extraColor || '#4caf50',
            'circle-stroke-color': '#fff', 'circle-stroke-width': 2,
          },
        })
        map.on('click', 'extra-points', (e) => {
          if (!e.features?.length) return
          const props = e.features[0].properties as any
          const coords = (e.features[0].geometry as any).coordinates.slice() as [number, number]
          if (popupRef.current) popupRef.current.remove()
          popupRef.current = new maplibregl.Popup({ maxWidth: '200px', closeButton: false })
            .setLngLat(coords)
            .setHTML(`<div style="font-family:Outfit,sans-serif;font-size:12px;color:#1a1612;padding:2px 0;">🪨 <strong>${props.label}</strong></div>`)
            .addTo(map)
        })
        map.on('mouseenter', 'extra-points', () => { map.getCanvas().style.cursor = 'pointer' })
        map.on('mouseleave', 'extra-points', () => { map.getCanvas().style.cursor = '' })
      }

      // Click → popup + scroll to card
      map.on('click', 'item-points', (e) => {
        if (!e.features?.length) return
        const props = e.features[0].properties as any
        const coords = (e.features[0].geometry as any).coordinates.slice() as [number, number]

        if (popupRef.current) popupRef.current.remove()
        popupRef.current = new maplibregl.Popup({ maxWidth: '200px', closeButton: false })
          .setLngLat(coords)
          .setHTML(`<div style="font-family:Outfit,sans-serif;font-size:12px;color:#1a1612;padding:2px 0;"><strong>${props.label}</strong></div>`)
          .addTo(map)

        // Scroll the list to the matching card
        const idx = props.idx
        const card = document.querySelectorAll('.dt-list-item')[idx]
        if (card) {
          card.scrollIntoView({ behavior: 'smooth', block: 'center' })
          card.classList.add('dt-list-highlight')
          setTimeout(() => card.classList.remove('dt-list-highlight'), 2000)
        }
      })

      map.on('mouseenter', 'item-points', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', 'item-points', () => { map.getCanvas().style.cursor = '' })

      // Center marker
      new maplibregl.Marker({ color: '#fff' }).setLngLat([center.lon, center.lat]).addTo(map)
    })

    return () => { map.remove() }
  }, [items, center, color, labels, extraItems, extraColor, extraLabels])

  return <div ref={ref} className="dt-mini-map" />
}

// ── Story Card with pagination + reading level toggle ──

function StoryCard({ narrative, loading, readingLevel, onChangeLevel, speaking, audioLoading, onSpeak }: {
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
      <h3 className="dt-story-label">Deep Time Story</h3>
      <section className="dt-story-card">
        {/* Reading level toggle */}
        <div className="dt-story-controls">
          <div className="dt-reading-toggle">
            {(['adult', 'kid_friendly', 'expert'] as const).map(level => (
              <button key={level} className={`dt-reading-btn${readingLevel === level ? ' active' : ''}`}
                onClick={() => onChangeLevel(level)}>
                {level === 'kid_friendly' ? 'Kids' : level === 'expert' ? 'Expert' : 'Adult'}
              </button>
            ))}
          </div>
          <button className={`dt-listen-btn-sm${speaking ? ' active' : ''}`} onClick={onSpeak} disabled={audioLoading || loading}>
            {audioLoading ? '⏳' : speaking ? '⏹' : '🔊'}
          </button>
        </div>

        {/* Story content */}
        {loading ? (
          <div className="dt-story-loading">Generating deep time narrative...</div>
        ) : (
          <div className="dt-story-md">
            <Markdown>{pageSentences.join(' ')}</Markdown>
          </div>
        )}

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="dt-story-pagination">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="dt-page-btn">← Prev</button>
            <span className="dt-page-info">{page + 1} / {totalPages}</span>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="dt-page-btn">Next →</button>
          </div>
        )}
      </section>
    </>
  )
}

// ── Deep Time Timeline with cleanup + pagination ──

const ERA_CONTEXT: Record<string, string> = {
  'Quaternary': 'Ice ages and early humans',
  'Holocene': 'Modern era — last 11,700 years',
  'Pleistocene': 'Ice ages, mammoths, saber-toothed cats',
  'Neogene': 'Grasslands spread, modern mammals appear',
  'Pliocene': 'Climate cooling, Panama land bridge forms',
  'Miocene': 'Grasslands, horses, and great apes evolve',
  'Paleogene': 'Mammals diversify after dinosaur extinction',
  'Oligocene': 'Cooling climate, open woodlands',
  'Eocene': 'Subtropical forests, early horses and whales',
  'Paleocene': 'Recovery from mass extinction, mammals rise',
  'Cretaceous': 'Dinosaurs rule, flowering plants appear',
  'Jurassic': 'Age of dinosaurs, first birds',
  'Triassic': 'First dinosaurs and mammals',
  'Permian': 'Before the Great Dying — largest extinction',
  'Carboniferous': 'Giant insects, coal swamp forests',
  'Devonian': 'Age of fishes, first land plants',
}

function TimelineSection({ items }: { items: any[] }) {
  const [page, setPage] = useState(0)
  const ITEMS_PER_PAGE = 5

  // Clean and deduplicate timeline
  const cleaned = (() => {
    const seen = new Set<string>()
    return items
      .filter(item => {
        // Must have a name and a period or age
        const name = item.type === 'fossil' ? item.taxon_name : item.name
        if (!name || name === 'null') return false
        if (!item.period && !item.age_max_ma) return false
        // For fossils, must have phylum or period
        if (item.type === 'fossil' && !item.phylum && !item.period) return false
        // Deduplicate
        const key = `${item.type}|${name}|${item.period || ''}`
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      .sort((a, b) => (b.age_max_ma || 0) - (a.age_max_ma || 0))
  })()

  const totalPages = Math.max(1, Math.ceil(cleaned.length / ITEMS_PER_PAGE))
  const pageItems = cleaned.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)

  useEffect(() => { setPage(0) }, [items])

  if (cleaned.length === 0) return null

  return (
    <section className="dt-timeline-section">
      <h3>Deep Time Timeline</h3>
      <div className="dt-timeline">
        {pageItems.map((item, i) => {
          const isRock = item.type === 'geologic_unit'
          const name = isRock ? (item.name || item.formation || 'Unknown unit') : (item.taxon_name || '?')
          const age = item.age_max_ma ? `${item.age_max_ma} Ma` : ''
          const period = item.period || ''
          const context = ERA_CONTEXT[period] || ''
          const meta = isRock
            ? [item.rock_type, item.lithology, period].filter(Boolean).join(' · ')
            : [item.phylum, item.class_name, period].filter(Boolean).join(' · ')

          return (
            <div key={i} className={`dt-tl-item ${item.type}`}>
              <div className="dt-tl-dot">{isRock ? '🪨' : '🦴'}</div>
              <div className="dt-tl-content">
                <div className="dt-tl-header">
                  {age && <span className="dt-tl-age">{age}</span>}
                  {period && <span className="dt-tl-period">{period}</span>}
                </div>
                <div className="dt-tl-name">{name}</div>
                <div className="dt-tl-meta">{meta}</div>
                {context && <div className="dt-tl-context">{context}</div>}
              </div>
            </div>
          )
        })}
      </div>

      {totalPages > 1 && (
        <div className="dt-story-pagination">
          <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="dt-page-btn">← Older</button>
          <span className="dt-page-info">{page + 1} / {totalPages}</span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="dt-page-btn">Newer →</button>
        </div>
      )}
    </section>
  )
}

// ── Fossil List grouped by period ──

const PERIOD_ORDER = [
  'Cambrian','Ordovician','Silurian','Devonian','Carboniferous','Permian',
  'Triassic','Jurassic','Cretaceous','Paleocene','Eocene','Oligocene',
  'Miocene','Pliocene','Pleistocene','Holocene','Quaternary','Neogene','Paleogene',
]

function FossilGroupedList({ fossils }: { fossils: any[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const ITEMS_VISIBLE = 5

  // Group by period
  const groups: Record<string, any[]> = {}
  for (const f of fossils) {
    const period = f.period || 'Unknown'
    if (!groups[period]) groups[period] = []
    groups[period].push(f)
  }

  // Sort periods by geological age
  const sortedPeriods = Object.keys(groups).sort((a, b) => {
    const ai = PERIOD_ORDER.indexOf(a)
    const bi = PERIOD_ORDER.indexOf(b)
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
  })

  if (fossils.length === 0) return <div className="dt-empty">No fossils match filters.</div>

  return (
    <div className="dt-grouped-list">
      {sortedPeriods.map(period => {
        const items = groups[period]
        const isExpanded = expanded[period]
        const visible = isExpanded ? items : items.slice(0, ITEMS_VISIBLE)
        const context = ERA_CONTEXT[period] || ''

        return (
          <div key={period} className="dt-group">
            <div className="dt-group-header">
              <div className="dt-group-title">
                <span className="dt-group-period">{period}</span>
                <span className="dt-group-count">{items.length}</span>
              </div>
              {context && <div className="dt-group-context">{context}</div>}
            </div>
            <div className="dt-group-items">
              {visible.map((f, i) => (
                <FossilCard key={i} fossil={f} />
              ))}
            </div>
            {items.length > ITEMS_VISIBLE && (
              <button className="dt-group-toggle" onClick={() => setExpanded(prev => ({ ...prev, [period]: !prev[period] }))}>
                {isExpanded ? 'Show less' : `Show all ${items.length}`}
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}

function FossilCard({ fossil: f }: { fossil: any }) {
  const sid = f.source_id || ''
  const sourceLink = sid.startsWith('occ:')
    ? `https://paleobiodb.org/classic/checkTaxonInfo?taxon_no=${sid.replace('occ:', '')}`
    : /^\d+$/.test(sid) ? `https://www.gbif.org/occurrence/${sid}`
    : `https://www.idigbio.org/portal/records/${sid}`
  const sourceLabel = sid.startsWith('occ:') ? 'PBDB' : /^\d+$/.test(sid) ? 'GBIF' : 'iDigBio'

  return (
    <div className="dt-fossil-card">
      <div className="dt-fossil-thumb">
        {f.image_url
          ? <img src={f.image_url} alt={f.taxon_name} loading="lazy" />
          : <span className="dt-fossil-icon">{PHYLUM_ICONS[f.phylum] || '🪨'}</span>}
      </div>
      <div className="dt-fossil-body">
        <div className="dt-fossil-name">{f.taxon_name}</div>
        {f.common_name && <div className="dt-fossil-common">{f.common_name}</div>}
        <div className="dt-fossil-meta">
          {f.phylum && <span>{f.phylum}</span>}
          {f.class_name && <span> · {f.class_name}</span>}
          {f.age_max_ma && <span> · {f.age_max_ma} Ma</span>}
        </div>
        <div className="dt-fossil-bottom">
          {f.rarity && (
            <span className={`dt-rarity-badge ${f.rarity}`}>
              {f.rarity === 'very_rare' ? '💎 Very Rare' : f.rarity === 'rare' ? '⭐ Rare' : f.rarity === 'uncommon' ? 'Uncommon' : 'Common'}
            </span>
          )}
          {f.museum && <span className="dt-fossil-museum">{f.museum}</span>}
          {f.distance_km != null && <span className="dt-fossil-dist">{f.distance_km} km</span>}
          {sid && <a href={sourceLink} target="_blank" rel="noopener noreferrer" className="dt-fossil-source">{sourceLabel} ↗</a>}
          {f.morphosource_url && <a href={f.morphosource_url} target="_blank" rel="noopener noreferrer" className="dt-fossil-source">3D Model ↗</a>}
        </div>
        {f.image_url && f.image_license && (
          <div className="dt-fossil-license">{f.image_license}</div>
        )}
      </div>
    </div>
  )
}

// ── Mineral List grouped by commodity ──

function MineralGroupedList({ minerals }: { minerals: any[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const ITEMS_VISIBLE = 5

  const COMMODITY_ICONS: Record<string, string> = {
    'gold': '🥇', 'silver': '🥈', 'copper': '🟤', 'mercury': '💧',
    'agate': '💎', 'obsidian': '⚫', 'thunderegg': '🥚', 'opal': '🔮',
    'pumice': '🪨', 'perlite': '⚪', 'diatomite': '🟡',
  }

  function getIcon(commodity: string): string {
    const lower = commodity.toLowerCase()
    for (const [key, icon] of Object.entries(COMMODITY_ICONS)) {
      if (lower.includes(key)) return icon
    }
    return '💎'
  }

  // Group by primary commodity
  const groups: Record<string, any[]> = {}
  for (const m of minerals) {
    const commodity = (m.commodity || 'Unknown').split(',')[0].trim()
    if (!groups[commodity]) groups[commodity] = []
    groups[commodity].push(m)
  }
  const sortedCommodities = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length)

  if (minerals.length === 0) return <div className="dt-empty">No minerals match filter.</div>

  return (
    <div className="dt-grouped-list">
      {sortedCommodities.map(commodity => {
        const items = groups[commodity]
        const isExpanded = expanded[commodity]
        const visible = isExpanded ? items : items.slice(0, ITEMS_VISIBLE)
        const icon = getIcon(commodity)

        return (
          <div key={commodity} className="dt-group">
            <div className="dt-group-header">
              <div className="dt-group-title">
                <span>{icon}</span>
                <span className="dt-group-period">{commodity}</span>
                <span className="dt-group-count">{items.length}</span>
              </div>
            </div>
            <div className="dt-group-items">
              {visible.map((m, i) => (
                <div key={i} className="dt-mineral-card">
                  {m.image_url && (
                    <div className="dt-mineral-thumb">
                      <img src={m.image_url} alt={m.commodity} loading="lazy" />
                    </div>
                  )}
                  <div className="dt-mineral-body">
                    <div className="dt-mineral-name">{m.site_name}</div>
                    <div className="dt-mineral-meta">{m.commodity}</div>
                    <div className="dt-mineral-bottom">
                      {m.dev_status && <span className="dt-mineral-status">{m.dev_status}</span>}
                      {m.distance_km != null && <span className="dt-mineral-dist">{m.distance_km} km</span>}
                    </div>
                    {m.image_url && m.image_license && <div className="dt-mineral-license">{m.image_license}</div>}
                  </div>
                </div>
              ))}
            </div>
            {items.length > ITEMS_VISIBLE && (
              <button className="dt-group-toggle" onClick={() => setExpanded(prev => ({ ...prev, [commodity]: !prev[commodity] }))}>
                {isExpanded ? 'Show less' : `Show all ${items.length}`}
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Period filter as a button that opens a selection modal ──

function PeriodFilterModal({ periods, selected, onSelect }: {
  periods: string[]; selected: string; onSelect: (p: string) => void
}) {
  const [open, setOpen] = useState(false)
  const label = selected || 'All Periods'

  return (
    <>
      <div className="dt-period-selector">
        <button className="dt-period-btn" onClick={() => setOpen(true)}>
          {label} <span className="dt-period-arrow">▾</span>
        </button>
      </div>

      {open && (
        <div className="dt-period-overlay" onClick={() => setOpen(false)}>
          <div className="dt-period-modal" onClick={e => e.stopPropagation()}>
            <div className="dt-period-modal-header">
              <span>Select Period</span>
              <button className="dt-period-modal-close" onClick={() => setOpen(false)}>✕</button>
            </div>
            <div className="dt-period-modal-list">
              <button
                className={`dt-period-modal-item${!selected ? ' active' : ''}`}
                onClick={() => { onSelect(''); setOpen(false) }}
              >
                All Periods
              </button>
              {periods.map(p => (
                <button
                  key={p}
                  className={`dt-period-modal-item${selected === p ? ' active' : ''}`}
                  onClick={() => { onSelect(p); setOpen(false) }}
                >
                  <span>{p}</span>
                  {ERA_CONTEXT[p] && <span className="dt-period-modal-context">{ERA_CONTEXT[p]}</span>}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
