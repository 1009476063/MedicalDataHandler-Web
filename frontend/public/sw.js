/**
 * Service Worker for MedVista.
 * Caches slice binary responses for offline/fast repeat access.
 * Uses request body hash as cache key for POST requests.
 */

const CACHE_NAME = 'medvista-slices-v1'
const SLICE_CACHE_URLS = /\/api\/slice-binary|\/api\/slice$/

// Hash the POST body to create a unique cache key per request body
async function hashBody(body) {
  const buffer = await body.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

// Install: activate immediately
self.addEventListener('install', (event) => {
  self.skipWaiting()
})

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  )
  self.clients.claim()
})

// Fetch: cache slice responses, pass through everything else
self.addEventListener('fetch', (event) => {
  const { request } = event

  // Only cache POST requests to slice endpoints
  if (request.method !== 'POST' || !SLICE_CACHE_URLS.test(request.url)) {
    return
  }

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      // Read the body once so we can both hash it and forward it
      const bodyClone = request.clone()
      const body = await bodyClone.arrayBuffer()

      // Create a unique cache key using URL + body hash
      const bodyHash = await crypto.subtle.digest('SHA-256', body)
      const hashHex = Array.from(new Uint8Array(bodyHash))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('')
      const cacheKey = new Request(request.url + '#' + hashHex, {
        method: 'GET',
        headers: request.headers,
      })

      // Check cache first
      const cached = await cache.match(cacheKey)
      if (cached) {
        return cached
      }

      // Fetch from network and cache the response
      try {
        const response = await fetch(request)
        if (response.ok) {
          // Clone before caching (response body can only be consumed once)
          cache.put(cacheKey, response.clone())
        }
        return response
      } catch (err) {
        // Network failed, no cache available
        return new Response('Offline', { status: 503 })
      }
    })
  )
})
