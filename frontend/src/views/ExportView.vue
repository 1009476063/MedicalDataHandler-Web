<template>
  <div class="space-y-6 animate-fade-in">
    <div>
      <h1 class="text-2xl font-bold text-accent-900 dark:text-white">{{ $t('export.title') }}</h1>
      <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('export.subtitle') }}</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('export.nrrdExport') }}</h2>
        <p class="text-sm text-accent-600 dark:text-accent-400 mb-6">
          {{ $t('export.description') }}
        </p>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('export.patient') }}
            </label>
            <select
              v-model="selectedPatientId"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="">{{ $t('export.selectPatient') }}</option>
              <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
                {{ p.name || p.patient_id }}
              </option>
            </select>
          </div>

          <div v-if="selectedPatient">
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('export.series') }}
            </label>
            <div class="space-y-1.5 max-h-48 overflow-y-auto">
              <label
                v-for="s in selectedSeries"
                :key="s.series_uid"
                class="flex items-center gap-2 px-3 py-2 rounded-lg border border-accent-200 dark:border-accent-700 cursor-pointer hover:bg-accent-50 dark:hover:bg-accent-800/50 transition-colors"
              >
                <input
                  type="checkbox"
                  :checked="selectedSeriesUids.has(s.series_uid)"
                  class="rounded border-accent-300 text-primary-500 focus:ring-primary-500/50"
                  @change="toggleSeries(s.series_uid)"
                />
                <StatusBadge :status="s.modality" />
                <span class="text-sm text-accent-900 dark:text-white truncate">{{ s.series_description || s.series_uid }}</span>
              </label>
            </div>
            <div class="flex items-center justify-between mt-2">
              <button
                class="text-xs text-primary-500 hover:text-primary-600 transition-colors"
                @click="selectAllSeries"
              >
                {{ $t('export.selectAll') }}
              </button>
              <span class="text-xs text-accent-500">{{ $t('export.selected', { count: selectedSeriesUids.size }) }}</span>
            </div>
          </div>

          <div v-if="formatOptions.length > 1">
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('export.format') }}
            </label>
            <div class="space-y-2">
              <label
                v-for="opt in formatOptions"
                :key="opt.value"
                class="flex items-center gap-2 p-3 rounded-lg border border-accent-200 dark:border-accent-700 cursor-pointer hover:bg-accent-50 dark:hover:bg-accent-800/50 transition-colors"
              >
                <input v-model="exportFormat" type="radio" :value="opt.value" class="text-primary-500" />
                <div>
                  <p class="text-sm font-medium text-accent-900 dark:text-white">{{ $t(opt.label) }}</p>
                  <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t(opt.desc) }}</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Single export -->
          <div v-if="selectedSeriesUids.size === 1">
            <button
              :disabled="exporting"
              class="w-full px-4 py-2.5 bg-primary-500 hover:bg-primary-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              @click="handleSingleExport"
            >
              <ArrowDownTrayIcon class="w-4 h-4" />
              {{ exporting ? $t('export.exporting') : $t('export.exportNrrd') }}
            </button>
          </div>

          <!-- Batch export -->
          <div v-else-if="selectedSeriesUids.size > 1">
            <button
              :disabled="exporting"
              class="w-full px-4 py-2.5 bg-primary-500 hover:bg-primary-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              @click="handleBatchExport"
            >
              <ArrowDownTrayIcon class="w-4 h-4" />
              {{ exporting ? $t('export.exportingSeries', { current: exportProgress.current, total: exportProgress.total }) : $t('export.exportSeries', { count: selectedSeriesUids.size }) }}
            </button>
          </div>
        </div>
      </div>

      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('export.exportInfo') }}</h2>
        <div v-if="!selectedPatientId" class="text-center py-8">
          <InformationCircleIcon class="w-10 h-10 text-accent-300 dark:text-accent-600 mx-auto mb-2" />
          <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('export.selectToExport') }}</p>
        </div>
        <div v-else class="space-y-3">
          <div class="p-3 rounded-lg bg-accent-50 dark:bg-accent-800/50">
            <p class="text-xs font-medium text-accent-500 dark:text-accent-400 mb-1">{{ $t('export.patient') }}</p>
            <p class="text-sm text-accent-900 dark:text-white">{{ selectedPatient?.name || selectedPatientId }}</p>
          </div>

          <!-- Batch progress -->
          <div v-if="exporting && selectedSeriesUids.size > 1" class="space-y-2">
            <div class="flex items-center justify-between text-xs text-accent-500">
              <span>{{ $t('export.exportingProgress', { current: exportProgress.current, total: exportProgress.total }) }}</span>
              <span>{{ Math.round((exportProgress.current / exportProgress.total) * 100) }}%</span>
            </div>
            <div class="w-full bg-accent-200 dark:bg-accent-700 rounded-full h-2">
              <div
                class="bg-primary-500 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${(exportProgress.current / exportProgress.total) * 100}%` }"
              />
            </div>
          </div>

          <!-- Selected series list -->
          <div v-if="selectedSeriesUids.size > 0" class="space-y-1.5">
            <div
              v-for="uid in Array.from(selectedSeriesUids)"
              :key="uid"
              class="flex items-center gap-2 p-2 rounded-lg bg-accent-50 dark:bg-accent-800/50"
            >
              <StatusBadge :status="getSeriesModality(uid)" />
              <span class="text-xs text-accent-900 dark:text-white truncate flex-1">{{ getSeriesName(uid) }}</span>
              <span v-if="exportResults[uid]" class="text-xs" :class="exportResults[uid].success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ exportResults[uid].success ? $t('export.done') : $t('export.failed') }}
              </span>
            </div>
          </div>

          <div v-if="batchExportComplete" class="p-3 rounded-lg" :class="batchExportSuccess ? 'bg-green-50 dark:bg-green-900/20' : 'bg-yellow-50 dark:bg-yellow-900/20'">
            <p class="text-sm" :class="batchExportSuccess ? 'text-green-700 dark:text-green-300' : 'text-yellow-700 dark:text-yellow-300'">
              {{ batchExportMessage }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useSettings } from '@/composables/useSettings'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  ArrowDownTrayIcon,
  InformationCircleIcon,
} from '@heroicons/vue/24/outline'

