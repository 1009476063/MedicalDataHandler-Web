<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-accent-900 dark:text-white">{{ $t('dashboard.title') }}</h1>
        <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('dashboard.subtitle') }}</p>
      </div>
      <div v-if="!backendAvailable" class="flex items-center gap-2 px-3 py-1.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-xs font-medium">
        <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
        {{ $t('dashboard.clientMode') }}
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        :title="$t('dashboard.statPatients')"
        :value="patients.length"
        :icon="UserGroupIcon"
        color="primary"
      />
      <StatCard
        :title="$t('dashboard.statStudies')"
        :value="totalStudies"
        :icon="DocumentTextIcon"
        color="blue"
      />
      <StatCard
        :title="$t('dashboard.statSeries')"
        :value="totalSeries"
        :icon="CubeIcon"
        color="purple"
      />
      <StatCard
        :title="$t('dashboard.statSession')"
        :value="appStore.sessionId ? $t('dashboard.yes') : $t('dashboard.no')"
        :icon="CheckCircleIcon"
        color="green"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('dashboard.uploadSection') }}</h2>
        <div
          class="border-2 border-dashed border-accent-300 dark:border-accent-600 rounded-xl p-8 text-center hover:border-primary-400 dark:hover:border-primary-500 transition-colors cursor-pointer"
          @click="triggerFileInput"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <ArrowUpTrayIcon class="w-10 h-10 text-accent-400 mx-auto mb-3" />
          <p class="text-sm font-medium text-accent-700 dark:text-accent-300">
            {{ $t('dashboard.dropHint') }}
          </p>
          <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">
            {{ $t('dashboard.dropSupport') }}
          </p>
          <input
            ref="fileInput"
            type="file"
            multiple
            webkitdirectory
            class="hidden"
            @change="handleFileSelect"
          />
        </div>

        <!-- Client-side preview -->
        <div v-if="preview && !uploading" class="mt-4 space-y-3">
          <div class="flex items-center justify-between text-sm">
            <span class="font-medium text-accent-700 dark:text-accent-300">{{ $t('dashboard.previewTitle') }}</span>
            <button
              class="text-xs text-accent-500 hover:text-accent-700 dark:hover:text-accent-300"
              @click="clearPreview"
            >{{ $t('dashboard.clearPreview') }}</button>
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs text-accent-600 dark:text-accent-400">
            <div class="p-2 rounded-lg bg-accent-50 dark:bg-accent-800/50">
              <span class="font-medium">{{ $t('dashboard.previewFiles') }}:</span> {{ preview.totalFiles }}
            </div>
            <div class="p-2 rounded-lg bg-accent-50 dark:bg-accent-800/50">
              <span class="font-medium">{{ $t('dashboard.previewSize') }}:</span> {{ formatSize(preview.totalSize) }}
            </div>
            <div class="p-2 rounded-lg bg-accent-50 dark:bg-accent-800/50">
              <span class="font-medium">{{ $t('dashboard.previewPatients') }}:</span> {{ preview.patients.size }}
            </div>
            <div class="p-2 rounded-lg bg-accent-50 dark:bg-accent-800/50">
              <span class="font-medium">{{ $t('dashboard.previewParsed') }}:</span> {{ preview.parsedCount }} / {{ preview.totalFiles }}
            </div>
          </div>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div
              v-for="[pid, patient] in preview.patients"
              :key="pid"
              class="p-2 rounded-lg bg-accent-50 dark:bg-accent-800/50 text-xs"
            >
              <p class="font-medium text-accent-800 dark:text-accent-200">{{ patient.name || 'Unknown' }} <span class="text-accent-500">({{ pid }})</span></p>
              <div v-for="[studyName, study] in patient.studies" :key="studyName" class="ml-3 mt-1">
                <p class="text-accent-600 dark:text-accent-400">{{ studyName }}</p>
                <div v-for="[seriesName, series] in study.series" :key="seriesName" class="ml-3 mt-0.5 flex items-center gap-2">
                  <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">{{ series.modality }}</span>
                  <span class="text-accent-500 dark:text-accent-400 truncate">{{ seriesName || 'No description' }}</span>
                  <span class="text-accent-400 dark:text-accent-500">({{ series.fileCount }})</span>
                </div>
              </div>
            </div>
          </div>
          <button
            class="w-full px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors"
            @click="confirmUpload"
          >
            {{ $t('dashboard.uploadToServer') }}
          </button>
        </div>

        <div v-if="uploading" class="mt-4">
          <div class="flex items-center justify-between text-sm text-accent-600 dark:text-accent-400 mb-1">
            <span>{{ $t('dashboard.uploading') }}</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="w-full bg-accent-200 dark:bg-accent-700 rounded-full h-2">
            <div
              class="bg-primary-500 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${uploadProgress}%` }"
            />
          </div>
        </div>
        <button
          v-if="!uploading && !preview"
          class="mt-4 w-full px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors"
          @click="triggerFileInput"
        >
          {{ $t('dashboard.selectFiles') }}
        </button>
      </div>

      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('dashboard.recentPatients') }}</h2>
        <div v-if="patients.length === 0" class="text-center py-8">
          <FolderOpenIcon class="w-10 h-10 text-accent-300 dark:text-accent-600 mx-auto mb-2" />
          <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('dashboard.emptyTitle') }}</p>
          <p class="text-xs text-accent-400 dark:text-accent-500 mt-1">{{ $t('dashboard.emptyDesc') }}</p>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="patient in recentPatients"
            :key="patient.patient_id"
            class="flex items-center justify-between p-3 rounded-lg bg-accent-50 dark:bg-accent-800/50 hover:bg-accent-100 dark:hover:bg-accent-800 transition-colors cursor-pointer"
            @click="goToPatient(patient)"
          >
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                <UserIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p class="text-sm font-medium text-accent-900 dark:text-white">{{ patient.name || $t('dashboard.unknown') }}</p>
                <p class="text-xs text-accent-500 dark:text-accent-400">
                  {{ $t('dashboard.studies', { count: patient.studies?.length || 0 }) }}
                </p>
              </div>
            </div>
            <ChevronRightIcon class="w-4 h-4 text-accent-400" />
          </div>
        </div>
      </div>
    </div>

    <LogPanel />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { ParseResult } from '@/utils/dicomClientParser'
