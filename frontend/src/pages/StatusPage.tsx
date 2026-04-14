import { useEffect, useState } from 'react'
import './StatusPage.css'

const API = 'http://localhost:8001/api/v1'

interface SourceInfo {
  source_type: string
  description: string
  upstream_frequency: string
  refresh_schedule: string
  last_sync: string | null
  status: string
  record_count: number
}

// Static metadata about each source
const SOURCE_META: Record<string, { description: string; upstream: string; refresh: string }> = {
  inaturalist: { description: 'Citizen science species observations with photos', upstream: 'Continuous', refresh: 'Daily' },
  usgs: { description: 'Stream gauge readings — flow, temperature, dissolved oxygen', upstream: 'Real-time (15 min)', refresh: 'Daily' },
  snotel: { description: 'Snowpack, snow water equivalent, precipitation, air temp', upstream: 'Daily', refresh: 'Daily' },
  prism: { description: 'Gridded climate normals — monthly temp and precipitation', upstream: 'Monthly', refresh: 'Monthly' },
  biodata: { description: 'Professional macroinvertebrate and fish community surveys (USGS)', upstream: 'Quarterly', refresh: 'Monthly' },
  wqp_bugs: { description: 'Aquatic macroinvertebrate data from Water Quality Portal', upstream: 'Quarterly', refresh: 'Monthly' },
  owdp: { description: 'Water chemistry — nutrients, pH, conductivity, turbidity', upstream: 'Monthly', refresh: 'Weekly' },
  streamnet: { description: 'Salmon and steelhead abundance monitoring', upstream: 'Annually', refresh: 'Monthly' },
  mtbs: { description: 'Fire burn severity perimeters (MTBS/NIFC)', upstream: 'Annually', refresh: 'Quarterly' },
  nhdplus: { description: 'Stream flowlines, river miles, drainage network', upstream: 'Static', refresh: 'Annually' },
  restoration: { description: 'Restoration projects — OWRI, NOAA, PCSRF', upstream: 'Quarterly', refresh: 'Monthly' },
  fish_barrier: { description: 'Fish passage barriers with passage status', upstream: 'Annually', refresh: 'Quarterly' },
  fishing: { description: 'ODFW sport catch, harvest trends, stocking schedule', upstream: 'Monthly', refresh: 'Weekly' },
  deq_303d: { description: 'EPA 303(d) impaired waters — temperature, nutrients, bacteria', upstream: 'Biennial', refresh: 'Quarterly' },
  nwi: { description: 'National Wetlands Inventory — wetland polygons and types', upstream: 'Static', refresh: 'Annually' },
  wbd: { description: 'USGS watershed boundaries (HUC)', upstream: 'Static', refresh: 'Annually' },
  macrostrat: { description: 'Geologic units — rock type, age, formation, lithology', upstream: 'Rarely', refresh: 'Annually' },
  pbdb: { description: 'Paleobiology Database — fossil occurrences with taxonomy', upstream: 'Weekly', refresh: 'Monthly' },
  idigbio: { description: 'Museum fossil specimen records', upstream: 'Monthly', refresh: 'Monthly' },
  gbif: { description: 'GBIF fossil specimens with images from global museums', upstream: 'Weekly', refresh: 'Monthly' },
  blm_sma: { description: 'BLM land ownership and collecting legality', upstream: 'Annually', refresh: 'Quarterly' },
  dogami: { description: 'Oregon geology polygons (DOGAMI/OGDC)', upstream: 'Rarely', refresh: 'Annually' },
  mrds: { description: 'USGS mineral deposit locations — commodity, status', upstream: 'Rarely', refresh: 'Annually' },
  recreation: { description: 'USFS campgrounds/trailheads + OSMB boat ramps', upstream: 'Seasonally', refresh: 'Monthly' },
}

const LIVE_SOURCES = [
  { name: 'NWS Weather Forecast', description: '7-day weather forecast by watershed from api.weather.gov', upstream: 'Hourly', cache: '30 min' },
  { name: 'USGS Instantaneous Values', description: 'Real-time stream flow and water temperature', upstream: '15 minutes', cache: '15 min' },
]

