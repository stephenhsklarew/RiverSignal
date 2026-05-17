/**
 * /admin/river-stories                              — list grouped by watershed
 * /admin/river-stories/:watershed/:reading_level    — editor + regenerate audio
 *
 * v1 of the watershed admin console (per OF-1 of
 * plan-2026-05-17-watershed-admin-console.md).
 */
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import useSWR from 'swr'
import { API_BASE } from '../config'
import './AdminPhotosPage.css'
import './AdminRiverStoriesPage.css'

const WATERSHEDS: Record<string, string> = {
  mckenzie:    'McKenzie',
  deschutes:   'Deschutes',
  metolius:    'Metolius',
  klamath:     'Klamath',
  johnday:     'John Day',
  skagit:      'Skagit',
  green_river: 'Green River',
  shenandoah:  'Shenandoah',
}
const READING_LEVELS = ['kids', 'adult', 'expert'] as const

interface RiverStoryRow {
  watershed: string
  reading_level: string
  narrative: string | null
  narrative_length: number
  generated_at: string | null
  updated_at: string | null
  audio_url: string | null
  has_audio: boolean
}

interface RiverStoryDetail {
  story: RiverStoryRow & { exists: boolean }
  recent_changes: Array<{
    action: string
    prev_narrative: string | null
    new_narrative: string | null
    prev_audio_path: string | null
    new_audio_path: string | null
    changed_at: string | null
  }>
}

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then(r => {
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
})

export default function AdminRiverStoriesPage() {
  const { watershed, reading_level } = useParams<{ watershed: string; reading_level: string }>()
  return watershed && reading_level
    ? <RiverStoryEditor watershed={watershed} readingLevel={reading_level} />
    : <RiverStoriesList />
}

// ─── List view ─────────────────────────────────────────────────────

