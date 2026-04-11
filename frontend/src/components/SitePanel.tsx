import { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8001/api/v1'

interface SitePanelProps {
  site: any
  watershed: string
  onClose: () => void
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function SitePanel({ site, watershed, onClose }: SitePanelProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'species' | 'fishing' | 'story' | 'ask'>('overview')
  const [species, setSpecies] = useState<any[]>([])
  const [fishingBrief, setFishingBrief] = useState<any>(null)
  const [story, setStory] = useState<any>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    if (activeTab === 'species' && species.length === 0) {
      fetch(`${API_BASE}/sites/${watershed}/species?limit=30`)
        .then(r => r.json())
        .then(setSpecies)
        .catch(console.error)
    }
    if (activeTab === 'fishing' && !fishingBrief) {
      fetch(`${API_BASE}/sites/${watershed}/fishing/brief`)
        .then(r => r.json())
        .then(setFishingBrief)
        .catch(console.error)
    }
    if (activeTab === 'story' && !story) {
      fetch(`${API_BASE}/sites/${watershed}/story`)
        .then(r => r.json())
        .then(setStory)
        .catch(console.error)
    }
  }, [activeTab, watershed])

  const health = site.health || {}
  const scorecard = site.scorecard || {}
  const healthClass = (health.score || 0) >= 70 ? 'good' : (health.score || 0) >= 50 ? 'moderate' : 'poor'

  return (
    <div className="site-panel">
      <div className="site-panel-header">
        <div>
          <h2>{site.name}</h2>
          <div className="watershed-tag">{watershed} watershed</div>
        </div>
        <button className="site-panel-close" onClick={onClose}>×</button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e0e0e0' }}>
        {(['overview', 'species', 'fishing', 'story', 'ask'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            flex: 1, padding: '10px', border: 'none', background: activeTab === tab ? '#f0f4ff' : 'white',
            borderBottom: activeTab === tab ? '2px solid #0f3460' : '2px solid transparent',
            cursor: 'pointer', fontSize: '13px', fontWeight: activeTab === tab ? 600 : 400,
            textTransform: 'capitalize',
          }}>{tab}</button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Health Score */}
          <div className="site-section">
            <h3>River Health</h3>
            <div className="health-score">
              <div className={`health-number ${healthClass}`}>
                {health.score || '—'}
              </div>
              <div className="health-details">
                <div>Water temp: {health.water_temp_c != null ? `${health.water_temp_c}°C` : '—'}</div>
                <div>Dissolved O₂: {health.dissolved_oxygen_mg_l != null ? `${health.dissolved_oxygen_mg_l} mg/L` : '—'}</div>
                <div>Species this month: {health.species_this_month || '—'}</div>
              </div>
            </div>
          </div>

          {/* Scorecard */}
          <div className="site-section">
            <h3>Data Coverage</h3>
            <div className="scorecard-grid">
              {[
                { value: scorecard.total_species?.toLocaleString(), label: 'Species' },
                { value: scorecard.fish_species, label: 'Fish' },
                { value: scorecard.amphibian_species, label: 'Amphibians' },
                { value: scorecard.total_observations?.toLocaleString(), label: 'Observations' },
                { value: scorecard.total_interventions, label: 'Interventions' },
                { value: scorecard.usgs_stations, label: 'USGS Stations' },
                { value: scorecard.stream_reaches?.toLocaleString(), label: 'Stream Reaches' },
                { value: scorecard.fire_events, label: 'Fire Events' },
              ].map((item, i) => (
                <div key={i} className="scorecard-item">
                  <div className="scorecard-value">{item.value ?? '—'}</div>
                  <div className="scorecard-label">{item.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Indicators */}
          <div className="site-section">
            <h3>Indicator Species ({site.indicators?.length || 0})</h3>
            <ul className="indicator-list">
              {(site.indicators || []).map((ind: any, i: number) => (
                <li key={i} className="indicator-item">
                  <span className={`indicator-dot ${ind.status === 'detected' ? 'detected' : 'absent'}`} />
                  <span className="indicator-name">{ind.common_name}</span>
                  <span className="indicator-direction">
                    {ind.direction === 'positive' ? '↑ good' : '↓ invasive'}
                  </span>
                  {ind.detections > 0 && <span style={{ fontSize: 11, color: '#999' }}>{ind.detections}</span>}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {activeTab === 'species' && (
        <div className="site-section">
          <h3>Species Gallery</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {species.map((s: any, i: number) => (
              <div key={i} style={{ border: '1px solid #eee', borderRadius: 6, overflow: 'hidden' }}>
                {s.photo_url && (
                  <img src={s.photo_url} alt={s.common_name || s.taxon_name}
                    style={{ width: '100%', height: 100, objectFit: 'cover' }} loading="lazy" />
                )}
                <div style={{ padding: '6px 8px' }}>
                  <div style={{ fontSize: 12, fontWeight: 600 }}>{s.common_name || s.taxon_name}</div>
                  <div style={{ fontSize: 10, color: '#888', fontStyle: 'italic' }}>{s.taxon_name}</div>
                  {s.conservation_status && (
                    <span style={{ fontSize: 10, background: '#fee', color: '#c00', padding: '1px 4px', borderRadius: 3 }}>
                      {s.conservation_status}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'fishing' && (
        <div className="site-section">
          <h3>Fishing Brief</h3>
          {fishingBrief?.conditions && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13 }}>Water temp: {fishingBrief.conditions.water_temp_c ?? '—'}°C</div>
              <div style={{ fontSize: 13 }}>Flow: {fishingBrief.conditions.discharge_cfs ?? '—'} cfs</div>
              <div style={{ fontSize: 13 }}>Steelhead harvest: {fishingBrief.conditions.steelhead_harvest ?? '—'}</div>
              <div style={{ fontSize: 13 }}>Trout stocked: {fishingBrief.conditions.trout_stocked ?? '—'}</div>
            </div>
          )}
          <h3>Recent Stocking</h3>
          {(fishingBrief?.stocking || []).map((s: any, i: number) => (
            <div key={i} style={{ fontSize: 13, padding: '4px 0', borderBottom: '1px solid #f5f5f5' }}>
              {s.waterbody}: {s.fish?.toLocaleString()} fish ({s.date})
            </div>
          ))}
          <h3 style={{ marginTop: 12 }}>Species by Reach</h3>
          {(fishingBrief?.species_by_reach || []).slice(0, 10).map((s: any, i: number) => (
            <div key={i} style={{ fontSize: 13, padding: '4px 0', borderBottom: '1px solid #f5f5f5' }}>
              <strong>{s.common_name || s.species}</strong> — {s.stream} ({s.use_type})
            </div>
          ))}
        </div>
      )}

      {activeTab === 'story' && (
        <div className="site-section">
          <h3>River Story</h3>
          {story?.health && (
            <div style={{ marginBottom: 12, padding: 10, background: '#f0f8ff', borderRadius: 6, fontSize: 13 }}>
              Health Score: <strong>{story.health.score}</strong> |
              Temp: {story.health.water_temp_c}°C |
              DO: {story.health.do_mg_l} mg/L
            </div>
          )}
          <h3>Timeline</h3>
          {(story?.timeline || []).slice(0, 15).map((e: any, i: number) => (
            <div key={i} style={{ display: 'flex', gap: 8, padding: '6px 0', borderBottom: '1px solid #f5f5f5', fontSize: 13 }}>
              <span style={{ fontWeight: 600, minWidth: 40 }}>{e.year}</span>
              <span style={{
                fontSize: 10, padding: '2px 6px', borderRadius: 3, minWidth: 70, textAlign: 'center',
                background: e.type === 'fire' ? '#fee' : e.type === 'restoration' ? '#efe' : '#eef',
                color: e.type === 'fire' ? '#c00' : e.type === 'restoration' ? '#060' : '#006',
              }}>{e.type}</span>
              <span>{e.name}</span>
            </div>
          ))}
          {(story?.fire_recovery || []).length > 0 && (
            <>
              <h3 style={{ marginTop: 12 }}>Fire Recovery</h3>
              {story.fire_recovery.filter((r: any) => r.years_since >= -1 && r.years_since <= 5).map((r: any, i: number) => (
                <div key={i} style={{ fontSize: 13, padding: '4px 0' }}>
                  {r.obs_year} (year {r.years_since > 0 ? '+' : ''}{r.years_since}): {r.species?.toLocaleString()} species
                  {r.years_since === 0 && ' 🔥'}
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {activeTab === 'ask' && (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}>
          {/* Chat messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
            {chatMessages.length === 0 && (
              <div style={{ color: '#999', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>💬</div>
                <div>Ask anything about the {site.name}</div>
                <div style={{ marginTop: 12, textAlign: 'left' }}>
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>Try:</div>
                  {[
                    "Is this river healthy?",
                    "What fish are spawning here?",
                    "Did wildfire affect this watershed?",
                    "What insects are hatching this month?",
                    "What restoration projects happened recently?",
                    "Is it safe to swim here?",
                  ].map((q, i) => (
                    <div key={i} style={{
                      padding: '6px 10px', margin: '4px 0', background: '#f0f4ff',
                      borderRadius: 6, cursor: 'pointer', fontSize: 12,
                    }} onClick={() => { setChatInput(q) }}>
                      {q}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} style={{
                marginBottom: 12,
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}>
                <div style={{
                  maxWidth: '85%',
                  padding: '10px 14px',
                  borderRadius: 12,
                  fontSize: 13,
                  lineHeight: 1.5,
                  background: msg.role === 'user' ? '#0f3460' : '#f0f4ff',
                  color: msg.role === 'user' ? 'white' : '#1a1a2e',
                  whiteSpace: 'pre-wrap',
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div style={{ color: '#999', fontSize: 13, padding: '8px 0' }}>
                Thinking about the {site.name}...
              </div>
            )}
          </div>

          {/* Chat input */}
          <div style={{
            padding: '12px 16px',
            borderTop: '1px solid #e0e0e0',
            display: 'flex',
            gap: 8,
          }}>
            <input
              type="text"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && chatInput.trim() && !chatLoading) {
                  const question = chatInput.trim()
                  setChatInput('')
                  setChatMessages(prev => [...prev, { role: 'user', content: question }])
                  setChatLoading(true)

                  fetch(`${API_BASE}/sites/${watershed}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question }),
                  })
                    .then(r => r.json())
                    .then(data => {
                      setChatMessages(prev => [...prev, {
                        role: 'assistant',
                        content: data.answer || data.detail || 'Unable to answer right now.',
                      }])
                    })
                    .catch(() => {
                      setChatMessages(prev => [...prev, {
                        role: 'assistant',
                        content: 'Sorry, I need an ANTHROPIC_API_KEY configured to answer questions. The data is available through the other tabs.',
                      }])
                    })
                    .finally(() => setChatLoading(false))
                }
              }}
              placeholder={`Ask about the ${site.name}...`}
              style={{
                flex: 1,
                padding: '10px 14px',
                border: '1px solid #ddd',
                borderRadius: 8,
                fontSize: 13,
                outline: 'none',
              }}
            />
            <button
              onClick={() => {
                if (chatInput.trim() && !chatLoading) {
                  const question = chatInput.trim()
                  setChatInput('')
                  setChatMessages(prev => [...prev, { role: 'user', content: question }])
                  setChatLoading(true)

                  fetch(`${API_BASE}/sites/${watershed}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question }),
                  })
                    .then(r => r.json())
                    .then(data => {
                      setChatMessages(prev => [...prev, {
                        role: 'assistant',
                        content: data.answer || data.detail || 'Unable to answer right now.',
                      }])
                    })
                    .catch(() => {
                      setChatMessages(prev => [...prev, {
                        role: 'assistant',
                        content: 'Sorry, I need an ANTHROPIC_API_KEY configured to answer questions.',
                      }])
                    })
                    .finally(() => setChatLoading(false))
                }
              }}
              disabled={!chatInput.trim() || chatLoading}
              style={{
                padding: '10px 16px',
                background: '#0f3460',
                color: 'white',
                border: 'none',
                borderRadius: 8,
                cursor: chatInput.trim() && !chatLoading ? 'pointer' : 'not-allowed',
                opacity: chatInput.trim() && !chatLoading ? 1 : 0.5,
                fontSize: 13,
              }}
            >Ask</button>
          </div>
        </div>
      )}
    </div>
  )
}
