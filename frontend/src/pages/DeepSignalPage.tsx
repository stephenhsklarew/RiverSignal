import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import logo from '../assets/riversignal-logo.svg'
import MapView from '../components/MapView'
import '../App.css'
import './DeepSignalPage.css'

const API_BASE = '/api/v1'

const WATERSHEDS = ['klamath', 'mckenzie', 'deschutes', 'metolius', 'johnday']
const NAMES: Record<string, string> = {
  klamath: 'Upper Klamath', mckenzie: 'McKenzie', deschutes: 'Deschutes',
  metolius: 'Metolius', johnday: 'John Day',
}

interface GeoUnit {
  unit_name: string; formation: string; rock_type: string; lithology: string;
  period: string; age_min_ma: number | null; age_max_ma: number | null;
  description: string;
}

interface Fossil {
  taxon_name: string; phylum: string; class_name: string; period: string;
  age_min_ma: number | null; age_max_ma: number | null; distance_km: number | null;
}

export default function DeepSignalPage() {
  const { watershed: urlWatershed } = useParams()
  const [selected, setSelected] = useState(urlWatershed || 'johnday')
  const [geoUnits, setGeoUnits] = useState<GeoUnit[]>([])
  const [fossils, setFossils] = useState<Fossil[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch(`${API_BASE}/geology/watershed-link/${selected}`).then(r => r.json()),
      fetch(`${API_BASE}/fossils/near/44.66/-120.0?radius_km=100`).then(r => r.json()),
    ]).then(([link, fossilData]) => {
      setGeoUnits(link.geologic_units || [])
      setFossils(fossilData.fossils || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [selected])

  const rockTypeCounts: Record<string, number> = {}
  const periodCounts: Record<string, number> = {}
  geoUnits.forEach(u => {
    if (u.rock_type) rockTypeCounts[u.rock_type] = (rockTypeCounts[u.rock_type] || 0) + 1
    if (u.period) periodCounts[u.period] = (periodCounts[u.period] || 0) + 1
  })

  return (
    <div className="ds-layout">
      <div className="ds-topbar">
        <Link to="/" className="ds-logo-link">
          <img src={logo} alt="RiverSignal" className="ds-logo" />
        </Link>
        <span className="ds-product-badge">DeepSignal</span>
        <nav className="ds-nav">
          {WATERSHEDS.map(ws => (
            <button key={ws} className={`ds-nav-btn ${selected === ws ? 'active' : ''}`}
              onClick={() => setSelected(ws)}>
              {NAMES[ws]}
            </button>
          ))}
        </nav>
        <Link to="/riversignal" className="ds-switch-link">RiverSignal</Link>
        <Link to="/trail" className="ds-switch-link">DeepTrail</Link>
      </div>

      <div className="ds-main">
        <div className="ds-map-pane">
          <MapView sites={[]} selectedSite={null} onSelectSite={() => {}} />
        </div>

        <div className="ds-data-pane">
          {loading ? (
            <div className="ds-loading">Loading geology data...</div>
          ) : (
            <>
              <section className="ds-section">
                <h2>Geologic Units — {NAMES[selected]}</h2>
                <div className="ds-kpi-row">
                  <div className="ds-kpi">
                    <span className="ds-kpi-val">{geoUnits.length}</span>
                    <span className="ds-kpi-label">Units</span>
                  </div>
                  {Object.entries(rockTypeCounts).map(([type, count]) => (
                    <div className="ds-kpi" key={type}>
                      <span className="ds-kpi-val">{count}</span>
                      <span className="ds-kpi-label">{type}</span>
                    </div>
                  ))}
                </div>

                <div className="ds-table-wrap">
                  <table className="ds-table">
                    <thead>
                      <tr>
                        <th>Formation</th><th>Rock Type</th><th>Lithology</th>
                        <th>Period</th><th>Age (Ma)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {geoUnits.slice(0, 30).map((u, i) => (
                        <tr key={i}>
                          <td>{u.formation || u.unit_name}</td>
                          <td><span className={`rock-badge ${u.rock_type}`}>{u.rock_type}</span></td>
                          <td className="truncate">{u.lithology?.slice(0, 60)}</td>
                          <td>{u.period}</td>
                          <td>{u.age_max_ma ? `${u.age_max_ma}–${u.age_min_ma || '?'}` : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="ds-section">
                <h2>Fossil Occurrences</h2>
                <div className="ds-kpi-row">
                  <div className="ds-kpi">
                    <span className="ds-kpi-val">{fossils.length}</span>
                    <span className="ds-kpi-label">Fossils within 100km</span>
                  </div>
                </div>
                <div className="ds-table-wrap">
                  <table className="ds-table">
                    <thead>
                      <tr>
                        <th>Taxon</th><th>Phylum</th><th>Class</th>
                        <th>Period</th><th>Age (Ma)</th><th>Distance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fossils.slice(0, 30).map((f, i) => (
                        <tr key={i}>
                          <td className="italic">{f.taxon_name}</td>
                          <td>{f.phylum}</td>
                          <td>{f.class_name}</td>
                          <td>{f.period}</td>
                          <td>{f.age_max_ma ? `${f.age_max_ma}–${f.age_min_ma || '?'}` : '—'}</td>
                          <td>{f.distance_km ? `${f.distance_km} km` : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="ds-section">
                <h2>Geologic Periods</h2>
                <div className="ds-period-chips">
                  {Object.entries(periodCounts)
                    .sort(([,a], [,b]) => b - a)
                    .map(([period, count]) => (
                      <span key={period} className="ds-period-chip">
                        {period} <strong>{count}</strong>
                      </span>
                    ))}
                </div>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
