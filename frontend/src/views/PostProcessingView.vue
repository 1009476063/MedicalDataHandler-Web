<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('processing.title') }}</h1>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <CogIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('processing.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('processing.noDataDesc') }}</p>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- HU to RED Conversion -->
        <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <h2 class="text-sm font-semibold text-accent-900 dark:text-white mb-3 flex items-center gap-2">
            <BeakerIcon class="w-4 h-4 text-primary-500" />
            {{ $t('processing.huToRed') }}
          </h2>
          <p class="text-xs text-accent-500 dark:text-accent-400 mb-3">
            {{ $t('processing.huToRedDesc') }}
          </p>

          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('processing.patient') }}</label>
              <select
                v-model="huPatientId"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-700 border border-accent-200 dark:border-accent-600 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                <option value="">{{ $t('processing.selectPatient') }}</option>
                <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
                  {{ p.name || p.patient_id }}
                </option>
              </select>
            </div>

            <div v-if="huPatientId">
              <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('processing.ctSeries') }}</label>
              <select
                v-model="huSeriesUid"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-700 border border-accent-200 dark:border-accent-600 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                <option value="">{{ $t('processing.selectCtSeries') }}</option>
                <option v-for="s in ctSeries" :key="s.series_uid" :value="s.series_uid">
                  {{ s.description || s.series_uid }}
                </option>
              </select>
            </div>

            <button
              :disabled="!huSeriesUid || processing"
              class="w-full px-3 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              @click="convertHUtoRED"
            >
              {{ processing ? $t('processing.converting') : $t('processing.convertToRed') }}
            </button>

            <div v-if="huResult" class="p-2 rounded-lg text-xs" :class="huResult.success ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'">
              {{ huResult.message }}
            </div>
          </div>
        </div>

        <!-- Dose Summation -->
        <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <h2 class="text-sm font-semibold text-accent-900 dark:text-white mb-3 flex items-center gap-2">
            <Square3Stack3DIcon class="w-4 h-4 text-red-500" />
            {{ $t('processing.doseSummation') }}
          </h2>
          <p class="text-xs text-accent-500 dark:text-accent-400 mb-3">
            {{ $t('processing.doseSumDesc') }}
          </p>

          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('processing.patient') }}</label>
              <select
                v-model="dosePatientId"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-700 border border-accent-200 dark:border-accent-600 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                <option value="">{{ $t('processing.selectPatient') }}</option>
                <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
                  {{ p.name || p.patient_id }}
                </option>
              </select>
            </div>

            <div v-if="dosePatientId && doseFiles.length > 0">
              <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('processing.selectDoses') }}</label>
              <div class="space-y-1 max-h-32 overflow-y-auto">
                <label
                  v-for="d in doseFiles"
                  :key="d.id"
                  class="flex items-center gap-2 px-2 py-1.5 rounded text-xs text-accent-700 dark:text-accent-300 hover:bg-accent-50 dark:hover:bg-accent-700/50 cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    :checked="selectedDoseIds.has(d.id)"
                    class="rounded border-accent-300 text-red-500 focus:ring-red-500/50"
                    @change="toggleDoseFile(d.id)"
                  />
                  <span class="truncate">{{ d.filename || d.id }}</span>
                </label>
              </div>
            </div>

            <div v-if="dosePatientId && doseFiles.length === 0" class="text-xs text-accent-400 text-center py-2">
              {{ $t('processing.noDoseFiles') }}
            </div>

            <button
              :disabled="selectedDoseIds.size < 2 || processing"
              class="w-full px-3 py-2 bg-red-500 hover:bg-red-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              @click="sumDoses"
            >
              {{ processing ? $t('processing.summing') : $t('processing.sumDoses', { count: selectedDoseIds.size }) }}
            </button>

            <div v-if="doseResult" class="p-2 rounded-lg text-xs" :class="doseResult.success ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'">
              {{ doseResult.message }}
            </div>
          </div>
        </div>

        <!-- TG-263 Structure Renaming -->
        <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <h2 class="text-sm font-semibold text-accent-900 dark:text-white mb-3 flex items-center gap-2">
            <TagIcon class="w-4 h-4 text-green-500" />
            {{ $t('processing.tg263') }}
          </h2>
          <p class="text-xs text-accent-500 dark:text-accent-400 mb-3">
            {{ $t('processing.tg263Desc') }}
          </p>

          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('processing.patient') }}</label>
              <select
                v-model="renamePatientId"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-700 border border-accent-200 dark:border-accent-600 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                <option value="">{{ $t('processing.selectPatient') }}</option>
                <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
                  {{ p.name || p.patient_id }}
                </option>
              </select>
            </div>

            <div v-if="renamePatientId">
              <label class="block text-xs font-medium text-accent-700 dark:text-accent-300 mb-1">{{ $t('processing.structures') }}</label>
              <div class="space-y-1 max-h-40 overflow-y-auto">
                <div
                  v-for="s in structs"
                  :key="s.key"
                  class="flex items-center gap-2 px-2 py-1.5 rounded text-xs text-accent-700 dark:text-accent-300"
                >
                  <span class="truncate flex-1">{{ s.name }}</span>
                  <button
                    class="text-primary-500 hover:text-primary-600 transition-colors"
                    @click="showRenameDialog(s)"
                  >
                    {{ $t('processing.rename') }}
                  </button>
                </div>
              </div>
            </div>

            <button
              :disabled="!renamePatientId || structs.length === 0 || processing"
              class="w-full px-3 py-2 bg-green-500 hover:bg-green-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              @click="autoRenameStructs"
            >
              {{ processing ? $t('processing.renaming') : $t('processing.autoRename') }}
            </button>

            <div v-if="renameResult" class="p-2 rounded-lg text-xs" :class="renameResult.success ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'">
              {{ renameResult.message }}
            </div>
          </div>
        </div>

        <!-- Activity Log -->
        <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
          <h2 class="text-sm font-semibold text-accent-900 dark:text-white mb-3 flex items-center gap-2">
            <DocumentTextIcon class="w-4 h-4 text-accent-500" />
            {{ $t('processing.activityLog') }}
          </h2>
          <div class="space-y-1 max-h-64 overflow-y-auto font-mono text-xs">
            <div
              v-for="(log, idx) in activityLog"
              :key="idx"
              class="flex gap-2"
            >
              <span class="text-accent-400 flex-shrink-0">{{ log.time }}</span>
              <span :class="log.type === 'error' ? 'text-red-500' : log.type === 'success' ? 'text-green-500' : 'text-accent-600 dark:text-accent-400'">
                {{ log.message }}
              </span>
            </div>
            <div v-if="activityLog.length === 0" class="text-accent-400 text-center py-4">
              {{ $t('processing.noActivity') }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Rename Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showRenameModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          @click.self="showRenameModal = false"
        >
          <div class="bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-xl max-w-sm w-full mx-4 p-6 animate-scale-in">
            <h3 class="text-lg font-semibold text-accent-900 dark:text-white mb-2">{{ $t('processing.renameTitle') }}</h3>
            <p class="text-sm text-accent-600 dark:text-accent-400 mb-4">
              {{ $t('processing.currentName', { name: renameTarget?.name }) }}
            </p>
            <input
              v-model="newStructName"
              type="text"
              class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              :placeholder="$t('processing.newNamePlaceholder')"
              @keyup.enter="confirmRename"
            />
            <div class="flex justify-end gap-3 mt-4">
              <button
                class="px-4 py-2 text-sm text-accent-700 dark:text-accent-300 hover:bg-accent-100 dark:hover:bg-accent-800 rounded-lg transition-colors"
                @click="showRenameModal = false"
              >
                {{ $t('processing.cancel') }}
              </button>
              <button
                :disabled="!newStructName"
                class="px-4 py-2 text-sm bg-primary-500 hover:bg-primary-600 disabled:bg-accent-300 dark:disabled:bg-accent-700 text-white rounded-lg transition-colors"
                @click="confirmRename"
              >
                {{ $t('processing.renameConfirm') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import {
  CogIcon, BeakerIcon, Square3Stack3DIcon, TagIcon, DocumentTextIcon
} from '@heroicons/vue/24/outline'

const { t } = useI18n()
const appStore = useAppStore()

// HU to RED state
const huPatientId = ref('')
const huSeriesUid = ref('')
const huResult = ref<{ success: boolean; message: string } | null>(null)

// Dose summation state
const dosePatientId = ref('')
const selectedDoseIds = ref<Set<string>>(new Set())
const doseResult = ref<{ success: boolean; message: string } | null>(null)

// Structure renaming state
const renamePatientId = ref('')
const structs = ref<Array<{ key: string; name: string }>>([])
const renameResult = ref<{ success: boolean; message: string } | null>(null)
const showRenameModal = ref(false)
const renameTarget = ref<{ key: string; name: string } | null>(null)
const newStructName = ref('')

// Common state
const processing = ref(false)

// Activity log
interface LogEntry {
  time: string
  message: string
  type: 'info' | 'success' | 'error'
}
const activityLog = ref<LogEntry[]>([])

const patients = computed(() => appStore.patients || [])

const ctSeries = computed(() => {
  const patient = patients.value.find(p => p.patient_id === huPatientId.value)
  if (!patient) return []
  return patient.studies.flatMap(s => s.series || []).filter(s => s.modality === 'CT')
})

const doseFiles = ref<Array<{ id: string; filename: string }>>([])

function addLog(message: string, type: 'info' | 'success' | 'error' = 'info') {
  const now = new Date()
  const time = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  activityLog.value.unshift({ time, message, type })
  if (activityLog.value.length > 100) {
    activityLog.value.pop()
  }
}

// Load dose files when patient changes
watch(dosePatientId, async (pid) => {
  if (!pid) {
    doseFiles.value = []
    return
  }
  try {
    const res = await fetch(`/api/dicom/patient/${appStore.sessionId}/${pid}`)
    if (res.ok) {
      const data = await res.json()
      doseFiles.value = (data.files || [])
        .filter((f: any) => f.modality === 'RTDOSE')
        .map((f: any) => ({ id: f.id, filename: f.filename }))
    }
  } catch {
    doseFiles.value = []
  }
})

// Load structs when patient changes
watch(renamePatientId, async (pid) => {
  if (!pid) {
    structs.value = []
    return
  }
  try {
    const res = await fetch(`/api/dicom/structs/${appStore.sessionId}/${pid}`)
    if (res.ok) {
      const data = await res.json()
      structs.value = data.structures || []
    }
  } catch {
    structs.value = []
  }
})

function toggleDoseFile(id: string) {
  const newSet = new Set(selectedDoseIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  selectedDoseIds.value = newSet
}

async function convertHUtoRED() {
  if (!huSeriesUid.value || processing.value) return
  processing.value = true
  huResult.value = null
  addLog(`Starting HU to RED conversion for series ${huSeriesUid.value.slice(0, 8)}...`)

  try {
    const res = await fetch('/api/postprocessing/convert-hu', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: appStore.sessionId,
        patient_id: huPatientId.value,
        series_uid: huSeriesUid.value,
        conversion_type: 'red',
      }),
    })

    if (res.ok) {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `RED_${huSeriesUid.value.slice(0, 8)}.nrrd`
      a.click()
      URL.revokeObjectURL(url)
      huResult.value = { success: true, message: t('processing.redSuccess') }
      addLog('HU to RED conversion completed successfully', 'success')
    } else {
      const err = await res.json()
      huResult.value = { success: false, message: err.detail || t('processing.redFailed') }
      addLog(`HU to RED conversion failed: ${err.detail}`, 'error')
    }
  } catch (e: any) {
    huResult.value = { success: false, message: e.message || t('processing.networkError') }
    addLog(`HU to RED conversion error: ${e.message}`, 'error')
  } finally {
    processing.value = false
  }
}

async function sumDoses() {
  if (selectedDoseIds.value.size < 2 || processing.value) return
  processing.value = true
  doseResult.value = null
  addLog(`Starting dose summation for ${selectedDoseIds.value.size} doses...`)

  try {
    const res = await fetch('/api/postprocessing/sum-doses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: appStore.sessionId,
        patient_id: dosePatientId.value,
        dose_file_ids: Array.from(selectedDoseIds.value),
      }),
    })

    if (res.ok) {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'summed_dose.nrrd'
      a.click()
      URL.revokeObjectURL(url)
      doseResult.value = { success: true, message: t('processing.doseSuccess') }
      addLog('Dose summation completed successfully', 'success')
    } else {
      const err = await res.json()
      doseResult.value = { success: false, message: err.detail || t('processing.doseFailed') }
      addLog(`Dose summation failed: ${err.detail}`, 'error')
    }
  } catch (e: any) {
    doseResult.value = { success: false, message: e.message || t('processing.networkError') }
    addLog(`Dose summation error: ${e.message}`, 'error')
  } finally {
    processing.value = false
  }
}

