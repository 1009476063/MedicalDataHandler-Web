<template>
  <div
    class="relative bg-black rounded-xl overflow-hidden border border-accent-700"
    style="contain: layout paint"
    :class="drawMode ? 'cursor-none' : ''"
  >
    <div ref="containerRef" class="w-full h-full" />

    <!-- Draw overlay canvas (transparent, captures mouse events in WebGL mode) -->
    <canvas
      v-if="drawMode"
      ref="drawOverlayRef"
      class="absolute inset-0 w-full h-full z-10"
      style="cursor: none"
      @mousedown="onDrawMouseDown"
      @mousemove="onDrawMouseMove"
      @mouseup="onDrawMouseUp"
      @mouseleave="onDrawMouseLeave"
      @dblclick="$emit('draw-dblclick')"
    />

    <!-- Draw cursor overlay -->
    <div
      v-if="drawMode && drawCursorX !== null"
      class="pointer-events-none absolute border-2 rounded-full z-20"
      :style="drawCursorStyle"
    />

    <!-- Status overlay -->
    <div class="absolute top-2 left-2 space-y-1 pointer-events-none z-20">
      <div class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        {{ label }}
      </div>
      <div v-if="windowWidth !== null && windowCenter !== null" class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        W: {{ windowWidth }} L: {{ windowCenter }}
      </div>
    </div>

    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-black/40 z-20">
      <div class="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const props = withDefaults(defineProps<{
  viewportId: string
  label: string
  loading?: boolean
  windowWidth?: number | null
  windowCenter?: number | null
  drawMode?: boolean
  drawBrushRadius?: number
  drawCursorX?: number | null
  drawCursorY?: number | null
}>(), {
  loading: false,
  windowWidth: null,
  windowCenter: null,
  drawMode: false,
  drawBrushRadius: 5,
  drawCursorX: null,
  drawCursorY: null,
})

const emit = defineEmits<{
  'viewport-ready': [element: HTMLDivElement]
  'resize': []
  'draw-mousedown': [canvasX: number, canvasY: number]
  'draw-mousemove': [canvasX: number, canvasY: number]
  'draw-mouseup': [canvasX: number, canvasY: number]
  'draw-dblclick': []
}>()

const containerRef = ref<HTMLDivElement>()
const drawOverlayRef = ref<HTMLCanvasElement>()

const drawCursorStyle = computed(() => {
  if (props.drawCursorX === null || props.drawCursorY === null) return {}
  const size = props.drawBrushRadius * 2
  return {
    left: `${props.drawCursorX - size / 2}px`,
    top: `${props.drawCursorY - size / 2}px`,
    width: `${size}px`,
    height: `${size}px`,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  }
})

function onDrawMouseDown(e: MouseEvent) {
  const rect = (e.target as HTMLCanvasElement).getBoundingClientRect()
  emit('draw-mousedown', e.clientX - rect.left, e.clientY - rect.top)
}

function onDrawMouseMove(e: MouseEvent) {
  const rect = (e.target as HTMLCanvasElement).getBoundingClientRect()
  emit('draw-mousemove', e.clientX - rect.left, e.clientY - rect.top)
}

function onDrawMouseUp(e: MouseEvent) {
  const rect = (e.target as HTMLCanvasElement).getBoundingClientRect()
  emit('draw-mouseup', e.clientX - rect.left, e.clientY - rect.top)
}

function onDrawMouseLeave() {
  emit('draw-mouseup', -1, -1)
}

function onResize() {
  emit('resize')
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (containerRef.value) {
    emit('viewport-ready', containerRef.value)
    resizeObserver = new ResizeObserver(onResize)
    resizeObserver.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

defineExpose({
  getElement: () => containerRef.value,
})
</script>
