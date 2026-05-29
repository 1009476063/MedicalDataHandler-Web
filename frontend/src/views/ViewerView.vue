<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="flex items-center justify-between px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('viewer.title') }}</h1>
      <div class="flex items-center gap-2">
        <button
          class="p-1.5 rounded-lg hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
          :title="$t('viewer.screenshot')"
          @click="captureScreenshot"
        >
          <CameraIcon class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Measurement Toolbar -->
    <MeasurementToolbar
      :active-tool="tools.activeTool.value"
      :crosshairs-enabled="true"
      @select-tool="tools.setActive"
      @toggle-crosshairs="() => {}"
      @clear-all="tools.clearAll"
      @export-csv="exportMeasurementsCsv"
    />

    <div class="flex-1 flex min-h-0">
      <div class="flex-1 p-2 min-w-0">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-2 h-full">
          <div class="min-h-[200px]">
            <Cornerstone3DViewer
              ref="axialViewerRef"
              viewport-id="axial"
              label="Axial"
              :loading="loading"
              :window-width="windowWidth"
              :window-center="windowCenter"
              @viewport-ready="onViewportReady('axial', $event)"
              @resize="onViewportResize"
            />
          </div>
          <div class="min-h-[200px]">
            <Cornerstone3DViewer
              ref="sagittalViewerRef"
              viewport-id="sagittal"
              label="Sagittal"
              :loading="loading"
              :window-width="windowWidth"
              :window-center="windowCenter"
              @viewport-ready="onViewportReady('sagittal', $event)"
              @resize="onViewportResize"
            />
          </div>
          <div class="min-h-[200px]">
            <Cornerstone3DViewer
              ref="coronalViewerRef"
              viewport-id="coronal"
              label="Coronal"
              :loading="loading"
              :window-width="windowWidth"
              :window-center="windowCenter"
              @viewport-ready="onViewportReady('coronal', $event)"
              @resize="onViewportResize"
            />
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="w-64 border-l border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 overflow-y-auto hidden lg:block">
        <div class="p-4 space-y-4">
          <!-- Patient -->
          <div>
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.patient') }}</h3>
            <select
              v-model="appStore.selectedPatientId"
              class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              @change="onPatientChange"
            >
              <option value="">{{ $t('viewer.selectPatient') }}</option>
              <option v-for="p in patients" :key="p.patient_id" :value="p.patient_id">
                {{ p.name || p.patient_id }}
              </option>
            </select>
          </div>

          <!-- Series -->
          <div v-if="seriesList.length > 0">
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.series') }}</h3>
            <div class="space-y-1.5">
              <button
                v-for="s in seriesList"
                :key="s.series_uid"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2',
                  appStore.selectedSeriesUid === s.series_uid
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : 'hover:bg-accent-50 dark:hover:bg-accent-800/50 text-accent-700 dark:text-accent-300',
                ]"
                @click="onSeriesSelect(s.series_uid)"
              >
                <StatusBadge :status="s.modality" />
                <span class="truncate">{{ s.description || s.series_uid }}</span>
              </button>
            </div>
          </div>

          <!-- Volume Info -->
          <div v-if="seriesInfo">
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.volumeInfo') }}</h3>
            <div class="space-y-1 text-xs text-accent-600 dark:text-accent-400">
              <p>{{ $t('viewer.shape') }}: {{ seriesInfo.shape?.join(' x ') }}</p>
              <p>{{ $t('viewer.spacing') }}: {{ seriesInfo.spacing?.map((s: number) => s.toFixed(2)).join(' x ') }} mm</p>
              <p>{{ $t('viewer.range') }}: {{ seriesInfo.min?.toFixed(0) }} ~ {{ seriesInfo.max?.toFixed(0) }}</p>
              <p>{{ $t('viewer.mean') }}: {{ seriesInfo.mean?.toFixed(1) }}</p>
            </div>
          </div>

          <!-- Window/Level -->
          <div>
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.windowLevel') }}</h3>
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <label class="text-xs text-accent-500 w-8">W</label>
                <input
                  v-model.number="windowWidth"
                  type="range"
                  :min="1"
                  :max="4000"
                  class="flex-1 h-1.5 accent-primary-500"
                />
                <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ windowWidth }}</span>
              </div>
              <div class="flex items-center gap-2">
                <label class="text-xs text-accent-500 w-8">L</label>
                <input
                  v-model.number="windowCenter"
                  type="range"
                  :min="-1000"
                  :max="3000"
                  class="flex-1 h-1.5 accent-primary-500"
                />
                <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ windowCenter }}</span>
              </div>
            </div>
            <div class="flex flex-wrap gap-1 mt-2">
              <button
                v-for="preset in windowPresets"
                :key="preset.name"
                class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
                @click="applyPreset(preset)"
              >
                {{ preset.name }}
              </button>
            </div>
          </div>

          <!-- Structures (Overlay Controls) -->
          <div v-if="structs.length > 0">
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.structureOverlays') }}</h3>
            <div class="space-y-1.5">
              <div
                v-for="(s, i) in structs"
                :key="s.key"
                class="flex items-center gap-2 px-2 py-1.5 rounded text-xs text-accent-700 dark:text-accent-300 hover:bg-accent-50 dark:hover:bg-accent-800/50 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  :checked="enabledStructOverlays.has(s.key)"
                  class="rounded border-accent-300 text-primary-500 focus:ring-primary-500/50"
                  @change="toggleStructOverlay(s.key)"
                />
                <input
                  type="color"
                  :value="structColorMap[s.key] || structColors[i % structColors.length]"
                  class="w-5 h-5 rounded border-0 cursor-pointer flex-shrink-0"
                  @input="(e: Event) => setStructColor(s.key, (e.target as HTMLInputElement).value)"
                />
                <span class="truncate flex-1">{{ s.name }}</span>
                <span class="text-[10px] text-accent-400 px-1 py-0.5 rounded bg-accent-100 dark:bg-accent-800">
                  {{ inferStructType(s.name) }}
                </span>
                <button
                  :title="$t('viewer.centerOnRoi')"
                  class="p-0.5 rounded hover:bg-primary-100 dark:hover:bg-primary-900/30 text-accent-400 hover:text-primary-500 transition-colors"
                  @click.stop="centerOnRoi(s.key)"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </button>
              </div>
            </div>
            <div class="mt-2 flex items-center gap-2">
              <label class="text-xs text-accent-500">{{ $t('viewer.opacity') }}</label>
              <input
                v-model.number="overlayOpacity"
                type="range"
                :min="0.05"
                :max="1"
                step="0.05"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ Math.round(overlayOpacity * 100) }}%</span>
            </div>
            <div class="mt-2 flex items-center gap-2">
              <label class="text-xs text-accent-500">{{ $t('viewer.contour') }}</label>
              <input
                v-model.number="contourThickness"
                type="range"
                :min="0"
                :max="4"
                step="1"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ contourThickness }}px</span>
            </div>
          </div>

          <!-- Dose Overlays -->
          <div v-if="doseList.length > 0">
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.doseOverlays') }}</h3>
            <div class="space-y-1.5">
              <label
                v-for="d in doseList"
                :key="d.file_id"
                class="flex items-center gap-2 px-2 py-1.5 rounded text-xs text-accent-700 dark:text-accent-300 hover:bg-accent-50 dark:hover:bg-accent-800/50 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  :checked="enabledDoseOverlays.has(d.file_id)"
                  class="rounded border-accent-300 text-red-500 focus:ring-red-500/50"
                  @change="toggleDoseOverlay(d.file_id)"
                />
                <span class="w-3 h-3 rounded-full flex-shrink-0 bg-red-500" />
                <span class="truncate">{{ d.filename || d.file_id }}</span>
              </label>
            </div>
            <div class="mt-2 flex items-center gap-2">
              <label class="text-xs text-accent-500">{{ $t('viewer.opacity') }}</label>
              <input
                v-model.number="doseOpacity"
                type="range"
                :min="0.05"
                :max="1"
                step="0.05"
                class="flex-1 h-1.5 accent-red-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ Math.round(doseOpacity * 100) }}%</span>
            </div>
          </div>

          <!-- Segmentation Overlays -->
          <SegmentationPanel
            :seg-files="seg.segFiles.value"
            :overlays="seg.overlays.value"
            :loading="seg.loading.value"
            :error="seg.error.value"
            @toggle="(sf, sn, lbl) => seg.toggleOverlay(sf, sn, lbl)"
            @opacity="(fid, sn, op) => seg.updateOpacity(fid, sn, op)"
            @clear-all="seg.clearOverlays"
          />

          <!-- 4D Time Slider -->
          <TimeSlider
            v-if="fourD.is4D.value"
            :time-points="fourD.timePoints.value"
            :current-time-point="fourD.currentTimePoint.value"
            :playing="fourD.playing.value"
            :fps="fourD.fps.value"
            @step-forward="fourD.stepForward(appStore.selectedPatientId!, appStore.selectedSeriesUid!)"
            @step-backward="fourD.stepBackward(appStore.selectedPatientId!, appStore.selectedSeriesUid!)"
            @play="fourD.play(appStore.selectedPatientId!, appStore.selectedSeriesUid!)"
            @pause="fourD.pause"
            @update-fps="(f) => fourD.fps.value = f"
            @change-time-point="(pos) => { fourD.setTimePoint(pos); fourD.loadTimePoint(appStore.selectedPatientId!, appStore.selectedSeriesUid!, pos) }"
          />

          <!-- Orientation Label Color -->
          <div>
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.orientationLabels') }}</h3>
            <div class="flex items-center gap-2">
              <label class="text-xs text-accent-500">{{ $t('viewer.color') }}</label>
              <input
                v-model="orientationLabelColor"
                type="color"
                class="w-6 h-6 rounded border-0 cursor-pointer"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400">{{ orientationLabelColor }}</span>
            </div>
          </div>

          <!-- DICOM Tag Inspection -->
          <div>
            <button
              class="w-full flex items-center justify-between text-sm font-medium text-accent-700 dark:text-accent-300 mb-2"
              @click="showDicomTags = !showDicomTags"
            >
              <span>{{ $t('viewer.dicomTags') }}</span>
              <svg :class="['w-4 h-4 transition-transform', showDicomTags ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div v-if="showDicomTags" class="space-y-2">
              <input
                v-model="dicomTagSearch"
                type="text"
                :placeholder="$t('viewer.searchTags')"
                class="w-full px-2 py-1.5 text-xs bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-1 focus:ring-primary-500/50"
              />
              <div class="max-h-48 overflow-y-auto space-y-0.5 text-[11px] font-mono">
                <div
                  v-for="(tag, i) in filteredDicomTags"
                  :key="i"
                  class="px-1.5 py-0.5 rounded hover:bg-accent-100 dark:hover:bg-accent-800/50"
                >
                  <span class="text-accent-400">{{ tag.tag }}</span>
                  <span class="text-accent-600 dark:text-accent-300 ml-1">{{ tag.name }}</span>
                  <span class="text-accent-500 ml-1">[{{ tag.vr }}]</span>
                  <p class="text-accent-700 dark:text-accent-200 truncate">{{ tag.value }}</p>
                </div>
                <div v-if="filteredDicomTags.length === 0" class="text-accent-400 text-center py-2">
                  {{ $t('viewer.noTagsFound') }}
                </div>
              </div>
              <p class="text-[10px] text-accent-400 text-right">{{ filteredDicomTags.length }} / {{ dicomTags.length }} tags</p>
            </div>
          </div>

          <!-- Measurements -->
          <MeasurementPanel :measurements="tools.measurements.value" />

          <!-- Delete Patient -->
          <div v-if="appStore.selectedPatientId">
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.sessionActions') }}</h3>
            <button
              class="w-full px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              @click="confirmDeletePatient"
            >
              {{ $t('viewer.removePatient') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!appStore.sessionId" class="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-accent-900/80 z-10">
      <div class="text-center">
        <EyeIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
        <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('viewer.noDataTitle') }}</h3>
        <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('viewer.noDataDesc') }}</p>
        <button
          class="mt-4 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors"
          @click="$router.push('/')"
        >
          {{ $t('viewer.goToDashboard') }}
        </button>
      </div>
    </div>

    <!-- Confirmation Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showConfirmDialog"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          @click.self="cancelConfirm"
        >
          <div class="bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-xl max-w-sm w-full mx-4 p-6 animate-scale-in">
            <h3 class="text-lg font-semibold text-accent-900 dark:text-white mb-2">{{ confirmTitle }}</h3>
            <p class="text-sm text-accent-600 dark:text-accent-400 mb-6">{{ confirmMessage }}</p>
            <div class="flex justify-end gap-3">
              <button
                class="px-4 py-2 text-sm text-accent-700 dark:text-accent-300 hover:bg-accent-100 dark:hover:bg-accent-800 rounded-lg transition-colors"
                @click="cancelConfirm"
              >
                {{ $t('viewer.cancel') }}
              </button>
              <button
                class="px-4 py-2 text-sm bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                @click="executeConfirm"
              >
                {{ confirmButtonText }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import Cornerstone3DViewer from '@/components/viewer/Cornerstone3DViewer.vue'
import MeasurementToolbar from '@/components/viewer/MeasurementToolbar.vue'
import MeasurementPanel from '@/components/viewer/MeasurementPanel.vue'
import SegmentationPanel from '@/components/viewer/SegmentationPanel.vue'
import TimeSlider from '@/components/viewer/TimeSlider.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useTools } from '@/composables/useTools'
import { useSegmentation } from '@/composables/useSegmentation'
import { useFourD } from '@/composables/useFourD'
import type { SeriesInfo, StructInfo, DoseInfo } from '@/types'
import { EyeIcon, CameraIcon } from '@heroicons/vue/24/outline'
import {
  RenderingEngine,
  Enums,
  volumeLoader,
  eventTarget,
  type Types,
} from '@cornerstonejs/core'
import { registerMdhVolumeLoader, buildVolumeId } from '@/utils/cornerstoneVolumeLoader'
import { annotation } from '@cornerstonejs/tools'

const { t } = useI18n()
const appStore = useAppStore()
const tools = useTools()
const seg = useSegmentation()
const fourD = useFourD()

const windowCenter = ref(40)
const windowWidth = ref(400)
const loading = ref(false)
const seriesInfo = ref<SeriesInfo | null>(null)
const structs = ref<StructInfo[]>([])
const doseList = ref<DoseInfo[]>([])

// Cornerstone3D engine state
let csEngine: Types.IRenderingEngine | null = null
const engineReady = ref(false)
const viewportElements = ref<Record<string, HTMLDivElement>>({})
let volumeLoaded = false
let refreshOnAnnotationFn: (() => void) | null = null

// Overlay state (RT structures rendered via canvas overlay — Phase 2 will use Cornerstone3D segmentation)
const enabledStructOverlays = ref<Set<string>>(new Set())
const enabledDoseOverlays = ref<Set<string>>(new Set())
const overlayOpacity = ref(0.4)
const doseOpacity = ref(0.35)
const contourThickness = ref(0)
const structOverlayCache = ref<Record<string, number[][] | null>>({})
const doseOverlayCache = ref<Record<string, { data: number[][]; min: number; max: number } | null>>({})
const structColorMap = ref<Record<string, string>>({})

// DICOM tag inspection
const showDicomTags = ref(false)
const dicomTagSearch = ref('')
const dicomTags = ref<Array<{ tag: string; name: string; value: string; vr: string }>>([])

// Orientation labels
const showOrientationLabels = ref(true)
const orientationLabelColor = ref('#00ff00')

// Confirmation dialog
const showConfirmDialog = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmButtonText = ref(t('viewer.confirm'))
let confirmCallback: (() => void) | null = null

const patients = computed(() => appStore.patients || [])

const seriesList = computed(() => {
  const patient = patients.value.find(p => p.patient_id === appStore.selectedPatientId)
  if (!patient) return []
  return patient.studies.flatMap(s => s.series || [])
})

const structColors = [
  '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff',
  '#ff8000', '#8000ff', '#00ff80', '#ff0080', '#808000', '#008080',
]

const windowPresets = ref([
  { name: 'CT', center: 40, width: 400 },
  { name: 'Lung', center: -600, width: 1500 },
  { name: 'Bone', center: 400, width: 1800 },
  { name: 'Soft Tissue', center: 50, width: 350 },
  { name: 'Brain', center: 40, width: 80 },
  { name: 'Subdural', center: 75, width: 215 },
])

// Filtered DICOM tags
const filteredDicomTags = computed(() => {
  if (!dicomTagSearch.value) return dicomTags.value
  const q = dicomTagSearch.value.toLowerCase()
  return dicomTags.value.filter(
    t => t.tag.toLowerCase().includes(q) || t.name.toLowerCase().includes(q) || t.value.toLowerCase().includes(q)
  )
})

// TG-263 structure type inference
function inferStructType(name: string): string {
  const lower = name.toLowerCase()
  if (/^(gtv|ptv|ctv|itv|tv)\b/.test(lower)) return 'Target'
  if (/^(body|external|skin|patient)\b/.test(lower)) return 'External'
  if (/(lens|optic|eye|globe|retina|cochlea)/.test(lower)) return 'Sensory'
  if (/(brain|brainstem|cord|spinal|cerebell)/.test(lower)) return 'CNS'
  if (/(heart|lung|esophagus|trachea|larynx|pharynx|brachial)/.test(lower)) return 'Thorax'
  if (/(liver|kidney|stomach|bowel|rectum|bladder|pancreas|spleen|adrenal|gallbladder)/.test(lower)) return 'Abdomen'
  if (/(femoral|hip|pelvis|bone|rib|vertebra|spine)/.test(lower)) return 'Bone'
  if (/(parotid|submandibular|sublingual|mandible|oral|lip|cheek)/.test(lower)) return 'H&N'
  if (/(nodal|lymph|node)/.test(lower)) return 'Lymph'
  return 'OAR'
}

function toggleStructOverlay(key: string) {
  const next = new Set(enabledStructOverlays.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  enabledStructOverlays.value = next
}

function toggleDoseOverlay(fileId: string) {
  const next = new Set(enabledDoseOverlays.value)
  if (next.has(fileId)) next.delete(fileId)
  else next.add(fileId)
  enabledDoseOverlays.value = next
}

function setStructColor(structKey: string, color: string) {
  structColorMap.value = { ...structColorMap.value, [structKey]: color }
}

async function centerOnRoi(structKey: string) {
  const bounds = await appStore.getRoiBounds(structKey)
  if (!bounds || !seriesInfo.value?.origin || !seriesInfo.value?.spacing) return

  // Navigate Cornerstone3D viewports to the ROI center using setCamera
  if (!csEngine) return
  const origin = seriesInfo.value.origin
  const spacing = seriesInfo.value.spacing

  const worldPos: Types.Point3 = [
    bounds.center.x,
    bounds.center.y,
    bounds.center.z,
  ]

  for (const vpId of ['axial', 'sagittal', 'coronal'] as const) {
    const vp = csEngine.getViewport(vpId)
    if (vp) {
      const camera = vp.getCamera()
      vp.setCamera({ ...camera, focalPoint: worldPos })
    }
  }
  csEngine.render()
}

onMounted(async () => {
  // Initialize Cornerstone3D
  if (!volumeLoader) return
  registerMdhVolumeLoader()

  // Listen for annotation changes to refresh measurements
  refreshOnAnnotationFn = () => tools.refreshMeasurements('axial')
  eventTarget.addEventListener('CORNERSTONE_TOOLS_ANNOTATION_ADDED', refreshOnAnnotationFn)
  eventTarget.addEventListener('CORNERSTONE_TOOLS_ANNOTATION_MODIFIED', refreshOnAnnotationFn)
  eventTarget.addEventListener('CORNERSTONE_TOOLS_ANNOTATION_REMOVED', refreshOnAnnotationFn)

  // Load window presets from config
  try {
    const res = await fetch('/api/config/window-presets')
    if (res.ok) {
      const config = await res.json()
      if (config.rules && typeof config.rules === 'object') {
        windowPresets.value = Object.entries(config.rules).map(([name, vals]: [string, unknown]) => {
          const [width, center] = vals as [number, number]
          return { name, center, width }
        })
      }
    }
  } catch {
    // Keep default presets on failure
  }
})

onBeforeUnmount(() => {
  tools.destroy()
  if (refreshOnAnnotationFn) {
    eventTarget.removeEventListener('CORNERSTONE_TOOLS_ANNOTATION_ADDED', refreshOnAnnotationFn)
    eventTarget.removeEventListener('CORNERSTONE_TOOLS_ANNOTATION_MODIFIED', refreshOnAnnotationFn)
    eventTarget.removeEventListener('CORNERSTONE_TOOLS_ANNOTATION_REMOVED', refreshOnAnnotationFn)
  }
  if (csEngine) {
    csEngine.destroy()
    csEngine = null
  }
})

watch(
  () => [appStore.selectedSeriesUid, appStore.selectedPatientId],
  () => loadSeriesData()
)

async function onViewportReady(orientation: string, element: HTMLDivElement) {
  viewportElements.value[orientation] = element

  // Once all three viewports are ready, create the engine
  if (Object.keys(viewportElements.value).length === 3 && !csEngine) {
    csEngine = new RenderingEngine('cs3d-engine')
    csEngine.setViewports([
      {
        viewportId: 'axial',
        element: viewportElements.value.axial,
        type: Enums.ViewportType.ORTHOGRAPHIC,
        defaultOptions: { background: [0, 0, 0] as Types.Point3 },
      },
      {
        viewportId: 'sagittal',
        element: viewportElements.value.sagittal,
        type: Enums.ViewportType.ORTHOGRAPHIC,
        defaultOptions: { background: [0, 0, 0] as Types.Point3 },
      },
      {
        viewportId: 'coronal',
        element: viewportElements.value.coronal,
        type: Enums.ViewportType.ORTHOGRAPHIC,
        defaultOptions: { background: [0, 0, 0] as Types.Point3 },
      },
    ])
    engineReady.value = true

    // Create measurement tool group
    const toolGroup = tools.createToolGroup('cs3d-engine')
    if (toolGroup) {
      tools.addViewports('cs3d-engine', ['axial', 'sagittal', 'coronal'])
    }

    // If a series is already selected, load volume
    if (appStore.selectedSeriesUid) {
      await loadVolumeIntoViewports()
    }
  }
}

function onViewportResize() {
  csEngine?.resize(true)
}

async function loadVolumeIntoViewports() {
  if (!csEngine || !appStore.selectedSeriesUid || !appStore.selectedPatientId || !appStore.sessionId) return

  const volumeId = buildVolumeId(appStore.sessionId, appStore.selectedPatientId, appStore.selectedSeriesUid)

  loading.value = true
  try {
    for (const vpId of ['axial', 'sagittal', 'coronal'] as const) {
      const vp = csEngine.getViewport(vpId)
      if (vp) {
        await (vp as Types.IBaseVolumeViewport).setVolumes([{ volumeId }])
      }
    }
    volumeLoaded = true
    csEngine.render()
  } catch (err) {
    console.error('Failed to load volume:', err)
  } finally {
    loading.value = false
  }
}

async function loadSeriesData() {
  if (!appStore.selectedSeriesUid) return
  loading.value = true
  try {
    seriesInfo.value = await appStore.getSeriesInfo(appStore.selectedSeriesUid)
    structs.value = await appStore.getStructs()
    doseList.value = await appStore.getDoseInfo()

    // Load DICOM tags for the first file in this series
    await loadDicomTags()

    // Reset overlay state
    enabledStructOverlays.value.clear()
    enabledDoseOverlays.value.clear()
    structOverlayCache.value = {}
    doseOverlayCache.value = {}
    structColorMap.value = {}

    // Load volume into Cornerstone3D viewports
    if (engineReady.value) {
      await loadVolumeIntoViewports()
    }
  } finally {
    loading.value = false
  }
}

async function loadDicomTags() {
  if (!appStore.selectedPatientId || !appStore.selectedSeriesUid) return
  try {
    const files = await appStore.getPatientDetail(appStore.selectedPatientId)
    const seriesFile = files.find(f => f.series_uid === appStore.selectedSeriesUid)
    if (!seriesFile) return
    const metadata = await appStore.getFileMetadata(seriesFile.id)
    if (metadata?.all_tags) {
      dicomTags.value = Object.entries(metadata.all_tags as Record<string, Record<string, string>>).map(([tag, info]) => ({
        tag,
        name: info.name || tag,
        value: String(info.value || '').substring(0, 200),
        vr: info.vr || '',
      }))
    }
  } catch {
    dicomTags.value = []
  }
}

function applyPreset(preset: { center: number; width: number }) {
  windowCenter.value = preset.center
  windowWidth.value = preset.width
  if (csEngine) {
    for (const vpId of ['axial', 'sagittal', 'coronal'] as const) {
      const vp = csEngine.getViewport(vpId)
      if (vp) {
        ;(vp as Types.IBaseVolumeViewport).setProperties({
          voiRange: {
            upper: preset.center + preset.width / 2,
            lower: preset.center - preset.width / 2,
          },
        })
      }
    }
    csEngine.render()
  }
}

// Viewer refs (Cornerstone3D components)
const axialViewerRef = ref<InstanceType<typeof Cornerstone3DViewer> | null>(null)
const sagittalViewerRef = ref<InstanceType<typeof Cornerstone3DViewer> | null>(null)
const coronalViewerRef = ref<InstanceType<typeof Cornerstone3DViewer> | null>(null)

function captureScreenshot() {
  // Use Cornerstone3D rendering engine to capture the axial viewport
  if (!csEngine) return
  const vp = csEngine.getViewport('axial')
  if (!vp) return
  // Cornerstone3D viewport canvas is accessible via the element
  const canvas = document.querySelector('#axial canvas') as HTMLCanvasElement | null
  if (!canvas) return
  const dataUrl = canvas.toDataURL('image/png')
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = `slice_${appStore.selectedSeriesUid || 'unknown'}.png`
  link.click()
}

function exportMeasurementsCsv() {
  const items = tools.measurements.value
  if (items.length === 0) return
  const rows = [['Tool', 'Label', 'Value', 'Unit']]
  for (const item of items) {
    const stats = item.stats
    let value = ''
    let unit = ''
    if (item.toolName === 'Length' && typeof stats.length === 'number') {
      value = stats.length.toFixed(2)
      unit = 'mm'
    } else if (item.toolName === 'Angle' && typeof stats.angle === 'number') {
      value = stats.angle.toFixed(1)
      unit = '°'
    } else if ((item.toolName === 'RectangleROI' || item.toolName === 'EllipticalROI') && typeof stats.mean === 'number') {
      value = stats.mean.toFixed(1)
      unit = 'HU'
    } else if (item.toolName === 'Probe' && typeof stats.value === 'number') {
      value = stats.value.toFixed(1)
      unit = 'HU'
    }
    rows.push([item.toolName, item.label || '', value, unit])
  }
  const csv = rows.map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `measurements_${appStore.selectedSeriesUid || 'unknown'}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function onPatientChange() {
  appStore.selectedSeriesUid = null
  seriesInfo.value = null
  structs.value = []
  doseList.value = []
  enabledStructOverlays.value.clear()
  enabledDoseOverlays.value.clear()
  structOverlayCache.value = {}
  doseOverlayCache.value = {}
  seg.clearOverlays()
  seg.fetchSegFiles()
  fourD.reset()
  // Destroy existing engine if any — will be recreated on next viewport-ready
  if (csEngine) {
    csEngine.destroy()
    csEngine = null
    engineReady.value = false
  }
}

function onSeriesSelect(uid: string) {
  appStore.selectSeries(uid)
  // Detect 4D data for this series
  if (appStore.selectedPatientId) {
    fourD.detect4D(appStore.selectedPatientId, uid)
  }
}

// Confirmation dialog
function showConfirm(title: string, message: string, buttonText: string, callback: () => void) {
  confirmTitle.value = title
  confirmMessage.value = message
  confirmButtonText.value = buttonText
  confirmCallback = callback
  showConfirmDialog.value = true
}

function cancelConfirm() {
  showConfirmDialog.value = false
  confirmCallback = null
}

function executeConfirm() {
  showConfirmDialog.value = false
  confirmCallback?.()
  confirmCallback = null
}

function confirmDeletePatient() {
  if (!appStore.selectedPatientId) return
  const patient = patients.value.find(p => p.patient_id === appStore.selectedPatientId)
  const name = patient?.name || appStore.selectedPatientId
  showConfirm(
    t('viewer.confirmRemoveTitle'),
    t('viewer.confirmRemoveMessage', { name }),
    t('viewer.confirmRemoveBtn'),
    () => deletePatient()
  )
}

function deletePatient() {
  if (!appStore.selectedPatientId) return
  const idx = appStore.patients.findIndex(p => p.patient_id === appStore.selectedPatientId)
  const newPatients = [...appStore.patients]
  newPatients.splice(idx, 1)
  appStore.patients = newPatients

  if (newPatients.length > 0) {
    appStore.selectedPatientId = newPatients[0].patient_id
  } else {
    appStore.selectedPatientId = null
  }
  appStore.selectedSeriesUid = null
  onPatientChange()
}
</script>
