<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('sidebar.nav.logging') }}</h1>
      <span class="text-xs text-accent-400">{{ $t('common.activityLog') }}</span>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="logs.length === 0" class="flex items-center justify-center h-full">
        <div class="text-center">
          <ClipboardDocumentListIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('common.activityLog') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('common.noLogs') }}</p>
        </div>
      </div>

      <div v-else class="space-y-1">
        <div
          v-for="entry in logs"
          :key="entry.id"
          class="flex items-start gap-3 px-4 py-2 rounded-lg hover:bg-accent-50 dark:hover:bg-accent-800 transition-colors text-sm font-mono"
        >
          <span class="text-accent-400 whitespace-nowrap">{{ formatTime(entry.timestamp) }}</span>
          <span :class="levelColor(entry.level)" class="w-16 flex-shrink-0 text-xs font-semibold">{{ entry.level.toUpperCase() }}</span>
          <span class="text-accent-400 flex-shrink-0">[{{ entry.source }}]</span>
          <span class="text-accent-700 dark:text-accent-300 break-all">{{ entry.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ClipboardDocumentListIcon } from '@heroicons/vue/24/outline'

interface LogEntry {
  id: number
  timestamp: number
  level: string
  message: string
  source: string
}

const logs = ref<LogEntry[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null
let lastTimestamp = 0

function formatTime(ts: number): string {
  const d = new Date(ts * 1000)
  return d.toLocaleString('en-US', {
    month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  })
}

function levelColor(level: string): string {
  switch (level) {
    case 'error': return 'text-red-500'
    case 'warning': return 'text-yellow-500'
    case 'success': return 'text-green-500'
    default: return 'text-accent-500'
  }
}

async function fetchLogs() {
  try {
    const params = new URLSearchParams()
    if (lastTimestamp > 0) params.set('since', String(lastTimestamp))
    params.set('limit', '200')
    const res = await fetch(`/api/logging/logs?${params}`)
    const data = await res.json()
    if (data.logs.length > 0) {
      logs.value = [...logs.value.slice(-500), ...data.logs]
      lastTimestamp = data.logs[data.logs.length - 1].timestamp
    }
  } catch {
    // silently ignore polling errors
  }
}

onMounted(() => {
  fetchLogs()
  pollTimer = setInterval(fetchLogs, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>
