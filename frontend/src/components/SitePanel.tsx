import { useState, useEffect, useRef } from 'react'
import Markdown from 'react-markdown'

const API_BASE = 'http://localhost:8001/api/v1'

interface SitePanelProps {
  site: any
  watershed: string
  onClose: () => void
  initialQuestion?: string | null
  onQuestionConsumed?: () => void
  onShowSpeciesOnMap?: (taxonName: string) => void
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function SitePanel({ site, watershed, onClose, initialQuestion, onQuestionConsumed, onShowSpeciesOnMap }: SitePanelProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'species' | 'rocks' | 'fishing' | 'story' | 'recs' | 'predict' | 'ask'>(
    initialQuestion ? 'ask' : 'overview'
  )
  // Note: 'fishing' and 'recs' tabs are hidden but state type kept for backward compatibility
  const [species, setSpecies] = useState<any[]>([])
  const [speciesPage, setSpeciesPage] = useState(0)
  const [speciesClassFilter, setSpeciesClassFilter] = useState('')
  const [selectedSpecies, setSelectedSpecies] = useState<Set<string>>(new Set())
  const SPECIES_PER_PAGE = 12
  const [rocks, setRocks] = useState<any[]>([])
  const [rocksPage, setRocksPage] = useState(0)
  const [rocksTypeFilter, setRocksTypeFilter] = useState('')
  const [selectedRocks, setSelectedRocks] = useState<Set<string>>(new Set())
  const ROCKS_PER_PAGE = 12
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
    if (activeTab === 'species' && species.length === 0) {
      setSpeciesPage(0)
      fetch(`${API_BASE}/sites/${watershed}/species?limit=200`).then(r => r.json()).then(setSpecies).catch(console.error)
    }
    if (activeTab === 'rocks' && rocks.length === 0) {
      setRocksPage(0)
      // Fetch fossils and minerals, merge into one list
      const bbox = site.bbox || {}
      const lat = ((bbox.south || 0) + (bbox.north || 0)) / 2
      const lon = ((bbox.west || 0) + (bbox.east || 0)) / 2
      Promise.all([
        fetch(`${API_BASE}/fossils/near/${lat}/${lon}?radius_km=75`).then(r => r.json()).catch(() => ({ fossils: [] })),
        fetch(`${API_BASE}/minerals/near/${lat}/${lon}?radius_km=75`).then(r => r.json()).catch(() => ({ minerals: [] })),
      ]).then(([fossilData, mineralData]) => {
        const fossils = (fossilData.fossils || []).map((f: any, idx: number) => ({ ...f, rock_type: 'fossil', display_name: f.taxon_name, _uid: `f-${f.source_id || idx}`, category: f.phylum || 'Fossil' }))
        const minerals = (mineralData.minerals || []).map((m: any, idx: number) => ({ ...m, rock_type: 'mineral', display_name: m.site_name || m.commodity, _uid: `m-${m.source_id || idx}`, category: m.commodity?.split(',')[0]?.trim() || 'Mineral' }))
        setRocks([...fossils, ...minerals])
      })
    }
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
        {(['overview', 'story', 'species', 'rocks', 'predict', 'ask'] as const).map(tab => (
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

            {/* Seasonal Trip Planner */}
            <SeasonalPlanner watershed={watershed} />
          </>
        )}

        {activeTab === 'species' && (() => {
          const CLASS_LABELS: Record<string, string> = {
            Plantae: 'Plants', Insecta: 'Insects', Fungi: 'Fungi', Aves: 'Birds',
            Arachnida: 'Arachnids', Mammalia: 'Mammals', Animalia: 'Animals',
            Reptilia: 'Reptiles', Actinopterygii: 'Fish', Mollusca: 'Mollusks',
            Amphibia: 'Amphibians', Chromista: 'Algae', Protozoa: 'Protozoa',
          }
          // Get available classes with counts
          const classCounts: Record<string, number> = {}
          for (const s of species) {
            const cls = s.taxonomic_group || 'Other'
            classCounts[cls] = (classCounts[cls] || 0) + 1
          }
          const classes = Object.entries(classCounts).sort((a, b) => b[1] - a[1])

          // Filter and sort alphabetically
          const filtered = species
            .filter(s => !speciesClassFilter || s.taxonomic_group === speciesClassFilter)
            .sort((a, b) => (a.common_name || a.taxon_name).localeCompare(b.common_name || b.taxon_name))

          const totalPages = Math.max(1, Math.ceil(filtered.length / SPECIES_PER_PAGE))
          const pageSpecies = filtered.slice(speciesPage * SPECIES_PER_PAGE, (speciesPage + 1) * SPECIES_PER_PAGE)

          const toggleSelect = (taxon: string, e: React.MouseEvent) => {
            e.stopPropagation()
            setSelectedSpecies(prev => {
              const next = new Set(prev)
              if (next.has(taxon)) next.delete(taxon); else next.add(taxon)
              return next
            })
          }

          const showSelectedOnMap = () => {
            if (selectedSpecies.size === 0 || !onShowSpeciesOnMap) return
            // Search for all selected species
            const query = Array.from(selectedSpecies).join(' OR ')
            onShowSpeciesOnMap(query)
          }

          return (
          <div className="section">
            <div className="section-title">Species Gallery · {filtered.length} species</div>

            {/* Class filter chips */}
            <div className="species-class-filters">
              <button className={`sp-class-chip${!speciesClassFilter ? ' active' : ''}`}
                onClick={() => { setSpeciesClassFilter(''); setSpeciesPage(0) }}>
                All ({species.length})
              </button>
              {classes.map(([cls, count]) => (
                <button key={cls} className={`sp-class-chip${speciesClassFilter === cls ? ' active' : ''}`}
                  onClick={() => { setSpeciesClassFilter(speciesClassFilter === cls ? '' : cls); setSpeciesPage(0) }}>
                  {CLASS_LABELS[cls] || cls} ({count})
                </button>
              ))}
            </div>

            {/* Multi-select actions */}
            {selectedSpecies.size > 0 && onShowSpeciesOnMap && (
              <div className="species-select-bar">
                <span>{selectedSpecies.size} selected</span>
                <button className="sp-show-map-btn" onClick={showSelectedOnMap}>📍 Show on map</button>
                <button className="sp-clear-btn" onClick={() => setSelectedSpecies(new Set())}>Clear</button>
              </div>
            )}

            {/* Species grid */}
            <div className="species-grid">
              {pageSpecies.map((s: any, i: number) => {
                const isSelected = selectedSpecies.has(s.taxon_name)
                return (
                <div key={i} className={`species-card${onShowSpeciesOnMap ? ' clickable' : ''}${isSelected ? ' selected' : ''}`}
                  onClick={() => {
                    if (onShowSpeciesOnMap) {
                      const next = new Set(selectedSpecies)
                      if (next.has(s.taxon_name)) next.delete(s.taxon_name); else next.add(s.taxon_name)
                      setSelectedSpecies(next)
                      // Immediately show on map
                      if (next.size > 0) {
                        onShowSpeciesOnMap(Array.from(next).join(' OR '))
                      }
                    }
                  }}
                  title={`Tap to select ${s.common_name || s.taxon_name}`}>
                  {isSelected && <div className="sp-selected-badge">✓</div>}
                  {s.photo_url && <img src={s.photo_url} alt={s.common_name || s.taxon_name} loading="lazy" />}
                  <div className="sp-info">
                    <div className="sp-common">{s.common_name || s.taxon_name}</div>
                    <div className="sp-sci">{s.taxon_name}</div>
                    <div className="sp-class-label">{CLASS_LABELS[s.taxonomic_group] || s.taxonomic_group}</div>
                    {s.conservation_status && <span className="conservation-tag">{s.conservation_status}</span>}
                  </div>
                </div>
              )})}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="species-pagination">
                <button disabled={speciesPage === 0} onClick={() => setSpeciesPage(p => p - 1)}>← Prev</button>
                <span>{speciesPage + 1} / {totalPages}</span>
                <button disabled={speciesPage >= totalPages - 1} onClick={() => setSpeciesPage(p => p + 1)}>Next →</button>
              </div>
            )}
          </div>
          )
        })()}