function RiverStoriesList() {
  const { data, error } = useSWR<RiverStoryRow[]>(`${API_BASE}/admin/river-stories`, fetcher)

  // Group by watershed (3 reading levels per row)
  const byWatershed: Record<string, Record<string, RiverStoryRow>> = {}
  for (const r of data || []) {
    (byWatershed[r.watershed] ||= {})[r.reading_level] = r
  }
  const orderedWs = Object.keys(byWatershed).sort()

  return (
    <div className="admin-page">
      <header className="admin-header">
        <h1>River Story narratives</h1>
        <div className="admin-header-actions">
          <Link to="/admin/photos" className="admin-nav-link">→ Photos</Link>
        </div>
      </header>
      <div className="admin-subhint">
        Edit the per-watershed × reading-level narrative shown on /path/now.
        Regenerate the OpenAI audio after a text change so playback matches the new copy.
      </div>

      {error && <div className="admin-error">Failed to load: {String(error)}</div>}
      {!data && !error && <div className="admin-empty">Loading…</div>}

      <div className="rs-list">
        {orderedWs.map(ws => (
          <section key={ws} className="rs-group">
            <header className="rs-group-header">
              <span className="rs-group-name">{WATERSHEDS[ws] || ws}</span>
              <span className="rs-group-key">{ws}</span>
            </header>
            <div className="rs-level-row">
              {READING_LEVELS.map(lvl => {
                const row = byWatershed[ws]?.[lvl]
                return (
                  <Link
                    key={lvl}
                    to={`/admin/river-stories/${encodeURIComponent(ws)}/${encodeURIComponent(lvl)}`}
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
          </section>
        ))}
      </div>
    </div>
  )
}

// ─── Editor view ───────────────────────────────────────────────────

function RiverStoryEditor({ watershed, readingLevel }: { watershed: string; readingLevel: string }) {
  const navigate = useNavigate()
  const url = `${API_BASE}/admin/river-stories/${encodeURIComponent(watershed)}/${encodeURIComponent(readingLevel)}`
  const { data, mutate, error } = useSWR<RiverStoryDetail>(url, fetcher)

  const [narrative, setNarrative] = useState('')
  const [seeded, setSeeded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [audioBusy, setAudioBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [historyOpen, setHistoryOpen] = useState(false)

  useEffect(() => {
    if (data?.story && !seeded) {
      setNarrative(data.story.narrative || '')
      setSeeded(true)
    }
  }, [data, seeded])

  async function save() {
    if (!narrative.trim()) {
      setMsg('Narrative cannot be empty.'); return
    }
    setBusy(true); setMsg(null)
    try {
      const r = await fetch(url, {
        method: 'PUT', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ narrative: narrative.trim() }),
      })
      if (!r.ok) throw new Error(`Save failed: ${r.status}`)
      await mutate()
      setMsg(`Saved. After text changes the audio is now stale — click "Regenerate audio" so playback on /path/now/${watershed} matches.`)
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`)
    } finally { setBusy(false) }
  }

  async function regenerate() {
    if (!confirm('Regenerate the OpenAI TTS audio for this narrative? This costs ~$0.015 per regeneration.')) return
    setAudioBusy(true); setMsg(null)
    try {
      const r = await fetch(`${url}/regenerate-audio`, {
        method: 'POST', credentials: 'include',
      })
      const body = await r.json()
      if (!r.ok) throw new Error(body.detail || `Regen failed: ${r.status}`)
      await mutate()
      setMsg(`Audio regenerated (${Math.round((body.audio_bytes || 0) / 1024)} KB).`)
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`)
    } finally { setAudioBusy(false) }
  }

  if (error) return <div className="admin-page"><div className="admin-error">Failed to load: {String(error)}</div></div>
  if (!data) return <div className="admin-page"><div className="admin-empty">Loading…</div></div>

  const sp = data.story
  const wsLabel = WATERSHEDS[watershed] || watershed
  const charCount = narrative.length
  const dirty = (data.story.narrative || '') !== narrative

  return (
    <div className="admin-page">
      <header className="admin-header">
        <Link to="/admin/river-stories" className="admin-back">← All stories</Link>
        <h1>{wsLabel} — {readingLevel}</h1>
        <div className="admin-header-actions">
          <Link to="/admin/photos" className="admin-nav-link">→ Photos</Link>
        </div>
      </header>

      <div className="rs-editor-meta">
        <span><strong>{charCount.toLocaleString()}</strong> chars{dirty ? ' (unsaved)' : ''}</span>
        {sp.updated_at && <span>Last updated {new Date(sp.updated_at).toLocaleString()}</span>}
      </div>

      <textarea
        className="rs-narrative"
        value={narrative}
        onChange={e => setNarrative(e.target.value)}
        placeholder="Write the river story narrative…"
        rows={16}
      />

      <section className="rs-audio">
        <h3 className="rs-audio-title">Audio (OpenAI tts-1, voice "nova")</h3>
        {sp.has_audio && sp.audio_url
          ? <audio controls src={sp.audio_url} className="rs-audio-player" />
          : <div className="admin-empty">No audio cached yet for this narrative.</div>}
        <button
          type="button"
          className="rs-regenerate"
          onClick={regenerate}
          disabled={audioBusy || !sp.exists || dirty}
          title={dirty ? 'Save the narrative first' : ''}
        >
          {audioBusy ? 'Regenerating…' : '🔁 Regenerate audio from current narrative'}
        </button>
        {dirty && <div className="admin-hint">Save the narrative first; the regenerate button uses the saved text, not the unsaved draft.</div>}
      </section>

      <div className="admin-actions">
        <button className="admin-save" disabled={busy || !narrative.trim() || !dirty} onClick={save}>
          {busy ? 'Saving…' : 'Save narrative'}
        </button>
        {msg && <span className="admin-msg">{msg}</span>}
      </div>

      <section className="admin-history">
        <button type="button" className="admin-history-toggle" onClick={() => setHistoryOpen(o => !o)}>
          {historyOpen ? '▾' : '▸'} Recent changes ({data.recent_changes.length})
        </button>
        {historyOpen && (
          <ul className="admin-history-list">
            {data.recent_changes.map((c, i) => (
              <li key={i}>
                <span className={`admin-history-action ${c.action.includes('audio') ? 'update' : 'insert'}`}>
                  {c.action}
                </span>
                <span className="admin-history-date">
                  {c.changed_at && new Date(c.changed_at).toLocaleString()}
                </span>
              </li>
            ))}
            {data.recent_changes.length === 0 && <li className="admin-empty">No changes yet.</li>}
          </ul>
        )}
      </section>
    </div>
  )
}
