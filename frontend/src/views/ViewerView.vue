<template>
  <div class="h-full flex flex-col animate-fade-in">
    <ViewerHeader
      :gpu-info="gpuInfo"
      :canvas-mode="useCanvasFallback"
      :client-mode="appStore.isClientMode"
      @screenshot="captureScreenshot"
    />

    <!-- Restricted mode banner -->
    <div
      v-if="useCanvasFallback"
      class="flex items-center gap-2 px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200 text-xs"
    >
      <span class="font-medium">受限模式</span>
      <span>3D 渲染不可用。推荐使用 <strong>Chrome / Edge / Firefox</strong> 等支持 WebGL2 的浏览器以获得完整功能。</span>
    </div>

    <!-- Measurement Toolbar -->
    <MeasurementToolbar
      :canvas-mode="useCanvasFallback"
      :active-tool="useCanvasFallback ? (canvasTools.activeTool.value ?? 'Length') : tools.activeTool.value"
      :crosshairs-enabled="!useCanvasFallback"
      @select-tool="useCanvasFallback ? (canvasTools.activeTool.value = $event as 'Length' | 'Probe') : tools.setActive($event)"
      @toggle-crosshairs="() => {}"
      @clear-all="useCanvasFallback ? canvasTools.clearAnnotations() : tools.clearAll"
      @export-csv="exportMeasurementsCsv"
    />

    <div class="flex-1 flex min-h-0">
      <div class="flex-1 p-2 min-w-0">
        <!-- Canvas2D fallback mode -->
        <div v-if="useCanvasFallback" class="grid grid-cols-1 md:grid-cols-3 gap-2 h-full">
          <ImageSliceViewer
            v-for="orientation in ['axial', 'sagittal', 'coronal']"
            :key="orientation"
            :pixel-data="canvasSliceData[orientation]"
            :width="512"
            :height="512"
            :label="orientation"
            :slice-index="canvasSliceIndex[orientation]"
            :max-slice="canvasMaxSlice[orientation]"
            :window-center="windowCenter"
            :window-width="windowWidth"
            :loading="canvasLoading"
            :active-tool="canvasTools.activeTool.value"
            :annotations="canvasTools.annotations.value"
            :current-points="canvasTools.currentPoints.value"
            :overlays="canvasOverlays[orientation] || []"
            :spacing="seriesInfo?.spacing ? { x: seriesInfo.spacing[0] ?? 1, y: seriesInfo.spacing[1] ?? 1 } : null"
            @slice-change="(delta: number) => handleCanvasSliceChange(orientation, canvasSliceIndex[orientation] + delta)"
            @click="(x: number, y: number) => handleCanvasAnnotateClick(x, y, orientation)"
          />
        </div>
        <!-- Cornerstone3D WebGL mode -->
        <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-2 h-full">
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
      <ViewerSidebar
        :window-center="windowCenter"
        :window-width="windowWidth"
        :window-presets="windowPresets"
        :series-info="seriesInfo"
        :structs="structs"
        :dose-list="doseList"
        :enabled-struct-overlays="enabledStructOverlays"
        :enabled-dose-overlays="enabledDoseOverlays"
        :overlay-opacity="overlayOpacity"
        :dose-opacity="doseOpacity"
        :contour-thickness="contourThickness"
        :struct-color-map="structColorMap"
        :orientation-label-color="orientationLabelColor"
        :show-dicom-tags="showDicomTags"
        :dicom-tag-search="dicomTagSearch"
        :dicom-tags="dicomTags"
        :filtered-dicom-tags="filteredDicomTags"
        @patient-change="onPatientChange"
        @series-select="onSeriesSelect"
        @apply-preset="applyPreset"
        @toggle-struct-overlay="toggleStructOverlay"
        @set-struct-color="setStructColor"
        @center-on-roi="centerOnRoi"
        @toggle-dose-overlay="toggleDoseOverlay"
        @confirm-delete-patient="confirmDeletePatient"
        @toggle-dicom-tags="showDicomTags = !showDicomTags"
        @update:window-width="windowWidth = $event"
        @update:window-center="windowCenter = $event"
        @update:overlay-opacity="overlayOpacity = $event"
        @update:dose-opacity="doseOpacity = $event"
        @update:contour-thickness="contourThickness = $event"
        @update:orientation-label-color="orientationLabelColor = $event"
        @update:dicom-tag-search="dicomTagSearch = $event"
      />
    </div>

    <div v-if="!appStore.sessionId && !appStore.isClientMode" class="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-accent-900/80 z-10">
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
import ViewerHeader from '@/components/viewer/ViewerHeader.vue'
import ViewerSidebar from '@/components/viewer/ViewerSidebar.vue'
import { useTools } from '@/composables/useTools'
import { useSegmentation } from '@/composables/useSegmentation'
import { useFourD } from '@/composables/useFourD'
import { getSeriesImageIds } from '@/composables/useClientMode'
import { registerClientLoaders } from '@/utils/clientDicomLoader'
import type { SeriesInfo, StructInfo, DoseInfo } from '@/types'
import { EyeIcon } from '@heroicons/vue/24/outline'
import {
  RenderingEngine,
  Enums,
  volumeLoader,
  eventTarget,
  type Types,
} from '@cornerstonejs/core'
import { registerMdhVolumeLoader, buildVolumeId } from '@/utils/cornerstoneVolumeLoader'
import { annotation } from '@cornerstonejs/tools'
import { detectWebGL, type WebGLCapability } from '@/utils/webglDetector'
import ImageSliceViewer from '@/components/viewer/ImageSliceViewer.vue'
import { useCanvasTools } from '@/composables/useCanvasTools'

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

