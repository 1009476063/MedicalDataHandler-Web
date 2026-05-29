<template>
  <div>
    <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.measurements') }}</h3>
    <div v-if="measurements.length === 0" class="text-xs text-accent-400 dark:text-accent-500 py-2">
      {{ $t('viewer.noMeasurements') }}
    </div>
    <div v-else class="space-y-1.5 max-h-64 overflow-y-auto">
      <div
        v-for="item in measurements"
        :key="item.uid"
        class="px-2 py-1.5 rounded bg-accent-50 dark:bg-accent-800/50 text-xs"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-medium text-accent-700 dark:text-accent-300">{{ formatToolName(item.toolName) }}</span>
          <span v-if="item.label" class="text-accent-500 dark:text-accent-400 truncate ml-1">{{ item.label }}</span>
        </div>
        <div class="space-y-0.5 text-accent-600 dark:text-accent-400">
          <template v-if="item.toolName === 'Length'">
            <p>{{ $t('viewer.distance') }}: {{ formatLength(item.stats) }}</p>
          </template>
          <template v-else-if="item.toolName === 'Angle'">
            <p>{{ $t('viewer.deg') }}: {{ formatAngle(item.stats) }}</p>
          </template>
          <template v-else-if="item.toolName === 'RectangleROI' || item.toolName === 'EllipticalROI'">
            <p>{{ $t('viewer.area') }}: {{ formatArea(item.stats) }}</p>
            <p>{{ $t('viewer.mean') }}: {{ formatMean(item.stats) }} {{ $t('viewer.hu') }}</p>
            <p>{{ $t('viewer.stdDev') }}: {{ formatStdDev(item.stats) }}</p>
          </template>
          <template v-else-if="item.toolName === 'Probe'">
            <p>{{ $t('viewer.value') }}: {{ formatProbeValue(item.stats) }} {{ $t('viewer.hu') }}</p>
          </template>
          <template v-else-if="item.toolName === 'ArrowAnnotate'">
            <p class="text-accent-500 dark:text-accent-400 italic">Annotation</p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { MeasurementItem } from '@/types'

defineProps<{
  measurements: MeasurementItem[]
}>()

const { t } = useI18n()

function formatToolName(toolName: string): string {
  const map: Record<string, string> = {
    Length: t('viewer.length'),
    Angle: t('viewer.angle'),
    RectangleROI: t('viewer.rectangleROI'),
    EllipticalROI: t('viewer.ellipticalROI'),
    Probe: t('viewer.probe'),
    ArrowAnnotate: t('viewer.arrowAnnotate'),
  }
  return map[toolName] || toolName
}

function formatLength(stats: Record<string, unknown>): string {
  const length = stats.length as number | undefined
  if (length != null) return `${length.toFixed(2)} mm`
  return '-'
}

function formatAngle(stats: Record<string, unknown>): string {
  const angle = stats.angle as number | undefined
  if (angle != null) return `${angle.toFixed(1)}°`
  return '-'
}

function formatArea(stats: Record<string, unknown>): string {
  const area = stats.area as number | undefined
  if (area != null) return `${area.toFixed(2)} mm²`
  return '-'
}

function formatMean(stats: Record<string, unknown>): string {
  const mean = stats.mean as number | undefined
  if (mean != null) return mean.toFixed(1)
  return '-'
}

function formatStdDev(stats: Record<string, unknown>): string {
  const stdDev = stats.stdDev as number | undefined
  if (stdDev != null) return stdDev.toFixed(2)
  return '-'
}

function formatProbeValue(stats: Record<string, unknown>): string {
  const value = stats.value as number | undefined
  if (value != null) return value.toFixed(1)
  return '-'
}
</script>
