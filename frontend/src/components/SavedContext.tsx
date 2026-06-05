import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'

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

export function SavedProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<SavedItem[]>(loadSaved)

  useEffect(() => {
    persistSaved(items)
  }, [items])

  const save = useCallback((item: Omit<SavedItem, 'savedAt'>) => {
    setItems(prev => {
      const existing = prev.findIndex(i => i.type === item.type && i.id === item.id)
      const entry: SavedItem = { ...item, savedAt: new Date().toISOString() }
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = entry
        return updated
      }
      if (prev.length >= MAX_ITEMS) return prev // at limit
      return [...prev, entry]
    })
  }, [])

  const unsave = useCallback((type: SavedItem['type'], id: string) => {
    setItems(prev => prev.filter(i => !(i.type === type && i.id === id)))
  }, [])

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
    setItems(prev => prev.map(i => {
      if (i.shared || i.expiresAt) { kept++; const { expiresAt, shared, ...rest } = i; void expiresAt; void shared; return rest as SavedItem }
      return i
    }))
    return kept
  }, [])

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
