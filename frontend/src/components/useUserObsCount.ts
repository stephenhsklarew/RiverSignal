import { useEffect, useState } from 'react'
import { useAuth } from './AuthContext'
import { API_BASE } from '../config'

const cache = new Map<string, { count: number; ts: number }>()
const TTL_MS = 30_000

/** Notify subscribers when an entry changes — lets SavedPage seed the cache after its own fetch. */
const listeners = new Set<(ws: string) => void>()

export function setUserObsCount(watershed: string, count: number) {
  cache.set(watershed, { count, ts: Date.now() })
  listeners.forEach(fn => fn(watershed))
}

export function useUserObsCount(watershed: string): number {
  const { isLoggedIn } = useAuth()
  const [count, setCount] = useState(() => cache.get(watershed)?.count ?? 0)

  useEffect(() => {
    if (!isLoggedIn) { setCount(0); return }

    const cached = cache.get(watershed)
    if (cached && Date.now() - cached.ts < TTL_MS) {
      setCount(cached.count)
    } else {
      fetch(`${API_BASE}/observations/user?mine=true&watershed=${watershed}`, { credentials: 'include' })
        .then(r => r.json())
        .then(data => {
          const c = Array.isArray(data) ? data.length : 0
          cache.set(watershed, { count: c, ts: Date.now() })
          setCount(c)
        })
        .catch(() => {})
    }

    const onChange = (ws: string) => {
      if (ws === watershed) setCount(cache.get(ws)?.count ?? 0)
    }
    listeners.add(onChange)
    return () => { listeners.delete(onChange) }
  }, [watershed, isLoggedIn])

  return count
}
