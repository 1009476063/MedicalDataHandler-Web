<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-accent-900 dark:text-white">{{ $t('dashboard.title') }}</h1>
        <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('dashboard.subtitle') }}</p>
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
          v-if="!uploading"
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
            v-for="patient in patients.slice(0, 5)"
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
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
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
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const uploadProgress = ref(0)

const patients = computed(() => appStore.patients || [])
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

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    await uploadFiles(Array.from(target.files))
  }
}

function handleDrop(e: DragEvent) {
  const files = e.dataTransfer?.files
  if (files?.length) {
    uploadFiles(Array.from(files))
  }
}

async function uploadFiles(files: File[]) {
  uploading.value = true
  uploadProgress.value = 0
  try {
    await appStore.uploadFiles(files, (progress: number) => {
      uploadProgress.value = progress
    })
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
