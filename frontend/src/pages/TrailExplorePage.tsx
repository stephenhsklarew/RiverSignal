import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useDeepTrail, WATERSHEDS, type Fossil, type Mineral } from '../components/DeepTrailContext'
import DeepTrailHeader from '../components/DeepTrailHeader'
import SaveButton from '../components/SaveButton'
import { CardSettingsPanel, loadCardSettingsGeneric, type CardConfig } from '../components/CardSettings'
import PhotoObservation from '../components/PhotoObservation'
import './DeepTrailPage.css'

const API_BASE = 'http://localhost:8001/api/v1'

const PHYLUM_ICONS: Record<string, string> = {
  'Mollusca': '🐚', 'Chordata': '🦴', 'Arthropoda': '🦐', 'Plantae': '🌿',
  'Tracheophyta': '🌿', 'Bryophyta': '🌱', 'Cnidaria': '🪸', 'Echinodermata': '⭐',
  'Brachiopoda': '🐚', 'Foraminifera': '🔬', 'Radiolaria': '🔬',
}

const PERIOD_ORDER = [
  'Cambrian','Ordovician','Silurian','Devonian','Carboniferous','Permian',
  'Triassic','Jurassic','Cretaceous','Paleocene','Eocene','Oligocene',
  'Miocene','Pliocene','Pleistocene','Holocene','Quaternary','Neogene','Paleogene',
]

const ERA_CONTEXT: Record<string, string> = {
  'Quaternary': 'Ice ages and early humans',
  'Holocene': 'Modern era — last 11,700 years',
  'Pleistocene': 'Ice ages, mammoths, saber-toothed cats',
  'Neogene': 'Grasslands spread, modern mammals appear',
  'Pliocene': 'Climate cooling, Panama land bridge forms',
  'Miocene': 'Grasslands, horses, and great apes evolve',
  'Paleogene': 'Mammals diversify after dinosaur extinction',
  'Oligocene': 'Cooling climate, open woodlands',
  'Eocene': 'Subtropical forests, early horses and whales',
  'Paleocene': 'Recovery from mass extinction, mammals rise',
  'Cretaceous': 'Dinosaurs rule, flowering plants appear',
  'Jurassic': 'Age of dinosaurs, first birds',
  'Triassic': 'First dinosaurs and mammals',
  'Permian': 'Before the Great Dying — largest extinction',
  'Carboniferous': 'Giant insects, coal swamp forests',
  'Devonian': 'Age of fishes, first land plants',
}

const EXPLORE_CARDS: CardConfig[] = [
  { id: 'fossils_nearby', label: 'Fossils Found Nearby', icon: '🦴', visible: true },
  { id: 'minerals_nearby', label: 'Mineral Sites Nearby', icon: '💎', visible: true },
  { id: 'formation_explorer', label: 'Formation Explorer', icon: '🗺️', visible: true },
]

