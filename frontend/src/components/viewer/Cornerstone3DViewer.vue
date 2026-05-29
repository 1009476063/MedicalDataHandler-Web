<template>
  <div
    class="relative bg-black rounded-xl overflow-hidden border border-accent-700"
    style="contain: layout paint"
  >
    <div ref="containerRef" class="w-full h-full" />

    <!-- Status overlay -->
    <div class="absolute top-2 left-2 space-y-1 pointer-events-none">
      <div class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        {{ label }}
      </div>
      <div v-if="windowWidth !== null && windowCenter !== null" class="px-2 py-1 rounded bg-black/60 text-white text-xs font-mono">
        W: {{ windowWidth }} L: {{ windowCenter }}
      </div>
    </div>

    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-black/40">
      <div class="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = withDefaults(defineProps<{
  viewportId: string
  label: string
  loading?: boolean
  windowWidth?: number | null
  windowCenter?: number | null
}>(), {
  loading: false,
  windowWidth: null,
  windowCenter: null,
})

const emit = defineEmits<{
  'viewport-ready': [element: HTMLDivElement]
  'resize': []
}>()

const containerRef = ref<HTMLDivElement>()

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
