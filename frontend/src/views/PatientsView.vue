<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-accent-900 dark:text-white">{{ $t('patients.title') }}</h1>
        <p class="text-sm text-accent-500 dark:text-accent-400">
          {{ $t('patients.subtitle', { count: patients.length }) }}
        </p>
      </div>
      <button
        class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="refreshing"
        @click="handleRefresh"
      >
        <ArrowPathIcon :class="['w-4 h-4', refreshing ? 'animate-spin' : '']" />
        {{ $t('patients.refresh') }}
      </button>
    </div>

    <div class="flex items-center gap-3">
      <div class="flex-1 relative">
        <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-accent-400" />
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="$t('patients.searchPlaceholder')"
          class="w-full pl-10 pr-4 py-2 bg-white dark:bg-accent-900 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-colors"
        />
      </div>
    </div>

    <div v-if="filteredPatients.length === 0 && !appStore.uploading" class="text-center py-16">
      <UserGroupIcon class="w-16 h-16 text-accent-300 dark:text-accent-600 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('patients.emptyTitle') }}</h3>
      <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">
        {{ searchQuery ? $t('patients.emptySearch') : $t('patients.emptyUpload') }}
      </p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="patient in filteredPatients"
        :key="patient.patient_id"
        class="bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card overflow-hidden"
      >
        <div
          class="flex items-center justify-between p-4 cursor-pointer hover:bg-accent-50 dark:hover:bg-accent-800/50 transition-colors"
          @click="toggleExpand(patient.patient_id)"
        >
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-xl bg-primary-100 dark:bg-primary-900/30">
              <UserIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p class="font-medium text-accent-900 dark:text-white">{{ patient.name || $t('patients.unknown') }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">
                ID: {{ patient.patient_id }} · {{ $t('patients.studies', { count: patient.studies?.length || 0 }) }}
              </p>
            </div>
          </div>
          <ChevronDownIcon
            :class="[
              'w-5 h-5 text-accent-400 transition-transform',
              expandedPatients.has(patient.patient_id) ? 'rotate-180' : '',
            ]"
          />
        </div>

        <div v-if="expandedPatients.has(patient.patient_id)" class="border-t border-accent-200 dark:border-accent-700">
          <div v-if="patient.studies?.length" class="divide-y divide-accent-100 dark:divide-accent-800">
            <div
              v-for="study in patient.studies"
              :key="study.study_uid"
              class="px-4 py-3 ml-4"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <DocumentTextIcon class="w-4 h-4 text-accent-400" />
                  <span class="text-sm font-medium text-accent-800 dark:text-accent-200">
                    {{ study.description || study.study_uid }}
                  </span>
                </div>
                <span class="text-xs text-accent-500 dark:text-accent-400">
                  {{ $t('patients.studies', { count: study.series?.length || 0 }) }}
                </span>
              </div>

              <div v-if="study.series?.length" class="ml-6 space-y-2">
                <div
                  v-for="series in study.series"
                  :key="series.series_uid"
                  class="flex items-center justify-between p-2 rounded-lg bg-accent-50 dark:bg-accent-800/50"
                >
                  <div class="flex items-center gap-2">
                    <CubeIcon class="w-4 h-4 text-accent-400" />
                    <span class="text-sm text-accent-700 dark:text-accent-300">
                      {{ series.description || series.series_uid }}
                    </span>
                    <StatusBadge :status="series.modality" />
                  </div>
                  <span class="text-xs text-accent-500 dark:text-accent-400">
                    {{ $t('patients.slices', { count: series.file_count || 0 }) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="px-4 py-6 text-center">
            <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('patients.noStudies') }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  UserGroupIcon,
  UserIcon,
  DocumentTextIcon,
  CubeIcon,
  ChevronDownIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
} from '@heroicons/vue/24/outline'

const appStore = useAppStore()
const searchQuery = ref('')
const refreshing = ref(false)
const expandedPatients = reactive(new Set<string>())

async function handleRefresh() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    await appStore.refreshPatients()
  } finally {
    refreshing.value = false
  }
}

const patients = computed(() => appStore.patients || [])

const filteredPatients = computed(() => {
  if (!searchQuery.value) return patients.value
  const q = searchQuery.value.toLowerCase()
  return patients.value.filter(
    (p) =>
      (p.name?.toLowerCase().includes(q)) ||
      (p.patient_id?.toLowerCase().includes(q))
  )
})

function toggleExpand(patientId: string) {
  if (expandedPatients.has(patientId)) {
    expandedPatients.delete(patientId)
  } else {
    expandedPatients.add(patientId)
  }
}
</script>
