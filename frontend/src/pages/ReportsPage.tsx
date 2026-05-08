import { useState } from 'react'
import { Link } from 'react-router-dom'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import logo from '../assets/riversignal-logo.svg'
import DataFreshness from '../components/DataFreshness'
import '../App.css'
import { API_BASE } from '../config'
import './ReportsPage.css'

const WATERSHEDS = [
  { id: 'mckenzie', name: 'McKenzie River' },
  { id: 'deschutes', name: 'Deschutes River' },
  { id: 'metolius', name: 'Metolius River' },
  { id: 'klamath', name: 'Upper Klamath Basin' },
  { id: 'johnday', name: 'John Day River' },
  { id: 'skagit', name: 'Skagit River' },
]

export default function ReportsPage() {
  const [watershed, setWatershed] = useState('mckenzie')
  const [dateStart, setDateStart] = useState('2023-01-01')
  const [dateEnd, setDateEnd] = useState('2025-12-31')
  const [report, setReport] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [format, setFormat] = useState<'markdown' | 'json'>('markdown')

  const generateReport = () => {
    setLoading(true)
    setReport(null)
    fetch(`${API_BASE}/sites/${watershed}/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date_start: dateStart, date_end: dateEnd, format }),
    })
      .then(r => format === 'json' ? r.json().then(d => JSON.stringify(d, null, 2)) : r.text())
      .then(data => { setReport(data); setLoading(false) })
      .catch(e => { setReport(`Error: ${e.message}`); setLoading(false) })
  }

  const downloadReport = () => {
    if (!report) return
    const ext = format === 'json' ? 'json' : 'md'
    const mime = format === 'json' ? 'application/json' : 'text/markdown'
    const blob = new Blob([report], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${watershed}-report-${dateStart}-to-${dateEnd}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="app">
      <div className="topbar">
        <Link to="/" className="topbar-brand" style={{ textDecoration: 'none', color: 'inherit' }}>
          <img src={logo} alt="RiverSignal" style={{ height: 34 }} />
        </Link>
        <div className="topbar-nav">
          <Link to="/"><button>Home</button></Link>
          <Link to="/map"><button>Dashboard</button></Link>
          <button className="active">Reports</button>
        </div>
        <div className="topbar-status">
          <DataFreshness compact />
        </div>
      </div>

      <div className="reports-layout">
        {/* Sidebar controls */}
        <div className="reports-sidebar">
          <div className="reports-sidebar-section">
            <label className="reports-label">Watershed</label>
            <select value={watershed} onChange={e => setWatershed(e.target.value)} className="reports-select">
              {WATERSHEDS.map(ws => (
                <option key={ws.id} value={ws.id}>{ws.name}</option>
              ))}
            </select>
          </div>

          <div className="reports-sidebar-section">
            <label className="reports-label">Date Range</label>
            <div className="reports-date-row">
              <input type="date" value={dateStart} onChange={e => setDateStart(e.target.value)} className="reports-input" />
              <span className="reports-date-sep">to</span>
              <input type="date" value={dateEnd} onChange={e => setDateEnd(e.target.value)} className="reports-input" />
            </div>
          </div>

          <div className="reports-sidebar-section">
            <label className="reports-label">Format</label>
            <div className="reports-format-row">
              <button className={`reports-format-btn ${format === 'markdown' ? 'active' : ''}`} onClick={() => setFormat('markdown')}>Markdown</button>
              <button className={`reports-format-btn ${format === 'json' ? 'active' : ''}`} onClick={() => setFormat('json')}>JSON</button>
            </div>
          </div>

          <button className="reports-generate" onClick={generateReport} disabled={loading}>
            {loading ? 'Generating...' : 'Generate Report'}
          </button>

          {report && (
            <button className="reports-download" onClick={downloadReport}>
              Download {format === 'json' ? '.json' : '.md'}
            </button>
          )}

          <DataFreshness />

          <div className="reports-info">
            <div className="section-title">Report Contents</div>
            <ul>
              <li>Executive summary (AI-generated)</li>
              <li>Species richness by year</li>
              <li>Restoration interventions</li>
              <li>Water quality summary</li>
              <li>Indicator species checklist</li>
              <li>Anomaly alerts</li>
              <li>Invasive species detections</li>
              <li>Restoration outcomes (before/after)</li>
            </ul>
          </div>
        </div>

        {/* Report display */}
        <div className="reports-content">
          {!report && !loading && (
            <div className="reports-empty">
              <div className="reports-empty-icon">📄</div>
              <h3>Watershed Restoration Progress Report</h3>
              <p>Select a watershed and date range, then click Generate Report to create an OWEB-format progress report with species data, water quality, interventions, and outcomes.</p>
            </div>
          )}
          {loading && (
            <div className="reports-loading">
              <div className="thinking-dot" />
              Generating report for {WATERSHEDS.find(w => w.id === watershed)?.name}...
            </div>
          )}
          {report && format === 'markdown' && (
            <div className="reports-markdown">
              <Markdown remarkPlugins={[remarkGfm]}>{report}</Markdown>
            </div>
          )}
          {report && format === 'json' && (
            <pre className="reports-json">{report}</pre>
          )}
        </div>
      </div>
    </div>
  )
}
