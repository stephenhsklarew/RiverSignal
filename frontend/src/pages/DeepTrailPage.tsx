import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import logo from '../assets/riversignal-logo.svg'
import './DeepTrailPage.css'

const API_BASE = 'http://localhost:8001/api/v1'

// Deep time locations with coordinates
const LOCATIONS = [
  { id: 'painted-hills', name: 'Painted Hills', lat: 44.6631, lon: -120.2293, period: 'Oligocene', age: '33 Ma', story: 'Subtropical forest with towering redwoods, palms, and brontotheres' },
  { id: 'clarno', name: 'Clarno', lat: 44.9222, lon: -120.4211, period: 'Eocene', age: '44 Ma', story: 'Tropical forest with palms, crocodiles, and tiny dawn horses' },
  { id: 'john-day', name: 'John Day Fossil Beds', lat: 44.5755, lon: -119.6317, period: 'Miocene', age: '7-28 Ma', story: 'Open savanna with horses, camels, and saber-toothed cats' },
  { id: 'smith-rock', name: 'Smith Rock', lat: 44.3682, lon: -121.1426, period: 'Oligocene', age: '30 Ma', story: 'Welded tuff canyon from massive volcanic eruption' },
  { id: 'newberry', name: 'Newberry Volcanic', lat: 43.7220, lon: -121.2290, period: 'Pleistocene', age: '<1 Ma', story: 'Obsidian flows, lava tubes, and volcanic aquifers' },
]

interface Fossil {
  taxon_name: string; phylum: string; class_name: string; period: string;
  age_max_ma: number | null; distance_km: number | null;
}

interface TimelineItem {
  type: string; name: string; period: string; age_max_ma: number | null;
  rock_type?: string; taxon_name?: string; phylum?: string; description?: string;
}

