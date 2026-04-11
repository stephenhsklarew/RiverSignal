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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch(`${API_BASE}/fossils/near/${selectedLoc.lat}/${selectedLoc.lon}?radius_km=50`).then(r => r.json()),
      fetch(`${API_BASE}/deep-time/timeline/${selectedLoc.lat}/${selectedLoc.lon}`).then(r => r.json()),
      fetch(`${API_BASE}/land/at/${selectedLoc.lat}/${selectedLoc.lon}`).then(r => r.json()),
    ]).then(([fossilData, timelineData, land]) => {
      setFossils(fossilData.fossils || [])
      setTimeline(timelineData.timeline || [])
      setLandStatus(land)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [selectedLoc])

  const statusColor = landStatus?.collecting_status === 'permitted' ? '#4caf50'
    : landStatus?.collecting_status === 'prohibited' ? '#f44336' : '#ff9800'

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
      </div>

      {loading ? (
        <div className="dt-loading">Traveling through deep time...</div>
      ) : (
        <main className="dt-content">
          {/* Hero story card */}
          <section className="dt-story-card">
            <h2>{selectedLoc.name}</h2>
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

          {/* Fossil gallery */}
          <section className="dt-fossil-section">
            <h3>Fossils Found Nearby ({fossils.length})</h3>
            <div className="dt-fossil-grid">
              {fossils.slice(0, 20).map((f, i) => (
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
            </div>
          </section>
        </main>
      )}
    </div>
  )
}
