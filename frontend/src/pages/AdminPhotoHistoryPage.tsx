/**
 * /admin/photos/:species_key/history — full chronological audit timeline
 * for a curated species photo. Newest first.
 */
import { Link, useParams } from 'react-router-dom'
import useSWR from 'swr'
import { API_BASE } from '../config'
import './AdminPhotosPage.css'

interface HistoryEvent {
  action: string
  prev_photo_url: string | null
  new_photo_url: string | null
  prev_common_name: string | null
  new_common_name: string | null
  prev_scientific_name: string | null
  new_scientific_name: string | null
  changed_by_user_id: string | null
  changed_at: string | null
}

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then(r => {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
})

export default function AdminPhotoHistoryPage() {
  const { species_key = '' } = useParams<{ species_key: string }>()
  const { data, error } = useSWR<{ species_key: string; events: HistoryEvent[] }>(
    `${API_BASE}/admin/curated-photos/${encodeURIComponent(species_key)}/history`,
    fetcher,
  )

  return (
    <div className="admin-page">
      <header className="admin-header">
        <Link to={`/admin/photos/${encodeURIComponent(species_key)}`} className="admin-back">← {species_key}</Link>
        <h1>Full history</h1>
      </header>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}

      {data && data.events.length === 0 && (
        <div className="admin-empty">No edit history for this species yet.</div>
      )}

      {data && data.events.length > 0 && (
        <ul className="admin-history-list" style={{ background: '#fff', padding: 16, borderRadius: 12, border: '1px solid #e6e1d4' }}>
          {data.events.map((e, i) => (
            <li key={i} style={{ flexDirection: 'column', alignItems: 'stretch', gap: 4 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
                <span className={`admin-history-action ${e.action}`}>{e.action}</span>
                <span className="admin-history-date">
                  {e.changed_at && new Date(e.changed_at).toLocaleString()}
                </span>
              </div>
              {e.prev_photo_url !== e.new_photo_url && (
                <div style={{ fontSize: '0.78rem', color: '#555' }}>
                  <div>before: <code>{e.prev_photo_url || '(none)'}</code></div>
                  <div>after: <code>{e.new_photo_url || '(deleted)'}</code></div>
                </div>
              )}
              {(e.prev_common_name !== e.new_common_name || e.prev_scientific_name !== e.new_scientific_name) && (
                <div style={{ fontSize: '0.78rem', color: '#555' }}>
                  {e.prev_common_name !== e.new_common_name && (
                    <div>common: <code>{e.prev_common_name || '(none)'}</code> → <code>{e.new_common_name || '(none)'}</code></div>
                  )}
                  {e.prev_scientific_name !== e.new_scientific_name && (
                    <div>scientific: <code>{e.prev_scientific_name || '(none)'}</code> → <code>{e.new_scientific_name || '(none)'}</code></div>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
