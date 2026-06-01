<template>
  <div class="w-64 border-l border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 overflow-y-auto hidden lg:block">
    <div class="p-4 space-y-4">
      <!-- Patient -->
      <div>
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.patient') }}</h3>
        <select
          v-model="appStore.selectedPatientId"
          class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          @change="$emit('patientChange')"
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
            @click="$emit('seriesSelect', s.series_uid)"
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
              :value="windowWidth"
              type="range"
              :min="1"
              :max="4000"
              class="flex-1 h-1.5 accent-primary-500"
              @input="$emit('update:windowWidth', Number(($event.target as HTMLInputElement).value))"
            />
            <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ windowWidth }}</span>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-xs text-accent-500 w-8">L</label>
            <input
              :value="windowCenter"
              type="range"
              :min="-1000"
              :max="3000"
              class="flex-1 h-1.5 accent-primary-500"
              @input="$emit('update:windowCenter', Number(($event.target as HTMLInputElement).value))"
            />
            <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ windowCenter }}</span>
          </div>
        </div>
        <div class="flex flex-wrap gap-1 mt-2">
          <button
            v-for="preset in windowPresets"
            :key="preset.name"
            class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
            @click="$emit('applyPreset', preset)"
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
              @change="$emit('toggleStructOverlay', s.key)"
            />
            <input
              type="color"
              :value="structColorMap[s.key] || structColors[i % structColors.length]"
              class="w-5 h-5 rounded border-0 cursor-pointer flex-shrink-0"
              @input="$emit('setStructColor', s.key, ($event.target as HTMLInputElement).value)"
            />
            <span class="truncate flex-1">{{ s.name }}</span>
            <span class="text-[10px] text-accent-400 px-1 py-0.5 rounded bg-accent-100 dark:bg-accent-800">
              {{ inferStructType(s.name) }}
            </span>
            <button
              :title="$t('viewer.centerOnRoi')"
              class="p-0.5 rounded hover:bg-primary-100 dark:hover:bg-primary-900/30 text-accent-400 hover:text-primary-500 transition-colors"
              @click.stop="$emit('centerOnRoi', s.key)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </button>
          </div>
        </div>
        <div class="mt-2 flex items-center gap-2">
          <label class="text-xs text-accent-500">{{ $t('viewer.opacity') }}</label>
          <input
            :value="overlayOpacity"
            type="range"
            :min="0.05"
            :max="1"
            step="0.05"
            class="flex-1 h-1.5 accent-primary-500"
            @input="$emit('update:overlayOpacity', Number(($event.target as HTMLInputElement).value))"
          />
          <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ Math.round(overlayOpacity * 100) }}%</span>
        </div>
        <div class="mt-2 flex items-center gap-2">
          <label class="text-xs text-accent-500">{{ $t('viewer.contour') }}</label>
          <input
            :value="contourThickness"
            type="range"
            :min="0"
            :max="4"
            step="1"
            class="flex-1 h-1.5 accent-primary-500"
            @input="$emit('update:contourThickness', Number(($event.target as HTMLInputElement).value))"
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
              @change="$emit('toggleDoseOverlay', d.file_id)"
            />
            <span class="w-3 h-3 rounded-full flex-shrink-0 bg-red-500" />
            <span class="truncate">{{ d.filename || d.file_id }}</span>
          </label>
        </div>
        <div class="mt-2 flex items-center gap-2">
          <label class="text-xs text-accent-500">{{ $t('viewer.opacity') }}</label>
          <input
            :value="doseOpacity"
            type="range"
            :min="0.05"
            :max="1"
            step="0.05"
            class="flex-1 h-1.5 accent-red-500"
            @input="$emit('update:doseOpacity', Number(($event.target as HTMLInputElement).value))"
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

      <!-- PET-CT Fusion -->
      <div v-if="fusionEnabled || fusionAvailable">
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.fusion') }}</h3>
        <div class="space-y-2">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              :checked="fusionEnabled"
              class="rounded border-accent-300 text-primary-500 focus:ring-primary-500/50"
              @change="$emit('toggleFusion')"
            />
            <span class="text-xs text-accent-700 dark:text-accent-300">{{ $t('viewer.fusionEnabled') }}</span>
          </label>

          <template v-if="fusionEnabled">
            <div>
              <label class="text-xs text-accent-500">{{ $t('viewer.ctSeries') }}</label>
              <select
                :value="fusionCtUid"
                class="w-full px-2 py-1.5 mt-1 text-xs bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary-500/50"
                @change="$emit('setFusionCtSeries', ($event.target as HTMLSelectElement).value)"
              >
                <option value="">{{ $t('viewer.selectCtSeries') }}</option>
                <option v-for="p in petCtPairs" :key="p.ct_series_uid" :value="p.ct_series_uid">
                  {{ p.ct_description || p.ct_series_uid }}
                </option>
              </select>
            </div>

            <div>
              <label class="text-xs text-accent-500">{{ $t('viewer.ptSeries') }}</label>
              <select
                :value="fusionPtUid"
                class="w-full px-2 py-1.5 mt-1 text-xs bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary-500/50"
                @change="$emit('setFusionPtSeries', ($event.target as HTMLSelectElement).value)"
              >
                <option value="">{{ $t('viewer.selectPtSeries') }}</option>
                <option v-for="p in petCtPairs" :key="p.pt_series_uid" :value="p.pt_series_uid">
                  {{ p.pt_description || p.pt_series_uid }}
                </option>
              </select>
            </div>

            <div>
              <label class="text-xs text-accent-500">{{ $t('viewer.blend') }}</label>
              <div class="flex items-center gap-2 mt-1">
                <input
                  :value="fusionOpacity"
                  type="range"
                  :min="0"
                  :max="1"
                  step="0.05"
                  class="flex-1 h-1.5 accent-primary-500"
                  @input="$emit('updateFusionOpacity', Number(($event.target as HTMLInputElement).value))"
                />
                <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ Math.round(fusionOpacity * 100) }}%</span>
              </div>
            </div>

            <div>
              <label class="text-xs text-accent-500">{{ $t('viewer.blendMode') }}</label>
              <div class="flex gap-1 mt-1">
                <button
                  :class="['px-2 py-1 text-xs rounded transition-colors',
                    fusionBlendMode === 'additive' ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300' : 'bg-accent-100 dark:bg-accent-800 text-accent-600 dark:text-accent-400']"
                  @click="$emit('updateBlendMode', 'additive')"
                >{{ $t('viewer.additive') }}</button>
                <button
                  :class="['px-2 py-1 text-xs rounded transition-colors',
                    fusionBlendMode === 'default' ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300' : 'bg-accent-100 dark:bg-accent-800 text-accent-600 dark:text-accent-400']"
                  @click="$emit('updateBlendMode', 'default')"
                >{{ $t('viewer.default') }}</button>
              </div>
            </div>

            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                :checked="fusionShowSuv"
                class="rounded border-accent-300 text-primary-500 focus:ring-primary-500/50"
                @change="$emit('toggleSuv')"
              />
              <span class="text-xs text-accent-700 dark:text-accent-300">{{ $t('viewer.showSuv') }}</span>
            </label>

            <div v-if="fusionSuvInfo && fusionShowSuv" class="text-[11px] text-accent-500 space-y-0.5 pl-4">
              <p v-if="fusionSuvInfo.patient_weight">{{ $t('viewer.suvValue') }}: {{ fusionSuvInfo.suv_factor?.toFixed(4) ?? 'N/A' }}</p>
              <p>W: {{ fusionSuvInfo.patient_weight ?? 'N/A' }} kg</p>
              <p>Dose: {{ fusionSuvInfo.total_dose ?? 'N/A' }} Bq</p>
            </div>
          </template>

          <p v-if="!fusionEnabled && petCtPairs.length === 0" class="text-xs text-accent-400">{{ $t('viewer.noPairsFound') }}</p>
        </div>
      </div>

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
        @update-fps="(f) => fourD.setFps(f)"
        @change-time-point="(pos) => { fourD.setTimePoint(pos); fourD.loadTimePoint(appStore.selectedPatientId!, appStore.selectedSeriesUid!, pos) }"
      />

      <!-- AI Analysis -->
      <div>
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.ai.title') }}</h3>
        <AIPanel
          v-model:slice-strategy="sliceStrategy"
          :models="aiModels"
          :loading="aiLoading"
          :progress="aiProgress"
          :progress-message="aiProgressMessage"
          :analysis-result="aiResult"
          :confidence-threshold="confidenceThreshold"
          :study-summary="aiStudySummary"
          :summary-loading="aiSummaryLoading"
          @fetch-models="$emit('fetch-ai-models')"
          @run-analysis="(modelId, prompt, strategy) => $emit('run-ai-analysis', modelId, prompt, strategy)"
          @reset="$emit('reset-ai')"
          @create-sr="$emit('create-sr')"
          @generate-summary="$emit('generate-ai-summary')"
        />
      </div>

      <!-- Orientation Label Color -->
      <div>
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.orientationLabels') }}</h3>
        <div class="flex items-center gap-2">
          <label class="text-xs text-accent-500">{{ $t('viewer.color') }}</label>
          <input
            :value="orientationLabelColor"
            type="color"
            class="w-6 h-6 rounded border-0 cursor-pointer"
            @input="$emit('update:orientationLabelColor', ($event.target as HTMLInputElement).value)"
          />
          <span class="text-xs text-accent-600 dark:text-accent-400">{{ orientationLabelColor }}</span>
        </div>
      </div>

      <!-- DICOM Tag Inspection -->
      <div>
        <button
          class="w-full flex items-center justify-between text-sm font-medium text-accent-700 dark:text-accent-300 mb-2"
          @click="$emit('toggleDicomTags')"
        >
          <span>{{ $t('viewer.dicomTags') }}</span>
          <svg :class="['w-4 h-4 transition-transform', showDicomTags ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div v-if="showDicomTags" class="space-y-2">
          <input
            :value="dicomTagSearch"
            type="text"
            :placeholder="$t('viewer.searchTags')"
            class="w-full px-2 py-1.5 text-xs bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-1 focus:ring-primary-500/50"
            @input="$emit('update:dicomTagSearch', ($event.target as HTMLInputElement).value)"
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

      <!-- ROI Drawing -->
      <div v-if="drawMode">
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('roi.labels') }}</h3>
        <ROIPanel
          :labels="roiLabels"
          :active-label="roiActiveLabel"
          :ai-loading="roiAiLoading"
          :ai-progress="roiAiProgress"
          :ai-message="roiAiMessage"
          @select-label="(id) => $emit('roi-select-label', id)"
          @update-label-color="(id, c) => $emit('roi-update-label-color', id, c)"
          @remove-label="(id) => $emit('roi-remove-label', id)"
          @erode="$emit('roi-erode')"
          @dilate="$emit('roi-dilate')"
          @smooth="$emit('roi-smooth')"
          @clear-label="$emit('roi-clear-label')"
          @run-auto-segment="$emit('roi-run-auto-segment')"
          @run-text-segment="(p) => $emit('roi-run-text-segment', p)"
          @run-reference-segment="$emit('roi-run-reference-segment')"
          @export-nifti="$emit('roi-export-nifti')"
          @export-dicom-seg="$emit('roi-export-dicom-seg')"
        />
      </div>

      <!-- Measurements -->
      <MeasurementPanel :measurements="tools.measurements.value" />

      <!-- Delete Patient -->
      <div v-if="appStore.selectedPatientId">
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.sessionActions') }}</h3>
        <button
          class="w-full px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
          @click="$emit('confirmDeletePatient')"
        >
          {{ $t('viewer.removePatient') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { useTools } from '@/composables/useTools'
import { useSegmentation } from '@/composables/useSegmentation'
import { useFourD } from '@/composables/useFourD'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SegmentationPanel from '@/components/viewer/SegmentationPanel.vue'
import TimeSlider from '@/components/viewer/TimeSlider.vue'
import MeasurementPanel from '@/components/viewer/MeasurementPanel.vue'
import AIPanel from '@/components/viewer/AIPanel.vue'
import ROIPanel from '@/components/viewer/ROIPanel.vue'
import type { SeriesInfo, StructInfo, DoseInfo, PetCtPair, SuvInfo, AIModel, ROILabel } from '@/types'

const props = defineProps<{
  windowCenter: number
  windowWidth: number
  windowPresets: Array<{ name: string; center: number; width: number }>
  seriesInfo: SeriesInfo | null
  structs: StructInfo[]
  doseList: DoseInfo[]
  enabledStructOverlays: Set<string>
  enabledDoseOverlays: Set<string>
  overlayOpacity: number
  doseOpacity: number
  contourThickness: number
  structColorMap: Record<string, string>
  orientationLabelColor: string
  showDicomTags: boolean
  dicomTagSearch: string
  dicomTags: Array<{ tag: string; name: string; value: string; vr: string }>
  filteredDicomTags: Array<{ tag: string; name: string; value: string; vr: string }>
  fusionEnabled: boolean
  fusionAvailable: boolean
  fusionCtUid: string
  fusionPtUid: string
  fusionOpacity: number
  fusionBlendMode: string
  fusionShowSuv: boolean
  fusionSuvInfo: SuvInfo | null
  petCtPairs: PetCtPair[]
  aiModels: AIModel[]
  aiLoading: boolean
  aiProgress: number
  aiProgressMessage: string
  aiResult: Record<string, unknown> | null
  confidenceThreshold: number
  aiStudySummary: { summary: string; key_findings: string[]; recommendations: string[] } | null
  aiSummaryLoading: boolean
  drawMode?: boolean
  roiLabels: ROILabel[]
  roiActiveLabel: number
  roiAiLoading: boolean
  roiAiProgress: number
  roiAiMessage: string
}>()

defineEmits<{
  patientChange: []
  seriesSelect: [uid: string]
  applyPreset: [preset: { name: string; center: number; width: number }]
  toggleStructOverlay: [key: string]
  setStructColor: [key: string, color: string]
  centerOnRoi: [key: string]
  toggleDoseOverlay: [fileId: string]
  confirmDeletePatient: []
  toggleDicomTags: []
  'update:windowWidth': [value: number]
  'update:windowCenter': [value: number]
  'update:overlayOpacity': [value: number]
  'update:doseOpacity': [value: number]
  'update:contourThickness': [value: number]
  'update:orientationLabelColor': [value: string]
  'update:dicomTagSearch': [value: string]
  toggleFusion: []
  setFusionCtSeries: [uid: string]
  setFusionPtSeries: [uid: string]
  updateFusionOpacity: [value: number]
  updateBlendMode: [mode: string]
  toggleSuv: []
  'fetch-ai-models': []
  'run-ai-analysis': [modelId: string, prompt: string, sliceStrategy: string]
  'reset-ai': []
  'create-sr': []
  'generate-ai-summary': []
  'roi-select-label': [id: number]
  'roi-update-label-color': [id: number, color: string]
  'roi-remove-label': [id: number]
  'roi-erode': []
  'roi-dilate': []
  'roi-smooth': []
  'roi-clear-label': []
  'roi-run-auto-segment': []
  'roi-run-text-segment': [prompt: string]
  'roi-run-reference-segment': []
  'roi-export-nifti': []
  'roi-export-dicom-seg': []
}>()

const sliceStrategy = ref('middle')

const appStore = useAppStore()
const tools = useTools()
const seg = useSegmentation()
const fourD = useFourD()

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
</script>
