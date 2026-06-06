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
import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import useSWR from 'swr'
import { API_BASE } from '../config'
import { SPLASH_PHOTOS, SPLASH_META } from '../lib/watershedSplash'
import './AdminPhotosPage.css'
import './AdminRiverStoriesPage.css'

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

interface WatershedInsect {
  species_key: string
  common_name: string
  scientific_name: string | null
  insect_order: string | null
  photo_url: string | null
  curated: 'specific' | 'global' | 'none'
}

/** Which curation table the photo editor/list targets:
 *  'fish'   → gold.curated_species_photos  (Fish Present)
 *  'insect' → gold.curated_insect_photos   (What Fish Are Eating Now) */
type PhotoKind = 'fish' | 'insect'

/** Tabs on the per-watershed view. 'story' edits the River Story narrative;
 *  'splash' edits the /path splash card image + description. */
type WatershedTab = PhotoKind | 'story' | 'splash'

const READING_LEVELS = ['kids', 'adult', 'expert'] as const

interface RiverStoryRow {
  watershed: string
  reading_level: string
  narrative: string | null
  narrative_length: number
  updated_at: string | null
  has_audio: boolean
}

/** Passed to the editor via router state so iNat search is usable
 *  immediately when no curated row exists yet for this item. */
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
  const typeParam = params.get('type')
  const tab: WatershedTab =
    typeParam === 'insect' ? 'insect'
    : typeParam === 'story' ? 'story'
    : typeParam === 'splash' ? 'splash'
    : 'fish'
  if (species_key) {
    // The photo editor only handles fish/insect; story has its own route.
    const kind: PhotoKind = tab === 'insect' ? 'insect' : 'fish'
    return <AdminPhotoEditor speciesKey={species_key} watershed={watershed || '*'} kind={kind} />
  }
  if (watershed) {
    return watershed === '*'
      ? <GlobalDefaultsList />
      : <WatershedView watershed={watershed} tab={tab} />
  }
  return <WatershedPicker />
}

// ─── Per-watershed view: Fish / Eating-Now / River Story tabs ──────

function WatershedView({ watershed, tab }: { watershed: string; tab: WatershedTab }) {
  const base = `/admin/photos?watershed=${encodeURIComponent(watershed)}`
  return (
    <div className="admin-page">
      <header className="admin-header">
        <Link to="/admin/photos" className="admin-back">← All watersheds</Link>
        <h1>{wsLabel(watershed)}</h1>
        <RevokeAdminButton />
      </header>

      <nav className="admin-tabs">
        <Link to={base} className={`admin-tab ${tab === 'fish' ? 'on' : ''}`}>🐟 Fish Present</Link>
        <Link to={`${base}&type=insect`} className={`admin-tab ${tab === 'insect' ? 'on' : ''}`}>🪰 What Fish Are Eating Now</Link>
        <Link to={`${base}&type=story`} className={`admin-tab ${tab === 'story' ? 'on' : ''}`}>📖 River Story</Link>
        <Link to={`${base}&type=splash`} className={`admin-tab ${tab === 'splash' ? 'on' : ''}`}>🖼️ Splash Card</Link>
      </nav>

      {tab === 'splash'
        ? <WatershedSplashEditor watershed={watershed} />
        : tab === 'story'
          ? <WatershedStoryList watershed={watershed} />
          : tab === 'insect'
            ? <WatershedInsectList watershed={watershed} />
            : <WatershedFishList watershed={watershed} />}
    </div>
  )
}

// ─── Watershed picker (entry point) ────────────────────────────────

