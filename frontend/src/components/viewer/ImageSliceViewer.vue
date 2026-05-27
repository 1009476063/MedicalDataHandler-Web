<template>
  <div
    class="relative bg-black rounded-xl overflow-hidden border border-accent-700"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @mouseleave="onMouseUp"
    @wheel.prevent="onWheel"
    @dblclick="resetView"
  >
    <canvas ref="canvas" class="w-full h-full block" />

    <!-- Orientation Labels -->
    <template v-if="showOrientationLabels">
      <span class="absolute text-xs font-bold pointer-events-none select-none" :style="orientationLabelStyle('top')">
        {{ orientationLabels.top }}
      </span>
      <span class="absolute text-xs font-bold pointer-events-none select-none" :style="orientationLabelStyle('bottom')">
        {{ orientationLabels.bottom }}
      </span>
      <span class="absolute text-xs font-bold pointer-events-none select-none" :style="orientationLabelStyle('left')">
        {{ orientationLabels.left }}
      </span>
      <span class="absolute text-xs font-bold pointer-events-none select-none" :style="orientationLabelStyle('right')">
        {{ orientationLabels.right }}
      </span>
    </template>

    <div class="absolute top-2 left-2 space-y-1">
      <div class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        {{ label }} · Slice {{ sliceIndex }}/{{ maxSlice }}
      </div>
      <div v-if="windowCenter !== null" class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        W: {{ windowWidth }} L: {{ windowCenter }}
      </div>
      <div v-if="zoomLevel !== 1" class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        {{ Math.round(zoomLevel * 100) }}%
      </div>
      <div v-if="rotation !== 0" class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        {{ rotation }}°{{ flipH ? ' H' : '' }}{{ flipV ? ' V' : '' }}
      </div>
    </div>

    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-black/40">
      <LoadingSpinner size="md" text="" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

export interface OverlayData {
  mask: number[][] | number[][][] | null
  color: string
  opacity: number
  name?: string
  thickness?: number
}

const props = withDefaults(defineProps<{
  pixelData: number[][] | null
  width: number
  height: number
  label: string
  sliceIndex: number
  maxSlice: number
  windowCenter: number | null
  windowWidth: number | null
  loading: boolean
  overlays?: OverlayData[]
  rotation?: number
  flipH?: boolean
  flipV?: boolean
  showOrientationLabels?: boolean
  orientationLabelColor?: string
  crosshairX?: number | null
  crosshairY?: number | null
  zoomSpeed?: number
  panSpeed?: number
}>(), {
  overlays: () => [],
  rotation: 0,
  flipH: false,
  flipV: false,
  showOrientationLabels: true,
  orientationLabelColor: '#00ff00',
  crosshairX: null,
  crosshairY: null,
  zoomSpeed: 0.1,
  panSpeed: 1,
})

const emit = defineEmits<{
  'slice-change': [delta: number]
  'window-change': [center: number, width: number]
  'zoom-change': [zoom: number]
  'crosshair-move': [x: number, y: number]
  'reset-view': []
}>()

const canvas = ref<HTMLCanvasElement>()
let ctx: CanvasRenderingContext2D | null = null
let isDragging = false
let lastX = 0
let lastY = 0

// Zoom and pan state
const zoomLevel = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = false

const orientationLabels = computed(() => {
  const map: Record<string, { top: string; bottom: string; left: string; right: string }> = {
    axial: { top: 'A', bottom: 'P', left: 'R', right: 'L' },
    sagittal: { top: 'A', bottom: 'P', left: 'S', right: 'I' },
    coronal: { top: 'S', bottom: 'I', left: 'R', right: 'L' },
  }
  return map[props.label.toLowerCase()] || map.axial
})

function orientationLabelStyle(position: string) {
  const color = props.orientationLabelColor
  const base = `color: ${color}; text-shadow: 0 0 4px rgba(0,0,0,0.9), 0 0 8px rgba(0,0,0,0.7);`
  switch (position) {
    case 'top': return `${base} top: 8px; left: 50%; transform: translateX(-50%);`
    case 'bottom': return `${base} bottom: 8px; left: 50%; transform: translateX(-50%);`
    case 'left': return `${base} top: 50%; left: 8px; transform: translateY(-50%);`
    case 'right': return `${base} top: 50%; right: 8px; transform: translateY(-50%);`
    default: return base
  }
}

onMounted(() => {
  if (canvas.value) {
    ctx = canvas.value.getContext('2d')
    resizeCanvas()
  }
})

onBeforeUnmount(() => {
  // cleanup
})

watch(
  () => [props.width, props.height],
  () => resizeCanvas()
)

watch(
  () => props.pixelData,
  () => renderSlice()
)

watch(
  () => [props.windowCenter, props.windowWidth],
  () => renderSlice()
)

