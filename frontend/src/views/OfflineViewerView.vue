<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="flex items-center justify-between px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <div class="flex items-center gap-3">
        <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('viewer.title') }}</h1>
        <span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
          {{ $t('dashboard.clientMode') }}
        </span>
      </div>
      <button
        v-if="patients.length > 0"
        class="px-3 py-1.5 text-xs text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-800 rounded-lg transition-colors"
        @click="clearAll"
      >
        {{ $t('dashboard.clearPreview') }}
      </button>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Sidebar: file list -->
      <div class="w-64 border-r border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 flex flex-col">
        <div
          class="p-3 border-b border-accent-200 dark:border-accent-700"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <button
            class="w-full px-3 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors"
            @click="triggerFileInput"
          >
            {{ $t('dashboard.selectFiles') }}
          </button>
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".dcm,.dicom"
            class="hidden"
            @change="handleFileSelect"
          />
        </div>

        <div class="flex-1 overflow-y-auto">
          <div v-if="patients.length === 0" class="p-4 text-center">
            <FolderOpenIcon class="w-8 h-8 text-accent-300 dark:text-accent-600 mx-auto mb-2" />
            <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t('dashboard.dropHint') }}</p>
            <p class="text-[10px] text-accent-400 dark:text-accent-500 mt-1">{{ $t('dashboard.dropSupport') }}</p>
          </div>

          <div v-else class="py-1">
            <div
              v-for="patient in patients"
              :key="patient.patientId"
              class="border-b border-accent-100 dark:border-accent-800"
            >
              <button
                class="w-full px-3 py-2 text-left hover:bg-accent-50 dark:hover:bg-accent-800/50 transition-colors"
                @click="togglePatient(patient.patientId)"
              >
                <p class="text-sm font-medium text-accent-900 dark:text-white truncate">
                  {{ patient.patientName || 'Unknown' }}
                </p>
                <p class="text-[10px] text-accent-500 dark:text-accent-400">
                  {{ patient.patientId }} &middot; {{ patient.studies.size }} study{{ patient.studies.size !== 1 ? 's' : '' }}
                </p>
              </button>

              <div v-if="expandedPatients.has(patient.patientId)" class="pl-3">
                <div v-for="[studyUid, study] in patient.studies" :key="studyUid">
                  <p class="px-3 py-1 text-[10px] font-medium text-accent-500 dark:text-accent-400 uppercase">
                    {{ study.description || studyUid.slice(0, 12) + '...' }}
                  </p>
                  <div v-for="[seriesUid, series] in study.series" :key="seriesUid">
                    <button
                      class="w-full px-3 py-1.5 text-left text-xs hover:bg-accent-50 dark:hover:bg-accent-800/50 transition-colors flex items-center gap-2"
                      :class="{ 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300': selectedSeriesUid === seriesUid }"
                      @click="selectSeries(series)"
                    >
                      <span class="inline-block px-1 py-0.5 rounded text-[9px] font-medium bg-accent-100 dark:bg-accent-800 text-accent-600 dark:text-accent-400">
                        {{ series.modality }}
                      </span>
                      <span class="truncate">{{ series.description || 'No description' }}</span>
                      <span class="text-accent-400 dark:text-accent-500 ml-auto">{{ series.files.length }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Viewer area -->
      <div class="flex-1 flex flex-col min-w-0">
        <div v-if="!selectedImageId" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <CubeTransparentIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
            <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('viewer.noDataTitle') }}</p>
            <p class="text-xs text-accent-400 dark:text-accent-500 mt-1">{{ $t('viewer.noDataDesc') }}</p>
          </div>
        </div>

        <div v-else class="flex-1 relative">
          <Cornerstone3DViewer
            ref="viewerRef"
            viewport-id="offline"
            label="Offline"
            :loading="loading"
            :window-width="windowWidth"
            :window-center="windowCenter"
            @viewport-ready="onViewportReady"
            @resize="onViewportResize"
          />

          <!-- Image info overlay -->
          <div class="absolute bottom-3 left-3 px-2 py-1 rounded bg-black/60 text-white text-[10px] font-mono">
            W: {{ windowWidth }} L: {{ windowCenter }}
            <span v-if="currentImageIndex >= 0" class="ml-2">
              {{ currentImageIndex + 1 }} / {{ currentSeriesFiles.length }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import {
  loadClientFiles,
  getClientPatients,
} from '@/composables/useClientMode'
import { registerClientLoaders } from '@/utils/clientDicomLoader'
import Cornerstone3DViewer from '@/components/viewer/Cornerstone3DViewer.vue'
import {
  FolderOpenIcon,
  CubeTransparentIcon,
} from '@heroicons/vue/24/outline'
import {
  RenderingEngine,
  Enums,
  type Types,
} from '@cornerstonejs/core'

interface PatientInfo {
  patientId: string
  patientName: string
  studies: Map<string, {
    studyUid: string
    description: string
    series: Map<string, {
      seriesUid: string
      description: string
      modality: string
      files: Array<{ id: string; metadata: Record<string, unknown> }>
    }>
  }>
}

const fileInput = ref<HTMLInputElement>()
const viewerRef = ref<InstanceType<typeof Cornerstone3DViewer>>()
const patients = ref<PatientInfo[]>([])
const expandedPatients = ref(new Set<string>())
const selectedSeriesUid = ref<string>()
const selectedImageId = ref<string>()
const currentImageIndex = ref(-1)
const currentSeriesFiles = ref<Array<{ id: string; metadata: Record<string, unknown> }>>([])
const windowWidth = ref(400)
const windowCenter = ref(40)
const loading = ref(false)

let csEngine: Types.IRenderingEngine | null = null
const viewportElement = ref<HTMLDivElement>()

onMounted(() => {
  registerClientLoaders()
})

onBeforeUnmount(() => {
  if (csEngine) {
    csEngine.destroy()
    csEngine = null
  }
})

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    await loadFiles(Array.from(target.files))
  }
}