// WebGL capability and Canvas2D fallback
const webglCap = ref<WebGLCapability | null>(null)
const useCanvasFallback = ref(false)
const canvasSliceData = ref<Record<string, number[][] | null>>({
  axial: null,
  sagittal: null,
  coronal: null,
})
const canvasSliceIndex = ref<Record<string, number>>({ axial: 0, sagittal: 0, coronal: 0 })
const canvasMaxSlice = ref<Record<string, number>>({ axial: 0, sagittal: 0, coronal: 0 })
const canvasLoading = ref(false)
const canvasTools = useCanvasTools()
const canvasOverlays = ref<Record<string, Array<{ mask: number[][] | null; color: string; opacity: number; name?: string }>>>({})

// GPU info from backend
const gpuInfo = ref<{ gpu_available: boolean; gpu_name?: string } | null>(null)

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

function toggleStructOverlay(key: string) {
  const next = new Set(enabledStructOverlays.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  enabledStructOverlays.value = next
  // Load overlays for Canvas2D mode
  if (useCanvasFallback.value) {
    loadCanvasOverlays()
  }
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

// Load RT struct overlays for Canvas2D mode
async function loadCanvasOverlays() {
  if (!useCanvasFallback.value || !appStore.selectedSeriesUid) return

  const overlays: Record<string, Array<{ mask: number[][] | null; color: string; opacity: number; name?: string }>> = {}
  for (const orient of ['axial', 'sagittal', 'coronal'] as const) {
    overlays[orient] = []
  }

  for (const s of structs.value) {
    if (!enabledStructOverlays.value.has(s.key)) continue
    const color = structColorMap.value[s.key] || structColors[structs.value.indexOf(s) % structColors.length]

    for (const orient of ['axial', 'sagittal', 'coronal'] as const) {
      try {
        const maskData = await appStore.getStructMask(s.key, canvasSliceIndex.value[orient], orient)
        if (maskData?.data) {
          overlays[orient].push({
            mask: maskData.data,
            color,
            opacity: overlayOpacity.value,
            name: s.name,
          })
        }
      } catch {
        // skip on error
      }
    }
  }
  canvasOverlays.value = overlays
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
  // Detect WebGL capability
  webglCap.value = detectWebGL()

  if (!webglCap.value.webgl2 && !webglCap.value.webgl1) {
    useCanvasFallback.value = true
  } else {
    // Initialize Cornerstone3D
    if (volumeLoader) {
      registerMdhVolumeLoader()
      if (appStore.isClientMode) {
        registerClientLoaders()
      }
    }

    // Listen for annotation changes to refresh measurements
    refreshOnAnnotationFn = () => tools.refreshMeasurements('axial')
    eventTarget.addEventListener('CORNERSTONE_TOOLS_ANNOTATION_ADDED', refreshOnAnnotationFn)
    eventTarget.addEventListener('CORNERSTONE_TOOLS_ANNOTATION_MODIFIED', refreshOnAnnotationFn)
    eventTarget.addEventListener('CORNERSTONE_TOOLS_ANNOTATION_REMOVED', refreshOnAnnotationFn)
  }

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

  // Fetch GPU info from backend
  try {
    const resp = await fetch('/api/system/gpu-info')
    if (resp.ok) gpuInfo.value = await resp.json()
  } catch {
    // ignore
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

// WebGL context loss/restore handling
function setupContextLossHandlers() {
  const canvas = document.querySelector('#axial canvas') as HTMLCanvasElement | null
  if (!canvas) return
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault()
    console.warn('WebGL context lost')
  })
  canvas.addEventListener('webglcontextrestored', () => {
    console.info('WebGL context restored, reinitializing engine...')
    csEngine = null
    engineReady.value = false
    viewportElements.value = {}
    volumeLoaded = false
  })
}

// Canvas2D fallback: fetch rendered slices from backend
async function loadSlicesForCanvas() {
  if (!appStore.selectedSeriesUid) return
  canvasLoading.value = true
  try {
    const results = await Promise.all(
      (['axial', 'sagittal', 'coronal'] as const).map(async (orient) => {
        try {
          const data = await appStore.getSlice(
            appStore.selectedSeriesUid!,
            orient,
            canvasSliceIndex.value[orient] ?? 0,
            windowCenter.value,
            windowWidth.value,
          )
          return { orient, data: data?.data || null, maxSlice: data?.max_slice ?? 0 }
        } catch {
          return { orient, data: null, maxSlice: 0 }
        }
      })
    )
    for (const { orient, data, maxSlice } of results) {
      canvasSliceData.value = { ...canvasSliceData.value, [orient]: data }
      canvasMaxSlice.value = { ...canvasMaxSlice.value, [orient]: maxSlice }
    }
  } finally {
    canvasLoading.value = false
  }
}

async function handleCanvasSliceChange(orientation: string, newIndex: number) {
  if (!appStore.selectedSeriesUid) return
  canvasSliceIndex.value = { ...canvasSliceIndex.value, [orientation]: newIndex }
  try {
    const data = await appStore.getSlice(
      appStore.selectedSeriesUid,
      orientation,
      newIndex,
      windowCenter.value,
      windowWidth.value,
    )
    canvasSliceData.value = { ...canvasSliceData.value, [orientation]: data?.data || null }
  } catch {
    // keep existing data on error
  }
}

function handleCanvasAnnotateClick(x: number, y: number, orientation: string) {
  canvasTools.handleCanvasClick(x, y)

  // After annotation is created, fill in value
  const last = canvasTools.annotations.value[canvasTools.annotations.value.length - 1]
  if (!last) return

  const pixels = canvasSliceData.value[orientation]
  if (!pixels) return

  const px = Math.round(x)
  const py = Math.round(y)

  if (last.toolName === 'Probe' && pixels[py]?.[px] !== undefined) {
    canvasTools.setToolValue(last.uid, pixels[py][px])
  } else if (last.toolName === 'Length' && last.points.length === 2 && seriesInfo.value?.spacing) {
    const sp = seriesInfo.value.spacing
    const dx = (last.points[1].x - last.points[0].x) * (sp[0] ?? 1)
    const dy = (last.points[1].y - last.points[0].y) * (sp[1] ?? 1)
    canvasTools.setToolValue(last.uid, Math.sqrt(dx * dx + dy * dy))
  }
}

watch(
  () => [appStore.selectedSeriesUid, appStore.selectedPatientId],
  () => loadSeriesData()
)

async function onViewportReady(orientation: string, element: HTMLDivElement) {
  viewportElements.value[orientation] = element

  // Once all three viewports are ready, create the engine
  if (Object.keys(viewportElements.value).length === 3 && !csEngine) {
    try {
      csEngine = new RenderingEngine('cs3d-engine')
    } catch (err) {
      console.error('WebGL engine failed, falling back to Canvas2D:', err)
      useCanvasFallback.value = true
      return
    }
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
    setupContextLossHandlers()

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
  if (!csEngine || !appStore.selectedSeriesUid || !appStore.selectedPatientId) return

  loading.value = true
  try {
    if (appStore.isClientMode) {
      const imageIds = getSeriesImageIds(appStore.selectedSeriesUid)
      if (imageIds.length === 0) return
      for (const vpId of ['axial', 'sagittal', 'coronal'] as const) {
        const vp = csEngine.getViewport(vpId) as Types.IStackViewport
        if (vp) {
          await vp.setStack(imageIds, 0)
        }
      }
    } else {
      if (!appStore.sessionId) return
      const volumeId = buildVolumeId(appStore.sessionId, appStore.selectedPatientId, appStore.selectedSeriesUid)
      for (const vpId of ['axial', 'sagittal', 'coronal'] as const) {
        const vp = csEngine.getViewport(vpId)
        if (vp) {
          await (vp as Types.IBaseVolumeViewport).setVolumes([{ volumeId }])
        }
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
    // Parallelize independent API calls
    const [infoResult, structsResult, doseResult] = await Promise.all([
      appStore.getSeriesInfo(appStore.selectedSeriesUid),
      appStore.isClientMode ? Promise.resolve([] as StructInfo[]) : appStore.getStructs(),
      appStore.isClientMode ? Promise.resolve([] as DoseInfo[]) : appStore.getDoseInfo(),
    ])

    seriesInfo.value = infoResult
    structs.value = structsResult
    doseList.value = doseResult

    // Load DICOM tags in parallel with volume loading
    const volumePromise = useCanvasFallback.value
      ? loadSlicesForCanvas()
      : engineReady.value
        ? loadVolumeIntoViewports()
        : Promise.resolve()

    await Promise.all([loadDicomTags(), volumePromise])

    // Reset overlay state
    enabledStructOverlays.value.clear()
    enabledDoseOverlays.value.clear()
    structOverlayCache.value = {}
    doseOverlayCache.value = {}
    structColorMap.value = {}
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
