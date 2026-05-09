import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import logo from '../assets/riversignal-logo.svg'
import DataFreshness from '../components/DataFreshness'
import UserMenu from '../components/UserMenu'
import MapView from '../components/MapView'
import SitePanel from '../components/SitePanel'
import { API_BASE } from '../config'
import '../App.css'

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

  // Fossil overlay state (completely separate from observations)
  const [fossilOverlay, setFossilOverlay] = useState<any>(null)

  // Alerts + barriers
  const [alerts, setAlerts] = useState<any[]>([])
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<number>>(new Set())
  const [barrierOverlay, setBarrierOverlay] = useState<any>(null)
  const [showBarriers, setShowBarriers] = useState(false)
  const [showMyObs, setShowMyObs] = useState(searchParams.get('myobs') === 'true')

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

  // My Observations toggle
  useEffect(() => {
    if (showMyObs) {
      const wsParam = selectedSite ? `&watershed=${selectedSite}` : ''
      fetch(`${API_BASE}/observations/user/geojson?mine=true${wsParam}`, { credentials: 'include' })
        .then(r => r.json())
        .then(data => setObsOverlay(data))
        .catch(() => {})
    } else if (!obsSearch) {
      setObsOverlay(null)
    }
  }, [showMyObs, selectedSite])

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
    const term = obsSearch.trim()
    if (!term) return

    // Extract coordinates from input if present (end of string)
    // Handles: "43.74, -122.48" or "Oncorhynchus mykiss 43.74, -122.48"
    const coordPattern = /(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)\s*$/
    const coordMatch = term.match(coordPattern)

    let searchTerm = term
    let coords: { lat: number; lon: number } | null = null

    if (coordMatch) {
      const lat = parseFloat(coordMatch[1])
      const lon = parseFloat(coordMatch[2])
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        coords = { lat, lon }
        searchTerm = term.replace(coordPattern, '').trim()
      }
    }

    // If we have coordinates but no species term, just show a pin
    if (coords && !searchTerm) {
      setObsOverlay({
        type: 'FeatureCollection',
        features: [{
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [coords.lon, coords.lat] },
          properties: { taxon_name: `Location (${coords.lat}, ${coords.lon})`, common_name: '', observed_at: '', photo_url: '', quality_grade: '', source: 'coordinate' },
        }],
        count: 1,
      })
      return
    }

    // Species search — use proximity when coordinates provided
    const ws = selectedSite || 'mckenzie'
    const coordParams = coords ? `&lat=${coords.lat}&lon=${coords.lon}&radius_km=50` : ''
    setObsSearching(true)
    fetch(`${API_BASE}/sites/${ws}/observations/search?q=${encodeURIComponent(searchTerm)}&limit=5000${coordParams}`)
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
            placeholder={selectedSite ? "Search species or enter lat, lon..." : "Search species or enter lat, lon..."}
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

        {/* Map toggles */}
        <div className="map-toggles">
          <label className="barrier-toggle">
            <input type="checkbox" checked={showMyObs} onChange={e => { setShowMyObs(e.target.checked); if (e.target.checked) setObsSearch('') }} />
            <span className="barrier-toggle-label">My Observations</span>
          </label>
          {selectedSite && (
            <label className="barrier-toggle">
              <input type="checkbox" checked={showBarriers} onChange={e => setShowBarriers(e.target.checked)} />
              <span className="barrier-toggle-label">Barriers</span>
            </label>
          )}
        </div>

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
          fossilOverlay={fossilOverlay}
          barrierOverlay={showBarriers ? barrierOverlay : null}
        />
        {siteDetail && (
          <SitePanel
            site={siteDetail}
            watershed={selectedSite!}
            onClose={() => setSelectedSite(null)}
            initialQuestion={pendingQuestion}
            onQuestionConsumed={() => setPendingQuestion(null)}
            onShowFossilsOnMap={(taxonQuery) => {
              // FOSSIL PATH: completely separate from observations
              const searchTerms = taxonQuery.split(' OR ').map(t => t.trim()).filter(Boolean)
              Promise.all(searchTerms.map(term =>
                fetch(`${API_BASE}/fossils/search?q=${encodeURIComponent(term)}&watershed=${selectedSite}`)
                  .then(r => r.ok ? r.json() : { fossils: [] })
                  .catch(() => ({ fossils: [] }))
              )).then(results => {
                const allFossils = results.flatMap(r => r.fossils || [])
                const features = allFossils.filter((f: any) => f.latitude && f.longitude).map((f: any) => ({
                  type: 'Feature' as const,
                  geometry: { type: 'Point' as const, coordinates: [f.longitude, f.latitude] },
                  properties: {
                    taxon_name: f.taxon_name,
                    common_name: f.common_name || '',
                    period: f.period ? `${f.period} (${f.age_max_ma || '?'} Ma)` : '',
                    photo_url: f.image_url || '',
                    museum: f.museum || '',
                  },
                }))
                setFossilOverlay({ type: 'FeatureCollection', features, query: taxonQuery, watershed: selectedSite, count: features.length })
                setObsSearch(`🦴 ${taxonQuery} (${features.length})`)
              }).catch(err => console.error('Fossil search failed:', err))
            }}
            onShowSpeciesOnMap={(taxonQuery) => {
              // OBSERVATION PATH: query observations table only
              setObsSearch(taxonQuery)
              setObsSearching(true)
              setFossilOverlay(null) // Clear any fossil pins
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