watch(
  () => [props.overlays, props.rotation, props.flipH, props.flipV],
  () => renderSlice(),
  { deep: true }
)

function resizeCanvas() {
  if (!canvas.value) return
  const parent = canvas.value.parentElement
  if (!parent) return
  canvas.value.width = parent.clientWidth
  canvas.value.height = parent.clientHeight
  renderSlice()
}

function renderSlice() {
  if (!ctx || !canvas.value || !props.pixelData) return

  const cw = canvas.value.width
  const ch = canvas.value.height
  ctx.clearRect(0, 0, cw, ch)

  ctx.save()

  // Apply zoom and pan transforms
  const cx = cw / 2
  const cy = ch / 2
  ctx.translate(cx + panX.value, cy + panY.value)
  ctx.scale(zoomLevel.value, zoomLevel.value)
  ctx.translate(-cx, -cy)

  // Apply rotation and flip transforms
  ctx.translate(cx, cy)
  ctx.rotate((props.rotation * Math.PI) / 180)
  ctx.scale(props.flipH ? -1 : 1, props.flipV ? -1 : 1)
  ctx.translate(-cx, -cy)

  // Draw base image
  const data = props.pixelData
  const rows = data.length
  const cols = data[0]?.length || 0
  if (!rows || !cols) {
    ctx.restore()
    return
  }

  const wc = props.windowCenter ?? 0
  const ww = props.windowWidth ?? 1
  const lower = wc - ww / 2
  const upper = wc + ww / 2

  const imageData = ctx.createImageData(cols, rows)
  const pixels = imageData.data

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const val = data[r][c]
      let normalized = (val - lower) / (upper - lower)
      normalized = Math.max(0, Math.min(1, normalized))
      const gray = Math.round(normalized * 255)
      const idx = (r * cols + c) * 4
      pixels[idx] = gray
      pixels[idx + 1] = gray
      pixels[idx + 2] = gray
      pixels[idx + 3] = 255
    }
  }

  const offscreen = document.createElement('canvas')
  offscreen.width = cols
  offscreen.height = rows
  const offCtx = offscreen.getContext('2d')!
  offCtx.putImageData(imageData, 0, 0)

  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(offscreen, 0, 0, cw, ch)

  // Draw overlays
  for (const overlay of props.overlays) {
    if (!overlay.mask) continue
    drawOverlay(ctx, overlay, rows, cols, cw, ch)
  }

  ctx.restore()

  // Draw crosshairs (outside zoom/pan transform for screen-space positioning)
  if (props.crosshairX !== null && props.crosshairY !== null) {
    drawCrosshair(ctx, cw, ch)
  }
}

function drawCrosshair(ctx: CanvasRenderingContext2D, cw: number, ch: number) {
  const x = props.crosshairX!
  const y = props.crosshairY!
  if (x < 0 || y < 0 || x > cw || y > ch) return

  ctx.save()
  ctx.strokeStyle = 'rgba(0, 255, 0, 0.7)'
  ctx.lineWidth = 1
  ctx.setLineDash([4, 4])

  // Vertical line
  ctx.beginPath()
  ctx.moveTo(x, 0)
  ctx.lineTo(x, ch)
  ctx.stroke()

  // Horizontal line
  ctx.beginPath()
  ctx.moveTo(0, y)
  ctx.lineTo(cw, y)
  ctx.stroke()

  // Center circle
  ctx.setLineDash([])
  ctx.beginPath()
  ctx.arc(x, y, 6, 0, Math.PI * 2)
  ctx.stroke()

  ctx.restore()
}

function drawOverlay(
  ctx: CanvasRenderingContext2D,
  overlay: OverlayData,
  imgRows: number,
  imgCols: number,
  canvasW: number,
  canvasH: number
) {
  const mask = overlay.mask
  if (!mask || mask.length === 0) return

  // Parse color
  const color = parseColor(overlay.color)
  const alpha = Math.round(overlay.opacity * 255)

  const maskRows = mask.length
  const maskCols = (mask[0] as number[]).length
  const thickness = overlay.thickness ?? 0

  const overlayCanvas = document.createElement('canvas')
  overlayCanvas.width = maskCols
  overlayCanvas.height = maskRows
  const overlayCtx = overlayCanvas.getContext('2d')!
  const overlayImageData = overlayCtx.createImageData(maskCols, maskRows)
  const overlayPixels = overlayImageData.data

  if (thickness > 0) {
    // Contour mode: draw only border pixels (edge detection)
    for (let r = 0; r < maskRows; r++) {
      const row = mask[r] as number[]
      for (let c = 0; c < maskCols; c++) {
        if (row[c] > 0) {
          // Check if this is a border pixel (has at least one non-mask neighbor)
          let isBorder = false
          if (r === 0 || r === maskRows - 1 || c === 0 || c === maskCols - 1) {
            isBorder = true
          } else {
            const prev = mask[r - 1] as number[]
            const next = mask[r + 1] as number[]
            if (prev[c] === 0 || next[c] === 0 || row[c - 1] === 0 || row[c + 1] === 0) {
              isBorder = true
            }
          }
          if (isBorder) {
            const idx = (r * maskCols + c) * 4
            overlayPixels[idx] = color.r
            overlayPixels[idx + 1] = color.g
            overlayPixels[idx + 2] = color.b
            overlayPixels[idx + 3] = alpha
          }
        }
      }
    }
  } else {
    // Fill mode: fill entire mask region
    for (let r = 0; r < maskRows; r++) {
      const row = mask[r] as number[]
      for (let c = 0; c < maskCols; c++) {
        if (row[c] > 0) {
          const idx = (r * maskCols + c) * 4
          overlayPixels[idx] = color.r
          overlayPixels[idx + 1] = color.g
          overlayPixels[idx + 2] = color.b
          overlayPixels[idx + 3] = alpha
        }
      }
    }
  }

  overlayCtx.putImageData(overlayImageData, 0, 0)

  // Scale mask to canvas size and draw
  ctx.imageSmoothingEnabled = true
  ctx.drawImage(overlayCanvas, 0, 0, canvasW, canvasH)
}

