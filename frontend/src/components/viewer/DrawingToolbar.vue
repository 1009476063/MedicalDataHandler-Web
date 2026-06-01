<template>
  <div class="flex items-center gap-1 px-3 py-1.5 bg-white dark:bg-accent-900 border-b border-accent-200 dark:border-accent-700">
    <span class="text-xs font-medium text-accent-500 dark:text-accent-400 mr-1">{{ $t('roi.drawTools') }}:</span>
    <button
      v-for="tool in drawTools"
      :key="tool.id"
      :class="[
        'px-2 py-1 text-xs rounded transition-colors',
        activeTool === tool.id
          ? 'bg-primary-500 text-white'
          : 'bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700',
      ]"
      :title="tool.label"
      @click="$emit('select-tool', tool.id)"
    >
      {{ tool.icon }} {{ tool.label }}
    </button>

    <div class="w-px h-4 bg-accent-200 dark:bg-accent-700 mx-1" />

    <span class="text-[10px] text-accent-500">{{ $t('roi.radius') }}:</span>
    <input
      :value="brushRadius"
      type="range"
      min="1"
      max="30"
      class="w-16 h-1 accent-primary-500"
      @input="$emit('update:brushRadius', Number(($event.target as HTMLInputElement).value))"
    />
    <span class="text-[10px] text-accent-400 w-6">{{ brushRadius }}</span>

    <div class="flex-1" />

    <button
      :class="[
        'px-2 py-1 text-xs rounded transition-colors',
        canUndo
          ? 'bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700'
          : 'bg-accent-50 dark:bg-accent-800/50 text-accent-300 dark:text-accent-600 cursor-not-allowed',
      ]"
      :title="$t('roi.undo')"
      :disabled="!canUndo"
      @click="$emit('undo')"
    >
      ↶ {{ $t('roi.undo') }}
    </button>
    <button
      :class="[
        'px-2 py-1 text-xs rounded transition-colors',
        canRedo
          ? 'bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700'
          : 'bg-accent-50 dark:bg-accent-800/50 text-accent-300 dark:text-accent-600 cursor-not-allowed',
      ]"
      :title="$t('roi.redo')"
      :disabled="!canRedo"
      @click="$emit('redo')"
    >
      ↷ {{ $t('roi.redo') }}
    </button>

    <button
      class="px-2 py-1 text-xs rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors ml-1"
      :title="$t('roi.exitDraw')"
      @click="$emit('exit-draw')"
    >
      ✕ {{ $t('roi.exitDraw') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { ROIDrawTool } from '@/types'

const { t } = useI18n()

defineProps<{
  activeTool: ROIDrawTool
  brushRadius: number
  canUndo: boolean
  canRedo: boolean
}>()

defineEmits<{
  'select-tool': [tool: ROIDrawTool]
  'update:brushRadius': [radius: number]
  undo: []
  redo: []
  'exit-draw': []
}>()

const drawTools: Array<{ id: ROIDrawTool; icon: string; label: string }> = [
  { id: 'paintbrush', icon: '🖌', label: 'Brush' },
  { id: 'polygon', icon: '⬠', label: 'Polygon' },
  { id: 'rectangle', icon: '▭', label: 'Rect' },
  { id: 'ellipse', icon: '⬭', label: 'Ellipse' },
  { id: 'magic-wand', icon: '🪄', label: 'Wand' },
  { id: 'eraser', icon: '⌫', label: 'Eraser' },
]
</script>
