import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import logo from '../assets/riversignal-logo.svg'
import DataFreshness from '../components/DataFreshness'
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

  const NAMES: Record<string, string> = {
    klamath: 'Klamath', mckenzie: 'McKenzie', deschutes: 'Deschutes',
    metolius: 'Metolius', johnday: 'John Day',
  }

  return (
    <div className="app">
      <div className="topbar">
        <Link to="/" className="topbar-brand" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center', gap: 8 }}>
          <img src={logo} alt="RiverSignal" style={{ height: 34 }} />
          <span style={{ background: '#1a6b4a', color: '#fff', fontSize: '0.65rem', fontWeight: 600, padding: '2px 8px', borderRadius: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>RiverSignal</span>
        </Link>
        <div className="topbar-nav">
          {sites.map(s => (
            <button
              key={s.watershed}
              className={selectedSite === s.watershed ? 'active' : ''}
              onClick={() => setSelectedSite(s.watershed)}
            >
              {NAMES[s.watershed] || s.name}
            </button>
          ))}
        </div>
        <div className="topbar-nav" style={{ marginLeft: 'auto', gap: 2 }}>
          <Link to="/signal/reports"><button>Reports</button></Link>
          <Link to="/path"><button>RiverPath</button></Link>
          <Link to="/deepsignal"><button>DeepSignal</button></Link>
        </div>
        <div className="topbar-status">
          <DataFreshness compact />
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
