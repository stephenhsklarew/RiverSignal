import { useEffect, useState } from 'react'
import MapView from './components/MapView'
import SitePanel from './components/SitePanel'
import './App.css'

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

function App() {
  const [sites, setSites] = useState<Site[]>([])
  const [selectedSite, setSelectedSite] = useState<string | null>(null)
  const [siteDetail, setSiteDetail] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/sites`)
      .then(r => r.json())
      .then(data => { setSites(data); setLoading(false) })
      .catch(e => { console.error(e); setLoading(false) })
  }, [])

  useEffect(() => {
    if (selectedSite) {
      setSiteDetail(null)
      fetch(`${API_BASE}/sites/${selectedSite}`)
        .then(r => r.json())
        .then(setSiteDetail)
        .catch(console.error)
    } else {
      setSiteDetail(null)
    }
  }, [selectedSite])

  if (loading) return <div className="loading">Loading watersheds...</div>

  return (
    <div className="app">
      <header className="app-header">
        <h1>RiverSignal</h1>
        <span className="subtitle">Watershed Intelligence Platform</span>
        <span className="stats">{sites.reduce((a, s) => a + s.observations, 0).toLocaleString()} observations across {sites.length} watersheds</span>
      </header>
      <div className="app-body">
        <MapView
          sites={sites}
          selectedSite={selectedSite}
          onSelectSite={setSelectedSite}
        />
        {siteDetail && (
          <SitePanel
            site={siteDetail}
            watershed={selectedSite!}
            onClose={() => setSelectedSite(null)}
          />
        )}
      </div>
    </div>
  )
}

export default App
