/**
 * Warm the browser module cache for Cornerstone3D viewer chunks.
 * Uses dynamic import() during idle time so that when the user
 * navigates to /viewer, the modules are already downloaded.
 */

let prefetched = false

const VIEWER_MODULES = [
  () => import('@cornerstonejs/core'),
  () => import('@cornerstonejs/tools'),
  () => import('@cornerstonejs/streaming-image-volume-loader'),
]

export function prefetchViewerChunks() {
  if (prefetched) return
  prefetched = true

  const warmup = () => {
    for (const load of VIEWER_MODULES) {
      load().catch(() => {})
    }
  }

  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => { warmup() }, { timeout: 5000 })
  } else {
    setTimeout(warmup, 2000)
  }
}
