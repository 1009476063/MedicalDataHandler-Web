<template>
  <div class="flex items-center gap-1 px-3 py-1.5 bg-white dark:bg-accent-900 border-b border-accent-200 dark:border-accent-700">
    <span class="text-xs font-medium text-accent-500 dark:text-accent-400 mr-1">{{ $t('viewer.tools') }}:</span>
    <button
      v-for="tool in tools"
      :key="tool.name"
      :class="[
        'px-2 py-1 text-xs rounded transition-colors',
        activeTool === tool.name
          ? 'bg-primary-500 text-white'
          : 'bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700',
      ]"
      :title="tool.label"
      @click="$emit('select-tool', tool.name)"
    >
      {{ tool.label }}
    </button>

    <div class="w-px h-4 bg-accent-200 dark:bg-accent-700 mx-1" />

    <button
      :class="[
        'px-2 py-1 text-xs rounded transition-colors',
        crosshairsEnabled
          ? 'bg-primary-500 text-white'
          : 'bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700',
      ]"
      :title="$t('viewer.crosshairs')"
      @click="$emit('toggle-crosshairs')"
    >
      {{ $t('viewer.crosshairs') }}
    </button>

    <div class="flex-1" />

    <button
      class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400 transition-colors"
      :title="$t('viewer.clearAll')"
      @click="$emit('clear-all')"
    >
      {{ $t('viewer.clearAll') }}
    </button>
    <button
      class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
      :title="$t('viewer.exportCsv')"
      @click="$emit('export-csv')"
    >
      {{ $t('viewer.exportCsv') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { ToolName } from '@/composables/useTools'

const { t } = useI18n()

defineProps<{
  activeTool: ToolName
  crosshairsEnabled: boolean
}>()

defineEmits<{
  'select-tool': [toolName: ToolName]
  'toggle-crosshairs': []
  'clear-all': []
  'export-csv': []
}>()

const tools: { name: ToolName; label: string }[] = [
  { name: 'Length', label: 'mm' },
  { name: 'Angle', label: '°' },
  { name: 'RectangleROI', label: '□' },
  { name: 'EllipticalROI', label: '○' },
  { name: 'Probe', label: '+' },
  { name: 'ArrowAnnotate', label: '→' },
]
</script>
