<template>
  <div
    class="p-3 rounded-xl border transition-all"
    :class="borderClass"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <div>
        <h3 class="text-sm font-semibold" :class="titleClass">{{ title }}</h3>
        <p class="text-[10px] text-accent-400">{{ subtitle }}</p>
      </div>
      <span
        v-if="series"
        class="px-1.5 py-0.5 rounded text-[10px] font-medium"
        :class="selectedBadgeClass"
      >
        {{ $t('sequence.selected') }}
      </span>
      <span
        v-else
        class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-accent-100 dark:bg-accent-700 text-accent-500"
      >
        --
      </span>
    </div>

    <!-- Selected series info (single) -->
    <div v-if="series && !isList && !Array.isArray(series)" class="space-y-1">
      <div class="text-xs text-accent-700 dark:text-accent-300 truncate">
        {{ series.description || 'N/A' }}
      </div>
      <div class="flex gap-2 text-[10px] text-accent-400">
        <span>{{ series.file_count }} {{ $t('converter.slices') }}</span>
        <span v-if="series.series_number">#{{ series.series_number }}</span>
      </div>
    </div>

    <!-- Selected series list (DWI dual b-value, MG, US) -->
    <div v-if="series && isList && Array.isArray(series)" class="space-y-1">
      <div
        v-for="(item, idx) in series"
        :key="item.series_uid || idx"
        class="text-xs text-accent-700 dark:text-accent-300 truncate"
      >
        {{ item.description || 'N/A' }}
        <span class="text-[10px] text-accent-400">({{ item.file_count }} files)</span>
      </div>
    </div>

    <!-- DCE candidate list -->
    <div v-if="isList && candidates && candidates.length > 0 && title === $t('sequence.dce.title')" class="space-y-1 mt-2">
      <div class="text-[10px] text-accent-500 mb-1">{{ $t('sequence.dce.candidates', { count: candidates.length }) }}</div>
      <div
        v-for="(cand, idx) in candidates"
        :key="cand.series_uid || idx"
        class="flex items-center justify-between px-2 py-1 rounded text-xs cursor-pointer transition-colors"
        :class="selectedDceIndex === idx ? selectedCandidateClass : 'bg-accent-50 dark:bg-accent-700/50 hover:bg-accent-100 dark:hover:bg-accent-600/50'"
        @click="$emit('select-dce', idx)"
      >
        <span class="truncate text-accent-700 dark:text-accent-300">{{ cand.description || 'N/A' }}</span>
        <span class="text-[10px] text-accent-400 shrink-0 ml-1">{{ cand.file_count }} files</span>
      </div>
    </div>

    <!-- Reason -->
    <div v-if="reason" class="mt-2 text-[10px] text-accent-400 italic">
      {{ reason }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface SeriesInfo {
  series_uid: string
  description: string
  file_count: number
  series_number: number
}

const props = defineProps<{
  title: string
  subtitle: string
  color: 'green' | 'blue' | 'purple' | 'pink' | 'cyan'
  series: SeriesInfo | SeriesInfo[] | null
  reason: string
  candidates: SeriesInfo[]
  isList?: boolean
  selectedDceIndex?: number
}>()

defineEmits<{
  (e: 'select-dce', idx: number): void
}>()

const colorMap = {
  green: {
    border: 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10',
    title: 'text-green-700 dark:text-green-300',
    badge: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    selectedCandidate: 'bg-green-100 dark:bg-green-800/50 ring-1 ring-green-400 dark:ring-green-600',
  },
  blue: {
    border: 'border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10',
    title: 'text-blue-700 dark:text-blue-300',
    badge: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    selectedCandidate: 'bg-blue-100 dark:bg-blue-800/50 ring-1 ring-blue-400 dark:ring-blue-600',
  },
  purple: {
    border: 'border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10',
    title: 'text-purple-700 dark:text-purple-300',
    badge: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
    selectedCandidate: 'bg-purple-100 dark:bg-purple-800/50 ring-1 ring-purple-400 dark:ring-purple-600',
  },
  pink: {
    border: 'border-pink-200 dark:border-pink-800 bg-pink-50/50 dark:bg-pink-900/10',
    title: 'text-pink-700 dark:text-pink-300',
    badge: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300',
    selectedCandidate: 'bg-pink-100 dark:bg-pink-800/50 ring-1 ring-pink-400 dark:ring-pink-600',
  },
  cyan: {
    border: 'border-cyan-200 dark:border-cyan-800 bg-cyan-50/50 dark:bg-cyan-900/10',
    title: 'text-cyan-700 dark:text-cyan-300',
    badge: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300',
    selectedCandidate: 'bg-cyan-100 dark:bg-cyan-800/50 ring-1 ring-cyan-400 dark:ring-cyan-600',
  },
}

const borderClass = computed(() => colorMap[props.color].border)
const titleClass = computed(() => colorMap[props.color].title)
const selectedBadgeClass = computed(() => colorMap[props.color].badge)
const selectedCandidateClass = computed(() => colorMap[props.color].selectedCandidate)
</script>