function WatershedPicker() {
  const targets = WATERSHEDS.filter(w => w.value !== '*').slice().sort((a, b) => a.label.localeCompare(b.label))
  // Saved splash overrides win over the built-in defaults, so an uploaded
  // photo shows here too (not just on /path).
  const { data: splashData } = useSWR<{ overrides: { watershed: string; image_url: string | null }[] }>(
    `${API_BASE}/admin/watershed-splash`, fetcher)
  const overrideImg: Record<string, string> = {}
  for (const o of splashData?.overrides || []) {
    if (o.image_url) overrideImg[o.watershed] = o.image_url
  }
  return (
    <div className="admin-page">
      <header className="admin-header">
        <h1>Watershed admin</h1>
        <div className="admin-header-actions">
          <RevokeAdminButton />
        </div>
      </header>

      <p className="admin-hint" style={{ marginBottom: 16 }}>
        Pick a watershed, then manage its <strong>Fish Present</strong> photos,{' '}
        <strong>What Fish Are Eating Now</strong> photos, edit and record its{' '}
        <strong>River Story</strong> narrative, or set its <strong>Splash Card</strong>{' '}
        image and description.
      </p>

      <ul className="admin-grid">
        {targets.map(w => {
          const splash = overrideImg[w.value] || SPLASH_PHOTOS[w.value]
          return (
          <li key={w.value}>
            <Link to={`/admin/photos?watershed=${encodeURIComponent(w.value)}`} className="admin-card">
              <div className="admin-card-thumb">
                {splash
                  ? <img src={splash} alt={w.label} loading="lazy" />
                  : <div className="admin-card-placeholder">🏞️</div>}
              </div>
              <div className="admin-card-body">
                <div className="admin-card-name">{w.label}</div>
                <div className="admin-card-key">{w.value}</div>
              </div>
            </Link>
          </li>
          )
        })}
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
    <>
      <div className="admin-scope-banner">
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
    </>
  )
}

// ─── "What Fish Are Eating Now" prey in a watershed ────────────────

function WatershedInsectList({ watershed }: { watershed: string }) {
  const navigate = useNavigate()
  const { data, error } = useSWR<{ watershed: string; insects: WatershedInsect[] }>(
    `${API_BASE}/admin/watersheds/${encodeURIComponent(watershed)}/insects`,
    fetcher,
  )
  const [filter, setFilter] = useState('')

  const insects = useMemo(() => {
    const list = data?.insects || []
    if (!filter.trim()) return list
    const q = filter.toLowerCase()
    return list.filter(i =>
      i.common_name.toLowerCase().includes(q)
      || (i.scientific_name || '').toLowerCase().includes(q))
  }, [data, filter])

  function openEditor(i: WatershedInsect) {
    const seed: EditorSeed = {
      scientificName: i.scientific_name,
      commonName: i.common_name,
      photoUrl: i.photo_url,
    }
    navigate(
      `/admin/photos/${encodeURIComponent(i.species_key)}?watershed=${encodeURIComponent(watershed)}&type=insect`,
      { state: seed },
    )
  }

  return (
    <>
      <div className="admin-scope-banner">
        <span className="admin-inat-hint">
          Aquatic-insect &amp; prey items fish key on in this watershed (from the
          hatch chart). Tap one to find/select a photo from iNaturalist.
        </span>
      </div>

      <div className="admin-toolbar">
        <input
          type="search"
          placeholder="Filter prey by name…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="admin-filter"
        />
      </div>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}
      {data && insects.length === 0 && (
        <div className="admin-empty">
          No hatch-chart prey defined for this watershed yet.
        </div>
      )}

      <ul className="admin-grid">
        {insects.map(i => (
          <li key={i.species_key}>
            <button type="button" className="admin-card admin-card-button" onClick={() => openEditor(i)}>
              <div className="admin-card-thumb">
                {i.photo_url
                  ? <img src={i.photo_url} alt={i.common_name} loading="lazy" />
                  : <div className="admin-card-placeholder">🪰</div>}
              </div>
              <div className="admin-card-body">
                <div className="admin-card-name">{i.common_name}</div>
                {i.scientific_name && <div className="admin-card-sci">{i.scientific_name}</div>}
                <div className="admin-card-chips">
                  {i.curated === 'specific' && (
                    <span className="admin-scope-chip specific">📍 Custom photo</span>
                  )}
                  {i.curated === 'global' && (
                    <span className="admin-scope-chip global">🌐 Global default</span>
                  )}
                  {i.curated === 'none' && (
                    <span className="admin-source-chip">iNat auto</span>
                  )}
                  {i.insect_order && <span className="admin-source-chip">{i.insect_order}</span>}
                </div>
              </div>
            </button>
          </li>
        ))}
      </ul>
    </>
  )
}

