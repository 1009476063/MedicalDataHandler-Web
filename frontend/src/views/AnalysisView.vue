<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('sequence.title') }}</h1>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <MagnifyingGlassIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('converter.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('sequence.noData') }}</p>
        </div>
      </div>

      <div v-else class="space-y-4">
        <!-- Patient Selector -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
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

          <div class="p-4 bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 flex items-end">
            <button
              @click="analyzeSequences"
              :disabled="!selectedPatientId || analyzing"
              class="w-full px-4 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-accent-300 dark:disabled:bg-accent-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              <ArrowPathIcon v-if="analyzing" class="w-4 h-4 animate-spin" />
              {{ analyzing ? $t('sequence.analyzing') : $t('sequence.analyze') }}
            </button>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300">
          {{ error }}
        </div>

        <!-- Analysis Results -->
        <div v-if="analysisResult" class="space-y-4">
          <!-- Sequence Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div
              v-for="seq in analysisResult.all_series"
              :key="seq.series_uid"
              class="p-4 bg-white dark:bg-accent-800 rounded-xl border transition-colors"
              :class="seq.candidate_for
                ? 'border-primary-400 dark:border-primary-500 ring-1 ring-primary-200 dark:ring-primary-800'
                : 'border-accent-200 dark:border-accent-700'"
            >
              <div class="flex items-start justify-between mb-2">
                <div>
                  <span class="inline-block px-2 py-0.5 text-xs font-medium bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 rounded-full mb-1">
                    {{ seq.type || seq.modality }}
                  </span>
                  <h4 class="text-sm font-medium text-accent-900 dark:text-white">{{ seq.description || 'Unnamed' }}</h4>
                </div>
                <span v-if="seq.candidate_for" class="px-2 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 rounded-full">
                  {{ $t('sequence.selected') }}
                </span>
              </div>
              <div class="space-y-1 text-xs text-accent-500 dark:text-accent-400">
                <p>{{ $t('sequence.seriesModality') }}: {{ seq.modality }}</p>
                <p>{{ $t('sequence.seriesCount') }}: {{ seq.file_count }}</p>
                <p v-if="seq.dwi_info">{{ seq.dwi_info }}</p>
                <p v-if="seq.dce_info">{{ seq.dce_info }}</p>
                <p v-if="seq.reason" class="text-primary-600 dark:text-primary-400">{{ seq.reason }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Log Panel -->
        <LogPanel />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { MagnifyingGlassIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'
import LogPanel from '@/components/common/LogPanel.vue'

const appStore = useAppStore()
const patients = computed(() => appStore.patients)
const selectedPatientId = ref('')
const analyzing = ref(false)
const analysisResult = ref<any>(null)
const error = ref('')

function onPatientChange() {
  analysisResult.value = null
}

async function analyzeSequences() {
  if (!selectedPatientId.value || !appStore.sessionId) return
  analyzing.value = true
  try {
    const res = await fetch('/api/analysis/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: appStore.sessionId,
        patient_id: selectedPatientId.value,
      }),
    })
    const data = await res.json()
    if (data.success) {
      analysisResult.value = data.data
    } else {
      error.value = data.detail || 'Analysis failed'
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Network error during analysis'
  } finally {
    analyzing.value = false
  }
}
</script>