export default function TrailExplorePage() {
  useEffect(() => { document.title = 'Deep Trail'; return () => { document.title = 'RiverSignal' } }, [])
  const { locationId } = useParams<{ locationId: string }>()
  const navigate = useNavigate()
  const {
    loc, selectLocation, loading,
    fossils, minerals, rockhoundingSites, geoContext, rarityScores,
    periodFilter, setPeriodFilter, phylumFilter, setPhylumFilter,
    mineralFilter, setMineralFilter,
  } = useDeepTrail()

  const [cardConfig, setCardConfig] = useState<CardConfig[]>(() =>
    loadCardSettingsGeneric('deeptrail-explore-cards', EXPLORE_CARDS)
  )
  const [showSettings, setShowSettings] = useState(false)
  const [activeTab, setActiveTab] = useState<'fossils' | 'minerals'>('fossils')

  // Resolve locationId if loc is null
  useEffect(() => {
    if (loc) return
    if (!locationId) { navigate('/trail'); return }

    const ws = WATERSHEDS.find(w => w.id === locationId)
    if (ws) { selectLocation(ws); return }

    const parts = locationId.split(',')
    if (parts.length === 2) {
      const lat = parseFloat(parts[0])
      const lon = parseFloat(parts[1])
      if (!isNaN(lat) && !isNaN(lon)) {
        selectLocation({
          id: locationId,
          name: `${lat.toFixed(4)}°N, ${Math.abs(lon).toFixed(4)}°W`,
          lat,
          lon,
        })
        return
      }
    }

    navigate('/trail')
  }, [loc, locationId, navigate, selectLocation])

  if (!loc) {
    return <div className="dt-app"><div className="dt-loading">Loading...</div></div>
  }

  const filteredFossils = fossils.filter(f =>
    (!periodFilter || f.period === periodFilter) && (!phylumFilter || f.phylum === phylumFilter)
  )
  const filteredMinerals = mineralFilter ? minerals.filter(m => m.commodity?.includes(mineralFilter)) : minerals
  const fossilPeriods = [...new Set(fossils.map(f => f.period).filter(Boolean))].sort()
  const fossilPhyla = [...new Set(fossils.map(f => f.phylum).filter(Boolean))].sort()
  const mineralCommodities = [...new Set(minerals.flatMap(m => (m.commodity || '').split(', ')).filter(Boolean))].sort()

  return (
    <div className="dt-app">
      <DeepTrailHeader tab="explore" />

      {showSettings && (
        <CardSettingsPanel
          cards={cardConfig}
          onChange={setCardConfig}
          onClose={() => setShowSettings(false)}
          storageKey="deeptrail-explore-cards"
          defaults={EXPLORE_CARDS}
          title="Customize Explore Cards"
          dark
        />
      )}

      {loading ? <div className="dt-loading">Loading geology data...</div> : (
        <main className="dt-content" style={{ paddingBottom: 72 }}>
          <style>{cardConfig.map((c, i) => {
            const rules = [`[data-dtcard="${c.id}"] { order: ${i}; }`]
            if (!c.visible) rules.push(`[data-dtcard="${c.id}"] { display: none !important; }`)
            return rules.join('\n')
          }).join('\n')}</style>

          <section className="dt-loc-hero">
            <div className="dt-hero-top-row">
              <h1>{loc.name}</h1>
              <button className="dt-settings-btn" onClick={() => setShowSettings(true)} title="Customize sections">⚙</button>
            </div>
            <p className="dt-loc-coords">{loc.lat.toFixed(4)}°N, {Math.abs(loc.lon).toFixed(4)}°W</p>
          </section>

          {/* Unified map with all pins */}
          <MiniMap
            fossils={filteredFossils}
            minerals={filteredMinerals}
            rockhoundingSites={rockhoundingSites}
            center={loc}
          />

          {/* Toggle tabs */}
          <style>{`
            .dt-explore-tabs { display: flex; gap: 0; margin: 0 16px 8px; }
            .dt-explore-tab { flex: 1; padding: 8px; text-align: center; font-size: 0.82rem; font-weight: 600; background: #2a2318; border: 1px solid #3d3328; color: #8a7e6e; cursor: pointer; font-family: inherit; }
            .dt-explore-tab:first-child { border-radius: 8px 0 0 8px; }
            .dt-explore-tab:last-child { border-radius: 0 8px 8px 0; }
            .dt-explore-tab.active { background: #3d3328; color: #d4a96a; border-color: #d4a96a; }
          `}</style>
          <div className="dt-explore-tabs">
            <button
              className={`dt-explore-tab${activeTab === 'fossils' ? ' active' : ''}`}
              onClick={() => setActiveTab('fossils')}
            >
              Fossils
            </button>
            <button
              className={`dt-explore-tab${activeTab === 'minerals' ? ' active' : ''}`}
              onClick={() => setActiveTab('minerals')}
            >
              Minerals
            </button>
          </div>

          <div className="dt-card-container" style={{ display: 'flex', flexDirection: 'column' }}>

            {activeTab === 'fossils' && (
              <div data-dtcard="fossils_nearby">
                <PeriodFilterModal periods={fossilPeriods} selected={periodFilter} onSelect={setPeriodFilter} />
                <div className="dt-filter-chips">
                  <button className={`dt-chip${!phylumFilter ? ' active' : ''}`} onClick={() => setPhylumFilter('')}>All Types</button>
                  {fossilPhyla.map(p => (
                    <button key={p} className={`dt-chip${phylumFilter === p ? ' active' : ''}`} onClick={() => setPhylumFilter(phylumFilter === p ? '' : p)}>{PHYLUM_ICONS[p] || '🪨'} {p}</button>
                  ))}
                </div>
                <FossilGroupedList fossils={filteredFossils.map(f => ({
                  ...f,
                  rarity: rarityScores[f.taxon_name]?.rarity || null,
                  rarity_count: rarityScores[f.taxon_name]?.occurrences || null,
                }))} watershed={loc.id} />
              </div>
            )}

            {activeTab === 'minerals' && (
              <div data-dtcard="minerals_nearby">
                <div className="dt-filter-chips">
                  <button className={`dt-chip${!mineralFilter ? ' active' : ''}`} onClick={() => setMineralFilter('')}>All</button>
                  {mineralCommodities.map(c => (
                    <button key={c} className={`dt-chip${mineralFilter === c ? ' active' : ''}`} onClick={() => setMineralFilter(mineralFilter === c ? '' : c)}>{c}</button>
                  ))}
                </div>
                <MineralGroupedList minerals={filteredMinerals} watershed={loc.id} />
              </div>
            )}

            {/* Formation Explorer */}
            <div data-dtcard="formation_explorer">
              {geoContext?.units?.length > 0 && (
                <section className="dt-formation-section">
                  <h3>🗺️ Formation Explorer</h3>
                  <div className="dt-formation-list">
                    {geoContext.units.slice(0, 3).map((u: any, i: number) => (
                      <button key={i} className="dt-formation-btn"
                        onClick={() => {
                          fetch(`${API_BASE}/deep-time/formation/${encodeURIComponent(u.formation || u.unit_name)}`)
                            .then(r => r.json())
                            .then(d => alert(`${d.formation}: ${d.fossil_count} fossils found\n\n${d.fossils.slice(0, 5).map((f: any) => `• ${f.common_name || f.taxon} (${f.period})`).join('\n')}`))
                        }}>
                        <span className="dt-formation-name">{u.formation || u.unit_name}</span>
                        <span className="dt-formation-period">{u.period}</span>
                      </button>
                    ))}
                  </div>
                </section>
              )}
            </div>

          </div>
        </main>
      )}

      <PhotoObservation app="deeptrail" watershed={loc?.id} />
    </div>
  )
}

