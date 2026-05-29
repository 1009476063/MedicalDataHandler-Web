import { ref } from 'vue'
import { useAppStore } from '@/stores/app'
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
        color: segmentColor(segNum),
        opacity: 0.4,
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

function segmentColor(num: number): string {
  const colors = [
    '#ef4444', '#22c55e', '#3b82f6', '#f59e0b',
    '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
  ]
  return colors[(num - 1) % colors.length]
}
