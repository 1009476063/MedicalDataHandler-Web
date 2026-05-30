import { ref } from 'vue'

export interface CanvasAnnotation {
  uid: string
  toolName: 'Length' | 'Probe'
  points: { x: number; y: number }[]
  value?: number
  label?: string
}

export function useCanvasTools() {
  const activeTool = ref<'Length' | 'Probe' | null>(null)
  const annotations = ref<CanvasAnnotation[]>([])
  const currentPoints = ref<{ x: number; y: number }[]>([])

  function handleCanvasClick(x: number, y: number) {
    if (!activeTool.value) return

    currentPoints.value.push({ x, y })

    if (activeTool.value === 'Probe' || currentPoints.value.length === 2) {
      const ann: CanvasAnnotation = {
        uid: `canvas-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        toolName: activeTool.value,
        points: [...currentPoints.value],
      }
      annotations.value = [...annotations.value, ann]
      currentPoints.value = []
    }
  }

  function clearAnnotations() {
    annotations.value = []
    currentPoints.value = []
  }

  function removeAnnotation(uid: string) {
    annotations.value = annotations.value.filter(a => a.uid !== uid)
  }

  function setToolValue(uid: string, value: number) {
    annotations.value = annotations.value.map(a =>
      a.uid === uid ? { ...a, value } : a
    )
  }

  return {
    activeTool,
    annotations,
    currentPoints,
    handleCanvasClick,
    clearAnnotations,
    removeAnnotation,
    setToolValue,
  }
}
