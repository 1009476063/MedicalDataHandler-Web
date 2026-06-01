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
      :draw-mode="roi.drawMode.value"
      @select-tool="useCanvasFallback ? (canvasTools.activeTool.value = $event as 'Length' | 'Probe') : tools.setActive($event)"
      @toggle-crosshairs="() => {}"
      @clear-all="useCanvasFallback ? canvasTools.clearAnnotations() : tools.clearAll"
      @export-csv="exportMeasurementsCsv"
      @toggle-draw-mode="toggleDrawMode"
    />

    <!-- Drawing Toolbar (shown in draw mode) -->
    <DrawingToolbar
      v-if="roi.drawMode.value"
      :active-tool="drawInput.activeTool.value"
      :brush-radius="roi.brushRadius.value"
      :can-undo="roi.canUndo.value"
      :can-redo="roi.canRedo.value"
      @select-tool="onDrawToolSelect"
      @update:brush-radius="onDrawBrushRadiusUpdate"
      @undo="onDrawUndo"
      @redo="onDrawRedo"
      @exit-draw="toggleDrawMode"
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
            :draw-mode="roi.drawMode.value"
            :draw-brush-radius="roi.brushRadius.value"
            :draw-cursor-x="drawInput.cursorX.value"
            :draw-cursor-y="drawInput.cursorY.value"
            @slice-change="(delta: number) => handleCanvasSliceChange(orientation, canvasSliceIndex[orientation] + delta)"
            @click="(x: number, y: number) => handleCanvasAnnotateClick(x, y, orientation)"
            @draw-mousedown="onDrawMouseDown"
            @draw-mousemove="onDrawMouseMove"
            @draw-mouseup="onDrawMouseUp"
            @draw-dblclick="onDrawDblClick"
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
              :draw-mode="roi.drawMode.value"
              :draw-brush-radius="roi.brushRadius.value"
              :draw-cursor-x="drawInput.cursorX.value"
              :draw-cursor-y="drawInput.cursorY.value"
              @viewport-ready="onViewportReady('axial', $event)"
              @resize="onViewportResize"
              @draw-mousedown="onDrawMouseDown"
              @draw-mousemove="onDrawMouseMove"
              @draw-mouseup="onDrawMouseUp"
              @draw-dblclick="onDrawDblClick"
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
              :draw-mode="roi.drawMode.value"
              :draw-brush-radius="roi.brushRadius.value"
              :draw-cursor-x="drawInput.cursorX.value"
              :draw-cursor-y="drawInput.cursorY.value"
              @viewport-ready="onViewportReady('sagittal', $event)"
              @resize="onViewportResize"
              @draw-mousedown="onDrawMouseDown"
              @draw-mousemove="onDrawMouseMove"
              @draw-mouseup="onDrawMouseUp"
              @draw-dblclick="onDrawDblClick"
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
              :draw-mode="roi.drawMode.value"
              :draw-brush-radius="roi.brushRadius.value"
              :draw-cursor-x="drawInput.cursorX.value"
              :draw-cursor-y="drawInput.cursorY.value"
              @viewport-ready="onViewportReady('coronal', $event)"
              @resize="onViewportResize"
              @draw-mousedown="onDrawMouseDown"
              @draw-mousemove="onDrawMouseMove"
              @draw-mouseup="onDrawMouseUp"
              @draw-dblclick="onDrawDblClick"
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
        :fusion-enabled="fusion.fusionEnabled.value"
        :fusion-available="fusionAvailable"
        :fusion-ct-uid="fusion.ctSeriesUid.value || ''"
        :fusion-pt-uid="fusion.ptSeriesUid.value || ''"
        :fusion-opacity="fusion.fusionOpacity.value"
        :fusion-blend-mode="fusion.blendMode.value"
        :fusion-show-suv="fusion.showSuv.value"
        :fusion-suv-info="fusion.suvInfo.value"
        :pet-ct-pairs="fusion.petCtPairs.value"
        :ai-models="ai.models.value"
        :ai-loading="ai.loading.value"
        :ai-progress="ai.progress.value"
        :ai-progress-message="ai.progressMessage.value"
        :ai-result="ai.analysisResult.value"
        :ai-study-summary="ai.studySummary.value"
        :ai-summary-loading="ai.summaryLoading.value"
        :confidence-threshold="settings.analysisConfidenceThreshold.value"
        :draw-mode="roi.drawMode.value"
        :roi-labels="roi.labels.value"
        :roi-active-label="roi.activeLabel.value"
        :roi-ai-loading="roi.aiSegLoading.value"
        :roi-ai-progress="roi.aiSegProgress.value"
        :roi-ai-message="roi.aiSegMessage.value"
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
        @toggle-fusion="toggleFusion"
        @set-fusion-ct-series="setFusionCtSeries"
        @set-fusion-pt-series="setFusionPtSeries"
        @update-fusion-opacity="updateFusionOpacity"
        @update-blend-mode="updateBlendMode"
        @toggle-suv="toggleSuv"
        @fetch-ai-models="ai.fetchModels"
        @run-ai-analysis="(modelId, prompt, strategy) => ai.runAnalysis(appStore.sessionId!, appStore.selectedPatientId!, appStore.selectedSeriesUid!, modelId, prompt, strategy)"
        @reset-ai="ai.reset"
        @create-sr="createSrFromAi"
        @generate-ai-summary="generateAiSummary"
        @roi-select-label="onRoiSelectLabel"
        @roi-update-label-color="onRoiUpdateLabelColor"
        @roi-remove-label="onRoiRemoveLabel"
        @roi-erode="onRoiErode"
        @roi-dilate="onRoiDilate"
        @roi-smooth="onRoiSmooth"
        @roi-clear-label="onRoiClearLabel"
        @roi-run-auto-segment="onRoiRunAutoSegment"
        @roi-run-text-segment="onRoiRunTextSegment"
        @roi-run-reference-segment="onRoiRunReferenceSegment"
        @roi-export-nifti="onRoiExportNifti"
        @roi-export-dicom-seg="onRoiExportDicomSeg"
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

    <!-- Print Dialog -->
    <PrintDialog
      :visible="showPrintDialog"
      :image-data-url="screenshotDataUrl"
      @close="showPrintDialog = false"
    />
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
import { useFusion } from '@/composables/useFusion'
import { useAI } from '@/composables/useAI'
import { useSR } from '@/composables/useSR'
import { useSettings } from '@/composables/useSettings'
import { getSeriesImageIds } from '@/composables/useClientMode'
import type { SeriesInfo, StructInfo, DoseInfo } from '@/types'
import { EyeIcon } from '@heroicons/vue/24/outline'
import type { Types } from '@cornerstonejs/core'
import { detectWebGL, type WebGLCapability } from '@/utils/webglDetector'
import ImageSliceViewer from '@/components/viewer/ImageSliceViewer.vue'
import PrintDialog from '@/components/viewer/PrintDialog.vue'
import { useCanvasTools } from '@/composables/useCanvasTools'
import { useROIDrawing } from '@/composables/useROIDrawing'
import { useROIDrawInput } from '@/composables/useROIDrawInput'
import DrawingToolbar from '@/components/viewer/DrawingToolbar.vue'