export default function StatusPage() {
  const [sources, setSources] = useState<SourceInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [viewCount, setViewCount] = useState(0)
  const [totalRecords, setTotalRecords] = useState(0)

  useEffect(() => {
    fetch(`${API}/data-status`)
      .then(r => r.json())
      .then(data => {
        // Build sync map from pipelines array
        const syncMap: Record<string, { last_sync: string; failed: number; completed: number }> = {}
        for (const p of (data.pipelines || [])) {
          syncMap[p.source] = { last_sync: p.last_sync, failed: p.failed, completed: p.completed }
        }

        const combined: SourceInfo[] = Object.entries(SOURCE_META).map(([key, meta]) => ({
          source_type: key,
          description: meta.description,
          upstream_frequency: meta.upstream,
          refresh_schedule: meta.refresh,
          last_sync: syncMap[key]?.last_sync || null,
          status: syncMap[key] ? (syncMap[key].failed > 0 ? 'warning' : 'healthy') : 'unknown',
          record_count: 0,
        }))

        setSources(combined)
        const sv = data.silver?.views || 0
        const gv = data.gold?.views || 0
        setViewCount(sv + gv)
        const obs = data.bronze?.observations || 0
        const ts = data.bronze?.time_series || 0
        const interventions = data.bronze?.interventions || 0
        setTotalRecords(obs + ts + interventions)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const now = new Date()

  function freshness(lastSync: string | null): { label: string; cls: string } {
    if (!lastSync) return { label: 'Never synced', cls: 'stale' }
    const diff = now.getTime() - new Date(lastSync).getTime()
    const hours = diff / (1000 * 60 * 60)
    const days = hours / 24
    if (days < 1) return { label: `${Math.round(hours)}h ago`, cls: 'fresh' }
    if (days < 7) return { label: `${Math.round(days)}d ago`, cls: 'recent' }
    if (days < 30) return { label: `${Math.round(days)}d ago`, cls: 'aging' }
    return { label: `${Math.round(days)}d ago`, cls: 'stale' }
  }

  return (
    <div className="status-page">
      <div className="status-header">
        <h1 className="status-title">Data Pipeline Status</h1>
        <p className="status-summary">
          {sources.length + LIVE_SOURCES.length} data sources feeding {totalRecords.toLocaleString()} records across 5 Oregon watersheds
        </p>
        <div className="status-stats">
          <div className="status-stat">
            <span className="status-stat-value">{sources.length + LIVE_SOURCES.length}</span>
            <span className="status-stat-label">Data Sources</span>
          </div>
          <div className="status-stat">
            <span className="status-stat-value">{totalRecords.toLocaleString()}</span>
            <span className="status-stat-label">Total Records</span>
          </div>
          <div className="status-stat">
            <span className="status-stat-value">{viewCount}</span>
            <span className="status-stat-label">Materialized Views</span>
          </div>
          <div className="status-stat">
            <span className="status-stat-value">5</span>
            <span className="status-stat-label">Watersheds</span>
          </div>
        </div>
        <div className="status-legend">
          <span className="status-legend-item"><span className="status-badge healthy">healthy</span> Last sync completed successfully</span>
          <span className="status-legend-item"><span className="status-badge warning">warning</span> Last sync had some failures</span>
          <span className="status-legend-item"><span className="status-badge unknown">unknown</span> No sync record found</span>
          <span className="status-legend-item"><span className="status-badge live">live</span> Real-time API (not stored in database)</span>
        </div>
      </div>

      {loading ? (
        <div className="status-loading">Loading pipeline status...</div>
      ) : (
        <>
          {/* Ingested sources */}
          <section className="status-section">
            <h2>Ingested Data Sources ({sources.length})</h2>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Description</th>
                    <th>Upstream</th>
                    <th>Refresh</th>
                    <th>Last Synced</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map(s => {
                    const f = freshness(s.last_sync)
                    return (
                      <tr key={s.source_type}>
                        <td className="status-source">{s.source_type}</td>
                        <td className="status-desc">{s.description}</td>
                        <td className="status-freq">{s.upstream_frequency}</td>
                        <td className="status-freq">{s.refresh_schedule}</td>
                        <td className={`status-sync ${f.cls}`}>
                          {s.last_sync ? new Date(s.last_sync).toLocaleDateString() : '—'}
                          <span className="status-ago">{f.label}</span>
                        </td>
                        <td><span className={`status-badge ${s.status}`}>{s.status}</span></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* Live APIs */}
          <section className="status-section">
            <h2>Live API Sources ({LIVE_SOURCES.length})</h2>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Description</th>
                    <th>Upstream</th>
                    <th>Cache TTL</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {LIVE_SOURCES.map(s => (
                    <tr key={s.name}>
                      <td className="status-source">{s.name}</td>
                      <td className="status-desc">{s.description}</td>
                      <td className="status-freq">{s.upstream}</td>
                      <td className="status-freq">{s.cache}</td>
                      <td><span className="status-badge healthy">live</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
