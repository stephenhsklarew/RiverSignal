/**
 * /admin/photos               — list view of every curated species photo
 * /admin/photos/:species_key  — editor view: current photo, iNat candidates, save
 *
 * Gated by <AdminRoute>. Mobile-friendly layout (the admin may curate from
 * their phone). All writes go through PUT /admin/curated-photos/<species_key>
 * which writes an audit row in the same transaction.
 */
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import useSWR from 'swr'
import { API_BASE } from '../config'
import './AdminPhotosPage.css'

interface CuratedRow {
  species_key: string
  common_name: string
  scientific_name: string | null
  photo_url: string
  inat_user_handle: string | null
  license: string | null
  source: string | null
  updated_at: string | null
}

interface CuratedDetail {
  species: CuratedRow & {
    inat_observation_id: number | null
    exists: boolean
  }
  recent_changes: Array<{
    action: string
    prev_photo_url: string | null
    new_photo_url: string | null
    changed_by_user_id: string | null
    changed_at: string | null
  }>
}

interface InatCandidate {
  observation_id: number
  photo_url: string
  photographer: string | null
  license_code: string
  observed_on: string | null
  place_guess: string | null
  taxon_name: string | null
}

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then(r => {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
})

export default function AdminPhotosPage() {
  const { species_key } = useParams<{ species_key: string }>()
  return species_key
    ? <AdminPhotoEditor speciesKey={species_key} />
    : <AdminPhotosList />
}

// ─── List view ─────────────────────────────────────────────────────

