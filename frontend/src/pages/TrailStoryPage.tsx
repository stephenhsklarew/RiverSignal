import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import { useDeepTrail, WATERSHEDS } from '../components/DeepTrailContext'
import DeepTrailHeader from '../components/DeepTrailHeader'
import { CardSettingsPanel, loadCardSettingsGeneric, type CardConfig } from '../components/CardSettings'
import './DeepTrailPage.css'

const TRAIL_STORY_CARDS: CardConfig[] = [
  { id: 'deep_time_story', label: 'Deep Time Story', icon: '📖', visible: true },
  { id: 'geologic_context', label: 'Geologic Context', icon: '🪨', visible: true },
  { id: 'deep_time_timeline', label: 'Deep Time Timeline', icon: '🕰️', visible: true },
  { id: 'cross_domain', label: 'Why This River?', icon: '🌋', visible: true },
  { id: 'compare_eras', label: 'Compare Eras', icon: '⚖️', visible: true },
]

export default function TrailStoryPage() {
  useEffect(() => { document.title = 'Deep Trail'; return () => { document.title = 'RiverSignal' } }, [])
  const { locationId } = useParams<{ locationId: string }>()
  const navigate = useNavigate()
  const {
    loc, selectLocation, loading,
    storyNarrative, storyLoading, readingLevel, setReadingLevel,
    speaking, audioLoading, speakStory,
    geoContext, timeline, crossDomain,
    compareEra1, setCompareEra1, compareEra2, setCompareEra2,
    compareData, fetchCompareData,
  } = useDeepTrail()

  const [cardConfig, setCardConfig] = useState<CardConfig[]>(() =>
    loadCardSettingsGeneric('deeptrail-story-cards', TRAIL_STORY_CARDS)
  )
  const [showSettings, setShowSettings] = useState(false)

  // Resolve locationId if loc is null
  useEffect(() => {
    if (loc) return
    if (!locationId) { navigate('/trail'); return }

    // Try watershed lookup
    const ws = WATERSHEDS.find(w => w.id === locationId)
    if (ws) { selectLocation(ws); return }

    // Try lat,lon parse
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

  return (
    <div className="dt-app">
      <DeepTrailHeader tab="story" />

      {showSettings && (
        <CardSettingsPanel
          cards={cardConfig}
          onChange={setCardConfig}
          onClose={() => setShowSettings(false)}
          storageKey="deeptrail-story-cards"
          defaults={TRAIL_STORY_CARDS}
          title="Customize Story Cards"
          dark
        />
      )}

      {loading ? <div className="dt-loading">Loading geology data...</div> : (
        <main className="dt-content" style={{ paddingBottom: 72 }}>
          {/* Dynamic CSS for card ordering/visibility */}
          <style>{cardConfig.map((c, i) => {
            const rules = [`[data-dtcard="${c.id}"] { order: ${i}; }`]
            if (!c.visible) rules.push(`[data-dtcard="${c.id}"] { display: none !important; }`)
            return rules.join('\n')
          }).join('\n')}</style>

          {/* Location hero */}
          <section className="dt-loc-hero">
            <div className="dt-hero-top-row">
              <h1>{loc.name}</h1>
              <button className="dt-settings-btn" onClick={() => setShowSettings(true)} title="Customize sections">⚙</button>
            </div>
            <p className="dt-loc-coords">{loc.lat.toFixed(4)}°N, {Math.abs(loc.lon).toFixed(4)}°W</p>
            {loc.photo && (
              <img src={loc.photo} alt={loc.name} className="dt-hero-img" />
            )}
          </section>

          <div className="dt-card-container" style={{ display: 'flex', flexDirection: 'column' }}>

            {/* 1. Deep Time Story */}
            <div data-dtcard="deep_time_story">
              <StoryCard
                narrative={storyNarrative}
                loading={storyLoading}
                readingLevel={readingLevel}
                onChangeLevel={setReadingLevel}
                speaking={speaking}
                audioLoading={audioLoading}
                onSpeak={speakStory}
              />
            </div>

            {/* 2. Geologic Context */}
            <div data-dtcard="geologic_context">
              {geoContext?.units?.length > 0 && (() => {
                const seen = new Set<string>()
                const unique = geoContext.units.filter((u: any) => {
                  const key = `${u.unit_name}|${u.rock_type}|${u.period}|${u.lithology}`
                  if (seen.has(key)) return false
                  seen.add(key)
                  return true
                })
                return unique.length > 0 ? (
                  <section className="dt-geo-section">
                    <h3>Geologic Context</h3>
                    {unique.slice(0, 3).map((u: any, i: number) => (
                      <div key={i} className="dt-geo-unit">
                        <span className={`rock-badge-dt ${u.rock_type || ''}`}>{u.rock_type || 'unknown'}</span>
                        <div>
                          <div className="dt-geo-name">{u.formation || u.unit_name}</div>
                          <div className="dt-geo-meta">{u.lithology ? `${u.lithology} · ` : ''}{u.period}{u.age_max_ma ? ` · ${u.age_max_ma}–${u.age_min_ma || '?'} Ma` : ''}</div>
                        </div>
                      </div>
                    ))}
                  </section>
                ) : null
              })()}
            </div>

            {/* 3. Deep Time Timeline */}
            <div data-dtcard="deep_time_timeline">
              {timeline.length > 0 && (
                <TimelineSection items={timeline} />
              )}
            </div>

            {/* 4. Why This River? */}
            <div data-dtcard="cross_domain">
              {crossDomain && crossDomain.connections?.length > 0 && (
                <section className="dt-cross-section">
                  <h3>🌋 Why This River?</h3>
                  {crossDomain.connections.map((c: any, i: number) => (
                    <div key={i} className="dt-cross-card">
                      <span className="dt-cross-icon">{c.icon}</span>
                      <div>
                        <div className="dt-cross-geo">{c.geology}</div>
                        <div className="dt-cross-text">{c.connection}</div>
                      </div>
                    </div>
                  ))}
                  {crossDomain.ecology?.river_name && (
                    <a href={`/path/now/${crossDomain.ecology.watershed}`} className="dt-cross-link">
                      See the {crossDomain.ecology.river_name} →
                    </a>
                  )}
                </section>
              )}
            </div>

            {/* 5. Compare Eras */}
            <div data-dtcard="compare_eras">
              <section className="dt-compare-section">
                <h3>⚖️ Compare Eras</h3>
                <div className="dt-compare-pickers">
                  <select className="dt-filter-select" value={compareEra1} onChange={e => setCompareEra1(e.target.value)}>
                    {['Eocene', 'Oligocene', 'Miocene', 'Pliocene', 'Pleistocene', 'Holocene'].map(e => (
                      <option key={e} value={e}>{e}</option>
                    ))}
                  </select>
                  <span className="dt-compare-vs">vs</span>
                  <select className="dt-filter-select" value={compareEra2} onChange={e => setCompareEra2(e.target.value)}>
                    {['Eocene', 'Oligocene', 'Miocene', 'Pliocene', 'Pleistocene', 'Holocene', 'Today'].map(e => (
                      <option key={e} value={e}>{e}</option>
                    ))}
                  </select>
                  <button className="dt-compare-go" onClick={fetchCompareData}>Compare</button>
                </div>
                {compareData && (
                  <div className="dt-compare-results">
                    <div className="dt-compare-col">
                      <div className="dt-compare-era-name">{compareData.era1.era}</div>
                      <div className="dt-compare-stat">{compareData.era1.fossil_count} fossils</div>
                      {compareData.era1.fossils?.slice(0, 3).map((f: any, i: number) => (
                        <div key={i} className="dt-compare-fossil">{f.name} ({f.phylum})</div>
                      ))}
                    </div>
                    <div className="dt-compare-col">
                      <div className="dt-compare-era-name">{compareData.era2.era}</div>
                      <div className="dt-compare-stat">{compareData.era2.fossil_count} fossils</div>
                      {compareData.era2.fossils?.slice(0, 3).map((f: any, i: number) => (
                        <div key={i} className="dt-compare-fossil">{f.name} ({f.phylum})</div>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            </div>

          </div>{/* end dt-card-container */}
        </main>
      )}
    </div>
  )
}

// ── StoryCard (local) ──

function StoryCard({ narrative, loading, readingLevel, onChangeLevel, speaking, audioLoading, onSpeak }: {
  narrative: string; loading: boolean; readingLevel: string;
  onChangeLevel: (level: string) => void;
  speaking: boolean; audioLoading: boolean; onSpeak: () => void;
}) {
  const [page, setPage] = useState(0)
  const SENTENCES_PER_PAGE = 5

  useEffect(() => { setPage(0) }, [narrative])

  const sentences = narrative
    .split(/(?<=[.!?])\s+/)
    .filter(s => s.trim().length > 10)
  const totalPages = Math.max(1, Math.ceil(sentences.length / SENTENCES_PER_PAGE))
  const pageSentences = sentences.slice(page * SENTENCES_PER_PAGE, (page + 1) * SENTENCES_PER_PAGE)

  return (
    <>
      <h3 className="dt-story-label">Deep Time Story</h3>
      <section className="dt-story-card">
        <div className="dt-story-controls">
          <div className="dt-reading-toggle">
            {(['adult', 'kid_friendly', 'expert'] as const).map(level => (
              <button key={level} className={`dt-reading-btn${readingLevel === level ? ' active' : ''}`}
                onClick={() => onChangeLevel(level)}>
                {level === 'kid_friendly' ? 'Kids' : level === 'expert' ? 'Expert' : 'Adult'}
              </button>
            ))}
          </div>
          <button className={`dt-listen-btn-sm${speaking ? ' active' : ''}`} onClick={onSpeak} disabled={audioLoading || loading}>
            {audioLoading ? '⏳' : speaking ? '⏹' : '🔊'}
          </button>
        </div>

        {loading ? (
          <div className="dt-story-loading">Generating deep time narrative...</div>
        ) : (
          <div className="dt-story-md">
            <Markdown>{pageSentences.join(' ')}</Markdown>
          </div>
        )}

        {!loading && totalPages > 1 && (
          <div className="dt-story-pagination">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="dt-page-btn">← Prev</button>
            <span className="dt-page-info">{page + 1} / {totalPages}</span>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="dt-page-btn">Next →</button>
          </div>
        )}
      </section>
    </>
  )
}

// ── TimelineSection (local) ──

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

function TimelineSection({ items }: { items: any[] }) {
  const [page, setPage] = useState(0)
  const ITEMS_PER_PAGE = 5

  const cleaned = (() => {
    const seen = new Set<string>()
    return items
      .filter(item => {
        const name = item.type === 'fossil' ? item.taxon_name : item.name
        if (!name || name === 'null') return false
        if (!item.period && !item.age_max_ma) return false
        if (item.type === 'fossil' && !item.phylum && !item.period) return false
        const key = `${item.type}|${name}|${item.period || ''}`
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      .sort((a, b) => (b.age_max_ma || 0) - (a.age_max_ma || 0))
  })()

  const totalPages = Math.max(1, Math.ceil(cleaned.length / ITEMS_PER_PAGE))
  const pageItems = cleaned.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)

  useEffect(() => { setPage(0) }, [items])

  if (cleaned.length === 0) return null

  return (
    <section className="dt-timeline-section">
      <h3>Deep Time Timeline</h3>
      <div className="dt-timeline">
        {pageItems.map((item, i) => {
          const isRock = item.type === 'geologic_unit'
          const name = isRock ? (item.name || item.formation || 'Unknown unit') : (item.taxon_name || '?')
          const age = item.age_max_ma ? `${item.age_max_ma} Ma` : ''
          const period = item.period || ''
          const context = ERA_CONTEXT[period] || ''
          const meta = isRock
            ? [item.rock_type, item.lithology, period].filter(Boolean).join(' · ')
            : [item.phylum, item.class_name, period].filter(Boolean).join(' · ')

          return (
            <div key={i} className={`dt-tl-item ${item.type}`}>
              <div className="dt-tl-dot">{isRock ? '🪨' : '🦴'}</div>
              <div className="dt-tl-content">
                <div className="dt-tl-header">
                  {age && <span className="dt-tl-age">{age}</span>}
                  {period && <span className="dt-tl-period">{period}</span>}
                </div>
                <div className="dt-tl-name">{name}</div>
                <div className="dt-tl-meta">{meta}</div>
                {context && <div className="dt-tl-context">{context}</div>}
              </div>
            </div>
          )
        })}
      </div>

      {totalPages > 1 && (
        <div className="dt-story-pagination">
          <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="dt-page-btn">← Older</button>
          <span className="dt-page-info">{page + 1} / {totalPages}</span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="dt-page-btn">Newer →</button>
        </div>
      )}
    </section>
  )
}