import { useClientMode } from '@/composables/useClientMode'

let _parseDicomFiles: typeof import('@/utils/dicomClientParser').parseDicomFiles | null = null
async function lazyParseDicomFiles(files: File[]): Promise<ParseResult> {
  if (!_parseDicomFiles) {
    const mod = await import('@/utils/dicomClientParser')
    _parseDicomFiles = mod.parseDicomFiles
  }
  return _parseDicomFiles(files)
}
import { useSettings } from '@/composables/useSettings'
import StatCard from '@/components/common/StatCard.vue'
import LogPanel from '@/components/common/LogPanel.vue'
import {
  UserGroupIcon,
  DocumentTextIcon,
  CubeIcon,
  CheckCircleIcon,
  ArrowUpTrayIcon,
  FolderOpenIcon,
  UserIcon,
  ChevronRightIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const appStore = useAppStore()
const { isClientMode, backendAvailable, checkBackend } = useClientMode()
const { recentPatientsCount } = useSettings()
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const uploadProgress = ref(0)
const pendingFiles = ref<File[]>([])
const preview = ref<ParseResult | null>(null)

onMounted(() => {
  checkBackend()
})

const patients = computed(() => appStore.patients || [])
const recentPatients = computed(() => patients.value.slice(0, recentPatientsCount.value))
const totalStudies = computed(() =>
  patients.value.reduce((sum, p) => sum + (p.studies?.length || 0), 0)
)
const totalSeries = computed(() =>
  patients.value.reduce(
    (sum, p) =>
      sum +
      (p.studies?.reduce((s: number, st: any) => s + (st.series?.length || 0), 0) || 0),
    0
  )
)

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    const files = Array.from(target.files)
    const hasMedicalFormat = files.some(f => /\.(nii\.gz|nii|nrrd|nhdr|mha|mhd)$/i.test(f.name))
    if (hasMedicalFormat) {
      await uploadFiles(files)
    } else {
      pendingFiles.value = files
      preview.value = await lazyParseDicomFiles(files)
    }
  }
}

function handleDrop(e: DragEvent) {
  const files = e.dataTransfer?.files
  if (files?.length) {
    const fileArray = Array.from(files)
    const hasMedicalFormat = fileArray.some(f => /\.(nii\.gz|nii|nrrd|nhdr|mha|mhd)$/i.test(f.name))
    if (hasMedicalFormat) {
      uploadFiles(fileArray)
    } else {
      pendingFiles.value = fileArray
      lazyParseDicomFiles(fileArray).then(r => { preview.value = r })
    }
  }
}

function clearPreview() {
  preview.value = null
  pendingFiles.value = []
}

async function confirmUpload() {
  if (pendingFiles.value.length > 0) {
    await uploadFiles(pendingFiles.value)
    clearPreview()
  }
}

async function uploadFiles(files: File[]) {
  uploading.value = true
  uploadProgress.value = 0
  try {
    await appStore.uploadFiles(files, (progress: number) => {
      uploadProgress.value = progress
    })
    // Navigate to viewer after successful upload
    if (appStore.selectedSeriesUid) {
      router.push('/viewer')
    }
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

function goToPatient(patient: any) {
  appStore.selectPatient(patient.patient_id)
  router.push('/patients')
}
</script>
