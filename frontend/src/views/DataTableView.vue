<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <div class="flex items-center justify-between">
        <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('datatable.title') }}</h1>
        <button
          v-if="tableRows.length > 0"
          class="px-3 py-1.5 text-xs font-medium text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
          @click="exportCSV"
        >
          {{ $t('datatable.exportCSV') }}
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <svg class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
          </svg>
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('datatable.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('datatable.noDataDesc') }}</p>
        </div>
      </div>

      <div v-else class="space-y-4">
        <!-- Filters -->
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex-1 min-w-[200px] relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-accent-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="$t('datatable.search')"
              class="w-full pl-9 pr-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>
          <select
            v-model="filterModality"
            class="px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          >
            <option value="">{{ $t('datatable.allModalities') }}</option>
            <option v-for="m in modalities" :key="m" :value="m">{{ m }}</option>
          </select>
          <select
            v-if="diseaseSites.length > 0"
            v-model="filterSite"
            class="px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          >
            <option value="">{{ $t('datatable.allSites') }}</option>
            <option v-for="site in diseaseSites" :key="site" :value="site">{{ site }}</option>
          </select>
          <select
            v-model="viewMode"
            class="px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          >
            <option value="series">{{ $t('datatable.bySeries') }}</option>
            <option value="patient">{{ $t('datatable.byPatient') }}</option>
          </select>
        </div>

        <!-- Table -->
        <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 overflow-hidden">
          <!-- Header -->
          <div class="grid gap-2 px-4 py-2.5 bg-accent-50 dark:bg-accent-700/50 text-xs font-medium text-accent-500 dark:text-accent-400 border-b border-accent-200 dark:border-accent-700"
            :class="viewMode === 'series' ? 'grid-cols-[1fr_1fr_120px_100px_80px]' : 'grid-cols-[1fr_1fr_100px_60px]'"
          >
            <button class="text-left flex items-center gap-1 hover:text-accent-700 dark:hover:text-accent-300" @click="toggleSort('name')">
              {{ viewMode === 'series' ? $t('datatable.colPatientStudy') : $t('datatable.colPatient') }}
              <SortIcon :field="'name'" :current="sortField" :dir="sortDir" />
            </button>
            <button class="text-left flex items-center gap-1 hover:text-accent-700 dark:hover:text-accent-300" @click="toggleSort('series_desc')">
              {{ viewMode === 'series' ? $t('datatable.colSeries') : $t('datatable.colID') }}
              <SortIcon :field="'series_desc'" :current="sortField" :dir="sortDir" />
            </button>
            <button class="text-left flex items-center gap-1 hover:text-accent-700 dark:hover:text-accent-300" @click="toggleSort('modality')">
              {{ $t('datatable.colModality') }}
              <SortIcon :field="'modality'" :current="sortField" :dir="sortDir" />
            </button>
            <button class="text-left flex items-center gap-1 hover:text-accent-700 dark:hover:text-accent-300" @click="toggleSort('file_count')">
              {{ $t('datatable.colSlices') }}
              <SortIcon :field="'file_count'" :current="sortField" :dir="sortDir" />
            </button>
            <span v-if="viewMode === 'series'" class="text-left">{{ $t('datatable.colAction') }}</span>
          </div>

          <!-- Rows -->
          <div class="divide-y divide-accent-100 dark:divide-accent-700 max-h-[calc(100vh-280px)] overflow-y-auto">
            <div
              v-for="(row, idx) in filteredRows"
              :key="idx"
              class="grid gap-2 px-4 py-3 text-sm hover:bg-accent-50 dark:hover:bg-accent-700/30 transition-colors items-center"
              :class="viewMode === 'series' ? 'grid-cols-[1fr_1fr_120px_100px_80px]' : 'grid-cols-[1fr_1fr_100px_60px]'"
            >
              <div>
                <p class="font-medium text-accent-900 dark:text-white truncate">
                  {{ viewMode === 'series' ? (row.patient_name || row.patient_id) : row.patient_name || 'Unknown' }}
                </p>
                <p v-if="viewMode === 'series'" class="text-xs text-accent-500 dark:text-accent-400 truncate">
                  {{ row.study_desc || row.study_uid }}
                </p>
              </div>
              <div class="truncate text-accent-700 dark:text-accent-300">
                {{ viewMode === 'series' ? (row.series_desc || row.series_uid) : row.patient_id }}
              </div>
              <div>
                <StatusBadge :status="row.modality" />
              </div>
              <div class="text-accent-600 dark:text-accent-400">
                {{ row.file_count }}
              </div>
              <div v-if="viewMode === 'series'">
                <button
                  class="text-xs text-primary-500 hover:text-primary-600 transition-colors"
                  @click="goToViewer(row.series_uid)"
                >
                  {{ $t('datatable.view') }}
                </button>
              </div>
            </div>
          </div>

          <div v-if="filteredRows.length === 0" class="p-8 text-center text-sm text-accent-400">
            {{ $t('datatable.noMatches') }}
          </div>
        </div>

        <!-- Summary -->
        <div class="flex items-center justify-between text-xs text-accent-500 dark:text-accent-400">
          <span>{{ $t('datatable.rowCount', { filtered: filteredRows.length, total: tableRows.length }) }}</span>
          <span>{{ $t('datatable.patientCount', { count: patients.length }) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import StatusBadge from '@/components/common/StatusBadge.vue'

const { t } = useI18n()
const appStore = useAppStore()
const router = useRouter()

const searchQuery = ref('')
const filterModality = ref('')
const filterSite = ref('')
const diseaseSites = ref<string[]>([])
const viewMode = ref<'series' | 'patient'>('series')
const sortField = ref('name')
const sortDir = ref<'asc' | 'desc'>('asc')

interface TableRow {
  patient_id: string
  patient_name: string
  study_uid: string
  study_desc: string
  series_uid: string
  series_desc: string
  modality: string
  file_count: number
  series_number: string
}

const patients = computed(() => appStore.patients || [])

const tableRows = computed<TableRow[]>(() => {
  const rows: TableRow[] = []
  for (const patient of patients.value) {
    for (const study of patient.studies) {
      for (const series of study.series) {
        rows.push({
          patient_id: patient.patient_id,
          patient_name: patient.name,
          study_uid: study.study_uid,
          study_desc: study.description,
          series_uid: series.series_uid,
          series_desc: series.description,
          modality: series.modality,
          file_count: series.file_count,
          series_number: series.series_number,
        })
      }
    }
  }
  return rows
})

const modalities = computed(() => {
  const mods = new Set(tableRows.value.map(r => r.modality))
  return Array.from(mods).sort()
})

const filteredRows = computed(() => {
  let result = [...tableRows.value]

  if (filterModality.value) {
    result = result.filter(r => r.modality === filterModality.value)
  }

  if (filterSite.value) {
    const site = filterSite.value.toLowerCase()
    result = result.filter(r =>
      r.study_desc.toLowerCase().includes(site) ||
      r.series_desc.toLowerCase().includes(site)
    )
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(r =>
      r.patient_name.toLowerCase().includes(q) ||
      r.patient_id.toLowerCase().includes(q) ||
      r.study_desc.toLowerCase().includes(q) ||
      r.series_desc.toLowerCase().includes(q) ||
      r.series_uid.toLowerCase().includes(q)
    )
  }

  result.sort((a, b) => {
    let va: string | number, vb: string | number
    switch (sortField.value) {
      case 'name': va = a.patient_name; vb = b.patient_name; break
      case 'series_desc': va = a.series_desc; vb = b.series_desc; break
      case 'modality': va = a.modality; vb = b.modality; break
      case 'file_count': va = a.file_count; vb = b.file_count; break
      default: va = a.patient_name; vb = b.patient_name
    }
    if (typeof va === 'number' && typeof vb === 'number') {
      return sortDir.value === 'asc' ? va - vb : vb - va
    }
    const cmp = String(va).localeCompare(String(vb))
    return sortDir.value === 'asc' ? cmp : -cmp
  })

  return result
})

function toggleSort(field: string) {
  if (sortField.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDir.value = 'asc'
  }
}

function goToViewer(seriesUid: string) {
  appStore.selectSeries(seriesUid)
  router.push('/viewer')
}

function exportCSV() {
  const headers = viewMode.value === 'series'
    ? [t('datatable.csvPatientName'), t('datatable.csvPatientID'), t('datatable.csvStudy'), t('datatable.csvSeries'), t('datatable.csvModality'), t('datatable.csvSlices')]
    : [t('datatable.csvPatientName'), t('datatable.csvPatientID'), t('datatable.csvModality'), t('datatable.csvSlices')]
  const rows = filteredRows.value.map(r =>
    viewMode.value === 'series'
      ? [r.patient_name, r.patient_id, r.study_desc, r.series_desc, r.modality, r.file_count]
      : [r.patient_name, r.patient_id, r.modality, r.file_count]
  )
  const csv = [headers, ...rows].map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'dicom_data.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  try {
    const res = await fetch('/api/config/disease-sites')
    if (res.ok) {
      const config = await res.json()
      if (config.rules && Array.isArray(config.rules)) {
        diseaseSites.value = config.rules
      }
    }
  } catch {
    // Keep empty on failure
  }
})
</script>