async function autoRenameStructs() {
  if (!renamePatientId.value || processing.value) return
  processing.value = true
  renameResult.value = null
  addLog('Starting auto-rename with TG-263 conventions...')

  try {
    const res = await fetch(`/api/postprocessing/auto-rename-structs?session_id=${appStore.sessionId}&patient_id=${renamePatientId.value}`, {
      method: 'POST',
    })

    if (res.ok) {
      const data = await res.json()
      renameResult.value = {
        success: true,
        message: t('processing.renamedCount', { count: data.renamed })
      }
      addLog(`Auto-renamed ${data.renamed} structures`, 'success')

      // Refresh struct list
      const structRes = await fetch(`/api/dicom/structs/${appStore.sessionId}/${renamePatientId.value}`)
      if (structRes.ok) {
        const structData = await structRes.json()
        structs.value = structData.structures || []
      }
    } else {
      const err = await res.json()
      renameResult.value = { success: false, message: err.detail || t('processing.renameFailed') }
      addLog(`Auto-rename failed: ${err.detail}`, 'error')
    }
  } catch (e: any) {
    renameResult.value = { success: false, message: e.message || t('processing.networkError') }
    addLog(`Auto-rename error: ${e.message}`, 'error')
  } finally {
    processing.value = false
  }
}

function showRenameDialog(struct: { key: string; name: string }) {
  renameTarget.value = struct
  newStructName.value = struct.name
  showRenameModal.value = true
}

async function confirmRename() {
  if (!renameTarget.value || !newStructName.value || !renamePatientId.value) return

  processing.value = true
  try {
    const res = await fetch('/api/postprocessing/rename-struct', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: appStore.sessionId,
        patient_id: renamePatientId.value,
        struct_key: renameTarget.value.key,
        new_name: newStructName.value,
      }),
    })

    if (res.ok) {
      addLog(`Renamed "${renameTarget.value.name}" to "${newStructName.value}"`, 'success')
      // Update local list
      const idx = structs.value.findIndex(s => s.key === renameTarget.value!.key)
      if (idx >= 0) {
        structs.value[idx] = { ...structs.value[idx], name: newStructName.value }
      }
    } else {
      const err = await res.json()
      addLog(`Rename failed: ${err.detail}`, 'error')
    }
  } catch (e: any) {
    addLog(`Rename error: ${e.message}`, 'error')
  } finally {
    processing.value = false
    showRenameModal.value = false
  }
}
</script>
