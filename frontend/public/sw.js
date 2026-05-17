// Service Worker for RiverPath (B2C) and DeepTrail (B2C) offline support
//
// Strategy:
//   - HTML / navigations: network-first, cache fallback (HTML is mutable per deploy)
//   - Hashed assets under /assets/: cache-first (content-addressable, immutable)
//   - API requests: stale-while-revalidate
//   - Non-GET (POST/PUT/DELETE): pass through, never cache
//
// The previous version (v2) used cache-first for HTML, which meant a cached
// /path served stale index.html referencing asset hashes that no longer
// existed after a redeploy — blank page on mobile until cache cleared.

// Bump these strings whenever a deploy changes API response shape or
// content that active users would otherwise see as 'stale.' The
// activate handler below deletes any cache whose name doesn't match
// these constants, so changing the version forces an eviction on
// every active client at their next navigation. Last bump 2026-05-17:
// curated hatch photos changed and stale-while-revalidate was keeping
// users on the old Hendrickson/Sulphur images for a full cycle.
const CACHE_NAME = 'riversignal-v4'
const API_CACHE = 'riversignal-api-v4'
const API_BASE = '/api/v1/'

// Pre-cache HTML shells so first-load offline works. Network-first runtime
// strategy keeps them fresh; this is purely a cold-start fallback.
const PRECACHE = [
  '/',
  '/path',
  '/trail',
  '/favicon.svg',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME && k !== API_CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  if (url.origin !== self.location.origin) return

  // Cache.put() rejects non-GET requests — let POST/PUT/DELETE fall through.
  if (request.method !== 'GET') return

  // API: stale-while-revalidate (cached response served instantly, refreshed in background).
  if (url.pathname.startsWith(API_BASE)) {
    event.respondWith(
      caches.open(API_CACHE).then(async cache => {
        const cached = await cache.match(request)
        const fetchPromise = fetch(request).then(response => {
          if (response.ok) cache.put(request, response.clone())
          return response
        }).catch(() => cached)
        return cached || fetchPromise
      })
    )
    return
  }

  // Navigations / HTML: network-first. Always try the network so we get the
  // current build's index.html (with current asset hashes). Fall back to the
  // cache only when offline. Update the cache on every successful network hit.
  const isNavigation =
    request.mode === 'navigate' ||
    (request.headers.get('accept') || '').includes('text/html')

  if (isNavigation) {
    event.respondWith(
      fetch(request).then(response => {
        if (response.ok) {
          const clone = response.clone()
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone))
        }
        return response
      }).catch(() => caches.match(request).then(cached => cached || caches.match('/')))
    )
    return
  }

  // Hashed assets (/assets/*) and other static files: cache-first.
  // These URLs are content-addressable (Vite emits unique hashes per build),
  // so a cached entry is valid forever; a new hash is simply a new cache key.
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached
      return fetch(request).then(response => {
        if (response.ok) {
          const clone = response.clone()
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone))
        }
        return response
      })
    })
  )
})