function handleDrop(e: DragEvent) {
  const files = e.dataTransfer?.files
  if (files?.length) {
    loadFiles(Array.from(files))
  }
}

async function loadFiles(files: File[]) {
  loading.value = true
  try {
    await loadClientFiles(files)
    patients.value = getClientPatients() as PatientInfo[]
    if (patients.value.length > 0) {
      expandedPatients.value.add(patients.value[0].patientId)
    }
  } finally {
    loading.value = false
  }
}

function togglePatient(patientId: string) {
  const next = new Set(expandedPatients.value)
  if (next.has(patientId)) next.delete(patientId)
  else next.add(patientId)
  expandedPatients.value = next
}

function selectSeries(series: { seriesUid: string; description: string; modality: string; files: Array<{ id: string; metadata: Record<string, unknown> }> }) {
  selectedSeriesUid.value = series.seriesUid

  const sorted = [...series.files].sort((a, b) => {
    const instA = (a.metadata.instanceNumber as number) || 0
    const instB = (b.metadata.instanceNumber as number) || 0
    return instA - instB
  })

  currentSeriesFiles.value = sorted
  if (sorted.length > 0) {
    currentImageIndex.value = 0
    selectedImageId.value = sorted[0].id
    nextTick(() => renderImage(sorted[0].id))
  }
}

function onViewportReady(element: HTMLDivElement) {
  viewportElement.value = element

  if (!csEngine) {
    csEngine = new RenderingEngine('offline-engine')
    csEngine.setViewports([{
      viewportId: 'offline',
      element,
      type: Enums.ViewportType.STACK,
      defaultOptions: { background: [0, 0, 0] as Types.Point3 },
    }])
  }

  if (selectedImageId.value) {
    renderImage(selectedImageId.value)
  }
}

function onViewportResize() {
  csEngine?.resize(true)
}

async function renderImage(imageId: string) {
  if (!csEngine) return

  const vp = csEngine.getViewport('offline') as Types.IStackViewport
  if (!vp) return

  loading.value = true
  try {
    const imageIds = currentSeriesFiles.value.map(f => f.id)
    await vp.setStack(imageIds, currentImageIndex.value >= 0 ? currentImageIndex.value : 0)

    // Window/level is auto-detected by Cornerstone3D from image metadata
    vp.render()
  } catch (err) {
    console.error('Failed to render:', err)
  } finally {
    loading.value = false
  }
}

function clearAll() {
  patients.value = []
  expandedPatients.value.clear()
  selectedSeriesUid.value = undefined
  selectedImageId.value = undefined
  currentImageIndex.value = -1
  currentSeriesFiles.value = []
  if (csEngine) {
    csEngine.destroy()
    csEngine = null
  }
}
</script>
