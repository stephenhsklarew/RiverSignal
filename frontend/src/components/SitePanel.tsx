import { useState, useEffect, useRef } from 'react'
import Markdown from 'react-markdown'

const API_BASE = 'http://localhost:8001/api/v1'

interface SitePanelProps {
  site: any
  watershed: string
  onClose: () => void
  initialQuestion?: string | null
  onQuestionConsumed?: () => void
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function SitePanel({ site, watershed, onClose, initialQuestion, onQuestionConsumed }: SitePanelProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'species' | 'fishing' | 'story' | 'recs' | 'ask'>(
    initialQuestion ? 'ask' : 'overview'
  )
  const [species, setSpecies] = useState<any[]>([])
  const [fishingBrief, setFishingBrief] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any>(null)
  const [recsLoading, setRecsLoading] = useState(false)
  const [story, setStory] = useState<any>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [questionSent, setQuestionSent] = useState(false)

  // Auto-send question from URL (e.g., navigating from home page)
  useEffect(() => {
    if (initialQuestion && !questionSent && site) {
      setQuestionSent(true)
      setActiveTab('ask')
      setChatMessages([{ role: 'user', content: initialQuestion }])
      setChatLoading(true)
      fetch(`${API_BASE}/sites/${watershed}/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: initialQuestion }),
      })
        .then(r => r.json())
        .then(data => setChatMessages(prev => [...prev, { role: 'assistant', content: data.answer || data.detail || 'Unable to answer.' }]))
        .catch(() => setChatMessages(prev => [...prev, { role: 'assistant', content: 'Set ANTHROPIC_API_KEY to enable AI answers.' }]))
        .finally(() => { setChatLoading(false); onQuestionConsumed?.() })
    }
  }, [initialQuestion, site])

  useEffect(() => {
    if (activeTab === 'species' && species.length === 0)
      fetch(`${API_BASE}/sites/${watershed}/species?limit=30`).then(r => r.json()).then(setSpecies).catch(console.error)
    if (activeTab === 'fishing' && !fishingBrief)
      fetch(`${API_BASE}/sites/${watershed}/fishing/brief`).then(r => r.json()).then(setFishingBrief).catch(console.error)
    if (activeTab === 'story' && !story)
      fetch(`${API_BASE}/sites/${watershed}/story`).then(r => r.json()).then(setStory).catch(console.error)
    if (activeTab === 'recs' && !recommendations && !recsLoading) {
      setRecsLoading(true)
      fetch(`${API_BASE}/sites/${watershed}/recommendations`, { method: 'POST' })
        .then(r => r.json()).then(d => { setRecommendations(d); setRecsLoading(false) })
        .catch(() => setRecsLoading(false))
    }
  }, [activeTab, watershed])

  const health = site.health || {}
  const sc = site.scorecard || {}
  const healthClass = (health.score || 0) >= 70 ? 'good' : (health.score || 0) >= 50 ? 'moderate' : 'poor'

  const sendChat = () => {
    if (!chatInput.trim() || chatLoading) return
    const question = chatInput.trim()
    setChatInput('')
    setActiveTab('ask')
    setChatMessages(prev => [...prev, { role: 'user', content: question }])
    setChatLoading(true)
    fetch(`${API_BASE}/sites/${watershed}/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
      .then(r => r.json())
      .then(data => setChatMessages(prev => [...prev, { role: 'assistant', content: data.answer || data.detail || 'Unable to answer.' }]))
      .catch(() => setChatMessages(prev => [...prev, { role: 'assistant', content: 'Set ANTHROPIC_API_KEY to enable AI answers. Data available in other tabs.' }]))
      .finally(() => setChatLoading(false))
  }

  return (
    <div className="site-panel">
      {/* Header */}
      <div className="panel-header">
        <h2>
          {site.name}
          {health.score != null && <span className={`health-pill ${healthClass}`}>{health.score}</span>}
        </h2>
        <button className="panel-close" onClick={onClose}>×</button>
      </div>

      {/* Tabs */}
      <div className="panel-tabs">
        {(['overview', 'species', 'fishing', 'story', 'recs', 'ask'] as const).map(tab => (
          <button key={tab} className={`panel-tab${activeTab === tab ? ' active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="panel-content">

        {activeTab === 'overview' && (
          <>
            {/* KPI Grid */}
            <div className="section">
              <div className="section-title">Key Metrics</div>
              <div className="kpi-grid">
                <div className="kpi-card"><div className={`value ${health.water_temp_c != null && health.water_temp_c < 16 ? 'green' : 'amber'}`}>{health.water_temp_c ?? '—'}°C</div><div className="label">Water Temp</div></div>
                <div className="kpi-card"><div className={`value ${health.dissolved_oxygen_mg_l != null && health.dissolved_oxygen_mg_l > 8 ? 'green' : 'red'}`}>{health.dissolved_oxygen_mg_l ?? '—'}</div><div className="label">DO mg/L</div></div>
                <div className="kpi-card"><div className="value">{sc.total_species?.toLocaleString() ?? '—'}</div><div className="label">Species</div></div>
                <div className="kpi-card"><div className="value">{sc.total_interventions ?? '—'}</div><div className="label">Projects</div></div>
              </div>
            </div>

            {/* Scorecard */}
            <div className="section">
              <div className="section-title">Data Coverage</div>
              <div className="kpi-grid">
                <div className="kpi-card"><div className="value">{sc.fish_species ?? '—'}</div><div className="label">Fish</div></div>
                <div className="kpi-card"><div className="value">{sc.amphibian_species ?? '—'}</div><div className="label">Amphibians</div></div>
                <div className="kpi-card"><div className="value">{sc.usgs_stations ?? '—'}</div><div className="label">USGS Stn</div></div>
                <div className="kpi-card"><div className="value">{sc.fire_events ?? '—'}</div><div className="label">Fires</div></div>
              </div>
            </div>

            {/* Indicator Species Table */}
            <div className="section">
              <div className="section-title">Indicator Species</div>
              <table className="data-table">
                <thead><tr><th>Species</th><th>Status</th><th>Obs</th></tr></thead>
                <tbody>
                  {(site.indicators || []).map((ind: any, i: number) => (
                    <tr key={i}>
                      <td>{ind.common_name}</td>
                      <td><span className={`status-tag ${ind.status === 'detected' ? (ind.direction === 'negative' ? 'invasive' : 'detected') : 'absent'}`}>
                        {ind.direction === 'negative' ? 'invasive' : ind.status}
                      </span></td>
                      <td className="mono">{ind.detections}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* What's Here Now */}
            <WhatsHereNow watershed={watershed} />

            {/* Stewardship Opportunities */}
            <StewardshipSection watershed={watershed} />
          </>
        )}

        {activeTab === 'species' && (
          <div className="section">
            <div className="section-title">Species Gallery · {sc.total_species?.toLocaleString()} species</div>
            <div className="species-grid">
              {species.map((s: any, i: number) => (
                <div key={i} className="species-card">
                  {s.photo_url && <img src={s.photo_url} alt={s.common_name || s.taxon_name} loading="lazy" />}
                  <div className="sp-info">
                    <div className="sp-common">{s.common_name || s.taxon_name}</div>
                    <div className="sp-sci">{s.taxon_name}</div>
                    {s.conservation_status && <span className="conservation-tag">{s.conservation_status}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'fishing' && (
          <>
            <div className="section">
              <div className="section-title">Conditions</div>
              {fishingBrief?.conditions && (
                <>
                  <div className="metric-row"><span className="metric-label">Water Temp</span><span className="metric-value">{fishingBrief.conditions.water_temp_c ?? '—'}°C</span></div>
                  <div className="metric-row"><span className="metric-label">Flow</span><span className="metric-value">{fishingBrief.conditions.discharge_cfs?.toLocaleString() ?? '—'} cfs</span></div>
                  <div className="metric-row"><span className="metric-label">Steelhead Harvest</span><span className="metric-value">{fishingBrief.conditions.steelhead_harvest?.toLocaleString() ?? '—'}</span></div>
                  <div className="metric-row"><span className="metric-label">Trout Stocked</span><span className="metric-value good">{fishingBrief.conditions.trout_stocked?.toLocaleString() ?? '—'}</span></div>
                </>
              )}
            </div>
            <div className="section">
              <div className="section-title">Recent Stocking</div>
              <table className="data-table">
                <thead><tr><th>Waterbody</th><th>Fish</th><th>Date</th></tr></thead>
                <tbody>
                  {(fishingBrief?.stocking || []).map((s: any, i: number) => (
                    <tr key={i}><td>{s.waterbody}</td><td className="mono">{s.fish?.toLocaleString()}</td><td className="mono">{s.date}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="section">
              <div className="section-title">Species by Reach</div>
              <table className="data-table">
                <thead><tr><th>Stream</th><th>Species</th><th>Use</th></tr></thead>
                <tbody>
                  {(fishingBrief?.species_by_reach || []).slice(0, 12).map((s: any, i: number) => (
                    <tr key={i}><td>{s.stream}</td><td>{s.common_name || s.species}</td><td>{s.use_type}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {activeTab === 'story' && (
          <>
            {story?.health && (
              <div className="section">
                <div className="section-title">Current Health</div>
                <div className="kpi-grid">
                  <div className="kpi-card"><div className="value green">{story.health.score}</div><div className="label">Score</div></div>
                  <div className="kpi-card"><div className="value">{story.health.water_temp_c}°C</div><div className="label">Temp</div></div>
                  <div className="kpi-card"><div className="value">{story.health.do_mg_l}</div><div className="label">DO</div></div>
                  <div className="kpi-card"><div className="value">{story.health.species}</div><div className="label">Spp/mo</div></div>
                </div>
              </div>
            )}
            <div className="section">
              <div className="section-title">Timeline</div>
              {(story?.timeline || []).slice(0, 15).map((e: any, i: number) => (
                <div key={i} className="timeline-event">
                  <span className="timeline-year">{e.year}</span>
                  <span className={`timeline-type ${e.type}`}>{e.type}</span>
                  <span className="timeline-name">{e.name}</span>
                </div>
              ))}
            </div>
            {(story?.fire_recovery || []).length > 0 && (
              <div className="section">
                <div className="section-title">Fire Recovery</div>
                <table className="data-table">
                  <thead><tr><th>Year</th><th>Δ Fire</th><th>Species</th><th>Obs</th></tr></thead>
                  <tbody>
                    {story.fire_recovery.filter((r: any) => r.years_since >= -1 && r.years_since <= 6).map((r: any, i: number) => (
                      <tr key={i} style={r.years_since === 0 ? { background: 'var(--alert-light)' } : {}}>
                        <td className="mono">{r.obs_year}{r.years_since === 0 ? ' 🔥' : ''}</td>
                        <td className="mono">{r.years_since > 0 ? '+' : ''}{r.years_since}</td>
                        <td className="mono" style={r.years_since >= 4 ? { color: 'var(--accent)', fontWeight: 600 } : {}}>{r.species?.toLocaleString()}</td>
                        <td className="mono">{r.observation_count?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {activeTab === 'recs' && (
          <div className="section">
            <div className="section-title">Field Recommendations</div>
            {recsLoading ? (
              <div style={{ padding: 20, color: '#888', textAlign: 'center' }}>Generating recommendations...</div>
            ) : recommendations?.recommendations?.length > 0 ? (
              <div className="recs-list">
                {recommendations.recommendations.map((rec: any, i: number) => (
                  <div key={i} className="rec-card">
                    <div className="rec-rank">#{rec.rank || i + 1}</div>
                    <div className="rec-body">
                      <div className="rec-action">{rec.action}</div>
                      {rec.site && <div className="rec-site">{rec.site}</div>}
                      <div className="rec-sensitivity">{rec.time_sensitivity}</div>
                      <div className="rec-reasoning">{rec.reasoning}</div>
                      <span className="rec-tag">{rec.grounded_in}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : recommendations?.narrative ? (
              <div style={{ padding: 12, fontSize: 13, color: '#666', lineHeight: 1.6 }}>{recommendations.narrative}</div>
            ) : (
              <div style={{ padding: 20, color: '#888', textAlign: 'center' }}>No priority actions this period. Sites are in stable condition.</div>
            )}
          </div>
        )}

        {activeTab === 'ask' && (
          <AskTab
            site={site}
            chatMessages={chatMessages}
            chatLoading={chatLoading}
            onSuggestionClick={(q: string) => setChatInput(q)}
          />
        )}
      </div>

      {/* Bottom Chat Bar (always visible) */}
      <div className="chat-sidebar">
        <div className="chat-label">AI Assistant</div>
        <div className="chat-input-row">
          <input
            type="text"
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') sendChat() }}
            placeholder={`Ask about ${site.name}...`}
          />
          <button onClick={sendChat} disabled={!chatInput.trim() || chatLoading}>Query</button>
        </div>
      </div>
    </div>
  )
}

/* ── Ask Tab (extracted for proper layout) ── */
function AskTab({ site, chatMessages, chatLoading, onSuggestionClick }: {
  site: any; chatMessages: ChatMessage[];
  chatLoading: boolean; onSuggestionClick: (q: string) => void
}) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [chatMessages, chatLoading])

  return (
    <div className="ask-container">
      <div className="ask-messages" ref={scrollRef}>
        {chatMessages.length === 0 && (
          <div className="ask-empty">
            <div className="section-title">Suggested Questions</div>
            <div className="chat-suggestions">
              {[
                "Is this river healthy?",
                "What fish are spawning here?",
                "Did wildfire affect this watershed?",
                "What insects are hatching this month?",
                "Is it safe to swim here?",
                "What restoration projects happened recently?",
                "What species should I look for?",
                "How has biodiversity changed since the fire?",
              ].map((q, i) => (
                <button key={i} className="suggestion-chip" onClick={() => onSuggestionClick(q)}>{q}</button>
              ))}
            </div>
          </div>
        )}
        {chatMessages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            <div className="bubble">
              {msg.role === 'assistant' ? (
                <Markdown components={{
                  h1: ({children}) => <h3 className="md-h">{children}</h3>,
                  h2: ({children}) => <h4 className="md-h">{children}</h4>,
                  h3: ({children}) => <h5 className="md-h">{children}</h5>,
                  p: ({children}) => <p className="md-p">{children}</p>,
                  ul: ({children}) => <ul className="md-ul">{children}</ul>,
                  ol: ({children}) => <ol className="md-ol">{children}</ol>,
                  li: ({children}) => <li className="md-li">{children}</li>,
                  strong: ({children}) => <strong className="md-strong">{children}</strong>,
                  table: ({children}) => <table className="md-table">{children}</table>,
                  th: ({children}) => <th className="md-th">{children}</th>,
                  td: ({children}) => <td className="md-td">{children}</td>,
                  code: ({children}) => <code className="md-code">{children}</code>,
                }}>{msg.content}</Markdown>
              ) : msg.content}
            </div>
          </div>
        ))}
        {chatLoading && (
          <div className="chat-bubble assistant">
            <div className="bubble">
              <div className="chat-thinking">
                <span className="thinking-dot" />
                Analyzing {site.name} data...
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


/* ── What's Here Now ── */
function WhatsHereNow({ watershed }: { watershed: string }) {
  const [species, setSpecies] = useState<any[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/sites/${watershed}/species?limit=12`)
      .then(r => r.json())
      .then(data => setSpecies(data.filter((s: any) => s.photo_url).slice(0, 8)))
      .catch(console.error)
  }, [watershed])

  if (species.length === 0) return null

  return (
    <div className="section">
      <div className="section-title">What's Here Now</div>
      <div className="whats-here-grid">
        {species.map((s: any, i: number) => (
          <div key={i} className="whats-here-item">
            <img src={s.photo_url} alt={s.common_name} className="whats-here-photo" loading="lazy" />
            <div className="whats-here-name">{s.common_name || s.taxon_name}</div>
          </div>
        ))}
      </div>
    </div>
  )
}


/* ── Stewardship Opportunities ── */
function StewardshipSection({ watershed }: { watershed: string }) {
  const [opps, setOpps] = useState<any[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/sites/${watershed}/story`)
      .then(r => r.json())
      .then(data => {
        // Extract stewardship-relevant info from story data
        const items: any[] = []
        if (data.timeline) {
          data.timeline
            .filter((e: any) => e.type === 'restoration' || e.type === 'intervention')
            .slice(0, 5)
            .forEach((e: any) => items.push({ type: 'project', name: e.name, year: e.year, desc: e.description }))
        }
        setOpps(items)
      })
      .catch(console.error)
  }, [watershed])

  return (
    <div className="section">
      <div className="section-title">Stewardship & Restoration</div>
      {opps.length > 0 ? (
        <div className="stewardship-list">
          {opps.map((o, i) => (
            <div key={i} className="stewardship-item">
              <span className="stewardship-year">{o.year}</span>
              <span className="stewardship-name">{o.name}</span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: 12, color: '#888', padding: '8px 0' }}>
          Contact your local watershed council for volunteer opportunities.
        </div>
      )}
    </div>
  )
}