        {activeTab === 'rocks' && (() => {
          const ROCK_LABELS: Record<string, string> = {
            Tracheophyta: 'Fossil Plants', Mollusca: 'Fossil Mollusks', Chordata: 'Fossil Vertebrates',
            Arthropoda: 'Fossil Arthropods', Ochrophyta: 'Fossil Algae', Bryozoa: 'Fossil Bryozoans',
            Fossil: 'Other Fossils',
            Gold: 'Gold', Silver: 'Silver', Copper: 'Copper', Mercury: 'Mercury',
            'Sand and Gravel': 'Sand & Gravel', Stone: 'Decorative Stone',
            Mineral: 'Other Minerals',
          }
          const typeCounts: Record<string, number> = {}
          for (const r of rocks) {
            const cat = r.category || (r.rock_type === 'fossil' ? 'Fossil' : 'Mineral')
            typeCounts[cat] = (typeCounts[cat] || 0) + 1
          }
          const types = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])

          const filtered = rocks
            .filter(r => {
              if (!rocksTypeFilter) return true
              if (rocksTypeFilter === '_fossils') return r.rock_type === 'fossil'
              if (rocksTypeFilter === '_minerals') return r.rock_type === 'mineral'
              const cat = r.category || (r.rock_type === 'fossil' ? 'Fossil' : 'Mineral')
              return cat === rocksTypeFilter
            })
            .sort((a, b) => (a.display_name || '').localeCompare(b.display_name || ''))

          const totalPages = Math.max(1, Math.ceil(filtered.length / ROCKS_PER_PAGE))
          const pageRocks = filtered.slice(rocksPage * ROCKS_PER_PAGE, (rocksPage + 1) * ROCKS_PER_PAGE)

          const toggleRockSelect = (name: string, e: React.MouseEvent) => {
            e.stopPropagation()
            setSelectedRocks(prev => { const n = new Set(prev); if (n.has(name)) n.delete(name); else n.add(name); return n })
          }

          return (
          <div className="section">
            <div className="section-title">Rocks Gallery · {filtered.length} items</div>

            {/* Type filter chips */}
            <div className="species-class-filters">
              <button className={`sp-class-chip${!rocksTypeFilter ? ' active' : ''}`}
                onClick={() => { setRocksTypeFilter(''); setRocksPage(0) }}>
                All ({rocks.length})
              </button>
              <button className={`sp-class-chip${rocksTypeFilter === '_fossils' ? ' active' : ''}`}
                onClick={() => { setRocksTypeFilter(rocksTypeFilter === '_fossils' ? '' : '_fossils'); setRocksPage(0) }}>
                🦴 Fossils ({rocks.filter(r => r.rock_type === 'fossil').length})
              </button>
              <button className={`sp-class-chip${rocksTypeFilter === '_minerals' ? ' active' : ''}`}
                onClick={() => { setRocksTypeFilter(rocksTypeFilter === '_minerals' ? '' : '_minerals'); setRocksPage(0) }}>
                💎 Minerals ({rocks.filter(r => r.rock_type === 'mineral').length})
              </button>
              {types.slice(0, 8).map(([cat, count]) => (
                <button key={cat} className={`sp-class-chip${rocksTypeFilter === cat ? ' active' : ''}`}
                  onClick={() => { setRocksTypeFilter(rocksTypeFilter === cat ? '' : cat); setRocksPage(0) }}>
                  {ROCK_LABELS[cat] || cat} ({count})
                </button>
              ))}
            </div>

            {/* Multi-select bar */}
            {selectedRocks.size > 0 && onShowSpeciesOnMap && (
              <div className="species-select-bar">
                <span>{selectedRocks.size} selected</span>
                <button className="sp-show-map-btn" onClick={() => {
                  const names = rocks.filter(r => selectedRocks.has(r._uid)).map(r => r.display_name)
                  const unique = [...new Set(names)]
                  onShowSpeciesOnMap(unique.join(' OR '))
                }}>📍 Show on map</button>
                <button className="sp-clear-btn" onClick={() => setSelectedRocks(new Set())}>Clear</button>
              </div>
            )}

            {/* Grid */}
            <div className="species-grid">
              {pageRocks.map((r: any, i: number) => {
                const isSelected = selectedRocks.has(r._uid)
                const icon = r.rock_type === 'fossil' ? '🦴' : '💎'
                return (
                <div key={i} className={`species-card${onShowSpeciesOnMap ? ' clickable' : ''}${isSelected ? ' selected' : ''}`}
                  onClick={() => {
                    if (onShowSpeciesOnMap) {
                      const next = new Set(selectedRocks)
                      if (next.has(r._uid)) next.delete(r._uid); else next.add(r._uid)
                      setSelectedRocks(next)
                      // Immediately show on map
                      if (next.size > 0) {
                        const names = rocks.filter(rk => next.has(rk._uid)).map(rk => rk.display_name)
                        onShowSpeciesOnMap([...new Set(names)].join(' OR '))
                      }
                    }
                  }}
                  title={`Tap to select ${r.display_name}`}>
                  {isSelected && <div className="sp-selected-badge">✓</div>}
                  {r.image_url ? (
                    <img src={r.image_url} alt={r.display_name} loading="lazy" />
                  ) : (
                    <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, background: 'var(--bg)' }}>{icon}</div>
                  )}
                  <div className="sp-info">
                    <div className="sp-common">{r.display_name}</div>
                    {r.rock_type === 'fossil' && <div className="sp-sci">{r.period}{r.age_max_ma ? ` · ${r.age_max_ma} Ma` : ''}</div>}
                    {r.rock_type === 'mineral' && <div className="sp-sci">{r.commodity}</div>}
                    <div className="sp-class-label">{icon} {ROCK_LABELS[r.category] || r.category}</div>
                    {r.museum && <div style={{ fontSize: 8, color: 'var(--text-muted)' }}>{r.museum}</div>}
                  </div>
                </div>
              )})}
            </div>

