import type { SeriesInfo } from '@/types'
import { getSeriesMetadata } from '@/composables/useClientMode'

/** Build SeriesInfo from client-side metadata when no backend is available. */
export function buildClientSeriesInfo(meta: Record<string, unknown>[], length: number): SeriesInfo | null {
  if (meta.length === 0) return null
  const first = meta[0]
  const rows = (first.rows as number) || 0
  const cols = (first.columns as number) || 0
  const spacing = (first.pixelSpacing as number[]) || [1, 1]
  const wc = (first.windowCenter as number) || 0
  const ww = (first.windowWidth as number) || 400
  return {
    shape: [length, rows, cols],
    spacing: [spacing[0] || 1, spacing[1] || 1, 1],
    origin: (first.imagePositionPatient as number[]) || [0, 0, 0],
    min: wc - ww / 2,
    max: wc + ww / 2,
    mean: wc,
  } as SeriesInfo
}