// Lazy-loaded Cornerstone3D modules — loaded in onMounted to reduce initial bundle
let RenderingEngine: any
let Enums: any
let volumeLoader: any
let eventTarget: any
let buildVolumeId: any
let registerMdhVolumeLoader: any
let registerClientLoaders: any

const { t } = useI18n()
const appStore = useAppStore()
const tools = useTools()
const seg = useSegmentation()
const fourD = useFourD()
const fusion = useFusion()
const showPrintDialog = ref(false)
const screenshotDataUrl = ref('')
const ai = useAI()
const sr = useSR()
const settings = useSettings()
const roi = useROIDrawing()
const drawInput = useROIDrawInput({
  onPaintStroke: async (points, radius) => {
    const orient = getDrawOrientation()
    await roi.paintStroke(orient, canvasSliceIndex.value[orient], points.map(p => [p.x, p.y]), radius)
    await refreshRoiMasks(orient)
  },
  onShapeFill: async (shapeType, points) => {
    const orient = getDrawOrientation()
    await roi.fillShape(orient, canvasSliceIndex.value[orient], shapeType, points.map(p => [p.x, p.y]))
    await refreshRoiMasks(orient)
  },
  onFloodFill: async (x, y) => {
    const orient = getDrawOrientation()
    const pixelData = canvasSliceData.value[orient]
    if (pixelData) {
      await roi.floodFill(orient, canvasSliceIndex.value[orient], x, y, pixelData)
      await refreshRoiMasks(orient)
    }
  },
  onEraseStroke: async (points, radius) => {
    const orient = getDrawOrientation()
    await roi.eraseAt(orient, canvasSliceIndex.value[orient], points.map(p => [p.x, p.y]), radius)
    await refreshRoiMasks(orient)
  },
})

