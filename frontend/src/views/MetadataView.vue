<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('metadata.title') }}</h1>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- File list sidebar -->
      <div class="w-72 border-r border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 overflow-y-auto hidden lg:block">
        <div class="p-3">
          <div class="relative mb-3">
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="$t('metadata.searchFiles')"
              class="w-full pl-8 pr-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
            <svg class="absolute left-2.5 top-2.5 w-4 h-4 text-accent-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
          </div>

          <!-- Patient filter -->
          <select
            v-model="filterPatientId"
            class="w-full px-3 py-2 mb-3 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          >
            <option value="">{{ $t('metadata.allPatients') }}</option>
            <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
              {{ p.name || p.patient_id }}
            </option>
          </select>

          <!-- Modality filter -->
          <select
            v-model="filterModality"
            class="w-full px-3 py-2 mb-3 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          >
            <option value="">{{ $t('metadata.allModalities') }}</option>
            <option v-for="m in availableModalities" :key="m" :value="m">{{ m }}</option>
          </select>

          <!-- File list -->
          <div class="space-y-1">
            <button
              v-for="file in filteredFiles"
              :key="file.id"
              :class="[
                'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                selectedFileId === file.id
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'hover:bg-accent-50 dark:hover:bg-accent-800/50 text-accent-700 dark:text-accent-300',
              ]"
              @click="selectFile(file.id)"
            >
              <div class="flex items-center gap-2">
                <StatusBadge :status="file.modality" />
                <span class="truncate text-xs">{{ file.filename }}</span>
              </div>
            </button>
          </div>

          <div v-if="filteredFiles.length === 0" class="text-center py-8 text-sm text-accent-400">
            {{ $t('metadata.noFiles') }}
          </div>
        </div>
      </div>

      <!-- Metadata display -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="!selectedFileId" class="flex items-center justify-center h-full">
          <div class="text-center">
            <svg class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('metadata.selectFile') }}</h3>
            <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('metadata.selectFileDesc') }}</p>
          </div>
        </div>

        <div v-else-if="loadingMetadata" class="flex items-center justify-center h-full">
          <LoadingSpinner size="lg" :text="$t('metadata.loadingMetadata')" />
        </div>

        <div v-else-if="metadata" class="p-4 space-y-4">
          <!-- Tag search -->
          <div class="relative">
            <input
              v-model="tagSearch"
              type="text"
              :placeholder="$t('metadata.tagSearch')"
              class="w-full pl-8 pr-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
            <svg class="absolute left-2.5 top-2.5 w-4 h-4 text-accent-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
          </div>

          <!-- Key metadata cards -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div v-for="(card, idx) in keyMetadataCards" :key="idx" class="p-3 bg-white dark:bg-accent-800 rounded-lg border border-accent-200 dark:border-accent-700">
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ card.label }}</p>
              <p class="text-sm font-medium text-accent-900 dark:text-white mt-0.5 truncate">{{ card.value || 'N/A' }}</p>
            </div>
          </div>

          <!-- Full tag table -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 overflow-hidden">
            <div class="px-4 py-3 border-b border-accent-200 dark:border-accent-700 flex items-center justify-between">
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                {{ $t('metadata.dicomTags') }}
                <span class="text-accent-400 dark:text-accent-500 font-normal">{{ $t('metadata.tagCount', { count: filteredTags.length }) }}</span>
              </h3>
              <button
                class="text-xs text-primary-500 hover:text-primary-600 transition-colors"
                @click="copyAllTags"
              >
                {{ $t('metadata.copyAll') }}
              </button>
            </div>

            <!-- Table header -->
            <div class="grid grid-cols-[100px_1fr_50px_1fr] gap-2 px-4 py-2 bg-accent-50 dark:bg-accent-700/50 text-xs font-medium text-accent-500 dark:text-accent-400 border-b border-accent-200 dark:border-accent-700">
              <span>{{ $t('metadata.colTag') }}</span>
              <span>{{ $t('metadata.colName') }}</span>
              <span>{{ $t('metadata.colVR') }}</span>
              <span>{{ $t('metadata.colValue') }}</span>
            </div>

            <!-- Tag rows (virtual scrolled) -->
            <div
              ref="tagScrollContainer"
              class="max-h-[60vh] overflow-y-auto"
              @scroll="onTagScroll"
            >
              <div :style="{ height: tagTotalHeight + 'px', position: 'relative' }">
                <div
                  :style="{ transform: `translateY(${tagOffsetY}px)` }"
                  class="divide-y divide-accent-100 dark:divide-accent-700"
                >
                  <div
                    v-for="(tag, idx) in visibleTags"
                    :key="tagStartIndex + idx"
                    class="grid grid-cols-[100px_1fr_50px_1fr] gap-2 px-4 py-2 text-xs hover:bg-accent-50 dark:hover:bg-accent-700/30 transition-colors"
                  >
                    <span class="font-mono text-accent-500 dark:text-accent-400">{{ tag.tag }}</span>
                    <span class="text-accent-700 dark:text-accent-300 truncate">{{ tag.name }}</span>
                    <span class="font-mono text-accent-400 dark:text-accent-500">{{ tag.vr }}</span>
                    <span class="text-accent-900 dark:text-white font-mono truncate" :title="tag.value">{{ tag.value }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="filteredTags.length === 0" class="p-8 text-center text-sm text-accent-400">
              {{ $t('metadata.noTagsMatch') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const appStore = useAppStore()

const searchQuery = ref('')
const filterPatientId = ref('')
const filterModality = ref('')
const tagSearch = ref('')
const selectedFileId = ref<string | null>(null)
const metadata = ref<Record<string, { name: string; value: string; vr: string }> | null>(null)
const loadingMetadata = ref(false)
const allFiles = ref<Array<{ id: string; filename: string; modality: string; patient_id: string; series_uid: string }>>([])

const patients = computed(() => appStore.patients || [])

async function loadAllFiles() {
  if (!appStore.sessionId || patients.value.length === 0) {
    allFiles.value = []
    return
  }
  const files: Array<{ id: string; filename: string; modality: string; patient_id: string; series_uid: string }> = []
  for (const patient of patients.value) {
    try {
      const res = await fetch(`/api/dicom/patient/${appStore.sessionId}/${patient.patient_id}`)
      if (res.ok) {
        const data = await res.json()
        for (const f of data.files || []) {
          files.push({
            id: f.id,
            filename: f.filename,
            modality: f.modality,
            patient_id: patient.patient_id,
            series_uid: f.series_uid,
          })
        }
      }
    } catch { /* skip */ }
  }
  allFiles.value = files
}

watch(() => appStore.sessionId, () => { selectedFileId.value = null; metadata.value = null; loadAllFiles() }, { immediate: true })
watch(patients, () => loadAllFiles())

const availableModalities = computed(() => {
  const mods = new Set(allFiles.value.map(f => f.modality))
  return Array.from(mods).sort()
})

const filteredFiles = computed(() => {
  let result = allFiles.value

  if (filterPatientId.value) {
    result = result.filter(f => f.patient_id === filterPatientId.value)
  }

  if (filterModality.value) {
    result = result.filter(f => f.modality === filterModality.value)
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(f =>
      f.filename.toLowerCase().includes(q) ||
      f.patient_id.toLowerCase().includes(q) ||
      f.series_uid.toLowerCase().includes(q)
    )
  }

  return result
})

const keyMetadataCards = computed(() => {
  if (!metadata.value) return []
  const keys = [
    'PatientName', 'PatientID', 'PatientBirthDate', 'PatientSex',
    'StudyDescription', 'Modality', 'SeriesDescription', 'NumberOfFrames',
    'Rows', 'Columns', 'BitsAllocated', 'PixelSpacing',
    'ImagePositionPatient', 'RescaleIntercept', 'RescaleSlope',
  ]
  return keys
    .filter(k => metadata.value![k])
    .map(k => ({
      label: k,
      value: metadata.value![k].value,
    }))
    .slice(0, 8)
})

const filteredTags = computed(() => {
  if (!metadata.value) return []
  const tags = Object.entries(metadata.value).map(([tag, info]) => ({
    tag,
    name: info.name,
    vr: info.vr,
    value: info.value,
  }))

  if (!tagSearch.value) return tags

  const q = tagSearch.value.toLowerCase()
  return tags.filter(t =>
    t.tag.toLowerCase().includes(q) ||
    t.name.toLowerCase().includes(q) ||
    t.value.toLowerCase().includes(q)
  )
})

// Virtual scrolling for DICOM tags
const TAG_ROW_HEIGHT = 36
const TAG_VISIBLE_BUFFER = 10
const tagScrollContainer = ref<HTMLElement | null>(null)
const tagScrollTop = ref(0)

const tagTotalHeight = computed(() => filteredTags.value.length * TAG_ROW_HEIGHT)
const tagStartIndex = computed(() => Math.max(0, Math.floor(tagScrollTop.value / TAG_ROW_HEIGHT) - TAG_VISIBLE_BUFFER))
const tagEndIndex = computed(() => {
  const containerHeight = tagScrollContainer.value?.clientHeight || 600
  return Math.min(filteredTags.value.length, Math.ceil((tagScrollTop.value + containerHeight) / TAG_ROW_HEIGHT) + TAG_VISIBLE_BUFFER)
})
const visibleTags = computed(() => filteredTags.value.slice(tagStartIndex.value, tagEndIndex.value))
const tagOffsetY = computed(() => tagStartIndex.value * TAG_ROW_HEIGHT)

function onTagScroll(e: Event) {
  tagScrollTop.value = (e.target as HTMLElement).scrollTop
}

watch(filteredTags, () => {
  tagScrollTop.value = 0
  if (tagScrollContainer.value) tagScrollContainer.value.scrollTop = 0
})

watch(selectedFileId, async (fileId) => {
  if (!fileId) {
    metadata.value = null
    return
  }
  loadingMetadata.value = true
  metadata.value = null
  try {
    const res = await fetch(`/api/dicom/metadata/${appStore.sessionId}/${fileId}`)
    if (res.ok) {
      const data = await res.json()
      metadata.value = data.all_tags || data.metadata || data
    }
  } catch {
    metadata.value = null
  } finally {
    loadingMetadata.value = false
  }
})

function selectFile(fileId: string) {
  selectedFileId.value = fileId
}

function copyAllTags() {
  if (!metadata.value) return
  const lines = Object.entries(metadata.value).map(
    ([tag, info]) => `${tag}\t${info.name}\t${info.vr}\t${info.value}`
  )
  navigator.clipboard.writeText(lines.join('\n'))
}
</script>
