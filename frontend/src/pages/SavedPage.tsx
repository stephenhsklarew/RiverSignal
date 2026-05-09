import { useEffect } from 'react'
import { useSaved, type SavedItem } from '../components/SavedContext'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import './SavedPage.css'

const TYPE_ICONS: Record<SavedItem['type'], string> = {
  reach: '📍', species: '🐟', fly: '🪶', recreation: '⛺', restoration: '♻',
  fossil: '🦴', mineral: '💎', rocksite: '🪨', observation: '📷',
}

const WATERSHED_LABELS: Record<string, string> = {
  mckenzie: 'McKenzie River', deschutes: 'Deschutes River', green_river: 'Green River',
  metolius: 'Metolius River', klamath: 'Upper Klamath Basin', johnday: 'John Day River',
  skagit: 'Skagit River',
}

export default function SavedPage() {
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const { listSaved, unsave } = useSaved()
  const headerWs = getSelectedWatershed() || 'mckenzie'
  const all = listSaved().filter(item => (item.watershed || 'other') === headerWs)

  return (
    <div className="saved-page">
      <WatershedHeader watershed={headerWs} basePath="/path/now" />

      {all.length === 0 ? (
        <div className="saved-empty-state">
          <div className="saved-empty-icon">♥</div>
          <div className="saved-empty-text">
            No saved items for {WATERSHED_LABELS[headerWs] || headerWs}.<br />
            Tap the heart icon on any reach, species, fly, or recreation site to save it here.
          </div>
        </div>
      ) : (
        <section className="saved-group">
          <h2 className="saved-group-title">
            📍 {WATERSHED_LABELS[headerWs] || headerWs}
            <span className="saved-group-count">{all.length}</span>
          </h2>
          {all.map(item => (
            <div key={`${item.type}-${item.id}`} className="saved-item">
              {item.thumbnail ? (
                <img src={item.thumbnail} alt="" className="saved-item-thumb" />
              ) : (
                <span className="saved-item-icon">{TYPE_ICONS[item.type] || '📌'}</span>
              )}
              <div className="saved-item-info">
                <div className="saved-item-label">{item.label}</div>
                {item.sublabel && <div className="saved-item-sub">{item.sublabel}</div>}
                <div className="saved-item-meta">
                  {item.type} · saved {new Date(item.savedAt).toLocaleDateString()}
                </div>
              </div>
              <button
                onClick={() => unsave(item.type, item.id)}
                className="saved-item-delete"
                aria-label={`Remove ${item.label} from saved`}
              >
                ✕
              </button>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
