import { useEffect, useState } from 'react'
import useSWR from 'swr'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useSaved, type SavedItem } from '../components/SavedContext'
import { useAuth } from '../components/AuthContext'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import { setUserObsCount } from '../components/useUserObsCount'
import type { PhotoMeta } from '../components/TappablePhoto'
import { API_BASE } from '../config'
import './SavedPage.css'

const TYPE_ICONS: Record<SavedItem['type'], string> = {
  reach: '📍', species: '🐟', fly: '🪶', recreation: '⛺', restoration: '♻',
  fossil: '🦴', mineral: '💎', rocksite: '🪨', observation: '📷',
}

/** Human-friendly section headers per saved-item type */
const TYPE_LABELS: Record<SavedItem['type'], string> = {
  reach: 'Reaches',
  species: 'Species',
  fly: 'Recommended Flies',
  recreation: 'Recreation Sites',
  restoration: 'Restoration Projects',
  fossil: 'Fossils',
  mineral: 'Minerals',
  rocksite: 'Rock Sites',
  observation: 'Observations',
}

/** Render order for sections */
const TYPE_ORDER: SavedItem['type'][] = [
  'observation', 'species', 'fly', 'reach', 'recreation', 'restoration', 'fossil', 'mineral', 'rocksite',
]

const WATERSHED_LABELS: Record<string, string> = {
  mckenzie: 'McKenzie River', deschutes: 'Deschutes River', green_river: 'Green River',
  metolius: 'Metolius River', klamath: 'Upper Klamath Basin', johnday: 'John Day River',
  skagit: 'Skagit River', shenandoah: 'Shenandoah River',
  mad_river_oh: 'Mad River',
  ipswich_river_ma: 'Ipswich River',
  clinch_river_va: 'Clinch River',
  new_river_va: 'New River',
  chattahoochee: 'Chattahoochee River',
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
  const navigate = useNavigate()
  const { listSaved, unsave, keepShared } = useSaved()
  const { isLoggedIn } = useAuth()
  const headerWs = getSelectedWatershed() || 'mckenzie'
  const [searchParams] = useSearchParams()
  const cameFromShare = searchParams.get('shared') === '1'
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [sharing, setSharing] = useState(false)
  const [copied, setCopied] = useState(false)

  // When a recipient signs in, convert their shared (expiring) items to permanent.
  useEffect(() => {
    if (isLoggedIn) keepShared()
  }, [isLoggedIn, keepShared])

  function openObservation(obs: UserObservation) {
    if (!obs.photo_url) return
    const ws = obs.watershed || headerWs
    const photo: PhotoMeta = {
      url: obs.photo_url,
      title: obs.common_name || obs.species_name || obs.category || 'Observation',
      subtitle: obs.scientific_name || undefined,
      observedAt: obs.observed_at || undefined,
      caption: obs.notes || undefined,
      observer: 'You',
      source: obs.visibility === 'private' ? 'Private observation' : 'Your observation',
    }
    navigate(`/path/now/${ws}/photo`, {
      state: { photo, backTo: { path: '/path/saved', label: 'Back to Saved' } },
    })
  }

  // Fetch user's observations from the API (synced across devices) via
  // SWR — stale-while-revalidate keeps the list snappy on navigation.
  // Pass null key when logged-out to skip the fetch entirely.
  const { data: apiObsRaw } = useSWR<UserObservation[]>(
    isLoggedIn ? `/observations/user?mine=true&watershed=${headerWs}` : null,
    { dedupingInterval: 60_000 },
  )
  const apiObs: UserObservation[] = Array.isArray(apiObsRaw) ? apiObsRaw : []
  useEffect(() => {
    setUserObsCount(headerWs, isLoggedIn ? apiObs.length : 0)
  }, [isLoggedIn, headerWs, apiObs.length])

  // Non-observation saved items from localStorage (filtered by watershed)
  const savedItems = listSaved().filter(
    item => item.type !== 'observation' && (item.watershed || 'other') === headerWs
  )

  // Group saved items by type
  const byType: Partial<Record<SavedItem['type'], SavedItem[]>> = {}
  for (const item of savedItems) {
    if (!byType[item.type]) byType[item.type] = []
    byType[item.type]!.push(item)
  }

  const hasObs = apiObs.length > 0
  const hasSaved = savedItems.length > 0
  const isEmpty = !hasObs && !hasSaved
  const sharedItems = savedItems.filter(i => i.shared)

  async function handleShare() {
    setSharing(true); setCopied(false); setShareUrl(null)
    // Observations are excluded (private, backend-synced) — share the saved
    // species/flies/reaches/recreation/geology items for this watershed.
    const items = savedItems.map(s => ({
      type: s.type, id: s.id,
      data: { watershed: s.watershed, label: s.label, sublabel: s.sublabel,
              thumbnail: s.thumbnail, latitude: s.latitude, longitude: s.longitude },
    }))
    try {
      const r = await fetch(`${API_BASE}/saved/share`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ watershed: headerWs, sections: Object.keys(byType), items }),
      })
      const d = await r.json()
      if (r.ok && d.url) setShareUrl(`${window.location.origin}${d.url}`)
    } finally { setSharing(false) }
  }

  async function copyShareLink() {
    if (!shareUrl) return
    try { await navigator.clipboard.writeText(shareUrl); setCopied(true) } catch { /* ignore */ }
  }

  return (
    <div className="saved-page">
      <WatershedHeader watershed={headerWs} basePath="/path/now" />

      {(cameFromShare || sharedItems.length > 0) && sharedItems.length > 0 && (
        <div className="saved-shared-banner" style={{ background: '#eef6ff', border: '1px solid #9cc3ef', borderRadius: 10, padding: '10px 14px', margin: '10px 0', fontSize: 14 }}>
          📬 <strong>{sharedItems.length}</strong> shared item{sharedItems.length === 1 ? '' : 's'} added to your Saved.
          {isLoggedIn
            ? ' Kept in your account.'
            : ' These expire in 24 hours — sign in to keep them permanently.'}
        </div>
      )}

      {hasSaved && (
        <div className="saved-actions" style={{ display: 'flex', justifyContent: 'flex-end', margin: '6px 0' }}>
          <button className="saved-share-btn" onClick={handleShare} disabled={sharing}
            style={{ fontWeight: 600, padding: '6px 12px', borderRadius: 8, border: '1px solid var(--accent, #2b6cb0)', background: 'var(--accent, #2b6cb0)', color: '#fff' }}>
            {sharing ? 'Creating link…' : '🔗 Share these'}
          </button>
        </div>
      )}

      {shareUrl && (
        <div className="saved-share-modal" role="dialog" aria-label="Share link"
          style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: 10, padding: 14, margin: '8px 0', boxShadow: '0 2px 8px rgba(0,0,0,.08)' }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Share link (expires in 24 hours)</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <input readOnly value={shareUrl} onFocus={e => e.currentTarget.select()}
              style={{ flex: 1, padding: '6px 8px', border: '1px solid #d0d7de', borderRadius: 6, fontSize: 13 }} />
            <button onClick={copyShareLink} style={{ padding: '6px 12px', borderRadius: 6, fontWeight: 600 }}>
              {copied ? '✓ Copied' : 'Copy'}
            </button>
            <button onClick={() => setShareUrl(null)} aria-label="Close" style={{ padding: '6px 10px', borderRadius: 6 }}>✕</button>
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 6 }}>
            Anyone with this link sees these {WATERSHED_LABELS[headerWs] || headerWs} items in their Saved for 24 hours (observations excluded).
          </div>
        </div>
      )}

      {isEmpty ? (
        <div className="saved-empty-state">
          <div className="saved-empty-icon" style={{ color: 'var(--alert, #c4432b)' }}>♥</div>
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
                <Link to={`/path/saved/map/${headerWs}`} className="saved-map-all">
                  View all on map
                </Link>
              </h2>
              {apiObs.map(obs => {
                const tappable = !!obs.photo_url
                const label = obs.common_name || obs.species_name || obs.category || 'Observation'
                return (
                  <div
                    key={obs.id}
                    className={`saved-item${tappable ? ' saved-item-tappable' : ''}`}
                    role={tappable ? 'button' : undefined}
                    tabIndex={tappable ? 0 : undefined}
                    onClick={tappable ? () => openObservation(obs) : undefined}
                    onKeyDown={tappable ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openObservation(obs) }
                    } : undefined}
                    aria-label={tappable ? `View ${label} in detail` : undefined}
                  >
                    {obs.photo_url ? (
                      <img src={obs.photo_url} alt="" className="saved-item-thumb" />
                    ) : (
                      <span className="saved-item-icon">📷</span>
                    )}
                    <div className="saved-item-info">
                      <div className="saved-item-label">{label}</div>
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
                        to={`/path/saved/map/${headerWs}`}
                        className="saved-item-map-link"
                        aria-label={`View ${obs.common_name || 'observation'} on map`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        📍
                      </Link>
                    )}
                  </div>
                )
              })}
            </section>
          )}

          {/* Saved items grouped by type */}
          {TYPE_ORDER.filter(t => t !== 'observation' && byType[t]).map(type => (
            <section key={type} className="saved-group">
              <h2 className="saved-group-title">
                {TYPE_ICONS[type]} {TYPE_LABELS[type]}
                <span className="saved-group-count">{byType[type]!.length}</span>
              </h2>
              {byType[type]!.map(item => (
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
                      saved {new Date(item.savedAt).toLocaleDateString()}
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
          ))}
        </>
      )}
    </div>
  )
}