            {totalPages > 1 && (
              <div className="species-pagination">
                <button disabled={rocksPage === 0} onClick={() => setRocksPage(p => p - 1)}>← Prev</button>
                <span>{rocksPage + 1} / {totalPages}</span>
                <button disabled={rocksPage >= totalPages - 1} onClick={() => setRocksPage(p => p + 1)}>Next →</button>
              </div>
            )}
          </div>
          )
        })()}

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
            <FlyRecommendations watershed={watershed} />
            <BarriersTable watershed={watershed} />
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

        {activeTab === 'predict' && (
          <PredictionsPanel watershed={watershed} />
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


/* ── Seasonal Trip Planner ── */
function SeasonalPlanner({ watershed }: { watershed: string }) {
  const [data, setData] = useState<any>(null)
  const MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  useEffect(() => {
    fetch(`${API_BASE}/sites/${watershed}/seasonal`)
      .then(r => r.json()).then(setData).catch(console.error)
  }, [watershed])

  if (!data?.seasonal_patterns?.length) return null

  return (
    <div className="section">
      <div className="section-title">Best Time to Visit</div>
      <div className="seasonal-grid">
        {data.seasonal_patterns.slice(0, 6).map((p: any, i: number) => (
          <div key={i} className="seasonal-card">
            <div className="seasonal-group">{p.taxon_group}</div>
            <div className="seasonal-peak">Peak: {MONTHS[p.peak_month] || '?'}</div>
            <div className="seasonal-obs">{p.avg_observations} avg obs</div>
          </div>
        ))}
      </div>
      {data.hatch_chart?.length > 0 && (
        <>
          <div className="section-title" style={{ marginTop: 12 }}>Insect Hatch Chart</div>
          <div className="hatch-mini">
            {data.hatch_chart.slice(0, 10).map((h: any, i: number) => (
              <div key={i} className="hatch-row">
                <span className="hatch-name">{h.common_name || h.taxon_name}</span>
                <span className="hatch-month">{h.month_name}</span>
                <span className="hatch-count">{h.count}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}


/* ── Fish Passage Barriers Table ── */
function BarriersTable({ watershed }: { watershed: string }) {
  const [barriers, setBarriers] = useState<any[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/sites/${watershed}/fishing/barriers`)
      .then(r => r.json()).then(d => setBarriers(d || [])).catch(console.error)
  }, [watershed])

  if (barriers.length === 0) return null

  return (
    <div className="section">
      <div className="section-title">Fish Passage Barriers ({barriers.length})</div>
      <table className="data-table">
        <thead><tr><th>Stream</th><th>Type</th><th>Status</th></tr></thead>
        <tbody>
          {barriers.slice(0, 15).map((b: any, i: number) => (
            <tr key={i}>
              <td>{b.stream_name || b.barrier_name || '—'}</td>
              <td>{b.barrier_type || '—'}</td>
              <td><span className={`status-tag ${b.passage_status === 'Passable' ? 'detected' : b.passage_status === 'Blocked' ? 'invasive' : 'absent'}`}>
                {b.passage_status || '—'}
              </span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


/* ── Fly Recommendations ── */
function FlyRecommendations({ watershed }: { watershed: string }) {
  const [flies, setFlies] = useState<any[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/sites/${watershed}/fishing/fly-recommendations`)
      .then(r => r.json()).then(d => setFlies(d || [])).catch(console.error)
  }, [watershed])

  if (flies.length === 0) return null

  // Deduplicate by fly pattern name
  const seen = new Set<string>()
  const unique = flies.filter(f => {
    if (seen.has(f.fly_pattern)) return false
    seen.add(f.fly_pattern)
    return true
  })

  return (
    <div className="section">
      <div className="section-title">What to Fish With This Month</div>
      <div className="fly-recs">
        {unique.slice(0, 8).map((f: any, i: number) => (
          <div key={i} className="fly-card">
            {f.fly_image_url && (
              <img src={f.fly_image_url} alt={f.fly_pattern} className="fly-img" loading="lazy" />
            )}
            <div className="fly-info">
              <div className="fly-name">{f.fly_pattern}</div>
              <div className="fly-meta">{f.fly_size} · {f.fly_type} · {f.life_stage}</div>
              <div className="fly-insect">Matches: {f.insect}</div>
              <div className="fly-tip">{f.time_of_day} · {f.water_type}</div>
              {f.notes && <div className="fly-notes">{f.notes}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}


/* ── Predictions Panel ── */
function PredictionsPanel({ watershed }: { watershed: string }) {
  const [screen, setScreen] = useState<'hub' | 'builder' | 'results'>('hub')
  const [predType, setPredType] = useState('')
  const [history, setHistory] = useState<any[]>([])
  const [result, setResult] = useState<any>(null)
  const [generating, setGenerating] = useState(false)
  const [intervention, setIntervention] = useState('native_planting')
  const [scale, setScale] = useState('500 trees / 2 acres')
  const [horizon, setHorizon] = useState(12)
  const [accSummary, setAccSummary] = useState<any>(null)

  useEffect(() => {
    fetch(`${API_BASE}/sites/${watershed}/predictions`)
      .then(r => r.json())
      .then(d => { setHistory(d.predictions || []); setAccSummary(d.accuracy_summary) })
      .catch(console.error)
  }, [watershed])

  const generate = () => {
    setGenerating(true)
    fetch(`${API_BASE}/sites/${watershed}/predictions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prediction_type: predType,
        intervention_type: intervention,
        intervention_scale: scale,
        horizon_months: horizon,
        scenario: 'with_intervention',
      }),
    })
      .then(r => r.json())
      .then(d => {
        // If narrative contains JSON, try to parse it and extract structured data
        if (d.narrative && d.narrative.startsWith('{')) {
          try {
            const parsed = JSON.parse(d.narrative)
            if (parsed.predictions) d.predictions = parsed.predictions
            if (parsed.risk_factors) d.risk_factors = parsed.risk_factors
            if (parsed.scenario_comparison) d.scenario_comparison = parsed.scenario_comparison
            if (parsed.narrative) d.narrative = parsed.narrative
            if (parsed.overall_confidence) { d.confidence = parsed.overall_confidence; d.confidence_level = parsed.overall_confidence >= 75 ? 'HIGH' : parsed.overall_confidence >= 50 ? 'MEDIUM' : 'LOW' }
          } catch { /* not JSON, keep as narrative text */ }
        }
        // Strip markdown code fences from narrative
        if (d.narrative && d.narrative.startsWith('```')) {
          d.narrative = d.narrative.replace(/^```json?\n?/, '').replace(/```$/, '').trim()
          try { const p = JSON.parse(d.narrative); if (p.narrative) { Object.assign(d, p); d.narrative = p.narrative } } catch {}
        }
        setResult(d); setScreen('results'); setGenerating(false)
      })
      .catch(() => setGenerating(false))
  }

  const TYPES = [
    { id: 'species_return', icon: '🌿', name: 'Species Return', desc: 'What will come back?' },
    { id: 'fire_recovery', icon: '🔥', name: 'Fire Recovery', desc: 'When will it recover?' },
    { id: 'thermal_forecast', icon: '🌡️', name: 'Thermal Forecast', desc: 'Will it get too warm?' },
    { id: 'invasive_spread', icon: '🌱', name: 'Invasive Spread', desc: 'Where is it heading?' },
  ]

  // ── Hub ──
  if (screen === 'hub') return (
    <div className="section">
      <div className="section-title">Predictions</div>
      <div className="pred-types">
        {TYPES.map(t => (
          <button key={t.id} className="pred-type-card" onClick={() => { setPredType(t.id); setScreen('builder') }}>
            <span className="pred-type-icon">{t.icon}</span>
            <div>
              <div className="pred-type-name">{t.name}</div>
              <div className="pred-type-desc">{t.desc}</div>
            </div>
          </button>
        ))}
      </div>
      {accSummary && accSummary.resolved > 0 && (
        <div className="pred-accuracy-bar">
          Accuracy: {accSummary.avg_accuracy?.toFixed(0) || '—'}% ({accSummary.confirmed}/{accSummary.resolved} confirmed)
        </div>
      )}
      {history.length > 0 && (
        <>
          <div className="section-title" style={{ marginTop: 12 }}>Recent</div>
          {history.slice(0, 5).map((p: any, i: number) => (
            <div key={i} className="pred-history-item" onClick={() => {
              fetch(`${API_BASE}/predictions/${p.id}`).then(r => r.json())
                .then(d => {
                  if (d.narrative && d.narrative.startsWith('{')) {
                    try { const p = JSON.parse(d.narrative); if (p.predictions) Object.assign(d, p); if (p.narrative) d.narrative = p.narrative } catch {}
                  }
                  setResult(d); setScreen('results')
                })
            }}>
              <span className="pred-hist-type">{TYPES.find(t => t.id === p.type)?.icon || '📊'}</span>
              <span className="pred-hist-name">{p.type.replace('_', ' ')}</span>
              <span className={`pred-hist-badge ${p.confidence_level?.toLowerCase()}`}>{p.confidence_level}</span>
              <span className="pred-hist-status">{p.status}</span>
            </div>
          ))}
        </>
      )}
    </div>
  )

  // ── Builder ──
  if (screen === 'builder') return (
    <div className="section">
      <button className="pred-back" onClick={() => setScreen('hub')}>← Back</button>
      <div className="section-title">{TYPES.find(t => t.id === predType)?.name}</div>

      {predType === 'species_return' && (
        <>
          <label className="pred-label">Intervention type</label>
          <select value={intervention} onChange={e => setIntervention(e.target.value)} className="pred-select">
            <option value="native_planting">Native planting</option>
            <option value="invasive_removal">Invasive removal</option>
            <option value="riparian_fencing">Riparian fencing</option>
            <option value="large_wood">Large wood placement</option>
            <option value="channel_reconnection">Channel reconnection</option>
          </select>
          <label className="pred-label">Scale</label>
          <select value={scale} onChange={e => setScale(e.target.value)} className="pred-select">
            <option value="500 trees / 2 acres">500 trees / 2 acres</option>
            <option value="1000 trees / 5 acres">1,000 trees / 5 acres</option>
            <option value="2000 trees / 10 acres">2,000 trees / 10 acres</option>
            <option value="100m riparian fencing">100m riparian fencing</option>
            <option value="500m riparian fencing">500m riparian fencing</option>
          </select>
        </>
      )}

      <label className="pred-label">Timeframe</label>
      <div className="pred-horizon-btns">
        {[6, 12, 24].map(m => (
          <button key={m} className={`pred-horizon-btn${horizon === m ? ' active' : ''}`}
            onClick={() => setHorizon(m)}>{m} months</button>
        ))}
      </div>

      <button className="pred-generate-btn" onClick={generate} disabled={generating}>
        {generating ? 'Generating...' : 'Generate Prediction →'}
      </button>
    </div>
  )

  // ── Results ──
  if (screen === 'results' && result) return (
    <div className="section">
      <button className="pred-back" onClick={() => setScreen('hub')}>← Predictions</button>
      <div className="section-title">{result.type?.replace('_', ' ') || 'Prediction'}</div>

      {/* Confidence bar */}
      <div className="pred-conf-bar">
        <div className="pred-conf-fill" style={{ width: `${result.confidence || 0}%` }}></div>
        <span className="pred-conf-text">{result.confidence?.toFixed(0)}% {result.confidence_level}</span>
      </div>

      {/* Predictions */}
      {result.predictions?.length > 0 && (
        <>
          <div className="pred-sub-title">Expected Outcomes</div>
          {result.predictions.map((p: any, i: number) => (
            <div key={i} className="pred-item">
              <div className="pred-item-name">{p.species}</div>
              <div className="pred-item-bar">
                <div className="pred-item-fill" style={{ width: `${p.confidence || 50}%` }}></div>
                <span>{p.confidence?.toFixed(0)}%</span>
              </div>
              <div className="pred-item-text">{p.prediction}</div>
              {p.evidence && <div className="pred-item-evidence">{p.evidence}</div>}
            </div>
          ))}
        </>
      )}

      {/* Risk factors */}
      {result.risk_factors?.length > 0 && (
        <>
          <div className="pred-sub-title">Risk Factors</div>
          {result.risk_factors.map((r: any, i: number) => (
            <div key={i} className="pred-risk">
              <span className={`pred-risk-badge ${r.severity}`}>⚠ {r.severity}</span>
              <div>{r.risk}</div>
              {r.mitigation && <div className="pred-risk-mit">{r.mitigation}</div>}
            </div>
          ))}
        </>
      )}

      {/* Scenario comparison */}
      {result.scenario_comparison && (
        <>
          <div className="pred-sub-title">Scenario Comparison</div>
          <table className="data-table">
            <thead><tr><th></th><th>With Intervention</th><th>Baseline</th></tr></thead>
            <tbody>
              {Object.keys(result.scenario_comparison.with_intervention || {}).map((k: string) => (
                <tr key={k}>
                  <td>{k.replace('_', ' ')}</td>
                  <td className="mono">{result.scenario_comparison.with_intervention[k]}</td>
                  <td className="mono">{result.scenario_comparison.baseline?.[k] || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {/* Narrative */}
      {result.narrative && (
        <>
          <div className="pred-sub-title">Analysis</div>
          <div className="pred-narrative">{result.narrative}</div>
        </>
      )}

      <div className="pred-meta">
        Check date: {result.check_date} · Status: {result.status}
      </div>
    </div>
  )

  return null
}
