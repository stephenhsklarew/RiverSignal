import { createContext, useContext, useState, useEffect, useRef, useCallback, type ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { API_BASE } from '../config'

export interface SavedItem {
  type: 'reach' | 'species' | 'fly' | 'recreation' | 'restoration' | 'fossil' | 'mineral' | 'rocksite' | 'observation'
  id: string
  watershed: string
  label: string
  sublabel?: string
  thumbnail?: string
  latitude?: number
  longitude?: number
  savedAt: string
  // Observation attribution carried through a share so the original photographer
  // and privacy are preserved on the recipient's copy (see SavedPage.handleShare).
  observer?: string
  source?: string
  observedAt?: string
  visibility?: string
  originObservationId?: string
  // Set on items received via a shared link: they auto-expire (24h) and show a
  // "shared with you" affordance until kept (see addShared / keepShared).
  expiresAt?: string
  shared?: boolean
}

interface SavedContextValue {
  save: (item: Omit<SavedItem, 'savedAt'>) => void
  unsave: (type: SavedItem['type'], id: string) => void
  isSaved: (type: SavedItem['type'], id: string) => boolean
  listSaved: (type?: SavedItem['type']) => SavedItem[]
  countSaved: (watershed?: string) => number
  /** Add items received from a shared link — flagged shared + expiring at expiresAt. */
  addShared: (items: Omit<SavedItem, 'savedAt'>[], expiresAt: string) => number
  /** Convert all shared/expiring items into permanent saves (called on sign-in). */
  keepShared: () => number
}

const STORAGE_KEY = 'riverpath-saved'
const MAX_ITEMS = 500

const SavedCtx = createContext<SavedContextValue | null>(null)

function loadSaved(): SavedItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    // Drop shared items whose 24h window has passed.
    const now = Date.now()
    return parsed.filter((i: SavedItem) => !i.expiresAt || new Date(i.expiresAt).getTime() > now)
  } catch {
    return []
  }
}

function persistSaved(items: SavedItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // QuotaExceededError — silently fail, items remain in state
  }
}

// ── Server sync (cross-device, when logged in) ──
// localStorage stays the local source of truth; server calls fail silently
// (mirrors AuthContext.syncSettings).
function toServerItem(i: SavedItem) {
  return {
    type: i.type, id: i.id, watershed: i.watershed,
    payload: {
      label: i.label, sublabel: i.sublabel, thumbnail: i.thumbnail,
      latitude: i.latitude, longitude: i.longitude,
      observer: i.observer, source: i.source, observedAt: i.observedAt,
      visibility: i.visibility, originObservationId: i.originObservationId,
    },
  }
}

function fromServerItem(d: any): SavedItem {
  return {
    type: d.type, id: d.id, watershed: d.watershed || 'other',
    label: d.label || d.id, sublabel: d.sublabel, thumbnail: d.thumbnail,
    latitude: d.latitude, longitude: d.longitude,
    observer: d.observer, source: d.source, observedAt: d.observedAt,
    visibility: d.visibility, originObservationId: d.originObservationId,
    savedAt: d.savedAt || new Date().toISOString(),
  }
}

function serverUpsert(items: SavedItem[]) {
  if (!items.length) return
  fetch(`${API_BASE}/saved/items`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
    body: JSON.stringify({ items: items.map(toServerItem) }),
  }).catch(() => {})
}

function serverDelete(type: string, id: string) {
  fetch(`${API_BASE}/saved/items/${encodeURIComponent(type)}/${encodeURIComponent(id)}`,
    { method: 'DELETE', credentials: 'include' }).catch(() => {})
}

/** Union by type+id; signed-in → everything becomes permanent (drop shared/expiry). */
function mergePermanent(local: SavedItem[], server: SavedItem[]): SavedItem[] {
  const map = new Map<string, SavedItem>()
  for (const it of [...server, ...local]) {
    const { expiresAt: _e, shared: _s, ...rest } = it
    void _e; void _s
    map.set(`${it.type}:${it.id}`, rest as SavedItem)
  }
  return [...map.values()]
}

export function SavedProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<SavedItem[]>(loadSaved)
  const { isLoggedIn } = useAuth()
  const itemsRef = useRef(items)
  itemsRef.current = items

  useEffect(() => {
    persistSaved(items)
  }, [items])

  // On login: push local items up, then pull the account's items and merge in.
  // Runs once per logged-in session — this is what makes Saved cross-device.
  const syncedRef = useRef(false)
  useEffect(() => {
    if (!isLoggedIn) { syncedRef.current = false; return }
    if (syncedRef.current) return
    syncedRef.current = true
    ;(async () => {
      try {
        serverUpsert(itemsRef.current)
        const res = await fetch(`${API_BASE}/saved/items`, { credentials: 'include' })
        if (!res.ok) return
        const data = await res.json()
        const serverItems: SavedItem[] = (data.items || []).map(fromServerItem)
        setItems(prev => mergePermanent(prev, serverItems))
      } catch { /* offline — localStorage remains source of truth */ }
    })()
  }, [isLoggedIn])

  const save = useCallback((item: Omit<SavedItem, 'savedAt'>) => {
    const entry: SavedItem = { ...item, savedAt: new Date().toISOString() }
    setItems(prev => {
      const existing = prev.findIndex(i => i.type === item.type && i.id === item.id)
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = entry
        return updated
      }
      if (prev.length >= MAX_ITEMS) return prev // at limit
      return [...prev, entry]
    })
    if (isLoggedIn) serverUpsert([entry])
  }, [isLoggedIn])

  const unsave = useCallback((type: SavedItem['type'], id: string) => {
    setItems(prev => prev.filter(i => !(i.type === type && i.id === id)))
    if (isLoggedIn) serverDelete(type, id)
  }, [isLoggedIn])

  const isSaved = useCallback((type: SavedItem['type'], id: string) => {
    return items.some(i => i.type === type && i.id === id)
  }, [items])

  const listSaved = useCallback((type?: SavedItem['type']) => {
    return type ? items.filter(i => i.type === type) : items
  }, [items])

  const countSaved = useCallback((watershed?: string) => {
    if (!watershed) return items.length
    return items.filter(i => (i.watershed || 'other') === watershed).length
  }, [items])

  const addShared = useCallback((incoming: Omit<SavedItem, 'savedAt'>[], expiresAt: string) => {
    let added = 0
    setItems(prev => {
      const next = [...prev]
      for (const it of incoming) {
        if (next.length >= MAX_ITEMS) break
        const existing = next.findIndex(i => i.type === it.type && i.id === it.id)
        if (existing >= 0) continue // already saved (keep the user's own copy)
        next.push({ ...it, savedAt: new Date().toISOString(), expiresAt, shared: true })
        added++
      }
      return next
    })
    return added
  }, [])

  const keepShared = useCallback(() => {
    let kept = 0
    const keptItems: SavedItem[] = []
    setItems(prev => prev.map(i => {
      if (i.shared || i.expiresAt) {
        kept++
        const { expiresAt, shared, ...rest } = i; void expiresAt; void shared
        keptItems.push(rest as SavedItem)
        return rest as SavedItem
      }
      return i
    }))
    if (isLoggedIn) serverUpsert(keptItems)
    return kept
  }, [isLoggedIn])

  return (
    <SavedCtx.Provider value={{ save, unsave, isSaved, listSaved, countSaved, addShared, keepShared }}>
      {children}
    </SavedCtx.Provider>
  )
}

export function useSaved(): SavedContextValue {
  const ctx = useContext(SavedCtx)
  if (!ctx) throw new Error('useSaved must be used within SavedProvider')
  return ctx
}
