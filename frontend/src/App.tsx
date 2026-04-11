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

  const totalObs = sites.reduce((a, s) => a + s.observations, 0)
  const totalTs = sites.reduce((a, s) => a + s.time_series, 0)

  return (
    <div className="app">
      {/* Top Bar */}
      <div className="topbar">
        <div className="topbar-brand">
          <span className="dot" />
          RiverSignal
        </div>
        <div className="topbar-nav">
          <button className="active">Dashboard</button>
          <button>Reports</button>
          <button>Interventions</button>
          <button>Data Sources</button>
        </div>
        <div className="topbar-status">
          <span className="status-dot" />
          <span>15 pipelines · {(totalObs + totalTs).toLocaleString()} records · synced</span>
        </div>
      </div>

      {/* Main Body */}
      <div className={`app-body${siteDetail ? '' : ' no-panel'}`}>
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