// ─── River Story narratives for a watershed ────────────────────────

function WatershedStoryList({ watershed }: { watershed: string }) {
  const { data, error } = useSWR<RiverStoryRow[]>(`${API_BASE}/admin/river-stories`, fetcher)

  const byLevel = useMemo(() => {
    const m: Record<string, RiverStoryRow> = {}
    for (const r of (data || []).filter(r => r.watershed === watershed)) {
      m[r.reading_level] = r
    }
    return m
  }, [data, watershed])

  return (
    <>
      <div className="admin-scope-banner">
        <span className="admin-inat-hint">
          The /path/now narrative for each reading level. Open one to edit the
          text and (re)record the OpenAI audio.
        </span>
      </div>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}

      <div className="rs-level-row">
        {READING_LEVELS.map(lvl => {
          const row = byLevel[lvl]
          return (
            <Link
              key={lvl}
              to={`/admin/river-stories/${encodeURIComponent(watershed)}/${encodeURIComponent(lvl)}`}
              className={`rs-level-card ${row ? '' : 'rs-level-card-empty'}`}
            >
              <div className="rs-level-label">{lvl}</div>
              {row ? (
                <>
                  <div className="rs-level-meta">
                    {row.narrative_length.toLocaleString()} chars · {row.has_audio ? '🔊 audio' : '🔇 no audio'}
                  </div>
                  <div className="rs-level-snippet">
                    {(row.narrative || '').slice(0, 140)}…
                  </div>
                  {row.updated_at && (
                    <div className="rs-level-updated">
                      Updated {new Date(row.updated_at).toLocaleDateString()}
                    </div>
                  )}
                </>
              ) : (
                <div className="rs-level-empty">No narrative yet — open to write one.</div>
              )}
            </Link>
          )
        })}
      </div>
    </>
  )
}

// ─── Splash card editor (image + description on /path) ─────────────

interface SplashDetail {
  splash: {
    watershed: string
    image_url: string | null
    tagline: string | null
    narrative: string | null
    updated_at: string | null
    exists: boolean
  }
  recent_changes: Array<{
    action: string
    new_image_url: string | null
    new_tagline: string | null
    changed_at: string | null
  }>
}

