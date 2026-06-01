<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('converter.title') }}</h1>
      <div v-if="queueStatus" class="flex items-center gap-3 text-xs text-accent-500 dark:text-accent-400">
        <span class="flex items-center gap-1">
          <span class="inline-block w-1.5 h-1.5 rounded-full" :class="queueStatus.uploads_available > 0 ? 'bg-green-500' : 'bg-red-500'" />
          {{ $t('converter.uploadsAvailable', { current: queueStatus.uploads_available, max: queueStatus.max_uploads }) }}
        </span>
        <span class="flex items-center gap-1">
          <span class="inline-block w-1.5 h-1.5 rounded-full" :class="queueStatus.conversions_available > 0 ? 'bg-green-500' : 'bg-red-500'" />
          {{ $t('converter.conversionsAvailable', { current: queueStatus.conversions_available, max: queueStatus.max_conversions }) }}
        </span>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <!-- No session -->
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <ArrowsRightLeftIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('converter.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('converter.noDataDesc') }}</p>
        </div>
      </div>

      <div v-else class="space-y-4">
        <!-- Patient & Modality Selection Row -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <!-- Patient selector -->
          <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
            <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('converter.patient') }}</label>
            <select
              v-model="selectedPatientId"
              class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-700 border border-accent-200 dark:border-accent-600 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              @change="onPatientChange"
            >
              <option value="">{{ $t('converter.selectPatient') }}</option>
              <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
                {{ p.name || p.patient_id }}
              </option>
            </select>
          </div>

          <!-- Modality selector -->
          <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
            <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('converter.modality') }}</label>
            <select
              v-model="selectedModality"
              class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-700 border border-accent-200 dark:border-accent-600 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="auto">{{ $t('converter.autoDetect') }}</option>
              <option value="MR">MR</option>
              <option value="MG">MG</option>
              <option value="US">US</option>
            </select>
          </div>

          <!-- Analyze button -->
          <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 flex items-end">
            <button
              :disabled="!selectedPatientId || analyzing"
              class="w-full px-3 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              @click="analyzeSequences"
            >
              {{ analyzing ? $t('sequence.analyzing') : $t('sequence.analyze') }}
            </button>
          </div>
        </div>

        <!-- Sequence Analysis Results -->
        <div v-if="analysisResult" class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <h2 class="text-sm font-semibold text-accent-900 dark:text-white mb-3 flex items-center gap-2">
            <ClipboardDocumentListIcon class="w-4 h-4 text-primary-500" />
            {{ $t('sequence.title') }}
          </h2>

          <!-- All Series Table -->
          <details class="mb-4">
            <summary class="text-xs font-medium text-accent-600 dark:text-accent-400 cursor-pointer hover:text-accent-800 dark:hover:text-accent-200">
              {{ $t('sequence.allSeries') }} ({{ analysisResult.all_series.length }})
            </summary>
            <div class="mt-2 max-h-48 overflow-y-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-accent-500 dark:text-accent-400 border-b border-accent-100 dark:border-accent-700">
                    <th class="text-left py-1 px-2">#</th>
                    <th class="text-left py-1 px-2">{{ $t('sequence.seriesDescription') }}</th>
                    <th class="text-left py-1 px-2">{{ $t('sequence.seriesType') }}</th>
                    <th class="text-left py-1 px-2">{{ $t('sequence.seriesCount') }}</th>
                    <th class="text-left py-1 px-2">{{ $t('sequence.reason') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="s in analysisResult.all_series"
                    :key="s.series_uid"
                    class="border-b border-accent-50 dark:border-accent-700/50 text-accent-700 dark:text-accent-300"
                  >
                    <td class="py-1 px-2">{{ s.series_number }}</td>
                    <td class="py-1 px-2 truncate max-w-[200px]">{{ s.description || 'N/A' }}</td>
                    <td class="py-1 px-2">
                      <span
                        class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                        :class="{
                          'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300': s.type === 'ADC',
                          'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300': s.type === 'DWI',
                          'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300': s.type === 'DCE',
                          'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300': s.type === 'MG',
                          'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300': s.type === 'US',
                          'bg-accent-100 dark:bg-accent-700 text-accent-500': s.type === 'OTHER',
                        }"
                      >{{ s.type }}</span>
                    </td>
                    <td class="py-1 px-2">{{ s.file_count }}</td>
                    <td class="py-1 px-2 text-[10px] text-accent-400 truncate max-w-[180px]">{{ s.reason }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>

          <!-- Selected Sequence Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <!-- ADC Card -->
            <SequenceCard
              :title="$t('sequence.adc.title')"
              :subtitle="$t('sequence.adc.subtitle')"
              color="green"
              :series="analysisResult.selected.ADC"
              :reason="analysisResult.reasons.ADC"
              :candidates="[]"
            />

            <!-- DWI Card -->
            <SequenceCard
              :title="$t('sequence.dwi.title')"
              :subtitle="$t('sequence.dwi.subtitle')"
              color="blue"
              :series="analysisResult.selected.DWI"
              :reason="analysisResult.reasons.DWI"
              :candidates="[]"
              :is-list="Array.isArray(analysisResult.selected.DWI)"
            />

            <!-- DCE Card -->
            <SequenceCard
              :title="$t('sequence.dce.title')"
              :subtitle="$t('sequence.dce.subtitle')"
              color="purple"
              :series="analysisResult.selected.DCE"
              :reason="analysisResult.reasons.DCE"
              :candidates="analysisResult.selected.DCE || []"
              :is-list="true"
              @select-dce="selectDceSeries"
            />

            <!-- MG Card -->
            <SequenceCard
              :title="$t('sequence.mg.title')"
              :subtitle="$t('sequence.mg.subtitle')"
              color="pink"
              :series="analysisResult.selected.MG"
              :reason="analysisResult.reasons.MG"
              :candidates="[]"
              :is-list="true"
            />

            <!-- US Card -->
            <SequenceCard
              :title="$t('sequence.us.title')"
              :subtitle="$t('sequence.us.subtitle')"
              color="cyan"
              :series="analysisResult.selected.US"
              :reason="analysisResult.reasons.US"
              :candidates="[]"
              :is-list="true"
            />
          </div>

          <!-- Convert Selected Button -->
          <div class="mt-4 flex gap-2">
            <button
              :disabled="converting || selectedConvertSeries.length === 0 || queueBusy"
              :title="queueBusy ? $t('converter.queueFull') : ''"
              class="flex-1 px-3 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              @click="convertSelectedSequences"
            >
              {{ converting ? $t('converter.converting') : $t('sequence.convertSelected') }} ({{ selectedConvertSeries.length }} {{ $t('converter.slices') }})
            </button>
          </div>
        </div>

        <!-- Conversion progress (SSE) -->
        <div v-if="conversionProgress.length > 0" class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">
            {{ $t('converter.converting') }} {{ conversionCurrent }}/{{ conversionTotal }}
          </label>
          <div class="w-full bg-accent-100 dark:bg-accent-700 rounded-full h-1.5">
            <div
              class="bg-primary-500 h-1.5 rounded-full transition-all duration-300"
              :style="{ width: conversionTotal > 0 ? (conversionCurrent / conversionTotal * 100) + '%' : '0%' }"
            />
          </div>
          <div class="max-h-32 overflow-y-auto space-y-0.5 mt-2">
            <div
              v-for="p in conversionProgress"
              :key="p.series_uid"
              class="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px]"
              :class="{
                'text-green-600 dark:text-green-400': p.status === 'done',
                'text-red-600 dark:text-red-400': p.status === 'error',
                'text-accent-500': p.status === 'pending',
              }"
            >
              <span v-if="p.status === 'done'" class="shrink-0">&#10003;</span>
              <span v-else-if="p.status === 'error'" class="shrink-0">&#10007;</span>
              <span v-else class="shrink-0 w-1.5 h-1.5 rounded-full bg-accent-400 animate-pulse" />
              <span class="truncate">{{ p.description }}</span>
            </div>
          </div>
        </div>

        <!-- Result -->
        <div v-if="convertResult" class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <div
            v-if="convertResult.errors.length === 0"
            class="p-2 rounded-lg text-xs bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
          >
            {{ $t('converter.convertSuccess', { count: convertResult.files.length }) }}
          </div>
          <div v-else class="p-2 rounded-lg text-xs bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300">
            {{ $t('converter.convertPartial', { success: convertResult.files.length, failed: convertResult.errors.length }) }}
          </div>

          <div v-if="convertResult.files.length > 0" class="space-y-1 mt-2">
            <div
              v-for="f in convertResult.files"
              :key="f.name"
              class="flex items-center justify-between px-2 py-1.5 bg-accent-50 dark:bg-accent-700/50 rounded text-xs"
            >
              <span class="truncate text-accent-700 dark:text-accent-300">{{ f.name }}</span>
              <button
                class="ml-2 shrink-0 px-2 py-0.5 bg-primary-500 hover:bg-primary-600 text-white rounded text-[10px] font-medium transition-colors"
                @click="downloadFile(f.name)"
              >
                {{ $t('converter.download') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Activity Log -->
        <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <h2 class="text-sm font-semibold text-accent-900 dark:text-white mb-3 flex items-center gap-2">
            <ClipboardDocumentListIcon class="w-4 h-4 text-accent-500" />
            {{ $t('converter.activityLog') }}
          </h2>
          <div v-if="logs.length === 0" class="text-xs text-accent-400 text-center py-4">
            {{ $t('converter.noActivity') }}
          </div>
          <div v-else class="max-h-40 overflow-y-auto space-y-1">
            <div
              v-for="(log, i) in logs"
              :key="i"
              class="flex items-start gap-2 px-2 py-1 rounded text-xs"
              :class="{
                'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300': log.type === 'success',
                'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300': log.type === 'error',
                'bg-accent-50 dark:bg-accent-700/50 text-accent-600 dark:text-accent-400': log.type === 'info',
              }"
            >
              <span class="shrink-0">{{ log.time }}</span>
              <span class="flex-1">{{ log.message }}</span>
            </div>
          </div>
        </div>

        <!-- DICOM Anonymization (collapsed) -->
        <details class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <summary class="text-sm font-semibold text-accent-900 dark:text-white cursor-pointer flex items-center gap-2">
            <ShieldCheckIcon class="w-4 h-4 text-blue-500" />
            {{ $t('converter.anonymize') }}
          </summary>
          <div class="mt-3 space-y-3">
            <p class="text-xs text-accent-500 dark:text-accent-400">
              {{ $t('converter.anonymizeDesc') }}
            </p>
            <div>
              <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('converter.patient') }}</label>
              <select
                v-model="anonPatientId"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-700 border border-accent-200 dark:border-accent-600 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                <option value="">{{ $t('converter.selectPatient') }}</option>
                <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
                  {{ p.name || p.patient_id }}
                </option>
              </select>
            </div>
            <button
              :disabled="!anonPatientId || anonymizing"
              class="w-full px-3 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              @click="anonymizeDicoms"
            >
              {{ anonymizing ? $t('converter.anonymizing') : $t('converter.anonymizeBtn') }}
            </button>
            <div v-if="anonResult" class="space-y-2">
              <div
                v-if="anonResult.errors.length === 0"
                class="p-2 rounded-lg text-xs bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
              >
                {{ $t('converter.anonymizeSuccess', { count: anonResult.files.length }) }}
              </div>
              <div v-else class="p-2 rounded-lg text-xs bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300">
                {{ $t('converter.anonymizePartial', { success: anonResult.files.length, failed: anonResult.errors.length }) }}
              </div>
              <div v-if="anonResult.files.length > 0" class="space-y-1">
                <div
                  v-for="f in anonResult.files"
                  :key="f.name"
                  class="flex items-center justify-between px-2 py-1.5 bg-accent-50 dark:bg-accent-700/50 rounded text-xs"
                >
                  <span class="truncate text-accent-700 dark:text-accent-300">{{ f.name }}</span>
                  <button
                    class="ml-2 shrink-0 px-2 py-0.5 bg-primary-500 hover:bg-primary-600 text-white rounded text-[10px] font-medium transition-colors"
                    @click="downloadFile(f.name)"
                  >
                    {{ $t('converter.download') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useSettings } from '@/composables/useSettings'
import axios from 'axios'
import {
  ArrowsRightLeftIcon,
  ShieldCheckIcon,
  ClipboardDocumentListIcon,
} from '@heroicons/vue/24/outline'
import SequenceCard from '@/components/common/SequenceCard.vue'
import type { QueueStatus } from '@/types'

const { t } = useI18n()
const appStore = useAppStore()
const { defaultModality, analysisConfidenceThreshold, dceMinFileCount } = useSettings()

const patients = computed(() => appStore.patients)

// Patient & modality selection
const selectedPatientId = ref('')
const selectedModality = ref(defaultModality.value)

// Sequence analysis state
const analyzing = ref(false)
const analysisResult = ref<{
  all_series: Array<{
    series_uid: string
    description: string
    type: string
    file_count: number
    series_number: number
    reason: string
  }>
  selected: {
    ADC: { series_uid: string; description: string; file_count: number; series_number: number } | null
    DWI: Array<{ series_uid: string; description: string; file_count: number; series_number: number }> | null
    DCE: Array<{ series_uid: string; description: string; file_count: number; series_number: number }> | null
    MG: Array<{ series_uid: string; description: string; file_count: number; series_number: number }> | null
    US: Array<{ series_uid: string; description: string; file_count: number; series_number: number }> | null
  }
  reasons: Record<string, string>
} | null>(null)

// Selected DCE candidate index
const selectedDceIndex = ref(0)

// Collect all selected series for conversion
const selectedConvertSeries = computed(() => {
  if (!analysisResult.value) return []
  const selected = analysisResult.value.selected
  const series: Array<{ series_uid: string; description: string; file_count: number; series_number: number }> = []

  if (selected.ADC) series.push(selected.ADC)
  if (selected.DWI && Array.isArray(selected.DWI)) {
    for (const s of selected.DWI) series.push(s)
  } else if (selected.DWI) {
    series.push(selected.DWI as { series_uid: string; description: string; file_count: number; series_number: number })
  }
  if (selected.DCE && Array.isArray(selected.DCE)) {
    for (const s of selected.DCE) series.push(s)
  }
  if (selected.MG && Array.isArray(selected.MG)) {
    for (const s of selected.MG) series.push(s)
  } else if (selected.MG) {
    series.push(selected.MG as { series_uid: string; description: string; file_count: number; series_number: number })
  }
  if (selected.US && Array.isArray(selected.US)) {
    for (const s of selected.US) series.push(s)
  } else if (selected.US) {
    series.push(selected.US as { series_uid: string; description: string; file_count: number; series_number: number })
  }

  return series
})

// Conversion state
const converting = ref(false)
const convertResult = ref<{
  files: Array<{ name: string; path: string }>
  errors: string[]
} | null>(null)

// SSE progress state
const conversionProgress = ref<Array<{
  series_uid: string
  description: string
  status: 'done' | 'error' | 'pending'
}>>([])
const conversionCurrent = ref(0)
const conversionTotal = ref(0)

// Queue status polling
const queueStatus = ref<QueueStatus | null>(null)
const queueBusy = computed(() => queueStatus.value?.conversions_available === 0)
let queuePollTimer: ReturnType<typeof setInterval> | null = null

async function fetchQueueStatus() {
  try {
    const res = await axios.get('/api/converter/queue-status')
    queueStatus.value = res.data
  } catch {
    queueStatus.value = null
  }
}

function startQueuePolling() {
  fetchQueueStatus()
  queuePollTimer = setInterval(fetchQueueStatus, 10000)
}

onMounted(() => {
  if (appStore.sessionId) startQueuePolling()
})

onUnmounted(() => {
  if (queuePollTimer) clearInterval(queuePollTimer)
})

// Anonymization state
const anonPatientId = ref('')
const anonymizing = ref(false)
const anonResult = ref<{
  files: Array<{ name: string; path: string }>
  errors: string[]
} | null>(null)

// Activity log
const logs = ref<Array<{ time: string; message: string; type: 'info' | 'success' | 'error' }>>([])

function addLog(message: string, type: 'info' | 'success' | 'error' = 'info') {
  const now = new Date()
  const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  logs.value.unshift({ time, message, type })
  if (logs.value.length > 50) logs.value.pop()
}

function onPatientChange() {
  analysisResult.value = null
  selectedDceIndex.value = 0
  convertResult.value = null
  conversionProgress.value = []
}

function selectDceSeries(idx: number) {
  selectedDceIndex.value = idx
  if (analysisResult.value && analysisResult.value.selected.DCE) {
    const dce = analysisResult.value.selected.DCE
    if (idx >= 0 && idx < dce.length) {
      analysisResult.value = {
        ...analysisResult.value,
        selected: {
          ...analysisResult.value.selected,
          DCE: [dce[idx]],
        },
      }
    }
  }
}

async function analyzeSequences() {
  if (!selectedPatientId.value || !appStore.sessionId) return
  analyzing.value = true
  analysisResult.value = null
  convertResult.value = null
  addLog(t('sequence.scanningLog'), 'info')

  try {
    const res = await axios.post('/api/analysis/analyze', {
      session_id: appStore.sessionId,
      patient_id: selectedPatientId.value,
      confidence_threshold: analysisConfidenceThreshold.value,
      dce_min_file_count: dceMinFileCount.value,
    })
    analysisResult.value = res.data
    addLog(t('sequence.scanDone', { count: res.data.all_series.length }), 'success')
  } catch {
    addLog(t('sequence.scanFailed'), 'error')
  } finally {
    analyzing.value = false
  }
}

async function convertSelectedSequences() {
  if (!selectedPatientId.value || !appStore.sessionId || selectedConvertSeries.value.length === 0) return
  converting.value = true
  convertResult.value = null
  conversionProgress.value = []
  conversionCurrent.value = 0
  conversionTotal.value = selectedConvertSeries.value.length
  addLog(t('converter.convertingLog'), 'info')

  const pendingList = selectedConvertSeries.value.map(s => ({
    series_uid: s.series_uid,
    description: s.description || 'N/A',
    status: 'pending' as const,
  }))
  conversionProgress.value = pendingList

  try {
    const response = await fetch('/api/converter/convert-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: appStore.sessionId,
        patient_id: selectedPatientId.value,
        modality: selectedModality.value,
        selected_series: selectedConvertSeries.value.map(s => s.series_uid),
      }),
    })

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const msg = JSON.parse(line.slice(6))
            if (msg.type === 'progress') {
              conversionCurrent.value = msg.current
              conversionTotal.value = msg.total
              const idx = conversionProgress.value.findIndex(p => p.series_uid === msg.series_uid)
              if (idx >= 0) {
                conversionProgress.value[idx] = {
                  ...conversionProgress.value[idx],
                  status: msg.status === 'done' ? 'done' : 'error',
                }
              }
              if (msg.status === 'done') {
                addLog(`Converted: ${msg.description}`, 'success')
              } else {
                addLog(`Failed: ${msg.description}`, 'error')
              }
            } else if (msg.type === 'complete') {
              convertResult.value = { files: msg.files, errors: msg.errors }
              if (msg.files.length > 0) {
                addLog(t('converter.convertDone', { count: msg.files.length }), 'success')
              }
              for (const err of msg.errors) {
                addLog(err, 'error')
              }
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  } catch {
    addLog(t('converter.convertFailed'), 'error')
  } finally {
    converting.value = false
  }
}

async function anonymizeDicoms() {
  if (!anonPatientId.value || !appStore.sessionId) return
  anonymizing.value = true
  anonResult.value = null
  addLog(t('converter.anonymizingLog'), 'info')

  try {
    const res = await axios.post('/api/converter/anonymize', {
      session_id: appStore.sessionId,
      patient_id: anonPatientId.value,
    })
    anonResult.value = res.data
    if (res.data.files.length > 0) {
      addLog(t('converter.anonymizeDone', { count: res.data.files.length }), 'success')
    }
  } catch {
    addLog(t('converter.anonymizeFailed'), 'error')
  } finally {
    anonymizing.value = false
  }
}

function downloadFile(filename: string) {
  if (!appStore.sessionId) return
  const url = `/api/converter/download/${appStore.sessionId}/${filename}`
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
}
</script>
