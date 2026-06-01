import { ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { useSettings } from './useSettings'
import type { SegFile, SegMask } from '@/types'

export interface SegOverlay {
  fileId: string
  segmentNumber: number
  label: string
  color: string
  opacity: number
  visible: boolean
}

export function useSegmentation() {
  const appStore = useAppStore()
  const { segmentOpacity: defaultSegmentOpacity, defaultSegmentPalette } = useSettings()
  const segFiles = ref<SegFile[]>([])
  const overlays = ref<SegOverlay[]>([])
  const loading = ref(false)
  const error = ref('')

  async function fetchSegFiles() {
    if (!appStore.sessionId || !appStore.selectedPatientId) return
    loading.value = true
    error.value = ''
    try {
      segFiles.value = await appStore.getSegFiles()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load segments'
    } finally {
      loading.value = false
    }
  }

  function toggleOverlay(segFile: SegFile, segNum: number, label: string) {
    const key = `${segFile.file_id}_${segNum}`
    const existing = overlays.value.find(o => `${o.fileId}_${o.segmentNumber}` === key)
    if (existing) {
      existing.visible = !existing.visible
    } else {
      overlays.value.push({
        fileId: segFile.file_id,
        segmentNumber: segNum,
        label,
        color: segmentColor(segNum, defaultSegmentPalette.value),
        opacity: defaultSegmentOpacity.value,
        visible: true,
      })
    }
  }

  function updateOpacity(segFileId: string, segNum: number, opacity: number) {
    const overlay = overlays.value.find(
      o => o.fileId === segFileId && o.segmentNumber === segNum,
    )
    if (overlay) overlay.opacity = opacity
  }

  function removeOverlay(segFileId: string, segNum: number) {
    overlays.value = overlays.value.filter(
      o => !(o.fileId === segFileId && o.segmentNumber === segNum),
    )
  }

  function clearOverlays() {
    overlays.value = []
  }

  async function fetchMask(fileId: string, segmentNumber: number): Promise<SegMask | null> {
    return await appStore.getSegMask(fileId, segmentNumber)
  }

  const activeOverlays = () => overlays.value.filter(o => o.visible)

  return {
    segFiles,
    overlays,
    loading,
    error,
    fetchSegFiles,
    toggleOverlay,
    updateOpacity,
    removeOverlay,
    clearOverlays,
    fetchMask,
    activeOverlays,
  }
}

const PALETTES: Record<string, string[]> = {
  vivid: ['#ef4444', '#22c55e', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'],
  pastel: ['#fca5a5', '#86efac', '#93c5fd', '#fcd34d', '#c4b5fd', '#f9a8d4', '#67e8f9', '#fdba74'],
  highContrast: ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#ff8000', '#8000ff'],
}

function segmentColor(num: number, palette = 'vivid'): string {
  const colors = PALETTES[palette] || PALETTES.vivid
  return colors[(num - 1) % colors.length]
}
