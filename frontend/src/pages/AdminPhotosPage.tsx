/**
 * Watershed-first photo workflow:
 *
 * /admin/photos                      — pick a watershed (or the global defaults)
 * /admin/photos?watershed=<slug>     — current fish images for that watershed
 * /admin/photos?watershed=*          — global default curated photos
 * /admin/photos/:species_key?watershed=<slug>
 *                                    — editor: current photo, iNat candidates, save
 *
 * Gated by <AdminRoute>. Mobile-friendly layout (the admin may curate from
 * their phone). All writes go through PUT /admin/curated-photos/<species_key>
 * which writes an audit row in the same transaction.
 */
import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import useSWR from 'swr'
import { API_BASE } from '../config'
import './AdminPhotosPage.css'

const WATERSHEDS = [
  { value: '*',           label: 'Global default (all watersheds)' },
  { value: 'mckenzie',    label: 'McKenzie' },
  { value: 'deschutes',   label: 'Deschutes' },
  { value: 'metolius',    label: 'Metolius' },
  { value: 'klamath',     label: 'Klamath' },
  { value: 'johnday',     label: 'John Day' },
  { value: 'skagit',      label: 'Skagit' },
  { value: 'green_river', label: 'Green River' },
  { value: 'shenandoah',  label: 'Shenandoah' },
  { value: 'mad_river_oh', label: 'Mad River' },
  { value: 'ipswich_river_ma', label: 'Ipswich River' },
  { value: 'clinch_river_va', label: 'Clinch River' },
  { value: 'new_river_va', label: 'New River' },
  { value: 'chattahoochee', label: 'Chattahoochee River' },
]

function wsLabel(value: string): string {
  const found = WATERSHEDS.find(w => w.value === value)
  return found ? found.label : value
}