export default function DeepTrailPage() {
  const { location: urlLocation } = useParams()
  const [selectedLoc, setSelectedLoc] = useState(LOCATIONS.find(l => l.id === urlLocation) || LOCATIONS[0])
  const [fossils, setFossils] = useState<Fossil[]>([])
  const [timeline, setTimeline] = useState<TimelineItem[]>([])
  const [landStatus, setLandStatus] = useState<any>(null)
  const [minerals, setMinerals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [periodFilter, setPeriodFilter] = useState<string>('')
  const [phylumFilter, setPhylumFilter] = useState<string>('')
  const [readingLevel, setReadingLevel] = useState<string>('adult')
  const [customLat, setCustomLat] = useState('')
  const [customLon, setCustomLon] = useState('')
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState<{role: string; text: string}[]>([])
  const [chatLoading, setChatLoading] = useState(false)

  const handleCustomLocation = (e: React.FormEvent) => {
    e.preventDefault()
    const lat = parseFloat(customLat)
    const lon = parseFloat(customLon)
    if (isNaN(lat) || isNaN(lon)) return
    setSelectedLoc({ id: 'custom', name: `${lat.toFixed(3)}, ${lon.toFixed(3)}`, lat, lon, period: '', age: '', story: '' })
  }

  const sendGeoChat = () => {
    if (!chatInput.trim() || chatLoading) return
    const q = chatInput.trim()
    setChatMessages(prev => [...prev, { role: 'user', text: q }])
    setChatInput('')
    setChatLoading(true)

    // Use the existing chat endpoint with geology context
    fetch(`${API_BASE}/deep-time/story`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: selectedLoc.lat, lon: selectedLoc.lon, reading_level: readingLevel, question: q }),
    })
      .then(r => r.json())
      .then(data => {
        const answer = data.context_summary || data.narrative || 'No geologic data available for this location.'
        setChatMessages(prev => [...prev, { role: 'assistant', text: answer }])
        setChatLoading(false)
      })
      .catch(() => {
        setChatMessages(prev => [...prev, { role: 'assistant', text: 'Unable to answer right now. Please try again.' }])
        setChatLoading(false)
      })
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch(`${API_BASE}/fossils/near/${selectedLoc.lat}/${selectedLoc.lon}?radius_km=50`).then(r => r.json()),
      fetch(`${API_BASE}/deep-time/timeline/${selectedLoc.lat}/${selectedLoc.lon}`).then(r => r.json()),
      fetch(`${API_BASE}/land/at/${selectedLoc.lat}/${selectedLoc.lon}`).then(r => r.json()),
      fetch(`${API_BASE}/minerals/near/${selectedLoc.lat}/${selectedLoc.lon}?radius_km=50`).then(r => r.json()),
    ]).then(([fossilData, timelineData, land, mineralData]) => {
      setFossils(fossilData.fossils || [])
      setTimeline(timelineData.timeline || [])
      setLandStatus(land)
      setMinerals(mineralData.minerals || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [selectedLoc])

  const statusColor = landStatus?.collecting_status === 'permitted' ? '#4caf50'
    : landStatus?.collecting_status === 'prohibited' ? '#f44336' : '#ff9800'

  // Fossil filtering
  const filteredFossils = fossils.filter(f => {
    if (periodFilter && f.period !== periodFilter) return false
    if (phylumFilter && f.phylum !== phylumFilter) return false
    return true
  })
  const fossilPeriods = [...new Set(fossils.map(f => f.period).filter(Boolean))].sort()
  const fossilPhyla = [...new Set(fossils.map(f => f.phylum).filter(Boolean))].sort()

  return (
    <div className="dt-app">
      <header className="dt-header">
        <div className="dt-header-top">
          <Link to="/" className="dt-logo-link">
            <img src={logo} alt="" className="dt-logo" />
          </Link>
          <span className="dt-badge">DeepTrail</span>
          <div className="dt-header-links">
            <Link to="/path" className="dt-nav-link">RiverPath</Link>
            <Link to="/deepsignal" className="dt-nav-link">DeepSignal</Link>
          </div>
        </div>
        <h1 className="dt-title">Discover the Ancient Worlds Beneath Your Feet</h1>
      </header>

      {/* Location selector — horizontal scroll on mobile */}
      <div className="dt-locations">
        {LOCATIONS.map(loc => (
          <button key={loc.id}
            className={`dt-loc-card ${selectedLoc.id === loc.id ? 'active' : ''}`}
            onClick={() => setSelectedLoc(loc)}>
            <span className="dt-loc-period">{loc.period}</span>
            <span className="dt-loc-name">{loc.name}</span>
            <span className="dt-loc-age">{loc.age}</span>
          </button>
        ))}
        {/* Custom location input */}
        <form onSubmit={handleCustomLocation} className="dt-custom-loc">
          <input type="text" value={customLat} onChange={e => setCustomLat(e.target.value)}
            placeholder="Lat" className="dt-custom-input" />
          <input type="text" value={customLon} onChange={e => setCustomLon(e.target.value)}
            placeholder="Lon" className="dt-custom-input" />
          <button type="submit" className="dt-custom-btn">Go</button>
        </form>
      </div>

      {loading ? (
        <div className="dt-loading">Traveling through deep time...</div>
      ) : (
        <main className="dt-content">
          {/* Hero story card with reading level toggle */}
          <section className="dt-story-card">
            <div className="dt-story-header">
              <h2>{selectedLoc.name}</h2>
              <div className="dt-reading-toggle">
                {(['adult', 'kid_friendly', 'expert'] as const).map(level => (
                  <button key={level}
                    className={`dt-reading-btn${readingLevel === level ? ' active' : ''}`}
                    onClick={() => setReadingLevel(level)}>
                    {level === 'kid_friendly' ? 'Kids' : level === 'expert' ? 'Expert' : 'Adult'}
                  </button>
                ))}
              </div>
            </div>
            <p className="dt-story-period">{selectedLoc.period} — {selectedLoc.age}</p>
            <p className="dt-story-text">{selectedLoc.story}</p>
          </section>

          {/* Legal collecting status */}
          {landStatus && (
            <section className="dt-legal-card">
              <div className="dt-legal-dot" style={{ background: statusColor }}></div>
              <div>
                <strong>Collecting: {landStatus.collecting_status || 'unknown'}</strong>
                <span className="dt-legal-agency"> — {landStatus.agency || 'Unknown agency'}</span>
                <p className="dt-legal-rules">{landStatus.collecting_rules}</p>
                <p className="dt-legal-disclaimer">{landStatus.disclaimer}</p>
              </div>
            </section>
          )}

          {/* Geologic timeline */}
          <section className="dt-timeline-section">
            <h3>Deep Time Timeline</h3>
            <div className="dt-timeline">
              {timeline.map((item, i) => (
                <div key={i} className={`dt-tl-item ${item.type}`}>
                  <div className="dt-tl-dot"></div>
                  <div className="dt-tl-content">
                    <span className="dt-tl-age">
                      {item.age_max_ma ? `${item.age_max_ma} Ma` : ''}
                    </span>
                    <span className="dt-tl-name">
                      {item.type === 'fossil' ? item.taxon_name : item.name}
                    </span>
                    <span className="dt-tl-meta">
                      {item.type === 'fossil'
                        ? `${item.phylum} — ${item.period}`
                        : `${item.rock_type || ''} — ${item.period}`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Fossil gallery with filters */}
          <section className="dt-fossil-section">
            <h3>Fossils Found Nearby ({filteredFossils.length})</h3>
            <div className="dt-filter-row">
              <select value={periodFilter} onChange={e => setPeriodFilter(e.target.value)} className="dt-filter-select">
                <option value="">All Periods</option>
                {fossilPeriods.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <select value={phylumFilter} onChange={e => setPhylumFilter(e.target.value)} className="dt-filter-select">
                <option value="">All Phyla</option>
                {fossilPhyla.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="dt-fossil-grid">
              {filteredFossils.slice(0, 30).map((f, i) => (
                <div key={i} className="dt-fossil-card">
                  <div className="dt-fossil-name">{f.taxon_name}</div>
                  <div className="dt-fossil-meta">
                    {f.phylum}{f.class_name ? ` · ${f.class_name}` : ''}
                  </div>
                  <div className="dt-fossil-age">
                    {f.period} — {f.age_max_ma ? `${f.age_max_ma} Ma` : '?'}
                  </div>
                  {f.distance_km && (
                    <div className="dt-fossil-dist">{f.distance_km} km away</div>
                  )}
                </div>
              ))}
              {filteredFossils.length === 0 && (
                <div className="dt-empty">No fossils match the selected filters. Try broadening your search.</div>
              )}
            </div>
          </section>

          {/* Mineral deposits */}
          {minerals.length > 0 && (
            <section className="dt-mineral-section">
              <h3>Mineral Sites Nearby ({minerals.length})</h3>
              <div className="dt-fossil-grid">
                {minerals.slice(0, 20).map((m, i) => (
                  <div key={i} className="dt-fossil-card">
                    <div className="dt-fossil-name">{m.site_name}</div>
                    <div className="dt-fossil-meta">{m.commodity}</div>
                    <div className="dt-fossil-age">{m.dev_status}</div>
                    {m.distance_km && (
                      <div className="dt-fossil-dist">{m.distance_km} km away</div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Geology chat */}
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
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') sendGeoChat() }}
                placeholder="What was this place like 33 million years ago?"
                className="dt-chat-input"
              />
              <button onClick={sendGeoChat} disabled={!chatInput.trim() || chatLoading} className="dt-chat-btn">Ask</button>
            </div>
          </section>
        </main>
      )}
    </div>
  )
}
