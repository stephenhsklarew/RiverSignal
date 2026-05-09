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
}

interface SavedContextValue {
  save: (item: Omit<SavedItem, 'savedAt'>) => void
  unsave: (type: SavedItem['type'], id: string) => void
  isSaved: (type: SavedItem['type'], id: string) => boolean
  listSaved: (type?: SavedItem['type']) => SavedItem[]
  countSaved: () => number
}

const STORAGE_KEY = 'riverpath-saved'
const MAX_ITEMS = 500

const SavedCtx = createContext<SavedContextValue | null>(null)

function loadSaved(): SavedItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
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

  const countSaved = useCallback(() => items.length, [items])

  return (
    <SavedCtx.Provider value={{ save, unsave, isSaved, listSaved, countSaved }}>
      {children}
    </SavedCtx.Provider>
  )
}

export function useSaved(): SavedContextValue {
  const ctx = useContext(SavedCtx)
  if (!ctx) throw new Error('useSaved must be used within SavedProvider')
  return ctx
}
