import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import logo from '../assets/riversignal-logo.svg'
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

  useEffect(() => {
    fetch(`${API_BASE}/sites`)
      .then(r => r.json())
      .then(data => { setSites(data); setLoading(false) })
      .catch(e => { console.error(e); setLoading(false) })
  }, [])

  // Auto-select watershed from URL
  useEffect(() => {
    if (urlWatershed && !selectedSite) {
      setSelectedSite(urlWatershed)
    }
  }, [urlWatershed])

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
      <div className="topbar">
        <Link to="/" className="topbar-brand" style={{ textDecoration: 'none', color: 'inherit' }}>
          <img src={logo} alt="RiverSignal" style={{ height: 34 }} />
        </Link>
        <div className="topbar-nav">
          <Link to="/"><button>Home</button></Link>
          <button className="active">Dashboard</button>
          <button>Reports</button>
        </div>
        <div className="topbar-status">
          <span className="status-dot" />
          <span>15 pipelines · {(totalObs + totalTs).toLocaleString()} records</span>
        </div>
      </div>

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
            initialQuestion={pendingQuestion}
            onQuestionConsumed={() => setPendingQuestion(null)}
          />
        )}
      </div>
    </div>
  )
}
