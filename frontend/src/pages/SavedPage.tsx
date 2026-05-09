import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useSaved, type SavedItem } from '../components/SavedContext'
import { useAuth } from '../components/AuthContext'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import { API_BASE } from '../config'
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

interface UserObservation {
  id: string
  photo_url: string | null
  thumbnail_url: string | null
  latitude: number | null
  longitude: number | null
  observed_at: string | null
  species_name: string | null
  common_name: string | null
  category: string | null
  notes: string | null
  watershed: string | null
  visibility: string
  scientific_name: string | null
}

export default function SavedPage() {
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const { listSaved, unsave } = useSaved()
  const { isLoggedIn } = useAuth()
  const headerWs = getSelectedWatershed() || 'mckenzie'

  // Fetch user's observations from the API (synced across devices)
  const [apiObs, setApiObs] = useState<UserObservation[]>([])
  useEffect(() => {
    if (!isLoggedIn) { setApiObs([]); return }
    fetch(`${API_BASE}/observations/user?mine=true&watershed=${headerWs}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => { if (Array.isArray(data)) setApiObs(data) })
      .catch(() => {})
  }, [isLoggedIn, headerWs])

  // Non-observation saved items from localStorage (filtered by watershed)
  const savedItems = listSaved().filter(
    item => item.type !== 'observation' && (item.watershed || 'other') === headerWs
  )

  const hasObs = apiObs.length > 0
  const hasSaved = savedItems.length > 0
  const isEmpty = !hasObs && !hasSaved

  return (
    <div className="saved-page">
      <WatershedHeader watershed={headerWs} basePath="/path/now" />

      {isEmpty ? (
        <div className="saved-empty-state">
          <div className="saved-empty-icon">♥</div>
          <div className="saved-empty-text">
            No saved items for {WATERSHED_LABELS[headerWs] || headerWs}.<br />
            Tap the heart icon on any reach, species, fly, or recreation site to save it here.
          </div>
        </div>
      ) : (
        <>
          {/* Observations section — fetched from API */}
          {hasObs && (
            <section className="saved-group">
              <h2 className="saved-group-title">
                📷 Observations
                <span className="saved-group-count">{apiObs.length}</span>
                <Link to={`/riversignal/${headerWs}?myobs=true`} className="saved-map-all">
                  View all on map
                </Link>
              </h2>
              {apiObs.map(obs => (
                <div key={obs.id} className="saved-item">
                  {obs.photo_url ? (
                    <img src={obs.photo_url} alt="" className="saved-item-thumb" />
                  ) : (
                    <span className="saved-item-icon">📷</span>
                  )}
                  <div className="saved-item-info">
                    <div className="saved-item-label">
                      {obs.common_name || obs.species_name || obs.category || 'Observation'}
                    </div>
                    {obs.scientific_name && (
                      <div className="saved-item-sub">{obs.scientific_name}</div>
                    )}
                    <div className="saved-item-meta">
                      {obs.visibility === 'private' ? 'private' : 'public'}
                      {obs.observed_at && ` · ${new Date(obs.observed_at).toLocaleDateString()}`}
                    </div>
                  </div>
                  {obs.latitude && obs.longitude && (
                    <Link
                      to={`/riversignal/${headerWs}?myobs=true`}
                      className="saved-item-map-link"
                      aria-label={`View ${obs.common_name || 'observation'} on map`}
                    >
                      📍
                    </Link>
                  )}
                </div>
              ))}
            </section>
          )}

          {/* Other saved items from localStorage */}
          {hasSaved && (
            <section className="saved-group">
              <h2 className="saved-group-title">
                📍 {WATERSHED_LABELS[headerWs] || headerWs}
                <span className="saved-group-count">{savedItems.length}</span>
              </h2>
              {savedItems.map(item => (
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
        </>
      )}
    </div>
  )
}
