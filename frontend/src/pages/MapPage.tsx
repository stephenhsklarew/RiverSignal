import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import logo from '../assets/riversignal-logo.svg'
import DataFreshness from '../components/DataFreshness'
import UserMenu from '../components/UserMenu'
import MapView from '../components/MapView'
import SitePanel from '../components/SitePanel'
import '../App.css'

const API_BASE = 'http://localhost:8001/api/v1'

export interface Site {
  id: string
  name: string
  watershed: string
  bbox: { north: number; south: number; east: number; west: number }
  observations: number
  time_series: number
  interventions: number
}

export default function MapPage() {
  const { watershed: urlWatershed } = useParams()
  const [searchParams] = useSearchParams()
  const initialQuestion = searchParams.get('q')

  const [sites, setSites] = useState<Site[]>([])
  const [selectedSite, setSelectedSite] = useState<string | null>(urlWatershed || null)
  const [siteDetail, setSiteDetail] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(initialQuestion)

  // Observation search state
  const [obsSearch, setObsSearch] = useState('')
  const [obsOverlay, setObsOverlay] = useState<any>(null)
  const [, setObsSearching] = useState(false)

  // Alerts + barriers
  const [alerts, setAlerts] = useState<any[]>([])
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<number>>(new Set())
  const [barrierOverlay, setBarrierOverlay] = useState<any>(null)
  const [showBarriers, setShowBarriers] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/sites`)
      .then(r => r.json())
      .then(data => { setSites(data); setLoading(false) })
      .catch(e => { console.error(e); setLoading(false) })
  }, [])

  useEffect(() => {
    if (urlWatershed && !selectedSite) setSelectedSite(urlWatershed)
  }, [urlWatershed])

  useEffect(() => {
    if (selectedSite) {
      setSiteDetail(null)
      setAlerts([])
      setDismissedAlerts(new Set())
      fetch(`${API_BASE}/sites/${selectedSite}`)
        .then(r => r.json()).then(setSiteDetail).catch(console.error)
      // Fetch alerts
      fetch(`${API_BASE}/sites/${selectedSite}/fishing/alerts`)
        .then(r => r.json()).then(d => setAlerts(d.alerts || [])).catch(() => {})
      // Fetch barriers for map overlay
      if (showBarriers) loadBarriers(selectedSite)
    } else {
      setSiteDetail(null)
      setAlerts([])
      setBarrierOverlay(null)
    }
  }, [selectedSite])

  useEffect(() => {
    if (showBarriers && selectedSite) loadBarriers(selectedSite)
    else setBarrierOverlay(null)
  }, [showBarriers, selectedSite])

  const loadBarriers = (ws: string) => {
    fetch(`${API_BASE}/sites/${ws}/fishing/barriers`)
      .then(r => r.json())
      .then(barriers => {
        const features = barriers.filter((b: any) => b.latitude && b.longitude).map((b: any) => ({
          type: 'Feature' as const,
          geometry: { type: 'Point' as const, coordinates: [b.longitude, b.latitude] },
          properties: { name: b.barrier_name || b.stream_name, type: b.barrier_type, status: b.passage_status },
        }))
        setBarrierOverlay({ type: 'FeatureCollection', features })
      })
      .catch(() => {})
  }

  const handleObsSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!obsSearch.trim() || !selectedSite) return
    setObsSearching(true)
    fetch(`${API_BASE}/sites/${selectedSite}/observations/search?q=${encodeURIComponent(obsSearch.trim())}&limit=5000`)
      .then(r => r.json())
      .then(data => { setObsOverlay(data); setObsSearching(false) })
      .catch(() => setObsSearching(false))
  }

  const clearObsSearch = () => { setObsSearch(''); setObsOverlay(null) }

  const visibleAlerts = alerts.filter((_, i) => !dismissedAlerts.has(i))

  if (loading) return <div className="loading">Loading watersheds...</div>

  return (
    <div className="app">
      <div className="topbar">
        <Link to="/" className="topbar-brand" style={{ textDecoration: 'none', color: 'inherit' }}>
          <img src={logo} alt="RiverSignal" style={{ height: 34 }} />
        </Link>
        <div className="topbar-nav">
          <Link to="/"><button>Home</button></Link>
          <button className="active">Dashboard</button>
          <Link to="/riversignal/reports"><button>Reports</button></Link>
        </div>

        {/* Observation search */}
        <form onSubmit={handleObsSearch} className="obs-search-form">
          <span className="obs-search-icon">&#x1F50D;</span>
          <input
            type="text"
            value={obsSearch}
            onChange={e => setObsSearch(e.target.value)}
            placeholder={selectedSite ? "Map observations: mayfly, salmon, eagle..." : "Select a watershed to search"}
            disabled={!selectedSite}
            className={`obs-search-input${obsOverlay?.count > 0 ? ' has-results' : ''}`}
          />
          {obsOverlay && (
            <>
              <span className="obs-search-count">{obsOverlay.count} found</span>
              <button type="button" onClick={clearObsSearch} className="obs-search-clear" title="Clear search">&times;</button>
            </>
          )}
        </form>

        {/* Barrier toggle */}
        {selectedSite && (
          <label className="barrier-toggle">
            <input type="checkbox" checked={showBarriers} onChange={e => setShowBarriers(e.target.checked)} />
            <span className="barrier-toggle-label">Barriers</span>
          </label>
        )}

        <div className="topbar-status">
          <DataFreshness compact />
        </div>
        <UserMenu />
      </div>

      {/* Fishing alerts — minimal inline ticker */}
      {visibleAlerts.length > 0 && (
        <div className="alerts-ticker">
          {visibleAlerts.map((a, i) => (
            <span key={i} className={`alert-chip ${a.severity}`}>
              {i > 0 && <span className="alert-sep"></span>}
              <span className="alert-dot"></span>
              <span className="alert-val">{a.message.match(/\d+/)?.[0]}</span>
              <span className="alert-txt">{a.message.replace(/^\d+\s*/, '')}</span>
            </span>
          ))}
          <button className="alert-dismiss-all" onClick={() => setDismissedAlerts(new Set(alerts.map((_, i) => i)))}>×</button>
        </div>
      )}

      <div className={`app-body${siteDetail ? '' : ' no-panel'}`}>
        <MapView
          sites={sites}
          selectedSite={selectedSite}
          onSelectSite={setSelectedSite}
          observationOverlay={obsOverlay}
          barrierOverlay={showBarriers ? barrierOverlay : null}
        />
        {siteDetail && (
          <SitePanel
            site={siteDetail}
            watershed={selectedSite!}
            onClose={() => setSelectedSite(null)}
            initialQuestion={pendingQuestion}
            onQuestionConsumed={() => setPendingQuestion(null)}
            onShowSpeciesOnMap={(taxonQuery, source) => {
              setObsSearch(taxonQuery)
              setObsSearching(true)

              if (source === 'fossils') {
                // Query fossils endpoint and convert to GeoJSON
                const bbox = siteDetail?.bbox || {}
                const lat = ((bbox.south || 0) + (bbox.north || 0)) / 2
                const lon = ((bbox.west || 0) + (bbox.east || 0)) / 2
                const latSpan = Math.abs((bbox.north || 0) - (bbox.south || 0))
                const lonSpan = Math.abs((bbox.east || 0) - (bbox.west || 0))
                const radiusKm = Math.min(400, Math.max(75, Math.round(Math.max(latSpan, lonSpan) * 111 / 2)))
                fetch(`${API_BASE}/fossils/near/${lat}/${lon}?radius_km=${radiusKm}`)
                  .then(r => r.json())
                  .then(data => {
                    const searchTerms = taxonQuery.toLowerCase().split(' or ').map((t: string) => t.trim())
                    const matching = (data.fossils || []).filter((f: any) =>
                      searchTerms.some((term: string) =>
                        (f.taxon_name || '').toLowerCase().includes(term) ||
                        (f.common_name || '').toLowerCase().includes(term)
                      )
                    )
                    const features = matching.filter((f: any) => f.latitude && f.longitude).map((f: any) => ({
                      type: 'Feature' as const,
                      geometry: { type: 'Point' as const, coordinates: [f.longitude, f.latitude] },
                      properties: {
                        taxon_name: f.taxon_name,
                        common_name: f.common_name || '',
                        observed_at: f.period ? `${f.period} (${f.age_max_ma || '?'} Ma)` : '',
                        photo_url: f.image_url || '',
                        source: 'fossil',
                        museum: f.museum || '',
                      },
                    }))
                    setObsOverlay({ type: 'FeatureCollection', features, query: taxonQuery, watershed: selectedSite, count: features.length })
                    setObsSearching(false)
                  })
                  .catch(() => setObsSearching(false))
                return
              }

              // Default: query observations
              const taxa = taxonQuery.split(' OR ').map(t => t.trim()).filter(Boolean)
              if (taxa.length <= 1) {
                fetch(`${API_BASE}/sites/${selectedSite}/observations/search?q=${encodeURIComponent(taxonQuery)}&limit=5000`)
                  .then(r => r.json())
                  .then(data => { setObsOverlay(data); setObsSearching(false) })
                  .catch(() => setObsSearching(false))
              } else {
                Promise.all(taxa.map(t =>
                  fetch(`${API_BASE}/sites/${selectedSite}/observations/search?q=${encodeURIComponent(t)}&limit=2000`)
                    .then(r => r.json()).catch(() => ({ features: [] }))
                )).then(results => {
                  const merged = {
                    type: 'FeatureCollection',
                    features: results.flatMap(r => r.features || []),
                    query: taxonQuery,
                    watershed: selectedSite,
                    count: results.reduce((a, r) => a + (r.count || 0), 0),
                  }
                  setObsOverlay(merged)
                  setObsSearching(false)
                }).catch(() => setObsSearching(false))
              }
            }}
          />
        )}
      </div>
    </div>
  )
}