// ── MiniMap with fossil, mineral, and rockhounding pins ──

function MiniMap({ fossils, minerals, rockhoundingSites, center }: {
  fossils: Fossil[]
  minerals: Mineral[]
  rockhoundingSites: any[]
  center: { lat: number; lon: number }
}) {
  const ref = useRef<HTMLDivElement>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)

  useEffect(() => {
    if (!ref.current) return
    const map = new maplibregl.Map({
      container: ref.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [center.lon, center.lat],
      zoom: 8,
      interactive: true,
    })

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      // Fossil pins (amber)
      const fossilFeatures = fossils.filter(f => f.latitude && f.longitude).map((f, idx) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [f.longitude, f.latitude] },
        properties: { idx, label: f.common_name || f.taxon_name },
      }))
      map.addSource('fossils', { type: 'geojson', data: { type: 'FeatureCollection', features: fossilFeatures } })
      map.addLayer({
        id: 'fossil-points', type: 'circle', source: 'fossils',
        paint: { 'circle-radius': 7, 'circle-color': '#d4a96a', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5 },
      })

      // Mineral pins (orange)
      const mineralFeatures = minerals.filter(m => m.latitude && m.longitude).map((m, idx) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [m.longitude, m.latitude] },
        properties: { idx, label: m.site_name },
      }))
      map.addSource('minerals', { type: 'geojson', data: { type: 'FeatureCollection', features: mineralFeatures } })
      map.addLayer({
        id: 'mineral-points', type: 'circle', source: 'minerals',
        paint: { 'circle-radius': 7, 'circle-color': '#e65100', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5 },
      })

      // Rockhounding pins (green)
      const rockFeatures = rockhoundingSites.filter(s => s.latitude && s.longitude).map((s, idx) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [s.longitude, s.latitude] },
        properties: { idx, label: s.name },
      }))
      map.addSource('rockhounding', { type: 'geojson', data: { type: 'FeatureCollection', features: rockFeatures } })
      map.addLayer({
        id: 'rock-points', type: 'circle', source: 'rockhounding',
        paint: { 'circle-radius': 8, 'circle-color': '#4caf50', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 },
      })

      // Click handlers
      const handleClick = (layerId: string) => (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
        if (!e.features?.length) return
        const props = e.features[0].properties as any
        const coords = (e.features[0].geometry as any).coordinates.slice() as [number, number]
        if (popupRef.current) popupRef.current.remove()
        popupRef.current = new maplibregl.Popup({ maxWidth: '200px', closeButton: false })
          .setLngLat(coords)
          .setHTML(`<div style="font-family:Outfit,sans-serif;font-size:12px;color:#1a1612;padding:2px 0;"><strong>${props.label}</strong></div>`)
          .addTo(map)
      }

      for (const layerId of ['fossil-points', 'mineral-points', 'rock-points']) {
        map.on('click', layerId, handleClick(layerId))
        map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer' })
        map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = '' })
      }

      // Center marker
      new maplibregl.Marker({ color: '#fff' }).setLngLat([center.lon, center.lat]).addTo(map)
    })

    return () => { map.remove() }
  }, [fossils, minerals, rockhoundingSites, center])

  return <div ref={ref} className="dt-mini-map" />
}