async function refreshRoiMasks(orient: string) {
  if (!roi.activeLabelMapId.value) return
  const masks = await roi.loadSliceMasks(orient, canvasSliceIndex.value[orient])
  roiMasksByOrientation.value = { ...roiMasksByOrientation.value, [orient]: masks }
}

const windowPresetsMap: Record<string, { center: number; width: number }> = {
  auto: { center: 40, width: 400 },
  ct: { center: 40, width: 400 },
  mri: { center: 500, width: 1200 },
  bone: { center: 400, width: 1800 },
  lung: { center: -600, width: 1500 },
  soft_tissue: { center: 50, width: 350 },
  pet: { center: 2.5, width: 15 },
}
const initialWl = windowPresetsMap[settings.defaultWindow.value] || windowPresetsMap.ct
const windowCenter = ref(initialWl.center)
const windowWidth = ref(initialWl.width)
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

// ROI masks cache per orientation for overlay rendering
const roiMasksByOrientation = ref<Record<string, Record<number, number[][]>>>({})

const orientationForCurrentSlice = computed(() => {
  if (drawInput.activeTool.value === 'polygon') return 'axial'
  return 'axial'
})

function getDrawOrientation(): string {
  return orientationForCurrentSlice.value
}

// GPU info from backend
const gpuInfo = ref<{ gpu_available: boolean; gpu_name?: string } | null>(null)

// Cornerstone3D engine state
let csEngine: any = null
const engineReady = ref(false)
const viewportElements = ref<Record<string, HTMLDivElement>>({})
let volumeLoaded = false
let refreshOnAnnotationFn: (() => void) | null = null

// Overlay state (RT structures rendered via canvas overlay — Phase 2 will use Cornerstone3D segmentation)
const enabledStructOverlays = ref<Set<string>>(new Set())
const enabledDoseOverlays = ref<Set<string>>(new Set())
const overlayOpacity = settings.structOpacity
const doseOpacity = settings.doseOpacity
const contourThickness = settings.contourThickness
const structOverlayCache = ref<Record<string, number[][] | null>>({})
const doseOverlayCache = ref<Record<string, { data: number[][]; min: number; max: number } | null>>({})
const structColorMap = ref<Record<string, string>>({})

// DICOM tag inspection
const showDicomTags = ref(false)
const dicomTagSearch = ref('')
const dicomTags = ref<Array<{ tag: string; name: string; value: string; vr: string }>>([])

// Orientation labels
const showOrientationLabels = settings.showOrientationLabels
const orientationLabelColor = settings.orientationLabelColor

// Confirmation dialog
const showConfirmDialog = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmButtonText = ref(t('viewer.confirm'))
let confirmCallback: (() => void) | null = null

const patients = computed(() => appStore.patients || [])

const fusionAvailable = computed(() => fusion.petCtPairs.value.length > 0)

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

