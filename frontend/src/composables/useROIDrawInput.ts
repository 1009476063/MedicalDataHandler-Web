import { ref } from 'vue'
import type { ROIDrawTool } from '@/types'

export interface DrawPoint {
  x: number
  y: number
}

export interface DrawInputCallbacks {
  onPaintStroke: (points: DrawPoint[], radius: number) => void
  onShapeFill: (shapeType: 'polygon' | 'rectangle' | 'ellipse', points: DrawPoint[]) => void
  onFloodFill: (x: number, y: number) => void
  onEraseStroke: (points: DrawPoint[], radius: number) => void
}

export function useROIDrawInput(callbacks: DrawInputCallbacks) {
  const activeTool = ref<ROIDrawTool>('paintbrush')
  const brushRadius = ref(5)
  const isDrawing = ref(false)
  const cursorX = ref(-1)
  const cursorY = ref(-1)

  // Current stroke points (paintbrush / eraser)
  const currentStrokePoints = ref<DrawPoint[]>([])

  // Polygon vertices
  const polygonPoints = ref<DrawPoint[]>([])

  // Rectangle corners
  const rectStart = ref<DrawPoint | null>(null)
  const rectEnd = ref<DrawPoint | null>(null)

  // Ellipse center and radius point
  const ellipseCenter = ref<DrawPoint | null>(null)
  const ellipseRadiusPoint = ref<DrawPoint | null>(null)

  function handleMouseDown(x: number, y: number): void {
    cursorX.value = x
    cursorY.value = y
    const point: DrawPoint = { x, y }

    switch (activeTool.value) {
      case 'paintbrush':
      case 'eraser':
        isDrawing.value = true
        currentStrokePoints.value = [point]
        break

      case 'polygon':
        // Add vertex (dblclick handled separately)
        polygonPoints.value = [...polygonPoints.value, point]
        break

      case 'rectangle':
        isDrawing.value = true
        rectStart.value = point
        rectEnd.value = point
        break

      case 'ellipse':
        isDrawing.value = true
        ellipseCenter.value = point
        ellipseRadiusPoint.value = point
        break

      case 'magic-wand':
        callbacks.onFloodFill(x, y)
        break
    }
  }

  function handleMouseMove(x: number, y: number): void {
    cursorX.value = x
    cursorY.value = y
    if (!isDrawing.value) return
    const point: DrawPoint = { x, y }

    switch (activeTool.value) {
      case 'paintbrush':
      case 'eraser':
        currentStrokePoints.value = [...currentStrokePoints.value, point]
        break

      case 'rectangle':
        rectEnd.value = point
        break

      case 'ellipse':
        ellipseRadiusPoint.value = point
        break
    }
  }

  function handleMouseUp(_x: number, _y: number): void {
    if (!isDrawing.value) return
    isDrawing.value = false

    switch (activeTool.value) {
      case 'paintbrush': {
        const points = currentStrokePoints.value
        if (points.length > 0) {
          callbacks.onPaintStroke(points, brushRadius.value)
        }
        currentStrokePoints.value = []
        break
      }

      case 'eraser': {
        const points = currentStrokePoints.value
        if (points.length > 0) {
          callbacks.onEraseStroke(points, brushRadius.value)
        }
        currentStrokePoints.value = []
        break
      }

      case 'rectangle': {
        const start = rectStart.value
        const end = rectEnd.value
        if (start && end) {
          const points = [start, end]
          callbacks.onShapeFill('rectangle', points)
        }
        rectStart.value = null
        rectEnd.value = null
        break
      }

      case 'ellipse': {
        const center = ellipseCenter.value
        const radiusPt = ellipseRadiusPoint.value
        if (center && radiusPt) {
          const points = [center, radiusPt]
          callbacks.onShapeFill('ellipse', points)
        }
        ellipseCenter.value = null
        ellipseRadiusPoint.value = null
        break
      }
    }
  }

  function handleDoubleClick(): void {
    if (activeTool.value === 'polygon' && polygonPoints.value.length >= 3) {
      callbacks.onShapeFill('polygon', [...polygonPoints.value])
    }
    polygonPoints.value = []
  }

  function getPreviewPoints(): DrawPoint[] {
    switch (activeTool.value) {
      case 'polygon':
        return polygonPoints.value
      case 'rectangle':
        if (rectStart.value && rectEnd.value) {
          return [rectStart.value, rectEnd.value]
        }
        return []
      case 'ellipse':
        if (ellipseCenter.value && ellipseRadiusPoint.value) {
          return [ellipseCenter.value, ellipseRadiusPoint.value]
        }
        return []
      default:
        return []
    }
  }

  function cancelCurrentAction(): void {
    isDrawing.value = false
    currentStrokePoints.value = []
    polygonPoints.value = []
    rectStart.value = null
    rectEnd.value = null
    ellipseCenter.value = null
    ellipseRadiusPoint.value = null
  }

  function setTool(tool: ROIDrawTool): void {
    cancelCurrentAction()
    activeTool.value = tool
  }

  return {
    activeTool,
    brushRadius,
    isDrawing,
    cursorX,
    cursorY,
    currentStrokePoints,
    polygonPoints,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleDoubleClick,
    getPreviewPoints,
    cancelCurrentAction,
    setTool,
  }
}
