import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Persists window scrollY in sessionStorage keyed by pathname+search and restores
 * it on subsequent mounts — e.g. after `navigate(-1)` from a detail page. React
 * Router's BrowserRouter doesn't restore scroll on its own when async content
 * means the page is too short at the moment history pops. Pass `ready=true` once
 * the page's primary content has rendered so restoration happens after layout.
 */
export function useScrollRestoration(ready: boolean) {
  const { pathname, search } = useLocation()
  const key = `riverpath-scroll:${pathname}${search}`
  const restored = useRef(false)

  useEffect(() => {
    if (!ready || restored.current) return
    restored.current = true
    const saved = sessionStorage.getItem(key)
    if (saved === null) return
    const y = parseInt(saved, 10)
    if (!Number.isFinite(y) || y <= 0) return
    requestAnimationFrame(() => window.scrollTo(0, y))
  }, [ready, key])

  useEffect(() => {
    let ticking = false
    const onScroll = () => {
      if (ticking) return
      ticking = true
      requestAnimationFrame(() => {
        sessionStorage.setItem(key, String(window.scrollY))
        ticking = false
      })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      sessionStorage.setItem(key, String(window.scrollY))
      window.removeEventListener('scroll', onScroll)
    }
  }, [key])
}
