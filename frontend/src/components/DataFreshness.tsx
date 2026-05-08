import { useEffect, useState } from 'react'
import { API_BASE } from '../config'

interface Pipeline {
  source: string
  last_sync: string | null
  total_jobs: number
  completed: number
  failed: number
}

interface CuratedSource {
  name: string
  table: string
  records: number
  description: string
  source: string
}

interface DataStatus {
  bronze: { observations: number; time_series: number; interventions: number; most_recent_sync: string | null; oldest_pipeline_sync: string | null }
  silver: { views: number }
  gold: { views: number }
  curated?: CuratedSource[]
  pipelines: Pipeline[]
}

function timeAgo(isoDate: string | null): string {
  if (!isoDate) return 'never'
  const diff = Date.now() - new Date(isoDate).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function DataFreshness({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState<DataStatus | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/data-status`)
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json() })
      .then(data => { if (data.bronze) setStatus(data) })
      .catch(() => {})  // Silently fail — component just won't render
  }, [])

  if (!status?.bronze) return null

  const lastSync = status.bronze.most_recent_sync

  if (compact) {
    return (
      <div className="freshness-compact" title="Click for pipeline details" onClick={() => setExpanded(!expanded)}>
        <span className="freshness-dot" />
        <span className="freshness-text">
          Data updated {timeAgo(lastSync)}
        </span>
        {expanded && (
          <div className="freshness-dropdown">
            <div className="freshness-header">
              <span>Pipeline</span><span>Last Sync</span><span>Status</span>
            </div>
            {status.pipelines.map(p => (
              <div key={p.source} className="freshness-row">
                <span className="freshness-source">{p.source}</span>
                <span className="freshness-time">{timeAgo(p.last_sync)}</span>
                <span className={`freshness-badge ${p.failed > 0 ? 'warn' : 'ok'}`}>
                  {p.failed > 0 ? `${p.failed} failed` : 'ok'}
                </span>
              </div>
            ))}
            <div className="freshness-summary">
              <span>Bronze: {(status.bronze.observations + status.bronze.time_series).toLocaleString()} records</span>
              <span>Silver: {status.silver.views} views</span>
              <span>Gold: {status.gold.views} views</span>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Full display for reports page
  return (
    <div className="freshness-full">
      <div className="freshness-full-header">
        <span className="freshness-dot" />
        <span>Data last updated {timeAgo(lastSync)}</span>
        <button className="freshness-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Hide' : 'Show'} pipeline details
        </button>
      </div>
      {expanded && (
        <div className="freshness-table">
          <table>
            <thead>
              <tr><th>Pipeline</th><th>Last Sync</th><th>Jobs</th><th>Failed</th></tr>
            </thead>
            <tbody>
              {status.pipelines.map(p => (
                <tr key={p.source}>
                  <td>{p.source}</td>
                  <td className="mono">{p.last_sync ? new Date(p.last_sync).toLocaleDateString() + ' ' + new Date(p.last_sync).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                  <td className="mono">{p.completed}</td>
                  <td className="mono" style={p.failed > 0 ? { color: 'var(--alert)' } : {}}>{p.failed}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="freshness-layers">
            <div><strong>Bronze:</strong> {status.bronze.observations.toLocaleString()} observations · {status.bronze.time_series.toLocaleString()} time series · {status.bronze.interventions.toLocaleString()} interventions</div>
            <div><strong>Silver:</strong> {status.silver.views} materialized views</div>
            <div><strong>Gold:</strong> {status.gold.views} materialized views</div>
          </div>
          {status.curated && status.curated.length > 0 && (
            <div className="freshness-curated">
              <div className="freshness-curated-title">Manually Curated Data</div>
              <table>
                <thead>
                  <tr><th>Name</th><th>Records</th><th>Description</th><th>Source</th></tr>
                </thead>
                <tbody>
                  {status.curated.map((c, i) => (
                    <tr key={i}>
                      <td>{c.name}</td>
                      <td className="mono">{c.records?.toLocaleString()}</td>
                      <td>{c.description}</td>
                      <td className="mono" style={{ fontSize: '10px' }}>{c.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