const { t } = useI18n()
const appStore = useAppStore()
const { exportDtype, exportUnit } = useSettings()
const selectedPatientId = ref('')
const selectedSeriesUids = ref<Set<string>>(new Set())
const exporting = ref(false)
const exportResult = ref<{ success: boolean; message: string } | null>(null)
const exportResults = reactive<Record<string, { success: boolean; message: string }>>({})
const exportProgress = reactive({ current: 0, total: 0 })
const batchExportComplete = ref(false)
const batchExportSuccess = ref(false)
const batchExportMessage = ref('')

const patients = computed(() => appStore.patients || [])
const selectedPatient = computed(() =>
  patients.value.find((p) => p.patient_id === selectedPatientId.value)
)
const selectedSeries = computed(() => {
  const studies = selectedPatient.value?.studies || []
  return studies.flatMap((s: any) => s.series || [])
})

const detectedModality = computed(() => {
  const uids = Array.from(selectedSeriesUids.value)
  if (uids.length === 0) return null
  const first = selectedSeries.value.find((s: any) => s.series_uid === uids[0])
  return first?.modality || null
})

const formatOptions = computed(() => {
  switch (detectedModality.value) {
    case 'CT':
      return [
        { value: 'ct', label: 'export.formatCT', desc: 'export.formatCTDesc' },
        { value: 'red', label: 'export.formatRED', desc: 'export.formatREDDesc' },
      ]
    case 'MR':
      return [
        { value: 'mr', label: 'export.formatMR', desc: 'export.formatMRDesc' },
      ]
    case 'PT':
      return [
        { value: 'pet', label: 'export.formatPET', desc: 'export.formatPETDesc' },
      ]
    default:
      return [
        { value: 'native', label: 'export.formatNative', desc: 'export.formatNativeDesc' },
      ]
  }
})

const exportFormat = ref('ct')
watch(detectedModality, () => {
  const opts = formatOptions.value
  if (opts.length > 0 && !opts.find(o => o.value === exportFormat.value)) {
    exportFormat.value = opts[0].value
  }
}, { immediate: true })

function toggleSeries(uid: string) {
  const newSet = new Set(selectedSeriesUids.value)
  if (newSet.has(uid)) {
    newSet.delete(uid)
  } else {
    newSet.add(uid)
  }
  selectedSeriesUids.value = newSet
}

function selectAllSeries() {
  const newSet = new Set(selectedSeries.value.map((s: any) => s.series_uid))
  selectedSeriesUids.value = newSet
}

function getSeriesModality(uid: string): string {
  const series = selectedSeries.value.find((s: any) => s.series_uid === uid)
  return series?.modality || 'UNK'
}

function getSeriesName(uid: string): string {
  const series = selectedSeries.value.find((s: any) => s.series_uid === uid)
  return series?.series_description || uid.slice(0, 12)
}

async function handleSingleExport() {
  const uid = Array.from(selectedSeriesUids.value)[0]
  if (!uid || exporting.value) return

  exporting.value = true
  exportResult.value = null
  try {
    const blob = await appStore.exportNrrd(selectedPatientId.value, uid, exportFormat.value, exportDtype.value, exportUnit.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedPatient.value?.name || 'export'}_${uid.slice(0, 8)}.nrrd.gz`
    a.click()
    URL.revokeObjectURL(url)
    exportResult.value = { success: true, message: t('export.exportSuccess') }
  } catch (e: any) {
    exportResult.value = { success: false, message: e.message || t('export.exportError') }
  } finally {
    exporting.value = false
  }
}

async function handleBatchExport() {
  if (selectedSeriesUids.value.size === 0 || exporting.value) return

  exporting.value = true
  batchExportComplete.value = false
  const uids = Array.from(selectedSeriesUids.value)
  exportProgress.total = uids.length
  exportProgress.current = 0

  // Clear previous results
  for (const key of Object.keys(exportResults)) {
    delete exportResults[key]
  }

  let successCount = 0
  let failCount = 0

  for (const uid of uids) {
    try {
      const blob = await appStore.exportNrrd(selectedPatientId.value, uid, exportFormat.value, exportDtype.value, exportUnit.value)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selectedPatient.value?.name || 'export'}_${uid.slice(0, 8)}.nrrd.gz`
      a.click()
      URL.revokeObjectURL(url)
      exportResults[uid] = { success: true, message: t('export.done') }
      successCount++
    } catch (e: any) {
      exportResults[uid] = { success: false, message: e.message || t('export.failed') }
      failCount++
    }
    exportProgress.current++
  }

  batchExportComplete.value = true
  batchExportSuccess.value = failCount === 0
  batchExportMessage.value = failCount === 0
    ? t('export.exportBatchSuccess', { count: successCount })
    : t('export.exportBatchPartial', { success: successCount, failed: failCount })
  exporting.value = false
}
</script>