function AdminPhotosList() {
  const navigate = useNavigate()
  const { data, error } = useSWR<CuratedRow[]>(`${API_BASE}/admin/curated-photos`, fetcher)
  const [filter, setFilter] = useState('')
  const [sort, setSort] = useState<'key' | 'updated'>('key')

  const rows = useMemo(() => {
    const list = data || []
    const filtered = filter.trim()
      ? list.filter(r =>
          r.species_key.toLowerCase().includes(filter.toLowerCase())
          || (r.common_name || '').toLowerCase().includes(filter.toLowerCase()))
      : list
    return [...filtered].sort((a, b) =>
      sort === 'key'
        ? a.species_key.localeCompare(b.species_key)
        : (a.updated_at || '').localeCompare(b.updated_at || ''))
  }, [data, filter, sort])

  return (
    <div className="admin-page">
      <header className="admin-header">
        <h1>Curated species photos</h1>
        <div className="admin-header-actions">
          <button
            className="admin-add-btn"
            onClick={() => {
              const k = prompt('New species_key (lowercase, e.g. "lake trout"):')
              if (k && k.trim()) navigate(`/admin/photos/${encodeURIComponent(k.trim().toLowerCase())}`)
            }}
          >+ Add species</button>
          <RevokeAdminButton />
        </div>
      </header>

      <div className="admin-toolbar">
        <input
          type="search"
          placeholder="Filter by species key or name…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="admin-filter"
        />
        <select value={sort} onChange={e => setSort(e.target.value as 'key' | 'updated')} className="admin-sort">
          <option value="key">Sort: A → Z</option>
          <option value="updated">Sort: Recently changed</option>
        </select>
      </div>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}

      <ul className="admin-grid">
        {rows.map(r => (
          <li key={r.species_key}>
            <Link to={`/admin/photos/${encodeURIComponent(r.species_key)}`} className="admin-card">
              <div className="admin-card-thumb">
                {r.photo_url
                  ? <img src={r.photo_url} alt={r.common_name} loading="lazy" />
                  : <div className="admin-card-placeholder">🐟</div>}
              </div>
              <div className="admin-card-body">
                <div className="admin-card-key">{r.species_key}</div>
                <div className="admin-card-name">{r.common_name}</div>
                {r.scientific_name && <div className="admin-card-sci">{r.scientific_name}</div>}
                {r.updated_at && (
                  <div className="admin-card-meta">
                    Updated {new Date(r.updated_at).toLocaleDateString()}
                  </div>
                )}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

// ─── Editor view ───────────────────────────────────────────────────

function AdminPhotoEditor({ speciesKey }: { speciesKey: string }) {
  const navigate = useNavigate()
  const url = `${API_BASE}/admin/curated-photos/${encodeURIComponent(speciesKey)}`
  const { data, mutate, error } = useSWR<CuratedDetail>(url, fetcher)

  // Editable fields
  const [commonName, setCommonName] = useState('')
  const [scientificName, setScientificName] = useState('')
  const [photoUrl, setPhotoUrl] = useState('')
  const [selectedObs, setSelectedObs] = useState<InatCandidate | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [historyOpen, setHistoryOpen] = useState(false)

  // Seed inputs from server on first load
  useMemo(() => {
    if (data?.species && commonName === '' && photoUrl === '') {
      setCommonName(data.species.common_name || speciesKey)
      setScientificName(data.species.scientific_name || '')
      setPhotoUrl(data.species.photo_url || '')
    }
  }, [data, speciesKey, commonName, photoUrl])

  // iNat search
  const inatUrl = scientificName.trim() && scientificName.includes(' ')
    ? `${API_BASE}/admin/inat/photos?scientific_name=${encodeURIComponent(scientificName.trim())}`
    : null
  const [searchEnabled, setSearchEnabled] = useState(false)
  const { data: inatData, isLoading: inatLoading } = useSWR<{ candidates: InatCandidate[]; error?: string }>(
    searchEnabled ? inatUrl : null,
    fetcher,
  )

  function pickCandidate(c: InatCandidate) {
    setSelectedObs(c)
    setPhotoUrl(c.photo_url)
  }

  async function save() {
    setBusy(true); setMsg(null)
    try {
      const r = await fetch(url, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          common_name: commonName.trim() || speciesKey,
          scientific_name: scientificName.trim() || null,
          photo_url: photoUrl.trim(),
          inat_observation_id: selectedObs?.observation_id ?? null,
          inat_user_handle: selectedObs?.photographer ?? null,
          license: selectedObs?.license_code ?? null,
          source: selectedObs ? 'inaturalist' : 'wikimedia',
        }),
      })
      if (!r.ok) throw new Error(`Save failed: ${r.status}`)
      await mutate()
      setMsg('Saved.')
      setSelectedObs(null)
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`)
    } finally {
      setBusy(false)
    }
  }

  async function deleteRow() {
    if (!confirm(`Delete the curated photo for "${speciesKey}"? iNat will fall through for this species.`)) return
    setBusy(true)
    try {
      const r = await fetch(url, { method: 'DELETE', credentials: 'include' })
      if (!r.ok) throw new Error(`Delete failed: ${r.status}`)
      navigate('/admin/photos', { replace: true })
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`)
      setBusy(false)
    }
  }

  if (error) return <div className="admin-page"><div className="admin-error">Failed to load: {String(error)}</div></div>
  if (!data) return <div className="admin-page"><div className="admin-empty">Loading…</div></div>

  return (
    <div className="admin-page">
      <header className="admin-header">
        <Link to="/admin/photos" className="admin-back">← All photos</Link>
        <h1>{commonName || speciesKey}</h1>
        <RevokeAdminButton />
      </header>

      <section className="admin-current">
        <div className="admin-current-thumb">
          {photoUrl
            ? <img src={photoUrl} alt={commonName} />
            : <div className="admin-current-placeholder">No photo</div>}
        </div>
        <div className="admin-current-meta">
          <label>species_key
            <input type="text" value={speciesKey} disabled />
          </label>
          <label>Common name
            <input type="text" value={commonName} onChange={e => setCommonName(e.target.value)} />
          </label>
          <label>Scientific name (binomial)
            <input
              type="text" value={scientificName}
              onChange={e => setScientificName(e.target.value)}
              placeholder="Genus species"
            />
          </label>
          <label>Photo URL (paste Wikimedia or any URL)
            <input type="url" value={photoUrl} onChange={e => setPhotoUrl(e.target.value)} />
          </label>
        </div>
      </section>

      <section className="admin-inat">
        <button
          type="button"
          className="admin-inat-search"
          onClick={() => setSearchEnabled(true)}
          disabled={!scientificName.trim() || !scientificName.includes(' ')}
        >
          {inatLoading ? 'Searching iNat…' : 'Search iNat for candidates'}
        </button>
        {!scientificName.includes(' ') && (
          <div className="admin-hint">Enter a binomial (Genus species) above to search.</div>
        )}
        {inatData?.error && <div className="admin-error">{inatData.error}</div>}
        {inatData?.candidates && inatData.candidates.length === 0 && (
          <div className="admin-empty">
            No iNat candidates. Try{' '}
            <a target="_blank" rel="noopener noreferrer"
              href={`https://commons.wikimedia.org/wiki/Special:Search/${encodeURIComponent(scientificName)}`}>
              Wikimedia Commons
            </a>{' '}and paste a URL above.
          </div>
        )}
        {inatData?.candidates && inatData.candidates.length > 0 && (
          <ul className="admin-candidates">
            {inatData.candidates.map(c => (
              <li
                key={c.observation_id}
                className={`admin-candidate ${selectedObs?.observation_id === c.observation_id ? 'on' : ''}`}
                onClick={() => pickCandidate(c)}
              >
                <img src={c.photo_url} alt="" loading="lazy" />
                <div className="admin-candidate-meta">
                  <div>📷 {c.photographer || 'unknown'}</div>
                  <div className="admin-candidate-license">{c.license_code}</div>
                  {c.observed_on && <div>{c.observed_on}</div>}
                  {c.place_guess && <div className="admin-candidate-place">{c.place_guess}</div>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="admin-actions">
        <button className="admin-save" disabled={busy || !photoUrl.trim()} onClick={save}>
          {busy ? 'Saving…' : 'Save'}
        </button>
        {data.species.exists && (
          <button className="admin-delete" disabled={busy} onClick={deleteRow}>Delete</button>
        )}
        {msg && <span className="admin-msg">{msg}</span>}
      </section>

      <section className="admin-history">
        <button type="button" className="admin-history-toggle" onClick={() => setHistoryOpen(o => !o)}>
          {historyOpen ? '▾' : '▸'} Recent changes ({data.recent_changes.length})
        </button>
        {historyOpen && (
          <>
            <ul className="admin-history-list">
              {data.recent_changes.map((c, i) => (
                <li key={i}>
                  <span className={`admin-history-action ${c.action}`}>{c.action}</span>
                  <span className="admin-history-date">
                    {c.changed_at && new Date(c.changed_at).toLocaleString()}
                  </span>
                  {c.prev_photo_url !== c.new_photo_url && (
                    <span className="admin-history-url">
                      {(c.new_photo_url || '(deleted)').split('/').slice(-1)[0]}
                    </span>
                  )}
                </li>
              ))}
              {data.recent_changes.length === 0 && <li className="admin-empty">No changes yet.</li>}
            </ul>
            <Link to={`/admin/photos/${encodeURIComponent(speciesKey)}/history`} className="admin-full-history">
              View full history →
            </Link>
          </>
        )}
      </section>
    </div>
  )
}

// ─── Self-service admin revocation ──────────────────────────────────

function RevokeAdminButton() {
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  async function revoke() {
    if (!confirm('Revoke your admin access? Re-granting requires a SQL update by a developer.')) return
    setBusy(true)
    try {
      await fetch(`${API_BASE}/admin/self/revoke`, { method: 'POST', credentials: 'include' })
      window.location.href = '/'
    } finally {
      setBusy(false)
      navigate('/', { replace: true })
    }
  }
  return (
    <button className="admin-revoke" disabled={busy} onClick={revoke} title="Self-revoke admin access">
      Revoke admin
    </button>
  )
}