// ── PeriodFilterModal ──

function PeriodFilterModal({ periods, selected, onSelect }: {
  periods: string[]; selected: string; onSelect: (p: string) => void
}) {
  const [open, setOpen] = useState(false)
  const label = selected || 'All Periods'

  return (
    <>
      <div className="dt-period-selector">
        <button className="dt-period-btn" onClick={() => setOpen(true)}>
          {label} <span className="dt-period-arrow">▾</span>
        </button>
      </div>

      {open && (
        <div className="dt-period-overlay" onClick={() => setOpen(false)}>
          <div className="dt-period-modal" onClick={e => e.stopPropagation()}>
            <div className="dt-period-modal-header">
              <span>Select Period</span>
              <button className="dt-period-modal-close" onClick={() => setOpen(false)}>✕</button>
            </div>
            <div className="dt-period-modal-list">
              <button
                className={`dt-period-modal-item${!selected ? ' active' : ''}`}
                onClick={() => { onSelect(''); setOpen(false) }}
              >
                All Periods
              </button>
              {periods.map(p => (
                <button
                  key={p}
                  className={`dt-period-modal-item${selected === p ? ' active' : ''}`}
                  onClick={() => { onSelect(p); setOpen(false) }}
                >
                  <span>{p}</span>
                  {ERA_CONTEXT[p] && <span className="dt-period-modal-context">{ERA_CONTEXT[p]}</span>}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// ── FossilGroupedList ──

function FossilGroupedList({ fossils, watershed }: { fossils: any[]; watershed: string }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const ITEMS_VISIBLE = 5

  const groups: Record<string, any[]> = {}
  for (const f of fossils) {
    const period = f.period || 'Unknown'
    if (!groups[period]) groups[period] = []
    groups[period].push(f)
  }

  const sortedPeriods = Object.keys(groups).sort((a, b) => {
    const ai = PERIOD_ORDER.indexOf(a)
    const bi = PERIOD_ORDER.indexOf(b)
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
  })

  if (fossils.length === 0) return <div className="dt-empty">No fossils match filters.</div>

  return (
    <div className="dt-grouped-list">
      {sortedPeriods.map(period => {
        const items = groups[period]
        const isExpanded = expanded[period]
        const visible = isExpanded ? items : items.slice(0, ITEMS_VISIBLE)
        const context = ERA_CONTEXT[period] || ''

        return (
          <div key={period} className="dt-group">
            <div className="dt-group-header">
              <div className="dt-group-title">
                <span className="dt-group-period">{period}</span>
                <span className="dt-group-count">{items.length}</span>
              </div>
              {context && <div className="dt-group-context">{context}</div>}
            </div>
            <div className="dt-group-items">
              {visible.map((f, i) => (
                <FossilCard key={i} fossil={f} watershed={watershed} />
              ))}
            </div>
            {items.length > ITEMS_VISIBLE && (
              <button className="dt-group-toggle" onClick={() => setExpanded(prev => ({ ...prev, [period]: !prev[period] }))}>
                {isExpanded ? 'Show less' : `Show all ${items.length}`}
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}

function FossilCard({ fossil: f, watershed }: { fossil: any; watershed: string }) {
  const sid = f.source_id || ''
  const sourceLink = sid.startsWith('occ:')
    ? `https://paleobiodb.org/classic/checkTaxonInfo?taxon_no=${sid.replace('occ:', '')}`
    : /^\d+$/.test(sid) ? `https://www.gbif.org/occurrence/${sid}`
    : `https://www.idigbio.org/portal/records/${sid}`
  const sourceLabel = sid.startsWith('occ:') ? 'PBDB' : /^\d+$/.test(sid) ? 'GBIF' : 'iDigBio'

  return (
    <div className="dt-fossil-card">
      <div className="dt-fossil-thumb">
        {f.image_url
          ? <img src={f.image_url} alt={f.taxon_name} loading="lazy" />
          : <span className="dt-fossil-icon">{PHYLUM_ICONS[f.phylum] || '🪨'}</span>}
      </div>
      <div className="dt-fossil-body">
        <div className="dt-fossil-name-row">
          <div className="dt-fossil-name">{f.taxon_name}</div>
          <SaveButton item={{
            type: 'fossil',
            id: `fossil-${f.source_id || f.taxon_name}`,
            watershed,
            label: f.common_name || f.taxon_name,
            sublabel: `${f.period || ''} ${f.phylum || ''}`.trim(),
          }} size={16} />
        </div>
        {f.common_name && <div className="dt-fossil-common">{f.common_name}</div>}
        <div className="dt-fossil-meta">
          {f.phylum && <span>{f.phylum}</span>}
          {f.class_name && <span> · {f.class_name}</span>}
          {f.age_max_ma && <span> · {f.age_max_ma} Ma</span>}
        </div>
        <div className="dt-fossil-bottom">
          {f.rarity && (
            <span className={`dt-rarity-badge ${f.rarity}`}>
              {f.rarity === 'very_rare' ? '💎 Very Rare' : f.rarity === 'rare' ? '⭐ Rare' : f.rarity === 'uncommon' ? 'Uncommon' : 'Common'}
            </span>
          )}
          {f.museum && <span className="dt-fossil-museum">{f.museum}</span>}
          {f.distance_km != null && <span className="dt-fossil-dist">{f.distance_km} km</span>}
          {sid && <a href={sourceLink} target="_blank" rel="noopener noreferrer" className="dt-fossil-source">{sourceLabel} ↗</a>}
          {f.morphosource_url && <a href={f.morphosource_url} target="_blank" rel="noopener noreferrer" className="dt-fossil-source">3D Model ↗</a>}
        </div>
        {f.image_url && f.image_license && (
          <div className="dt-fossil-license">{f.image_license}</div>
        )}
      </div>
    </div>
  )
}

// ── MineralGroupedList ──

function MineralGroupedList({ minerals, watershed }: { minerals: any[]; watershed: string }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const ITEMS_VISIBLE = 5

  const COMMODITY_ICONS: Record<string, string> = {
    'gold': '🥇', 'silver': '🥈', 'copper': '🟤', 'mercury': '💧',
    'agate': '💎', 'obsidian': '⚫', 'thunderegg': '🥚', 'opal': '🔮',
    'pumice': '🪨', 'perlite': '⚪', 'diatomite': '🟡',
  }

  function getIcon(commodity: string): string {
    const lower = commodity.toLowerCase()
    for (const [key, icon] of Object.entries(COMMODITY_ICONS)) {
      if (lower.includes(key)) return icon
    }
    return '💎'
  }

  const groups: Record<string, any[]> = {}
  for (const m of minerals) {
    const commodity = (m.commodity || 'Unknown').split(',')[0].trim()
    if (!groups[commodity]) groups[commodity] = []
    groups[commodity].push(m)
  }
  const sortedCommodities = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length)

  if (minerals.length === 0) return <div className="dt-empty">No minerals match filter.</div>

  return (
    <div className="dt-grouped-list">
      {sortedCommodities.map(commodity => {
        const items = groups[commodity]
        const isExpanded = expanded[commodity]
        const visible = isExpanded ? items : items.slice(0, ITEMS_VISIBLE)
        const icon = getIcon(commodity)

        return (
          <div key={commodity} className="dt-group">
            <div className="dt-group-header">
              <div className="dt-group-title">
                <span>{icon}</span>
                <span className="dt-group-period">{commodity}</span>
                <span className="dt-group-count">{items.length}</span>
              </div>
            </div>
            <div className="dt-group-items">
              {visible.map((m, i) => (
                <div key={i} className="dt-mineral-card">
                  {m.image_url && (
                    <div className="dt-mineral-thumb">
                      <img src={m.image_url} alt={m.commodity} loading="lazy" />
                    </div>
                  )}
                  <div className="dt-mineral-body">
                    <div className="dt-mineral-name-row">
                      <div className="dt-mineral-name">{m.site_name}</div>
                      <SaveButton item={{
                        type: 'mineral',
                        id: `mineral-${m.site_name}-${i}`,
                        watershed,
                        label: m.site_name,
                        sublabel: m.commodity,
                      }} size={16} />
                    </div>
                    <div className="dt-mineral-meta">{m.commodity}</div>
                    <div className="dt-mineral-bottom">
                      {m.dev_status && <span className="dt-mineral-status">{m.dev_status}</span>}
                      {m.distance_km != null && <span className="dt-mineral-dist">{m.distance_km} km</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {items.length > ITEMS_VISIBLE && (
              <button className="dt-group-toggle" onClick={() => setExpanded(prev => ({ ...prev, [commodity]: !prev[commodity] }))}>
                {isExpanded ? 'Show less' : `Show all ${items.length}`}
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}