// Load RT struct overlays + ROI masks for Canvas2D mode
async function loadCanvasOverlays() {
  if (!useCanvasFallback.value || !appStore.selectedSeriesUid) return

  const overlays: Record<string, Array<{ mask: number[][] | null; color: string; opacity: number; name?: string }>> = {}
  for (const orient of ['axial', 'sagittal', 'coronal'] as const) {
    overlays[orient] = []
  }

  // RT struct overlays
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

  // ROI label overlays
  if (roi.activeLabelMapId.value) {
    for (const orient of ['axial', 'sagittal', 'coronal'] as const) {
      const masks = roiMasksByOrientation.value[orient] || {}
      for (const [labelIdStr, mask] of Object.entries(masks)) {
        const labelId = Number(labelIdStr)
        const label = roi.labels.value.find(l => l.id === labelId)
        overlays[orient].push({
          mask,
          color: label?.color || '#ff0000',
          opacity: label?.opacity ?? 0.4,
          name: label?.name || `Label ${labelId}`,
        })
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

// Load ROI masks for all orientations when label map exists and draw mode is active
watch(
  [() => roi.activeLabelMapId.value, () => canvasSliceIndex.value.axial, () => canvasSliceIndex.value.sagittal, () => canvasSliceIndex.value.coronal],
  async () => {
    if (!roi.activeLabelMapId.value || !roi.drawMode.value) return
    for (const orient of ['axial', 'sagittal', 'coronal'] as const) {
      const masks = await roi.loadSliceMasks(orient, canvasSliceIndex.value[orient])
      roiMasksByOrientation.value = { ...roiMasksByOrientation.value, [orient]: masks }
    }
  },
)

// --- Draw Mode Handlers ---

const drawInputActive = ref(false)

function toggleDrawMode() {
  roi.drawMode.value = !roi.drawMode.value
  if (roi.drawMode.value) {
    drawInputActive.value = true
    // Exit measurement tool in canvas mode
    if (useCanvasFallback.value) {
      canvasTools.activeTool.value = null
    }
  } else {
    drawInputActive.value = false
    drawInput.cancelCurrentAction()
    roiMasksByOrientation.value = {}
  }
}

function onDrawToolSelect(tool: string) {
  drawInput.setTool(tool as any)
}

function onDrawBrushRadiusUpdate(val: number) {
  roi.brushRadius.value = val
}

function onDrawUndo() {
  roi.undo().then(() => {
    refreshRoiMasks('axial')
    refreshRoiMasks('sagittal')
    refreshRoiMasks('coronal')
  })
}

function onDrawRedo() {
  roi.redo().then(() => {
    refreshRoiMasks('axial')
    refreshRoiMasks('sagittal')
    refreshRoiMasks('coronal')
  })
}

// Draw event handlers — used by both Canvas2D and Cornerstone3D viewers
function onDrawMouseDown(e: { x: number; y: number }) {
  if (!roi.drawMode.value || !drawInputActive.value) return
  drawInput.handleMouseDown(e.x, e.y)
}

function onDrawMouseMove(e: { x: number; y: number }) {
  if (!roi.drawMode.value || !drawInputActive.value) return
  drawInput.handleMouseMove(e.x, e.y)
}

function onDrawMouseUp() {
  if (!roi.drawMode.value || !drawInputActive.value) return
  drawInput.handleMouseUp()
}

function onDrawDblClick() {
  if (!roi.drawMode.value || !drawInputActive.value) return
  drawInput.handleDoubleClick()
}

// ROI sidebar event handlers
function onRoiSelectLabel(id: number) {
  roi.activeLabel.value = id
}

function onRoiUpdateLabelColor(id: number, color: string) {
  roi.labels.value = roi.labels.value.map(l => l.id === id ? { ...l, color } : l)
}

function onRoiRemoveLabel(id: number) {
  roi.removeLabel(id)
}

function onRoiErode() {
  roi.erode().then(() => refreshAllRoiMasks())
}

function onRoiDilate() {
  roi.dilate().then(() => refreshAllRoiMasks())
}

function onRoiSmooth() {
  roi.smooth().then(() => refreshAllRoiMasks())
}

function onRoiClearLabel() {
  roi.invalidateCache()
  refreshAllRoiMasks()
}

async function refreshAllRoiMasks() {
  for (const orient of ['axial', 'sagittal', 'coronal'] as const) {
    await refreshRoiMasks(orient)
  }
}

async function onRoiRunAutoSegment() {
  if (!appStore.sessionId || !appStore.selectedPatientId || !appStore.selectedSeriesUid) return
  await roi.runAutoSegment(appStore.sessionId, appStore.selectedPatientId, appStore.selectedSeriesUid)
  refreshAllRoiMasks()
}

async function onRoiRunTextSegment(textPrompt: string) {
  if (!appStore.sessionId || !appStore.selectedPatientId || !appStore.selectedSeriesUid) return
  await roi.runTextSegment(appStore.sessionId, appStore.selectedPatientId, appStore.selectedSeriesUid, textPrompt)
  refreshAllRoiMasks()
}

async function onRoiRunReferenceSegment(refLabelMapId: string, refLabel: number) {
  if (!appStore.sessionId || !appStore.selectedPatientId || !appStore.selectedSeriesUid) return
  await roi.runReferenceSegment(appStore.sessionId, appStore.selectedPatientId, appStore.selectedSeriesUid, refLabelMapId, refLabel)
  refreshAllRoiMasks()
}

async function onRoiExportNifti() {
  const blob = await roi.exportNifti()
  if (!blob) return
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `roi_${appStore.selectedSeriesUid || 'export'}.nii.gz`
  a.click()
  URL.revokeObjectURL(url)
}

async function onRoiExportDicomSeg() {
  if (!appStore.selectedPatientId || !seriesInfo.value?.study_uid) return
  const blob = await roi.exportDicomSeg(appStore.selectedPatientId, seriesInfo.value.study_uid)
  if (!blob) return
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `roi_${appStore.selectedSeriesUid || 'export'}.dcm`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  // Detect WebGL capability
  webglCap.value = detectWebGL()

  // Start API calls immediately — don't block on Cornerstone3D download
  const presetsPromise = fetch('/api/config/window-presets')
    .then(r => r.ok ? r.json() : null)
    .catch(() => null)
  const gpuPromise = fetch('/api/system/gpu-info')
    .then(r => r.ok ? r.json() : null)
    .catch(() => null)

  if (!webglCap.value.webgl2 && !webglCap.value.webgl1) {
    useCanvasFallback.value = true
  } else {
    // Load Cornerstone3D modules dynamically (this is the heavy ~3MB download)
    const [csCore, csTools, csVolumeLoader, csClientLoader] = await Promise.all([
      import('@cornerstonejs/core'),
      import('@cornerstonejs/tools'),
      import('@/utils/cornerstoneVolumeLoader'),
      import('@/utils/clientDicomLoader'),
    ])
    RenderingEngine = csCore.RenderingEngine
    Enums = csCore.Enums
    volumeLoader = csCore.volumeLoader
    eventTarget = csCore.eventTarget
    registerMdhVolumeLoader = csVolumeLoader.registerMdhVolumeLoader
    buildVolumeId = csVolumeLoader.buildVolumeId
    registerClientLoaders = csClientLoader.registerClientLoaders

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

  // Apply API results (already in-flight from above)
  const [presetsData, gpuData] = await Promise.all([presetsPromise, gpuPromise])

  if (presetsData?.rules && typeof presetsData.rules === 'object') {
    windowPresets.value = Object.entries(presetsData.rules).map(([name, vals]: [string, unknown]) => {
      const [width, center] = vals as [number, number]
      return { name, center, width }
    })
  }

  if (gpuData) {
    gpuInfo.value = gpuData
  }
})

onBeforeUnmount(() => {
  removeContextLossHandlers()
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
let _glLostHandler: ((e: Event) => void) | null = null
let _glRestoredHandler: (() => void) | null = null
let _glCanvas: HTMLCanvasElement | null = null

function setupContextLossHandlers() {
  const canvas = document.querySelector('#axial canvas') as HTMLCanvasElement | null
  if (!canvas) return
  _glCanvas = canvas
  _glLostHandler = (e) => {
    e.preventDefault()
    console.warn('WebGL context lost')
  }
  _glRestoredHandler = () => {
    console.info('WebGL context restored, reinitializing engine...')
    csEngine = null
    engineReady.value = false
    viewportElements.value = {}
    volumeLoaded = false
  }
  canvas.addEventListener('webglcontextlost', _glLostHandler)
  canvas.addEventListener('webglcontextrestored', _glRestoredHandler)
}

function removeContextLossHandlers() {
  if (_glCanvas && _glLostHandler) {
    _glCanvas.removeEventListener('webglcontextlost', _glLostHandler)
    _glCanvas.removeEventListener('webglcontextrestored', _glRestoredHandler!)
    _glCanvas = null
    _glLostHandler = null
    _glRestoredHandler = null
  }
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
    const toolGroup = await tools.createToolGroup('cs3d-engine')
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
      const viewportIds = ['axial', 'sagittal', 'coronal'] as const

      if (fusion.fusionEnabled.value && fusion.ctSeriesUid.value && fusion.ptSeriesUid.value) {
        await fusion.enableFusion(
          csEngine,
          [...viewportIds],
          appStore.sessionId,
          appStore.selectedPatientId,
          fusion.ctSeriesUid.value,
          fusion.ptSeriesUid.value,
        )
      } else {
        const volumeId = buildVolumeId(appStore.sessionId, appStore.selectedPatientId, appStore.selectedSeriesUid)
        for (const vpId of viewportIds) {
          const vp = csEngine.getViewport(vpId)
          if (vp) {
            await (vp as Types.IBaseVolumeViewport).setVolumes([{ volumeId }])
          }
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

    // Auto-detect PET-CT pairs
    findPetCtPairs()
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
  if (!csEngine) return
  const vp = csEngine.getViewport('axial')
  if (!vp) return
  const canvas = document.querySelector('#axial canvas') as HTMLCanvasElement | null
  if (!canvas) return
  const dataUrl = canvas.toDataURL('image/png')
  screenshotDataUrl.value = dataUrl
  showPrintDialog.value = true
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

async function createSrFromAi() {
  if (!appStore.sessionId || !appStore.selectedPatientId || !ai.analysisResult.value) return
  const findings = (ai.analysisResult.value.findings as Array<{
    region: string
    description: string
    confidence: number
    severity: string
  }>) || []
  if (findings.length === 0) return

  const patient = appStore.currentPatient
  const patientName = patient?.name || ''
  const studyDate = patient?.studies?.[0]?.date || ''

  try {
    await sr.createFromAi(
      appStore.sessionId,
      appStore.selectedPatientId,
      patientName,
      studyDate,
      findings.map(f => ({ name: f.region, value: f.description, description: `${f.severity} (${Math.round(f.confidence * 100)}%)` })),
    )
  } catch {
    // error handled by useSR
  }
}

async function generateAiSummary() {
  if (!ai.analysisResult.value) return
  const findings = (ai.analysisResult.value.findings as Array<{
    region: string
    description: string
    confidence: number
    severity: string
  }>) || []
  if (findings.length === 0) return
  await ai.generateSummary(findings)
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
  fusion.petCtPairs.value = []
  fusion.fusionEnabled.value = false
  fusion.ctSeriesUid.value = null
  fusion.ptSeriesUid.value = null
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

// Fusion handlers
async function findPetCtPairs() {
  if (!appStore.sessionId || !appStore.selectedPatientId) return
  await fusion.findPetCtPairs(appStore.sessionId, appStore.selectedPatientId)
}

async function toggleFusion() {
  if (fusion.fusionEnabled.value) {
    await fusion.disableFusion(csEngine, ['axial', 'sagittal', 'coronal'])
    volumeLoaded = false
    // Reload the CT volume
    loadVolumeIntoViewports()
  } else {
    if (!fusion.ctSeriesUid.value || !fusion.ptSeriesUid.value) return
    loadVolumeIntoViewports()
  }
}

function setFusionCtSeries(uid: string) {
  fusion.ctSeriesUid.value = uid
  if (fusion.fusionEnabled.value) {
    loadVolumeIntoViewports()
  }
}

function setFusionPtSeries(uid: string) {
  fusion.ptSeriesUid.value = uid
  if (fusion.fusionEnabled.value) {
    loadVolumeIntoViewports()
  }
}

function updateFusionOpacity(value: number) {
  fusion.setFusionOpacity(csEngine, ['axial', 'sagittal', 'coronal'], value)
}

async function updateBlendMode(mode: string) {
  await fusion.setBlendMode(csEngine, ['axial', 'sagittal', 'coronal'], mode as 'default' | 'additive')
}

async function toggleSuv() {
  fusion.showSuv.value = !fusion.showSuv.value
  if (fusion.showSuv.value && fusion.ptSeriesUid.value && appStore.sessionId && appStore.selectedPatientId) {
    await fusion.fetchSuvInfo(appStore.sessionId, appStore.selectedPatientId, fusion.ptSeriesUid.value)
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
