import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useSaved, type SavedItem } from '../components/SavedContext'
import logo from '../assets/deeptrail-logo.svg'
import './DeepTrailPage.css'

const DT_TYPES: SavedItem['type'][] = ['rocksite', 'fossil', 'mineral']
const TYPE_LABELS: Record<string, { label: string; icon: string }> = {
  rocksite: { label: 'Rockhounding Sites', icon: '🪨' },
  fossil: { label: 'Fossils', icon: '🦴' },
  mineral: { label: 'Minerals', icon: '💎' },
}

export default function TrailSavedPage() {
  useEffect(() => { document.title = 'Deep Trail'; return () => { document.title = 'RiverSignal' } }, [])
  const { listSaved, unsave } = useSaved()
  const [filter, setFilter] = useState<string>('')

  const allItems = listSaved().filter(i => DT_TYPES.includes(i.type))
  const filtered = filter ? allItems.filter(i => i.type === filter) : allItems

  return (
    <div className="dt-app">
      <header className="dt-detail-header">
        <Link to="/trail" className="dt-back" style={{ textDecoration: 'none' }}>← Home</Link>
        <img src={logo} alt="DeepTrail" className="dt-logo" />
      </header>

      <main className="dt-content" style={{ paddingBottom: 72 }}>
        <section className="dt-loc-hero">
          <h1>Saved Items</h1>
          <p className="dt-loc-coords">{allItems.length} items saved</p>
        </section>

        {allItems.length === 0 ? (
          <div className="dt-empty" style={{ padding: '40px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>⭐</div>
            <div style={{ color: '#8a7e6e', fontSize: '0.9rem', lineHeight: 1.5 }}>
              No saved items yet.<br />
              Tap the star on any rockhounding site, fossil, or mineral to save it here.
            </div>
          </div>
        ) : (
          <>
            {/* Filter chips */}
            <div className="dt-filter-chips" style={{ padding: '0 16px', marginBottom: 8 }}>
              <button className={`dt-chip${!filter ? ' active' : ''}`} onClick={() => setFilter('')}>
                All ({allItems.length})
              </button>
              {DT_TYPES.map(t => {
                const count = allItems.filter(i => i.type === t).length
                if (count === 0) return null
                const info = TYPE_LABELS[t]
                return (
                  <button key={t} className={`dt-chip${filter === t ? ' active' : ''}`}
                    onClick={() => setFilter(filter === t ? '' : t)}>
                    {info.icon} {info.label} ({count})
                  </button>
                )
              })}
            </div>

            {/* Saved items list */}
            <div style={{ padding: '0 16px' }}>
              {filtered.sort((a, b) => new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime()).map(item => {
                const info = TYPE_LABELS[item.type] || { label: item.type, icon: '📌' }
                return (
                  <div key={`${item.type}-${item.id}`} className="dt-saved-card">
                    {item.thumbnail && (
                      <img src={item.thumbnail} alt={item.label} className="dt-saved-thumb" loading="lazy" />
                    )}
                    <div className="dt-saved-body">
                      <div className="dt-saved-name">{item.label}</div>
                      {item.sublabel && <div className="dt-saved-sub">{item.sublabel}</div>}
                      <div className="dt-saved-meta">
                        <span className="dt-saved-type">{info.icon} {info.label}</span>
                        <span className="dt-saved-date">{new Date(item.savedAt).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <button className="dt-saved-remove" onClick={() => unsave(item.type, item.id)} title="Remove">✕</button>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
