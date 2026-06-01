<template>
  <div class="border-t border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
    <button
      @click="expanded = !expanded"
      class="w-full flex items-center justify-between px-4 py-2 hover:bg-accent-50 dark:hover:bg-accent-800 transition-colors"
    >
      <div class="flex items-center gap-2">
        <DocumentTextIcon class="w-4 h-4 text-accent-500" />
        <span class="text-xs font-medium text-accent-700 dark:text-accent-300">{{ $t('common.activityLog') }}</span>
        <span v-if="unreadCount > 0" class="px-1.5 py-0.5 text-[10px] font-medium bg-primary-500 text-white rounded-full">
          {{ unreadCount }}
        </span>
      </div>
      <ChevronUpIcon
        :class="['w-4 h-4 text-accent-400 transition-transform', !expanded && 'rotate-180']"
      />
    </button>

    <Transition name="slide-down">
      <div v-if="expanded" class="max-h-48 overflow-y-auto px-4 pb-3">
        <div v-if="logs.length === 0" class="text-xs text-accent-400 py-2">{{ $t('common.noLogs') }}</div>
        <div
          v-for="entry in logs"
          :key="entry.id"
          class="flex items-start gap-2 py-1 text-xs font-mono"
        >
          <span class="text-accent-400 whitespace-nowrap">{{ formatTime(entry.timestamp) }}</span>
          <span :class="levelColor(entry.level)" class="w-14 flex-shrink-0">{{ entry.level.toUpperCase() }}</span>
          <span class="text-accent-400 flex-shrink-0">[{{ entry.source }}]</span>
          <span class="text-accent-700 dark:text-accent-300 break-all">{{ entry.message }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { DocumentTextIcon, ChevronUpIcon } from '@heroicons/vue/24/outline'

interface LogEntry {
  id: number
  timestamp: number
  level: string
  message: string
  source: string
}

const expanded = ref(false)
const logs = ref<LogEntry[]>([])
const unreadCount = ref(0)
let pollTimer: ReturnType<typeof setInterval> | null = null
let lastTimestamp = 0

function formatTime(ts: number): string {
  const d = new Date(ts * 1000)
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
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
    params.set('limit', '100')
    const res = await fetch(`/api/logging/logs?${params}`)
    if (!res.ok) return
    const data = await res.json()
    if (data?.logs?.length > 0) {
      logs.value = [...logs.value.slice(-200), ...data.logs]
      lastTimestamp = data.logs[data.logs.length - 1].timestamp
      if (!expanded.value) {
        unreadCount.value += data.logs.length
      }
    }
  } catch {
    // silently ignore polling errors
  }
}

function clearUnread() {
  unreadCount.value = 0
}

watch(expanded, (val) => {
  if (val) clearUnread()
})

onMounted(() => {
  fetchLogs()
  pollTimer = setInterval(fetchLogs, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
}
.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  max-height: 12rem;
}
</style>
