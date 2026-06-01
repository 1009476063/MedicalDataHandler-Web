import { ref, reactive, onBeforeUnmount } from 'vue'
import type { ROILabel, ROILabelMap, ROIDrawTool } from '@/types'
import * as roiApi from '@/api/roi'
import axios from 'axios'

export function useROIDrawing() {
  // State
  const activeLabelMapId = ref<string | null>(null)
  const labelMap = ref<ROILabelMap | null>(null)
  const labels = ref<ROILabel[]>([])
  const activeLabel = ref(1)
  const activeTool = ref<ROIDrawTool>('paintbrush')
  const brushRadius = ref(5)
  const threshold = ref(30)
  const isDrawing = ref(false)
  const drawMode = ref(false)

  // Slice masks cache: `${orientation}-${sliceIndex}` → { labelId: mask2d }
  const sliceMasksCache = reactive(new Map<string, Record<number, number[][]>>())

  // Undo / redo
  const canUndo = ref(false)
  const canRedo = ref(false)

  // AI segmentation
  const aiSegLoading = ref(false)
  const aiSegProgress = ref(0)
  const aiSegMessage = ref('')

  let activeEventSource: EventSource | null = null
  let pollAbortController: AbortController | null = null

  function cacheKey(orientation: string, sliceIndex: number): string {
    return `${orientation}-${sliceIndex}`
  }

  async function createLabelMap(
    sessionId: string,
    patientId: string,
    seriesUid: string,
    name = 'ROI',
    defaultLabels?: Array<{ id: number; name: string; color: string; opacity?: number }>,
  ): Promise<string | null> {
    try {
      const result = await roiApi.createLabelMap({
        session_id: sessionId,
        patient_id: patientId,
        series_uid: seriesUid,
        name,
        labels: defaultLabels,
      })
      activeLabelMapId.value = result.id
      await loadLabelMap(result.id)
      return result.id
    } catch {
      return null
    }
  }

  async function loadLabelMap(labelMapId: string): Promise<void> {
    try {
      const data = await roiApi.getLabelMap(labelMapId)
      activeLabelMapId.value = labelMapId
      labelMap.value = data
      labels.value = (data.labels || []) as ROILabel[]
    } catch {
      labelMap.value = null
      labels.value = []
    }
  }

  async function loadSliceMasks(
    orientation: string,
    sliceIndex: number,
  ): Promise<Record<number, number[][]>> {
    if (!activeLabelMapId.value) return {}
    const key = cacheKey(orientation, sliceIndex)
    try {
      const result = await roiApi.getSliceAllMasks({
        label_map_id: activeLabelMapId.value,
        slice_index: sliceIndex,
        orientation,
      })
      const masks = (result.masks || {}) as Record<number, number[][]>
      sliceMasksCache.set(key, masks)
      return masks
    } catch {
      return {}
    }
  }

  function getCachedMasks(orientation: string, sliceIndex: number): Record<number, number[][]> {
    return sliceMasksCache.get(cacheKey(orientation, sliceIndex)) || {}
  }

  function invalidateCache(orientation?: string, sliceIndex?: number): void {
    if (orientation !== undefined && sliceIndex !== undefined) {
      sliceMasksCache.delete(cacheKey(orientation, sliceIndex))
    } else {
      sliceMasksCache.clear()
    }
  }

  async function paintStroke(
    orientation: string,
    sliceIndex: number,
    points: number[][],
    radius: number,
  ): Promise<void> {
    if (!activeLabelMapId.value) return
    try {
      await roiApi.paintStroke({
        label_map_id: activeLabelMapId.value,
        label: activeLabel.value,
        slice_index: sliceIndex,
        orientation,
        points,
        radius,
      })
      invalidateCache(orientation, sliceIndex)
      await refreshUndoRedoState()
    } catch { /* ignore */ }
  }

  async function fillShape(
    orientation: string,
    sliceIndex: number,
    shapeType: 'polygon' | 'rectangle' | 'ellipse',
    points: number[][],
  ): Promise<void> {
    if (!activeLabelMapId.value) return
    try {
      await roiApi.fillShape({
        label_map_id: activeLabelMapId.value,
        label: activeLabel.value,
        slice_index: sliceIndex,
        orientation,
        shape_type: shapeType,
        points,
      })
      invalidateCache(orientation, sliceIndex)
      await refreshUndoRedoState()
    } catch { /* ignore */ }
  }

  async function floodFill(
    orientation: string,
    sliceIndex: number,
    seedX: number,
    seedY: number,
    pixelData: number[][],
  ): Promise<void> {
    if (!activeLabelMapId.value) return
    try {
      await roiApi.magicWand({
        label_map_id: activeLabelMapId.value,
        label: activeLabel.value,
        slice_index: sliceIndex,
        orientation,
        seed_x: seedX,
        seed_y: seedY,
        pixel_data: pixelData,
        threshold: threshold.value,
      })
      invalidateCache(orientation, sliceIndex)
      await refreshUndoRedoState()
    } catch { /* ignore */ }
  }

  async function eraseAt(
    orientation: string,
    sliceIndex: number,
    points: number[][],
    radius: number,
  ): Promise<void> {
    if (!activeLabelMapId.value) return
    try {
      await roiApi.paintStroke({
        label_map_id: activeLabelMapId.value,
        label: 0,
        slice_index: sliceIndex,
        orientation,
        points,
        radius,
      })
      invalidateCache(orientation, sliceIndex)
      await refreshUndoRedoState()
    } catch { /* ignore */ }
  }

  async function erode(orientation?: string, sliceIndex?: number): Promise<void> {
    if (!activeLabelMapId.value) return
    try {
      await roiApi.erode(activeLabelMapId.value, activeLabel.value)
      if (orientation !== undefined && sliceIndex !== undefined) {
        invalidateCache(orientation, sliceIndex)
      } else {
        invalidateCache()
      }
      await refreshUndoRedoState()
    } catch { /* ignore */ }
  }

  async function dilate(orientation?: string, sliceIndex?: number): Promise<void> {
    if (!activeLabelMapId.value) return
    try {
      await roiApi.dilate(activeLabelMapId.value, activeLabel.value)
      if (orientation !== undefined && sliceIndex !== undefined) {
        invalidateCache(orientation, sliceIndex)
      } else {
        invalidateCache()
      }
      await refreshUndoRedoState()
    } catch { /* ignore */ }
  }

  async function smooth(orientation?: string, sliceIndex?: number): Promise<void> {
    if (!activeLabelMapId.value) return
    try {
      await roiApi.smooth(activeLabelMapId.value, activeLabel.value)
      if (orientation !== undefined && sliceIndex !== undefined) {
        invalidateCache(orientation, sliceIndex)
      } else {
        invalidateCache()
      }
      await refreshUndoRedoState()
    } catch { /* ignore */ }
  }

  async function undo(): Promise<boolean> {
    if (!activeLabelMapId.value) return false
    try {
      const result = await roiApi.undo(activeLabelMapId.value)
      invalidateCache()
      await refreshUndoRedoState()
      return result.success as boolean
    } catch {
      return false
    }
  }

  async function redo(): Promise<boolean> {
    if (!activeLabelMapId.value) return false
    try {
      const result = await roiApi.redo(activeLabelMapId.value)
      invalidateCache()
      await refreshUndoRedoState()
      return result.success as boolean
    } catch {
      return false
    }
  }

  async function refreshUndoRedoState(): Promise<void> {
    if (!labelMap.value || !activeLabelMapId.value) {
      canUndo.value = false
      canRedo.value = false
      return
    }
    try {
      const data = await roiApi.getLabelMap(activeLabelMapId.value)
      labelMap.value = data
    } catch {
      // keep previous state
    }
  }

  // --- AI Segmentation ---

  async function runAutoSegment(
    sessionId: string,
    patientId: string,
    seriesUid: string,
  ): Promise<void> {
    if (!activeLabelMapId.value) return
    aiSegLoading.value = true
    aiSegProgress.value = 0
    aiSegMessage.value = 'Starting auto-segmentation...'
    try {
      const res = await axios.post('/api/ai/segment/auto', {
        session_id: sessionId,
        patient_id: patientId,
        series_uid: seriesUid,
        label_map_id: activeLabelMapId.value,
        label: activeLabel.value,
      })
      const jobId = res.data?.data?.job_id
      if (jobId) {
        await streamAISegProgress(jobId)
      }
    } catch (err) {
      aiSegMessage.value = err instanceof Error ? err.message : 'AI segmentation failed'
    } finally {
      aiSegLoading.value = false
    }
  }

  async function runTextSegment(
    sessionId: string,
    patientId: string,
    seriesUid: string,
    textPrompt: string,
  ): Promise<void> {
    if (!activeLabelMapId.value) return
    aiSegLoading.value = true
    aiSegProgress.value = 0
    aiSegMessage.value = 'Starting text-guided segmentation...'
    try {
      const res = await axios.post('/api/ai/segment/text', {
        session_id: sessionId,
        patient_id: patientId,
        series_uid: seriesUid,
        text_prompt: textPrompt,
        label_map_id: activeLabelMapId.value,
        label: activeLabel.value,
      })
      const jobId = res.data?.data?.job_id
      if (jobId) {
        await streamAISegProgress(jobId)
      }
    } catch (err) {
      aiSegMessage.value = err instanceof Error ? err.message : 'AI segmentation failed'
    } finally {
      aiSegLoading.value = false
    }
  }

  async function runReferenceSegment(
    sessionId: string,
    patientId: string,
    seriesUid: string,
    refLabelMapId: string,
    refLabel: number,
  ): Promise<void> {
    if (!activeLabelMapId.value) return
    aiSegLoading.value = true
    aiSegProgress.value = 0
    aiSegMessage.value = 'Starting reference-guided segmentation...'
    try {
      const res = await axios.post('/api/ai/segment/reference', {
        session_id: sessionId,
        patient_id: patientId,
        series_uid: seriesUid,
        ref_label_map_id: refLabelMapId,
        ref_label: refLabel,
        label_map_id: activeLabelMapId.value,
        label: activeLabel.value,
      })
      const jobId = res.data?.data?.job_id
      if (jobId) {
        await streamAISegProgress(jobId)
      }
    } catch (err) {
      aiSegMessage.value = err instanceof Error ? err.message : 'AI segmentation failed'
    } finally {
      aiSegLoading.value = false
    }
  }

  function streamAISegProgress(jobId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(`/api/ai/jobs/${jobId}/stream`)
      activeEventSource = eventSource

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          aiSegProgress.value = data.progress || 0
          aiSegMessage.value = data.message || ''

          if (data.done) {
            eventSource.close()
            activeEventSource = null
            invalidateCache()
            if (data.error) {
              reject(new Error(data.message))
            } else {
              resolve()
            }
          }
        } catch {
          // Ignore parse errors
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        activeEventSource = null
        pollAISegResults(jobId).then(resolve).catch(reject)
      }
    })
  }

  async function pollAISegResults(jobId: string): Promise<void> {
    const maxAttempts = 60
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const res = await axios.get(`/api/ai/jobs/${jobId}`)
        const job = res.data?.data
        if (job) {
          aiSegProgress.value = job.progress || 0
          aiSegMessage.value = job.status === 'completed' ? 'Done' : `Status: ${job.status}`
          if (job.status === 'completed') {
            invalidateCache()
            return
          }
          if (job.status === 'failed') {
            throw new Error(job.error || 'AI segmentation failed')
          }
        }
      } catch (err) {
        if (err instanceof Error && err.message.includes('failed')) throw err
      }
      await new Promise((r) => setTimeout(r, 1000))
    }
  }

  // --- Label Management ---

  function addLabel(id: number, name: string, color: string, opacity = 0.4): void {
    if (!activeLabelMapId.value) return
    roiApi.addLabel(activeLabelMapId.value, id, name, color, opacity)
    labels.value = [...labels.value, { id, name, color, visible: true, opacity, locked: false }]
  }

  function removeLabel(id: number): void {
    if (!activeLabelMapId.value) return
    roiApi.removeLabel(activeLabelMapId.value, id)
    labels.value = labels.value.filter((l) => l.id !== id)
    if (activeLabel.value === id && labels.value.length > 0) {
      activeLabel.value = labels.value[0].id
    }
  }

  function renameLabel(id: number, name: string): void {
    if (!activeLabelMapId.value) return
    roiApi.renameLabel(activeLabelMapId.value, id, name)
    labels.value = labels.value.map((l) => (l.id === id ? { ...l, name } : l))
  }

  // --- Export ---

  async function exportNifti(): Promise<Blob | null> {
    if (!activeLabelMapId.value) return null
    try {
      const res = await roiApi.exportNifti({ label_map_id: activeLabelMapId.value })
      return res.data
    } catch {
      return null
    }
  }

  async function exportDicomSeg(
    patientId: string,
    studyUid: string,
    labelColors?: Array<{ id: number; name: string; color: number[] }>,
  ): Promise<Blob | null> {
    if (!activeLabelMapId.value) return null
    try {
      const colors = labelColors || labels.value.map((l) => ({
        id: l.id,
        name: l.name,
        color: hexToRgb(l.color),
      }))
      const res = await roiApi.exportDicomSeg({
        label_map_id: activeLabelMapId.value,
        patient_id: patientId,
        study_uid: studyUid,
        labels: colors,
      })
      return res.data
    } catch {
      return null
    }
  }

  function hexToRgb(hex: string): number[] {
    const h = hex.replace('#', '')
    return [
      parseInt(h.substring(0, 2), 16),
      parseInt(h.substring(2, 4), 16),
      parseInt(h.substring(4, 6), 16),
    ]
  }

  // --- Reset ---

  function reset(): void {
    activeEventSource?.close()
    activeEventSource = null
    pollAbortController?.abort()
    pollAbortController = null
    activeLabelMapId.value = null
    labelMap.value = null
    labels.value = []
    activeLabel.value = 1
    activeTool.value = 'paintbrush'
    brushRadius.value = 5
    threshold.value = 30
    isDrawing.value = false
    drawMode.value = false
    sliceMasksCache.clear()
    canUndo.value = false
    canRedo.value = false
    aiSegLoading.value = false
    aiSegProgress.value = 0
    aiSegMessage.value = ''
  }

  onBeforeUnmount(() => {
    activeEventSource?.close()
    pollAbortController?.abort()
  })

  return {
    // State
    activeLabelMapId,
    labelMap,
    labels,
    activeLabel,
    activeTool,
    brushRadius,
    threshold,
    isDrawing,
    drawMode,
    sliceMasksCache,
    canUndo,
    canRedo,
    aiSegLoading,
    aiSegProgress,
    aiSegMessage,

    // Operations
    createLabelMap,
    loadLabelMap,
    loadSliceMasks,
    getCachedMasks,
    invalidateCache,
    paintStroke,
    fillShape,
    floodFill,
    eraseAt,
    erode,
    dilate,
    smooth,
    undo,
    redo,
    addLabel,
    removeLabel,
    renameLabel,

    // AI
    runAutoSegment,
    runTextSegment,
    runReferenceSegment,

    // Export
    exportNifti,
    exportDicomSeg,

    // Reset
    reset,
  }
}
