import { useSaved, type SavedItem } from '../components/SavedContext'
import './SavedPage.css'

const TYPE_ICONS: Record<SavedItem['type'], string> = {
  reach: '📍', species: '🐟', fly: '🪶', recreation: '⛺', restoration: '♻',
}

const WATERSHED_LABELS: Record<string, string> = {
  mckenzie: 'McKenzie River', deschutes: 'Deschutes River', metolius: 'Metolius River',
  klamath: 'Upper Klamath Basin', johnday: 'John Day River',
}

export default function SavedPage() {
  const { listSaved, unsave } = useSaved()
  const all = listSaved()

  // Group by watershed
  const byWatershed: Record<string, SavedItem[]> = {}
  for (const item of all) {
    const ws = item.watershed || 'other'
    if (!byWatershed[ws]) byWatershed[ws] = []
    byWatershed[ws].push(item)
  }
  const watershedKeys = Object.keys(byWatershed).sort()

  return (
    <div className="saved-page">
      <h1 className="saved-title">Saved</h1>

      {all.length === 0 ? (
        <p className="saved-empty">
          Nothing saved yet — tap the heart icon on any card to save it here.
        </p>
      ) : (
        watershedKeys.map(ws => (
          <section key={ws} className="saved-group">
            <h2 className="saved-group-title">
              📍 {WATERSHED_LABELS[ws] || ws}
              <span className="saved-group-count">{byWatershed[ws].length}</span>
            </h2>
            {byWatershed[ws].map(item => (
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
        ))
      )}
    </div>
  )
}
