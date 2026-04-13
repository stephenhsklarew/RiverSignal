import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import Markdown from 'react-markdown'
import logo from '../assets/deeptrail-logo.svg'
import './DeepTrailPage.css'

const API_BASE = 'http://localhost:8001/api/v1'

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
]

interface Location { id: string; name: string; lat: number; lon: number; photo?: string; caption?: string }
interface Fossil {
  taxon_name: string; common_name: string | null; phylum: string; class_name: string; period: string;
  age_max_ma: number | null; distance_km: number | null; source_id: string | null;
  image_url: string | null; museum: string | null; latitude: number; longitude: number;
}
interface Mineral {
  site_name: string; commodity: string; dev_status: string;
  distance_km: number | null; latitude: number; longitude: number;
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

type Screen = 'pick' | 'detail' | 'fossils' | 'minerals'

export default function DeepTrailPage() {
  const [screen, setScreen] = useState<Screen>('pick')
  const [loc, setLoc] = useState<Location | null>(null)
  const [customLat, setCustomLat] = useState('')
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

      {loading ? <div className="dt-loading">Loading geology data...</div> : (
        <main className="dt-content">
          <section className="dt-loc-hero">
            <h1>{loc!.name}</h1>
            <p className="dt-loc-coords">{loc!.lat.toFixed(4)}°N, {Math.abs(loc!.lon).toFixed(4)}°W</p>
            {loc!.photo && (
              <img src={loc!.photo} alt={loc!.name} className="dt-hero-img" />
            )}
            <div className="dt-reading-toggle">
              {(['adult', 'kid_friendly', 'expert'] as const).map(level => (
                <button key={level} className={`dt-reading-btn${readingLevel === level ? ' active' : ''}`}
                  onClick={() => setReadingLevel(level)}>
                  {level === 'kid_friendly' ? 'Kids' : level === 'expert' ? 'Expert' : 'Adult'}
                </button>
              ))}
            </div>
          </section>

          {/* Deep Time Story */}
          <section className="dt-story-card">
            <button className={`dt-listen-btn${speaking ? ' active' : ''}`} onClick={speakStory} disabled={audioLoading || storyLoading}>
              {audioLoading ? '⏳ Loading audio...' : speaking ? '⏹ Stop' : '🔊 Listen to Story'}
            </button>
            {storyLoading ? (
              <div className="dt-story-loading">Generating deep time narrative...</div>
            ) : (
              <div className="dt-story-md">
                <Markdown>{storyNarrative}</Markdown>
              </div>
            )}
          </section>

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

          {/* Geologic Context */}
          {geoContext?.units?.length > 0 && (
            <section className="dt-geo-section">
              <h3>Geologic Context</h3>
              {geoContext.units.slice(0, 3).map((u: any, i: number) => (
                <div key={i} className="dt-geo-unit">
                  <span className={`rock-badge-dt ${u.rock_type || ''}`}>{u.rock_type || 'unknown'}</span>
                  <div>
                    <div className="dt-geo-name">{u.formation || u.unit_name}</div>
                    <div className="dt-geo-meta">{u.lithology ? `${u.lithology} · ` : ''}{u.period}{u.age_max_ma ? ` · ${u.age_max_ma}–${u.age_min_ma || '?'} Ma` : ''}</div>
                  </div>
                </div>
              ))}
            </section>
          )}

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

          {/* Deep Time Timeline */}
          {timeline.length > 0 && (
            <section className="dt-timeline-section">
              <h3>Deep Time Timeline</h3>
              <div className="dt-timeline">
                {timeline.map((item, i) => (
                  <div key={i} className={`dt-tl-item ${item.type}`}>
                    <div className="dt-tl-dot"></div>
                    <div className="dt-tl-content">
                      <span className="dt-tl-age">{item.age_max_ma ? `${item.age_max_ma} Ma` : ''}</span>
                      <span className="dt-tl-name">{item.type === 'fossil' ? item.taxon_name : item.name}</span>
                      <span className="dt-tl-meta">{item.type === 'fossil' ? `${item.phylum} — ${item.period}` : `${item.rock_type || ''} — ${item.period}`}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Navigation links to fossil/mineral screens */}
          <section className="dt-nav-cards">
            <button className="dt-nav-card" onClick={() => setScreen('fossils')}>
              <span className="dt-nav-card-icon">🦴</span>
              <span className="dt-nav-card-label">Fossils Found Nearby</span>
              <span className="dt-nav-card-count">{fossils.length}</span>
              <span className="dt-nav-card-arrow">→</span>
            </button>
            <button className="dt-nav-card" onClick={() => setScreen('minerals')}>
              <span className="dt-nav-card-icon">💎</span>
              <span className="dt-nav-card-label">Mineral Sites Nearby</span>
              <span className="dt-nav-card-count">{minerals.length}</span>
              <span className="dt-nav-card-arrow">→</span>
            </button>
            {riverData && (
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
            )}
          </section>
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
        <span className="dt-badge-sm">Fossils ({filteredFossils.length})</span>
      </header>

      <MiniMap items={filteredFossils} center={loc!} color="#d4a96a"
        labels={filteredFossils.map(f => f.common_name || f.taxon_name)} />

      <div className="dt-list-filters">
        <select value={periodFilter} onChange={e => setPeriodFilter(e.target.value)} className="dt-filter-select">
          <option value="">All Periods</option>
          {fossilPeriods.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <select value={phylumFilter} onChange={e => setPhylumFilter(e.target.value)} className="dt-filter-select">
          <option value="">All Phyla</option>
          {fossilPhyla.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      <div className="dt-list">
        {filteredFossils.map((f, i) => (
          <div key={i} className="dt-list-item">
            <div className="dt-list-thumb">
              {f.image_url ? <img src={f.image_url} alt={f.taxon_name} loading="lazy" /> : <span>{PHYLUM_ICONS[f.phylum] || '🪨'}</span>}
            </div>
            <div className="dt-list-body">
              {f.common_name && <div className="dt-list-common">{f.common_name}</div>}
              <div className="dt-list-name">{f.taxon_name}</div>
              <div className="dt-list-meta">{f.phylum}{f.class_name ? ` · ${f.class_name}` : ''}{f.museum ? ` · ${f.museum}` : ''}</div>
              <div className="dt-list-sub">{f.period}{f.age_max_ma ? ` · ${f.age_max_ma} Ma` : ''}{f.distance_km != null ? ` · ${f.distance_km} km` : ''}</div>
            </div>
            {f.source_id && <a href={`https://paleobiodb.org/classic/checkTaxonInfo?taxon_no=${f.source_id}`} target="_blank" rel="noopener noreferrer" className="dt-list-link">PBDB →</a>}
          </div>
        ))}
        {filteredFossils.length === 0 && <div className="dt-empty">No fossils match filters.</div>}
      </div>
    </div>
  )

  // ═══════════════════════════════════════════════
  // SCREEN 3b: MINERAL LIST + MAP
  // ═══════════════════════════════════════════════
  return (
    <div className="dt-app">
      <header className="dt-detail-header">
        <button className="dt-back" onClick={() => setScreen('detail')}>← {loc!.name}</button>
        <span className="dt-badge-sm">Minerals ({filteredMinerals.length})</span>
      </header>

      <MiniMap items={filteredMinerals} center={loc!} color="#e65100"
        labels={filteredMinerals.map(m => m.site_name)} />

      <div className="dt-list-filters">
        <select value={mineralFilter} onChange={e => setMineralFilter(e.target.value)} className="dt-filter-select">
          <option value="">All Commodities</option>
          {mineralCommodities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="dt-list">
        {filteredMinerals.map((m, i) => {
          const comLower = (m.commodity || '').toLowerCase()
          const icon = comLower.includes('gold') ? '🥇' : comLower.includes('silver') ? '🥈'
            : comLower.includes('copper') ? '🟤' : comLower.includes('mercury') ? '💧' : '💎'
          return (
            <div key={i} className="dt-list-item">
              <div className="dt-list-thumb"><span>{icon}</span></div>
              <div className="dt-list-body">
                <div className="dt-list-name">{m.site_name}</div>
                <div className="dt-list-meta">{m.commodity}</div>
                <div className="dt-list-sub">{m.dev_status}{m.distance_km != null ? ` · ${m.distance_km} km` : ''}</div>
              </div>
            </div>
          )
        })}
        {filteredMinerals.length === 0 && <div className="dt-empty">No minerals match filter.</div>}
      </div>
    </div>
  )
}


// ═══════════════════════════════════════════════
// Compact MapLibre map for fossil/mineral lists
// ═══════════════════════════════════════════════
function MiniMap({ items, center, color, labels }: {
  items: { latitude: number; longitude: number }[];
  center: { lat: number; lon: number };
  color: string;
  labels?: string[];
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
  }, [items, center, color, labels])

  return <div ref={ref} className="dt-mini-map" />
}