function WatershedSplashEditor({ watershed }: { watershed: string }) {
  const url = `${API_BASE}/admin/watershed-splash/${encodeURIComponent(watershed)}`
  const { data, mutate, error } = useSWR<SplashDetail>(url, fetcher)

  const defImage = SPLASH_PHOTOS[watershed] || ''
  const defMeta = SPLASH_META[watershed] || { tagline: '', narrative: '' }

  const [imageUrl, setImageUrl] = useState('')
  const [tagline, setTagline] = useState('')
  const [narrative, setNarrative] = useState('')
  const [seeded, setSeeded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  // Seed from the saved override if present, otherwise from the built-in
  // defaults so the admin sees and can edit the current splash content.
  useEffect(() => {
    if (!data?.splash || seeded) return
    const sp = data.splash
    setImageUrl(sp.exists && sp.image_url ? sp.image_url : defImage)
    setTagline(sp.exists && sp.tagline != null ? sp.tagline : defMeta.tagline)
    setNarrative(sp.exists && sp.narrative != null ? sp.narrative : defMeta.narrative)
    setSeeded(true)
  }, [data, seeded, defImage, defMeta.tagline, defMeta.narrative])

  // Persist the override (image + text) to the DB.
  async function persist(img: string, tag: string, nar: string) {
    const r = await fetch(url, {
      method: 'PUT', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_url: img.trim() || null,
        tagline: tag.trim() || null,
        narrative: nar.trim() || null,
      }),
    })
    if (!r.ok) throw new Error(`Save failed: ${r.status}`)
    await mutate()
  }

  async function uploadImage(f: File) {
    setUploading(true); setMsg(null)
    try {
      const fd = new FormData()
      fd.append('file', f)
      const r = await fetch(`${url}/image`, { method: 'POST', credentials: 'include', body: fd })
      const body = await r.json()
      if (!r.ok) throw new Error(body.detail || `Upload failed: ${r.status}`)
      setImageUrl(body.image_url)
      // Auto-save so choosing a file persists immediately — no separate Save
      // click needed (which was easy to miss). Text edits still use Save.
      await persist(body.image_url, tagline, narrative)
      setMsg('Image uploaded and saved. The /path splash card updates on next load.')
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`)
    } finally { setUploading(false) }
  }

  async function save() {
    setBusy(true); setMsg(null)
    try {
      await persist(imageUrl, tagline, narrative)
      setMsg('Saved. The /path splash card shows the new image & text on next load.')
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`)
    } finally { setBusy(false) }
  }

  async function revert() {
    if (!confirm('Revert to the built-in default image and description for this watershed?')) return
    setBusy(true); setMsg(null)
    try {
      const r = await fetch(url, { method: 'DELETE', credentials: 'include' })
      if (!r.ok && r.status !== 404) throw new Error(`Revert failed: ${r.status}`)
      setImageUrl(defImage)
      setTagline(defMeta.tagline)
      setNarrative(defMeta.narrative)
      await mutate()
      setMsg('Reverted to the built-in default.')
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`)
    } finally { setBusy(false) }
  }

  return (
    <>
      <div className="admin-scope-banner">
        <span className="admin-inat-hint">
          The image and description shown for {wsLabel(watershed)} on the{' '}
          <code>/path</code> splash page. Replace the photo and edit the text,
          then Save.
        </span>
      </div>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}

      <section className="admin-current">
        <div className="admin-current-thumb">
          {imageUrl
            ? <img src={imageUrl} alt={wsLabel(watershed)} />
            : <div className="admin-current-placeholder">No image</div>}
        </div>
        <div className="admin-current-meta">
          <label>Upload a new image (JPG/PNG/WebP, max 8 MB)
            <input
              type="file"
              accept="image/*"
              disabled={uploading}
              onChange={e => { const f = e.target.files?.[0]; if (f) uploadImage(f) }}
            />
          </label>
          {uploading && <div className="admin-hint">Uploading…</div>}
          <label>Image URL (or paste any URL)
            <input type="url" value={imageUrl} onChange={e => setImageUrl(e.target.value)} />
          </label>
          <label>Tagline (short subtitle)
            <input
              type="text" value={tagline} maxLength={300}
              onChange={e => setTagline(e.target.value)}
              placeholder="Short subtitle shown under the name"
            />
          </label>
        </div>
      </section>

      <section className="admin-inat">
        <label className="admin-inat-hint" htmlFor="splash-narrative">Description (narrative)</label>
        <textarea
          id="splash-narrative"
          className="rs-narrative"
          value={narrative}
          onChange={e => setNarrative(e.target.value)}
          placeholder="The longer description shown on the splash card…"
          rows={10}
        />
      </section>

      <section className="admin-actions">
        <button className="admin-save" disabled={busy || uploading} onClick={save}>
          {busy ? 'Saving…' : 'Save'}
        </button>
        {data?.splash.exists && (
          <button className="admin-delete" disabled={busy} onClick={revert}>Revert to default</button>
        )}
        {msg && <span className="admin-msg">{msg}</span>}
      </section>

      {data && data.recent_changes.length > 0 && (
        <section className="admin-history">
          <ul className="admin-history-list">
            {data.recent_changes.map((c, i) => (
              <li key={i}>
                <span className={`admin-history-action ${c.action}`}>{c.action}</span>
                <span className="admin-history-date">
                  {c.changed_at && new Date(c.changed_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
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

function AdminPhotoEditor(
  { speciesKey, watershed, kind }: { speciesKey: string; watershed: string; kind: PhotoKind },
) {
  const navigate = useNavigate()
  const location = useLocation()
  const seed = (location.state as EditorSeed | null) || null
  const isInsect = kind === 'insect'
  const resource = isInsect ? 'curated-insect-photos' : 'curated-photos'
  const typeQ = isInsect ? '&type=insect' : ''
  // Where the back link / post-delete redirect returns to.
  const listUrl = watershed === '*'
    ? '/admin/photos?watershed=*'
    : `/admin/photos?watershed=${encodeURIComponent(watershed)}${typeQ}`
  const url = `${API_BASE}/admin/${resource}/${encodeURIComponent(speciesKey)}?watershed=${encodeURIComponent(watershed)}`
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
  // Proxy returns up to 50; the grid shows 12 per page. Fish require a
  // binomial; insects allow genus-only (hatch entries are often genus-level).
  const nameReady = isInsect ? scientificName.trim() !== '' : scientificName.includes(' ')
  const inatUrl = nameReady
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
      const feature = isInsect ? 'What Fish Are Eating Now' : 'Fish Present'
      setMsg(`Saved to ${target}. The public page caches ${feature} for 24h client-side — open it in a fresh tab or hard-refresh to see the new photo immediately.`)
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
      navigate(listUrl, { replace: true })
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
        <Link to={listUrl} className="admin-back">
          {watershed === '*'
            ? '← Global defaults'
            : `← ${wsLabel(watershed)} ${isInsect ? 'prey' : 'fish'}`}
        </Link>
        <h1>{commonName || speciesKey}</h1>
        <RevokeAdminButton />
      </header>

      <div className="admin-scope-banner">
        <span className={`admin-scope-chip ${watershed === '*' ? 'global' : 'specific'}`}>
          {watershed === '*' ? '🌐 Global default — applies to all watersheds' : `📍 ${wsLabel(watershed)} only`}
        </span>
        <span className="admin-source-chip">{isInsect ? '🪰 Fish food' : '🐟 Fish'}</span>
        {watershed === '*' && !isInsect && (
          <SpecializeForWatershed speciesKey={speciesKey} />
        )}
        {watershed !== '*' && (
          <Link
            to={`/admin/photos/${encodeURIComponent(speciesKey)}?watershed=*${typeQ}`}
            className="admin-scope-link"
          >
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
          No curated photo for <code>{speciesKey}</code> yet — enter a{' '}
          {isInsect ? 'genus or binomial' : 'binomial'} (e.g.{' '}
          <code>{isInsect ? 'Baetis' : 'Salmo trutta'}</code>) below to enable
          iNat search.
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
          <label>Scientific name ({isInsect ? 'genus or binomial' : 'binomial'})
            <input
              type="text" value={scientificName}
              onChange={e => setScientificName(e.target.value)}
              placeholder={isInsect ? 'Genus (or Genus species)' : 'Genus species'}
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
          disabled={!nameReady}
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
        {!nameReady && (
          <div className="admin-hint">
            Enter a {isInsect ? 'genus or binomial' : 'binomial (Genus species)'} above to search.
          </div>
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
            <Link
              to={`/admin/photos/${encodeURIComponent(speciesKey)}/history?watershed=${encodeURIComponent(watershed)}${typeQ}`}
              className="admin-full-history"
            >
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
  const targets = WATERSHEDS.filter(w => w.value !== '*').slice().sort((a, b) => a.label.localeCompare(b.label))
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