interface CuratedRow {
  species_key: string
  watershed: string
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
  /** Present only when the requested per-watershed row doesn't exist
   *  yet AND the species's global '*' row does. Used to pre-seed the
   *  editor so the iNat search button is immediately usable. */
  global_fallback: {
    common_name: string | null
    scientific_name: string | null
    photo_url: string | null
  } | null
  recent_changes: Array<{
    action: string
    prev_photo_url: string | null
    new_photo_url: string | null
    watershed: string
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

interface WatershedFish {
  species_key: string
  common_name: string
  scientific_name: string | null
  photo_url: string | null
  /** 'specific' = per-watershed override, 'global' = global default,
   *  'none' = automatic iNat/gallery fallback (not yet curated). */
  curated: 'specific' | 'global' | 'none'
}

/** Passed to the editor via router state so iNat search is usable
 *  immediately when no curated row exists yet for this fish. */
interface EditorSeed {
  scientificName?: string | null
  commonName?: string | null
  photoUrl?: string | null
}

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then(r => {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
})

export default function AdminPhotosPage() {
  const { species_key } = useParams<{ species_key: string }>()
  const [params] = useSearchParams()
  const watershed = params.get('watershed')
  if (species_key) {
    return <AdminPhotoEditor speciesKey={species_key} watershed={watershed || '*'} />
  }
  if (watershed) {
    return watershed === '*'
      ? <GlobalDefaultsList />
      : <WatershedFishList watershed={watershed} />
  }
  return <WatershedPicker />
}

// ─── Watershed picker (entry point) ────────────────────────────────

function WatershedPicker() {
  const targets = WATERSHEDS.filter(w => w.value !== '*')
  return (
    <div className="admin-page">
      <header className="admin-header">
        <h1>Fish photos by watershed</h1>
        <div className="admin-header-actions">
          <Link to="/admin/river-stories" className="admin-nav-link">→ River Stories</Link>
          <RevokeAdminButton />
        </div>
      </header>

      <p className="admin-hint" style={{ marginBottom: 16 }}>
        Pick a watershed to see the fish present there and their current
        images, then find and select replacements from iNaturalist.
      </p>

      <ul className="admin-grid">
        {targets.map(w => (
          <li key={w.value}>
            <Link to={`/admin/photos?watershed=${encodeURIComponent(w.value)}`} className="admin-card">
              <div className="admin-card-thumb admin-card-placeholder-thumb">
                <span className="admin-card-placeholder">🏞️</span>
              </div>
              <div className="admin-card-body">
                <div className="admin-card-name">{w.label}</div>
                <div className="admin-card-key">{w.value}</div>
              </div>
            </Link>
          </li>
        ))}
        <li>
          <Link to="/admin/photos?watershed=*" className="admin-card admin-card-add">
            <div className="admin-card-thumb admin-card-placeholder-thumb">
              <span className="admin-card-placeholder">🌐</span>
            </div>
            <div className="admin-card-body">
              <div className="admin-card-name">Global defaults</div>
              <div className="admin-card-key">applies to all watersheds</div>
            </div>
          </Link>
        </li>
      </ul>
    </div>
  )
}

// ─── Fish present in a watershed ───────────────────────────────────

function WatershedFishList({ watershed }: { watershed: string }) {
  const navigate = useNavigate()
  const { data, error } = useSWR<{ watershed: string; fish: WatershedFish[] }>(
    `${API_BASE}/admin/watersheds/${encodeURIComponent(watershed)}/fish`,
    fetcher,
  )
  const [filter, setFilter] = useState('')

  const fish = useMemo(() => {
    const list = data?.fish || []
    if (!filter.trim()) return list
    const q = filter.toLowerCase()
    return list.filter(f =>
      f.common_name.toLowerCase().includes(q)
      || (f.scientific_name || '').toLowerCase().includes(q))
  }, [data, filter])

  function openEditor(f: WatershedFish) {
    const seed: EditorSeed = {
      scientificName: f.scientific_name,
      commonName: f.common_name,
      photoUrl: f.photo_url,
    }
    navigate(
      `/admin/photos/${encodeURIComponent(f.species_key)}?watershed=${encodeURIComponent(watershed)}`,
      { state: seed },
    )
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <Link to="/admin/photos" className="admin-back">← All watersheds</Link>
        <h1>{wsLabel(watershed)}</h1>
        <RevokeAdminButton />
      </header>

      <div className="admin-scope-banner">
        <span className="admin-scope-chip specific">📍 {wsLabel(watershed)}</span>
        <span className="admin-inat-hint">
          Fish present in this watershed and their current images. Tap a fish
          to find/select a photo from iNaturalist.
        </span>
      </div>

      <div className="admin-toolbar">
        <input
          type="search"
          placeholder="Filter fish by name…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="admin-filter"
        />
      </div>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}
      {data && fish.length === 0 && (
        <div className="admin-empty">No fish found for this watershed.</div>
      )}

      <ul className="admin-grid">
        {fish.map(f => (
          <li key={f.species_key}>
            <button type="button" className="admin-card admin-card-button" onClick={() => openEditor(f)}>
              <div className="admin-card-thumb">
                {f.photo_url
                  ? <img src={f.photo_url} alt={f.common_name} loading="lazy" />
                  : <div className="admin-card-placeholder">🐟</div>}
              </div>
              <div className="admin-card-body">
                <div className="admin-card-name">{f.common_name}</div>
                {f.scientific_name && <div className="admin-card-sci">{f.scientific_name}</div>}
                <div className="admin-card-chips">
                  {f.curated === 'specific' && (
                    <span className="admin-scope-chip specific">📍 Custom photo</span>
                  )}
                  {f.curated === 'global' && (
                    <span className="admin-scope-chip global">🌐 Global default</span>
                  )}
                  {f.curated === 'none' && (
                    <span className="admin-source-chip">iNat auto</span>
                  )}
                </div>
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

// ─── Global default curated photos ─────────────────────────────────

function GlobalDefaultsList() {
  const navigate = useNavigate()
  const { data, error } = useSWR<CuratedRow[]>(`${API_BASE}/admin/curated-photos`, fetcher)
  const [filter, setFilter] = useState('')

  const rows = useMemo(() => {
    const list = (data || []).filter(r => r.watershed === '*')
    const q = filter.trim().toLowerCase()
    const filtered = q
      ? list.filter(r =>
          r.species_key.toLowerCase().includes(q)
          || (r.common_name || '').toLowerCase().includes(q))
      : list
    return filtered.slice().sort((a, b) => a.species_key.localeCompare(b.species_key))
  }, [data, filter])

  return (
    <div className="admin-page">
      <header className="admin-header">
        <Link to="/admin/photos" className="admin-back">← All watersheds</Link>
        <h1>Global defaults</h1>
        <div className="admin-header-actions">
          <button
            className="admin-add-btn"
            onClick={() => {
              const k = prompt('New species_key (lowercase, e.g. "lake trout"):')
              if (!k || !k.trim()) return
              navigate(`/admin/photos/${encodeURIComponent(k.trim().toLowerCase())}?watershed=*`)
            }}
          >+ Add species</button>
          <RevokeAdminButton />
        </div>
      </header>

      <div className="admin-scope-banner">
        <span className="admin-scope-chip global">🌐 Global default — applies to all watersheds</span>
      </div>

      <div className="admin-toolbar">
        <input
          type="search"
          placeholder="Filter by species key or name…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="admin-filter"
        />
      </div>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}
      {data && rows.length === 0 && <div className="admin-empty">No global defaults yet.</div>}

      <ul className="admin-grid">
        {rows.map(r => (
          <li key={r.species_key}>
            <Link
              to={`/admin/photos/${encodeURIComponent(r.species_key)}?watershed=*`}
              className="admin-card"
            >
              <div className="admin-card-thumb">
                {r.photo_url
                  ? <img src={r.photo_url} alt={r.common_name} loading="lazy" />
                  : <div className="admin-card-placeholder">🐟</div>}
              </div>
              <div className="admin-card-body">
                <div className="admin-card-name">{r.common_name}</div>
                {r.scientific_name && <div className="admin-card-sci">{r.scientific_name}</div>}
                <div className="admin-card-chips">
                  {r.source && <span className="admin-source-chip">{r.source}</span>}
                  {r.license && <span className="admin-license-chip">{r.license}</span>}
                </div>
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

function AdminPhotoEditor({ speciesKey, watershed }: { speciesKey: string; watershed: string }) {
  const navigate = useNavigate()
  const location = useLocation()
  const seed = (location.state as EditorSeed | null) || null
  const url = `${API_BASE}/admin/curated-photos/${encodeURIComponent(speciesKey)}?watershed=${encodeURIComponent(watershed)}`
  const { data, mutate, error } = useSWR<CuratedDetail>(url, fetcher)

  // Editable fields
  const [commonName, setCommonName] = useState('')
  const [scientificName, setScientificName] = useState('')
  const [photoUrl, setPhotoUrl] = useState('')
  const [selectedObs, setSelectedObs] = useState<InatCandidate | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [historyOpen, setHistoryOpen] = useState(false)

  // Seed inputs from server on first load. When the per-watershed row
  // doesn't exist yet but a global '*' row does, seed from the global
  // fallback so the iNat search button is immediately usable (and so
  // the user can save the global photo as the per-watershed default
  // by just clicking Save).
  useMemo(() => {
    if (!data?.species) return
    if (commonName !== '' || photoUrl !== '') return
    const sp = data.species
    const fb = data.global_fallback
    if (sp.exists) {
      setCommonName(sp.common_name || speciesKey)
      setScientificName(sp.scientific_name || '')
      setPhotoUrl(sp.photo_url || '')
    } else if (fb) {
      // Pre-seed from global default; iNat search now works immediately.
      setCommonName(fb.common_name || speciesKey)
      setScientificName(fb.scientific_name || '')
      setPhotoUrl(fb.photo_url || '')
    } else if (seed && (seed.scientificName || seed.commonName)) {
      // Arrived from the watershed fish list — seed the binomial and the
      // current (auto) photo so iNat search works immediately.
      setCommonName(seed.commonName || speciesKey)
      setScientificName(seed.scientificName || '')
      setPhotoUrl(seed.photoUrl || '')
    } else {
      // First-ever entry for this species (no global, no override).
      setCommonName(speciesKey)
    }
  }, [data, speciesKey, commonName, photoUrl, seed])

  // iNat search — pass the watershed so the proxy can filter to its bbox
  // (gives editorially-relevant candidates instead of generic global hits).
  // Proxy returns up to 50; the grid shows 12 per page.
  const inatUrl = scientificName.trim() && scientificName.includes(' ')
    ? `${API_BASE}/admin/inat/photos?scientific_name=${encodeURIComponent(scientificName.trim())}&watershed=${encodeURIComponent(watershed)}`
    : null
  const [searchEnabled, setSearchEnabled] = useState(false)
  const [inatPage, setInatPage] = useState(0)
  const { data: inatData, isLoading: inatLoading } = useSWR<{
    candidates: InatCandidate[]
    error?: string
    watershed?: string
  }>(
    searchEnabled ? inatUrl : null,
    fetcher,
    // Reset to page 0 whenever a new search returns.
    { onSuccess: () => setInatPage(0) },
  )

  const CANDIDATES_PER_PAGE = 12
  const allCandidates = inatData?.candidates || []
  const totalPages = Math.max(1, Math.ceil(allCandidates.length / CANDIDATES_PER_PAGE))
  const visibleCandidates = allCandidates.slice(
    inatPage * CANDIDATES_PER_PAGE,
    (inatPage + 1) * CANDIDATES_PER_PAGE,
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
      const target = watershed === '*'
        ? 'all watersheds'
        : `/path/now/${watershed}`
      setMsg(`Saved to ${target}. The public page caches Fish Present for 24h client-side — open it in a fresh tab or hard-refresh to see the new photo immediately.`)
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

  const sp = data.species
  const sourceLabel = sp.source || (selectedObs ? 'inaturalist' : 'manual')

  return (
    <div className="admin-page">
      <header className="admin-header">
        <Link
          to={watershed === '*' ? '/admin/photos?watershed=*' : `/admin/photos?watershed=${encodeURIComponent(watershed)}`}
          className="admin-back"
        >
          {watershed === '*' ? '← Global defaults' : `← ${wsLabel(watershed)} fish`}
        </Link>
        <h1>{commonName || speciesKey}</h1>
        <RevokeAdminButton />
      </header>

      <div className="admin-scope-banner">
        <span className={`admin-scope-chip ${watershed === '*' ? 'global' : 'specific'}`}>
          {watershed === '*' ? '🌐 Global default — applies to all watersheds' : `📍 ${wsLabel(watershed)} only`}
        </span>
        {watershed === '*' && (
          <SpecializeForWatershed speciesKey={speciesKey} />
        )}
        {watershed !== '*' && (
          <Link to={`/admin/photos/${encodeURIComponent(speciesKey)}?watershed=*`} className="admin-scope-link">
            View global default →
          </Link>
        )}
      </div>

      {!data.species.exists && data.global_fallback && (
        <div className="admin-prefill-hint">
          Pre-filled from the global default for <code>{speciesKey}</code>.
          Hit “Search iNat in {wsLabel(watershed)}” to find a locally-relevant
          photo, or just <strong>Save</strong> to use the global photo as this
          watershed's override.
        </div>
      )}
      {!data.species.exists && !data.global_fallback && (
        <div className="admin-prefill-hint">
          No global default for <code>{speciesKey}</code> yet — enter a binomial
          (e.g. <code>Salmo trutta</code>) below to enable iNat search.
        </div>
      )}

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
          <label>watershed scope
            <input type="text" value={watershed === '*' ? '* (global default)' : watershed} disabled />
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
          {sp.exists && (
            <div className="admin-meta-readout">
              <div><strong>Source:</strong> {sourceLabel}</div>
              {sp.inat_user_handle && <div><strong>Photographer:</strong> 📷 {sp.inat_user_handle}</div>}
              {sp.license && <div><strong>License:</strong> <code>{sp.license}</code></div>}
              {sp.updated_at && <div><strong>Last updated:</strong> {new Date(sp.updated_at).toLocaleString()}</div>}
            </div>
          )}
        </div>
      </section>

      <section className="admin-inat">
        <button
          type="button"
          className="admin-inat-search"
          onClick={() => setSearchEnabled(true)}
          disabled={!scientificName.trim() || !scientificName.includes(' ')}
        >
          {inatLoading
            ? 'Searching iNat…'
            : watershed === '*'
              ? 'Search iNat (global)'
              : `Search iNat in ${wsLabel(watershed)}`}
        </button>
        <span className="admin-inat-hint">
          {watershed === '*'
            ? 'Searches iNat worldwide — pick a photo that represents the species broadly.'
            : `Restricted to research-grade observations inside the ${wsLabel(watershed)} watershed bbox.`}
        </span>
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
        {allCandidates.length > 0 && (
          <>
            <div className="admin-candidates-meta">
              Showing {inatPage * CANDIDATES_PER_PAGE + 1}–
              {Math.min((inatPage + 1) * CANDIDATES_PER_PAGE, allCandidates.length)} of{' '}
              {allCandidates.length} candidates
            </div>
            <ul className="admin-candidates">
              {visibleCandidates.map(c => (
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
            {totalPages > 1 && (
              <div className="admin-candidates-pager">
                <button
                  type="button"
                  className="admin-candidates-pager-btn"
                  disabled={inatPage === 0}
                  onClick={() => setInatPage(p => Math.max(0, p - 1))}
                >← Prev</button>
                <span className="admin-candidates-pager-label">
                  Page {inatPage + 1} of {totalPages}
                </span>
                <button
                  type="button"
                  className="admin-candidates-pager-btn"
                  disabled={inatPage >= totalPages - 1}
                  onClick={() => setInatPage(p => Math.min(totalPages - 1, p + 1))}
                >Next →</button>
              </div>
            )}
          </>
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

// ─── Specialize-for-watershed dropdown (shown on the global editor) ──

function SpecializeForWatershed({ speciesKey }: { speciesKey: string }) {
  const navigate = useNavigate()
  const targets = WATERSHEDS.filter(w => w.value !== '*')
  function go(ws: string) {
    if (!ws) return
    navigate(`/admin/photos/${encodeURIComponent(speciesKey)}?watershed=${encodeURIComponent(ws)}`)
  }
  return (
    <span className="admin-specialize">
      <select
        defaultValue=""
        onChange={e => go(e.target.value)}
        className="admin-specialize-select"
        aria-label="Specialize this photo for a watershed"
      >
        <option value="" disabled>+ Specialize for a watershed…</option>
        {targets.map(t => (
          <option key={t.value} value={t.value}>{t.label}</option>
        ))}
      </select>
    </span>
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
