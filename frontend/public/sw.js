// Service Worker for RiverPath (B2C) and DeepTrail (B2C) offline support
// Stale-while-revalidate for API data, cache-first for static assets

const CACHE_NAME = 'riversignal-v2'
const API_CACHE = 'riversignal-api-v2'
const API_BASE = '/api/v1/'
const MAX_API_CACHE_AGE = 24 * 60 * 60 * 1000 // 24 hours

// Static assets to pre-cache
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

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return

  // Cache.put() rejects non-GET requests — let POST/PUT/DELETE fall through to the
  // network without interception. (Was throwing on /river-oracle, /chat, /observations.)
  if (request.method !== 'GET') return

  // API requests: stale-while-revalidate
  if (url.pathname.startsWith(API_BASE)) {
    event.respondWith(
      caches.open(API_CACHE).then(async cache => {
        const cached = await cache.match(request)
        const fetchPromise = fetch(request).then(response => {
          if (response.ok) {
            cache.put(request, response.clone())
          }
          return response
        }).catch(() => cached) // Fallback to cache if offline

        return cached || fetchPromise
      })
    )
    return
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached
      return fetch(request).then(response => {
        if (response.ok && request.method === 'GET') {
          const clone = response.clone()
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone))
        }
        return response
      })
    })
  )
})