function parseColor(color: string): { r: number; g: number; b: number } {
  if (color.startsWith('#')) {
    const hex = color.slice(1)
    if (hex.length === 6) {
      return {
        r: parseInt(hex.slice(0, 2), 16),
        g: parseInt(hex.slice(2, 4), 16),
        b: parseInt(hex.slice(4, 6), 16),
      }
    }
  }
  // Named colors fallback
  const namedColors: Record<string, { r: number; g: number; b: number }> = {
    red: { r: 255, g: 0, b: 0 },
    green: { r: 0, g: 255, b: 0 },
    blue: { r: 0, g: 0, b: 255 },
    yellow: { r: 255, g: 255, b: 0 },
    cyan: { r: 0, g: 255, b: 255 },
    magenta: { r: 255, g: 0, b: 255 },
    orange: { r: 255, g: 165, b: 0 },
    purple: { r: 128, g: 0, b: 128 },
    white: { r: 255, g: 255, b: 255 },
  }
  return namedColors[color.toLowerCase()] || { r: 255, g: 0, b: 0 }
}

function onMouseDown(e: MouseEvent) {
  isDragging = true
  lastX = e.clientX
  lastY = e.clientY
}

function onMouseMove(e: MouseEvent) {
  // Emit crosshair position on any mouse move
  if (canvas.value) {
    const rect = canvas.value.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    emit('crosshair-move', x, y)
  }

  if (!isDragging) return
  const dx = e.clientX - lastX
  const dy = e.clientY - lastY

  // Middle mouse button or Ctrl+left click = pan
  if (e.buttons === 4 || (e.buttons === 1 && e.ctrlKey)) {
    panX.value += dx * props.panSpeed
    panY.value += dy * props.panSpeed
    lastX = e.clientX
    lastY = e.clientY
    renderSlice()
    return
  }

  // Shift+drag or right-click drag = window/level
  if (e.shiftKey || e.buttons === 2) {
    const wc = (props.windowCenter ?? 0) + dy * 2
    const ww = Math.max(1, (props.windowWidth ?? 100) + dx * 2)
    emit('window-change', wc, ww)
  } else {
    // Normal left-drag = slice scrolling
    const delta = dy > 0 ? 1 : -1
    if (Math.abs(dy) > 3) {
      emit('slice-change', delta)
      lastY = e.clientY
    }
  }

  if (e.shiftKey) {
    lastX = e.clientX
    lastY = e.clientY
  }
}

function onMouseUp() {
  isDragging = false
}

function onWheel(e: WheelEvent) {
  // Ctrl+scroll = zoom
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -props.zoomSpeed : props.zoomSpeed
    const newZoom = Math.max(0.2, Math.min(5, zoomLevel.value + delta))
    zoomLevel.value = Math.round(newZoom * 10) / 10
    emit('zoom-change', zoomLevel.value)
    renderSlice()
    return
  }

  // Normal scroll = slice scrolling
  const delta = e.deltaY > 0 ? 1 : -1
  emit('slice-change', delta)
}

function resetView() {
  zoomLevel.value = 1
  panX.value = 0
  panY.value = 0
  emit('zoom-change', 1)
  renderSlice()
}

function resetWindowLevel() {
  emit('window-change', 0, 0)
}

function captureScreenshot(): string | null {
  if (!canvas.value) return null
  return canvas.value.toDataURL('image/png')
}

watch(
  () => [props.crosshairX, props.crosshairY],
  () => renderSlice()
)

defineExpose({ resetView, captureScreenshot, canvas })
</script>
