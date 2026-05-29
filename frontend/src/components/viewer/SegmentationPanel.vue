<template>
  <div v-if="segFiles.length > 0 || loading" class="space-y-3">
    <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300">{{ $t('viewer.segmentation') }}</h3>

    <div v-if="loading" class="text-xs text-accent-500">{{ $t('common.loading') }}</div>

    <div v-if="error" class="text-xs text-red-500">{{ error }}</div>

    <!-- SEG files and segments -->
    <div v-for="segFile in segFiles" :key="segFile.file_id" class="space-y-1.5">
      <div class="text-[10px] text-accent-500 dark:text-accent-400 font-mono truncate" :title="segFile.filename">
        {{ segFile.filename }}
      </div>

      <div v-for="seg in segFile.segments" :key="seg.segment_number" class="flex items-center gap-2 group">
        <button
          class="flex items-center gap-2 flex-1 min-w-0 px-2 py-1.5 rounded-lg text-xs transition-colors"
          :class="isActive(segFile.file_id, seg.segment_number)
            ? 'bg-accent-100 dark:bg-accent-800/80 text-accent-900 dark:text-white'
            : 'hover:bg-accent-50 dark:hover:bg-accent-800/50 text-accent-700 dark:text-accent-300'"
          @click="onToggle(segFile, seg)"
        >
          <span
            class="w-3 h-3 rounded-sm flex-shrink-0 border"
            :style="{
              backgroundColor: isActive(segFile.file_id, seg.segment_number) ? segmentColor(seg.segment_number) : 'transparent',
              borderColor: segmentColor(seg.segment_number),
            }"
          />
          <span class="truncate">{{ seg.label }}</span>
          <span class="text-[10px] text-accent-400 ml-auto flex-shrink-0">{{ seg.algorithm_type }}</span>
        </button>

        <!-- Opacity slider for active overlays -->
        <input
          v-if="isActive(segFile.file_id, seg.segment_number)"
          type="range"
          :min="0"
          :max="1"
          :step="0.05"
          :value="getOpacity(segFile.file_id, seg.segment_number)"
          class="w-12 h-1 accent-primary-500"
          :title="$t('viewer.segOpacity')"
          @input="onOpacityChange(segFile.file_id, seg.segment_number, $event)"
        />
      </div>
    </div>

    <!-- Active overlays count -->
    <div v-if="activeCount > 0" class="flex items-center justify-between pt-1 border-t border-accent-200 dark:border-accent-700">
      <span class="text-[10px] text-accent-500">{{ activeCount }} {{ $t('viewer.segActive') }}</span>
      <button
        class="text-[10px] text-red-500 hover:text-red-600 transition-colors"
        @click="onClearAll"
      >
        {{ $t('viewer.clearAll') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SegFile as SegFileType } from '@/types'
import type { SegOverlay } from '@/composables/useSegmentation'

const props = defineProps<{
  segFiles: SegFileType[]
  overlays: SegOverlay[]
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  toggle: [segFile: SegFileType, segNum: number, label: string]
  opacity: [fileId: string, segNum: number, opacity: number]
  clearAll: []
}>()

const activeCount = computed(() => props.overlays.filter(o => o.visible).length)

function isActive(fileId: string, segNum: number): boolean {
  return props.overlays.some(o => o.fileId === fileId && o.segmentNumber === segNum && o.visible)
}

function getOpacity(fileId: string, segNum: number): number {
  const overlay = props.overlays.find(o => o.fileId === fileId && o.segmentNumber === segNum)
  return overlay?.opacity ?? 0.4
}

function onToggle(segFile: SegFileType, seg: { segment_number: number; label: string }) {
  emit('toggle', segFile, seg.segment_number, seg.label)
}

function onOpacityChange(fileId: string, segNum: number, event: Event) {
  const val = parseFloat((event.target as HTMLInputElement).value)
  emit('opacity', fileId, segNum, val)
}

function onClearAll() {
  emit('clearAll')
}

function segmentColor(num: number): string {
  const colors = [
    '#ef4444', '#22c55e', '#3b82f6', '#f59e0b',
    '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
  ]
  return colors[(num - 1) % colors.length]
}
</script>
