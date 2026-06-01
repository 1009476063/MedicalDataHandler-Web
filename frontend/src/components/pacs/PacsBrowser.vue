<template>
  <div class="space-y-4">
    <!-- Connections -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300">PACS Connections</h3>
        <button
          class="px-2 py-1 text-xs rounded bg-primary-500 text-white hover:bg-primary-600 transition-colors"
          @click="$emit('connect')"
        >
          + Connect
        </button>
      </div>
      <div v-if="connections.length === 0" class="text-xs text-accent-400 py-2">
        {{ connectionsReady ? 'No PACS connections' : 'Loading connections...' }}
      </div>
      <div v-else class="space-y-1">
        <div
          v-for="conn in connections"
          :key="conn.name"
          class="flex items-center justify-between px-2 py-1.5 rounded bg-accent-50 dark:bg-accent-800/50 text-xs"
        >
          <span class="text-accent-700 dark:text-accent-300">{{ conn.name }}</span>
          <div class="flex items-center gap-1">
            <button
              class="px-1.5 py-0.5 rounded text-primary-500 hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-colors"
              @click="$emit('search', conn.name)"
            >
              Search
            </button>
            <button
              class="px-1.5 py-0.5 rounded text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              @click="$emit('disconnect', conn.name)"
            >
              ×
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Studies -->
    <div v-if="studies.length > 0">
      <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">Studies ({{ studies.length }})</h3>
      <div class="space-y-1 max-h-48 overflow-y-auto">
        <button
          v-for="study in studies"
          :key="studyUid(study)"
          class="w-full text-left px-2 py-1.5 rounded text-xs hover:bg-accent-100 dark:hover:bg-accent-800/50 transition-colors"
          @click="$emit('select-study', studyUid(study))"
        >
          <span class="font-medium text-accent-700 dark:text-accent-300">{{ studyName(study) }}</span>
          <span class="text-accent-400 ml-2">{{ studyDate(study) }}</span>
        </button>
      </div>
    </div>

    <!-- Series -->
    <div v-if="seriesList.length > 0">
      <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">Series ({{ seriesList.length }})</h3>
      <div class="space-y-1 max-h-48 overflow-y-auto">
        <div
          v-for="s in seriesList"
          :key="seriesUid(s)"
          class="flex items-center gap-2 px-2 py-1.5 rounded text-xs text-accent-700 dark:text-accent-300 hover:bg-accent-50 dark:hover:bg-accent-800/50"
        >
          <span class="px-1.5 py-0.5 rounded bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-[10px]">
            {{ seriesModality(s) }}
          </span>
          <span class="truncate flex-1">{{ seriesDescription(s) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PacsStudy, PacsSeries } from '@/composables/useDicomweb'

defineProps<{
  connections: Array<{ name: string; base_url: string }>
  connectionsReady: boolean
  studies: PacsStudy[]
  seriesList: PacsSeries[]
}>()

defineEmits<{
  connect: []
  disconnect: [name: string]
  search: [connection: string]
  'select-study': [studyUid: string]
}>()

function extractTag(tag: Record<string, unknown>, key: string): string {
  const field = tag[key] as { Value?: string[] } | undefined
  return field?.Value?.[0] || ''
}

function studyName(s: PacsStudy): string {
  return extractTag(s, '00100010') || extractTag(s, '00081030') || 'Unknown'
}

function studyDate(s: PacsStudy): string {
  return extractTag(s, '00080020') || ''
}

function studyUid(s: PacsStudy): string {
  return extractTag(s, '0020000D') || ''
}

function seriesModality(s: PacsSeries): string {
  return extractTag(s, '00080060') || ''
}

function seriesDescription(s: PacsSeries): string {
  return extractTag(s, '0008103E') || ''
}

function seriesUid(s: PacsSeries): string {
  return extractTag(s, '0020000E') || ''
}
</script>
