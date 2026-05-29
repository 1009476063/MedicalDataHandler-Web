<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="flex items-center justify-between px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('viewer.title') }}</h1>
      <div class="flex items-center gap-2">
        <!-- Rotation controls -->
        <button
          class="p-1.5 rounded-lg hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
          :title="$t('viewer.rotateLeft')"
          @click="rotateLeft"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v2M3 10l4-4M3 10l4 4"/></svg>
        </button>
        <button
          class="p-1.5 rounded-lg hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
          :title="$t('viewer.rotateRight')"
          @click="rotateRight"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a5 5 0 00-5 5v2m15-7l-4-4m4 4l-4 4"/></svg>
        </button>
        <div class="w-px h-5 bg-accent-200 dark:bg-accent-700 mx-1" />
        <button
          :class="['p-1.5 rounded-lg transition-colors', flipHorizontal ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600' : 'hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400']"
          :title="$t('viewer.flipH')"
          @click="flipHorizontal = !flipHorizontal"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 12l-3-3m3 3l3-3m7 0v12m0-12l3 3m-3-3l-3 3"/></svg>
        </button>
        <button
          :class="['p-1.5 rounded-lg transition-colors', flipVertical ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600' : 'hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400']"
          :title="$t('viewer.flipV')"
          @click="flipVertical = !flipVertical"
        >
          <svg class="w-4 h-4 rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 12l-3-3m3 3l3-3m7 0v12m0-12l3 3m-3-3l-3 3"/></svg>
        </button>
        <div class="w-px h-5 bg-accent-200 dark:bg-accent-700 mx-1" />
        <button
          :class="['p-1.5 rounded-lg transition-colors', showOrientationLabels ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600' : 'hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400']"
          :title="$t('viewer.toggleOrientation')"
          @click="showOrientationLabels = !showOrientationLabels"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"/></svg>
        </button>
        <div class="w-px h-5 bg-accent-200 dark:bg-accent-700 mx-1" />
        <button
          class="p-1.5 rounded-lg hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
          :title="$t('viewer.screenshot')"
          @click="captureScreenshot"
        >
          <CameraIcon class="w-4 h-4" />
        </button>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <div class="flex-1 p-2 min-w-0">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-2 h-full">
          <div class="min-h-[200px]">
            <ImageSliceViewer
              ref="axialViewerRef"
              label="Axial"
              :pixel-data="axialData"
              :width="viewerWidth"
              :height="viewerHeight"
              :slice-index="sliceIndex"
              :max-slice="maxSlice"
              :window-center="windowCenter"
              :window-width="windowWidth"
              :loading="loading"
              :overlays="axialOverlays"
              :rotation="rotation"
              :flip-h="flipHorizontal"
              :flip-v="flipVertical"
              :show-orientation-labels="showOrientationLabels"
              :orientation-label-color="orientationLabelColor"
              :zoom-speed="zoomSpeed"
              :pan-speed="panSpeed"
              :crosshair-x="crosshairAxial?.x ?? null"
              :crosshair-y="crosshairAxial?.y ?? null"
              @slice-change="onSliceChange"
              @window-change="onWindowChange"
              @crosshair-move="onAxialCrosshairMove"
            />
          </div>
          <div class="min-h-[200px]">
            <ImageSliceViewer
              ref="sagittalViewerRef"
              label="Sagittal"
              :pixel-data="sagittalData"
              :width="viewerWidth"
              :height="viewerHeight"
              :slice-index="sagSliceIndex"
              :max-slice="sagMaxSlice"
              :window-center="windowCenter"
              :window-width="windowWidth"
              :loading="loading"
              :overlays="sagittalOverlays"
              :rotation="rotation"
              :flip-h="flipHorizontal"
              :flip-v="flipVertical"
              :show-orientation-labels="showOrientationLabels"
              :orientation-label-color="orientationLabelColor"
              :zoom-speed="zoomSpeed"
              :pan-speed="panSpeed"
              :crosshair-x="crosshairSagittal?.x ?? null"
              :crosshair-y="crosshairSagittal?.y ?? null"
              @slice-change="onSagSliceChange"
              @window-change="onWindowChange"
              @crosshair-move="onSagittalCrosshairMove"
            />
          </div>
          <div class="min-h-[200px]">
            <ImageSliceViewer
              ref="coronalViewerRef"
              label="Coronal"
              :pixel-data="coronalData"
              :width="viewerWidth"
              :height="viewerHeight"
              :slice-index="corSliceIndex"
              :max-slice="corMaxSlice"
              :window-center="windowCenter"
              :window-width="windowWidth"
              :loading="loading"
              :overlays="coronalOverlays"
              :rotation="rotation"
              :flip-h="flipHorizontal"
              :flip-v="flipVertical"
              :show-orientation-labels="showOrientationLabels"
              :orientation-label-color="orientationLabelColor"
              :zoom-speed="zoomSpeed"
              :pan-speed="panSpeed"
              :crosshair-x="crosshairCoronal?.x ?? null"
              :crosshair-y="crosshairCoronal?.y ?? null"
              @slice-change="onCorSliceChange"
              @window-change="onWindowChange"
              @crosshair-move="onCoronalCrosshairMove"
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

          <!-- Crosshairs Toggle -->
          <div>
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.crosshairs') }}</h3>
            <label class="flex items-center gap-2 px-2 py-1.5 rounded text-xs text-accent-700 dark:text-accent-300 hover:bg-accent-50 dark:hover:bg-accent-800/50 cursor-pointer transition-colors">
              <input
                type="checkbox"
                v-model="showCrosshairs"
                class="rounded border-accent-300 text-primary-500 focus:ring-primary-500/50"
              />
              <span>{{ $t('viewer.showSyncCrosshairs') }}</span>
            </label>
          </div>

          <!-- Pan/Zoom Speed -->
          <div>
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.navigationSpeed') }}</h3>
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <label class="text-xs text-accent-500 w-10">{{ $t('viewer.zoom') }}</label>
                <input
                  v-model.number="zoomSpeed"
                  type="range"
                  :min="0.02"
                  :max="0.5"
                  step="0.02"
                  class="flex-1 h-1.5 accent-primary-500"
                />
                <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ zoomSpeed.toFixed(2) }}</span>
              </div>
              <div class="flex items-center gap-2">
                <label class="text-xs text-accent-500 w-10">{{ $t('viewer.pan') }}</label>
                <input
                  v-model.number="panSpeed"
                  type="range"
                  :min="0.2"
                  :max="3"
                  step="0.1"
                  class="flex-1 h-1.5 accent-primary-500"
                />
                <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ panSpeed.toFixed(1) }}</span>
              </div>
            </div>
          </div>

          <!-- Voxel Info -->
          <div v-if="voxelInfo">
            <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('viewer.voxelInfo') }}</h3>
            <div class="p-2 bg-accent-50 dark:bg-accent-800 rounded-lg text-xs space-y-1">
              <p class="text-accent-600 dark:text-accent-400">{{ $t('viewer.pane') }}: {{ voxelInfo.label }}</p>
              <p class="text-accent-600 dark:text-accent-400">{{ $t('viewer.position') }}: ({{ voxelInfo.x }}, {{ voxelInfo.y }})</p>
              <p class="font-mono text-accent-900 dark:text-white">{{ $t('viewer.value') }}: {{ voxelInfo.value !== null ? voxelInfo.value.toFixed(1) : $t('viewer.na') }}</p>
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
import ImageSliceViewer from '@/components/viewer/ImageSliceViewer.vue'
import type { OverlayData } from '@/components/viewer/ImageSliceViewer.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { SliceData, SeriesInfo, StructInfo, DoseInfo } from '@/types'
import { EyeIcon, CameraIcon } from '@heroicons/vue/24/outline'

const { t } = useI18n()
const appStore = useAppStore()

const currentOrientation = ref('axial')
const sliceIndex = ref(0)
const sagSliceIndex = ref(0)
const corSliceIndex = ref(0)
const maxSlice = ref(0)
const sagMaxSlice = ref(0)
const corMaxSlice = ref(0)
const windowCenter = ref(40)
const windowWidth = ref(400)
const loading = ref(false)
const seriesInfo = ref<SeriesInfo | null>(null)
const structs = ref<StructInfo[]>([])
const doseList = ref<DoseInfo[]>([])

const axialData = ref<number[][] | null>(null)
const sagittalData = ref<number[][] | null>(null)
const coronalData = ref<number[][] | null>(null)

// Synchronized crosshair state
const crosshairAxial = ref<{ x: number; y: number } | null>(null)
const crosshairSagittal = ref<{ x: number; y: number } | null>(null)
const crosshairCoronal = ref<{ x: number; y: number } | null>(null)
const showCrosshairs = ref(true)

// Voxel inspection
const voxelInfo = ref<{ x: number; y: number; value: number | null; label: string } | null>(null)

// Overlay state
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

// Rotation/flip state
const rotation = ref(0)
const flipHorizontal = ref(false)
const flipVertical = ref(false)

// Orientation labels
const showOrientationLabels = ref(true)
const orientationLabelColor = ref('#00ff00')

// Confirmation dialog
const showConfirmDialog = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmButtonText = ref(t('viewer.confirm'))
let confirmCallback: (() => void) | null = null

const viewerWidth = ref(512)
const viewerHeight = ref(512)
let resizeObserver: ResizeObserver | null = null

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

// Pan/zoom speed
const zoomSpeed = ref(0.1)
const panSpeed = ref(1)

// Treatment site filter
const treatmentSite = ref('')

// Overlay data computations
const axialOverlays = computed<OverlayData[]>(() => buildOverlays('axial'))
const sagittalOverlays = computed<OverlayData[]>(() => buildOverlays('sagittal'))
const coronalOverlays = computed<OverlayData[]>(() => buildOverlays('coronal'))

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

function setStructColor(structKey: string, color: string) {
  structColorMap.value = { ...structColorMap.value, [structKey]: color }
}

async function centerOnRoi(structKey: string) {
  const bounds = await appStore.getRoiBounds(structKey)
  if (!bounds || !seriesInfo.value?.origin || !seriesInfo.value?.spacing) return

  const origin = seriesInfo.value.origin
  const spacing = seriesInfo.value.spacing

  // DICOM coords: X (left-right), Y (anterior-posterior), Z (superior-inferior)
  // spacing: [axial(sagittal), coronal, sagittal(coronal)]
  const axialIdx = Math.round((bounds.center.z - origin[2]) / spacing[0])
  const sagIdx = Math.round((bounds.center.x - origin[0]) / spacing[2])
  const corIdx = Math.round((bounds.center.y - origin[1]) / spacing[1])

  sliceIndex.value = Math.max(0, Math.min(axialIdx, maxSlice.value))
  sagSliceIndex.value = Math.max(0, Math.min(sagIdx, sagMaxSlice.value))
  corSliceIndex.value = Math.max(0, Math.min(corIdx, corMaxSlice.value))

  await loadAllSlices()
}

function buildOverlays(orientation: string): OverlayData[] {
  const overlays: OverlayData[] = []

  // Structure overlays
  for (const struct of structs.value) {
    if (!enabledStructOverlays.value.has(struct.key)) continue
    const idx = structs.value.indexOf(struct)
    const mask = getOverlayMask(struct.key, orientation)
    overlays.push({
      mask,
      color: structColorMap.value[struct.key] || structColors[idx % structColors.length],
      opacity: overlayOpacity.value,
      name: struct.name,
      thickness: contourThickness.value,
    })
  }

  // Dose overlays
  for (const dose of doseList.value) {
    if (!enabledDoseOverlays.value.has(dose.file_id)) continue
    const doseData = getDoseOverlay(dose.file_id, orientation)
    if (doseData) {
      overlays.push({
        mask: doseData.data,
        color: '#ff0000',
        opacity: doseOpacity.value,
        name: dose.filename,
      })
    }
  }

  return overlays
}

function getOverlayMask(structKey: string, orientation: string): number[][] | null {
  const cacheKey = `${structKey}_${orientation}`
  return structOverlayCache.value[cacheKey] ?? null
}

function getDoseOverlay(doseFileId: string, orientation: string): { data: number[][]; min: number; max: number } | null {
  const cacheKey = `${doseFileId}_${orientation}`
  return doseOverlayCache.value[cacheKey] ?? null
}

onMounted(async () => {
  resizeObserver = new ResizeObserver(() => {
    viewerWidth.value = Math.max(200, Math.floor(window.innerWidth / 4))
    viewerHeight.value = Math.max(200, Math.floor(window.innerHeight / 3))
  })
  resizeObserver.observe(document.body)

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
  resizeObserver?.disconnect()
})

watch(
  () => [appStore.selectedSeriesUid, appStore.selectedPatientId],
  () => loadSeriesData()
)

async function loadSeriesData() {
  if (!appStore.selectedSeriesUid) return
  loading.value = true
  try {
    seriesInfo.value = await appStore.getSeriesInfo(appStore.selectedSeriesUid)
    if (seriesInfo.value?.shape) {
      maxSlice.value = seriesInfo.value.shape[0] - 1
      sagMaxSlice.value = seriesInfo.value.shape[1] - 1
      corMaxSlice.value = seriesInfo.value.shape[2] - 1
      sliceIndex.value = Math.floor(maxSlice.value / 2)
      sagSliceIndex.value = Math.floor(sagMaxSlice.value / 2)
      corSliceIndex.value = Math.floor(corMaxSlice.value / 2)

      if (seriesInfo.value.spacing) {
        const meanSpacing = seriesInfo.value.spacing.reduce((a: number, b: number) => a + b, 0) / 3
        viewerWidth.value = Math.min(800, Math.max(300, Math.round(512 * meanSpacing)))
        viewerHeight.value = viewerWidth.value
      }
    }
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

    await loadAllSlices()
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

async function loadAllSlices() {
  if (!appStore.selectedSeriesUid) return

  const [ax, sag, cor] = await Promise.all([
    appStore.getSliceBinary(appStore.selectedSeriesUid, 'axial', sliceIndex.value, windowCenter.value, windowWidth.value),
    appStore.getSliceBinary(appStore.selectedSeriesUid, 'sagittal', sagSliceIndex.value, windowCenter.value, windowWidth.value),
    appStore.getSliceBinary(appStore.selectedSeriesUid, 'coronal', corSliceIndex.value, windowCenter.value, windowWidth.value),
  ])

  axialData.value = ax?.data || null
  sagittalData.value = sag?.data || null
  coronalData.value = cor?.data || null

  // Load overlays for current slices
  await loadOverlaysForCurrentSlices()
}

async function loadOverlaysForCurrentSlices() {
  const loadPromises: Promise<void>[] = []

  // Load struct overlays
  for (const struct of structs.value) {
    if (!enabledStructOverlays.value.has(struct.key)) continue
    loadPromises.push(loadStructOverlay(struct.key))
  }

  // Load dose overlays
  for (const dose of doseList.value) {
    if (!enabledDoseOverlays.value.has(dose.file_id)) continue
    loadPromises.push(loadDoseOverlay(dose.file_id))
  }

  await Promise.all(loadPromises)
}

async function loadStructOverlay(structKey: string) {
  for (const orientation of ['axial', 'sagittal', 'coronal'] as const) {
    const sliceIdx = orientation === 'axial' ? sliceIndex.value
      : orientation === 'sagittal' ? sagSliceIndex.value
      : corSliceIndex.value
    const cacheKey = `${structKey}_${orientation}`
    if (structOverlayCache.value[cacheKey] !== undefined) continue
    try {
      const maskData = await appStore.getStructMask(structKey, sliceIdx, orientation)
      structOverlayCache.value[cacheKey] = maskData?.mask || null
    } catch {
      structOverlayCache.value[cacheKey] = null
    }
  }
}

async function loadDoseOverlay(doseFileId: string) {
  for (const orientation of ['axial', 'sagittal', 'coronal'] as const) {
    const sliceIdx = orientation === 'axial' ? sliceIndex.value
      : orientation === 'sagittal' ? sagSliceIndex.value
      : corSliceIndex.value
    const cacheKey = `${doseFileId}_${orientation}`
    if (doseOverlayCache.value[cacheKey] !== undefined) continue
    try {
      const doseData = await appStore.getDoseSlice(doseFileId, sliceIdx, orientation)
      doseOverlayCache.value[cacheKey] = doseData || null
    } catch {
      doseOverlayCache.value[cacheKey] = null
    }
  }
}

function toggleStructOverlay(structKey: string) {
  const newSet = new Set(enabledStructOverlays.value)
  if (newSet.has(structKey)) {
    newSet.delete(structKey)
  } else {
    newSet.add(structKey)
    // Load mask data when enabling
    loadStructOverlay(structKey)
  }
  enabledStructOverlays.value = newSet
}

function toggleDoseOverlay(doseFileId: string) {
  const newSet = new Set(enabledDoseOverlays.value)
  if (newSet.has(doseFileId)) {
    newSet.delete(doseFileId)
  } else {
    newSet.add(doseFileId)
    loadDoseOverlay(doseFileId)
  }
  enabledDoseOverlays.value = newSet
}

function onSliceChange(delta: number) {
  const next = sliceIndex.value + delta
  if (next >= 0 && next <= maxSlice.value) {
    sliceIndex.value = next
    loadAxialSlice()
  }
}

function onSagSliceChange(delta: number) {
  const next = sagSliceIndex.value + delta
  if (next >= 0 && next <= sagMaxSlice.value) {
    sagSliceIndex.value = next
    loadSagSlice()
  }
}

function onCorSliceChange(delta: number) {
  const next = corSliceIndex.value + delta
  if (next >= 0 && next <= corMaxSlice.value) {
    corSliceIndex.value = next
    loadCorSlice()
  }
}

async function loadAxialSlice() {
  if (!appStore.selectedSeriesUid) return
  const data = await appStore.getSliceBinary(appStore.selectedSeriesUid, 'axial', sliceIndex.value, windowCenter.value, windowWidth.value)
  axialData.value = data?.data || null
  // Reload overlays for new slice position
  if (enabledStructOverlays.value.size > 0 || enabledDoseOverlays.value.size > 0) {
    structOverlayCache.value = {}
    doseOverlayCache.value = {}
    await loadOverlaysForCurrentSlices()
  }
}

async function loadSagSlice() {
  if (!appStore.selectedSeriesUid) return
  const data = await appStore.getSliceBinary(appStore.selectedSeriesUid, 'sagittal', sagSliceIndex.value, windowCenter.value, windowWidth.value)
  sagittalData.value = data?.data || null
  if (enabledStructOverlays.value.size > 0 || enabledDoseOverlays.value.size > 0) {
    structOverlayCache.value = {}
    doseOverlayCache.value = {}
    await loadOverlaysForCurrentSlices()
  }
}

async function loadCorSlice() {
  if (!appStore.selectedSeriesUid) return
  const data = await appStore.getSliceBinary(appStore.selectedSeriesUid, 'coronal', corSliceIndex.value, windowCenter.value, windowWidth.value)
  coronalData.value = data?.data || null
  if (enabledStructOverlays.value.size > 0 || enabledDoseOverlays.value.size > 0) {
    structOverlayCache.value = {}
    doseOverlayCache.value = {}
    await loadOverlaysForCurrentSlices()
  }
}

function onWindowChange(center: number, width: number) {
  windowCenter.value = center
  windowWidth.value = width
  loadAllSlices()
}

function applyPreset(preset: { center: number; width: number }) {
  windowCenter.value = preset.center
  windowWidth.value = preset.width
  loadAllSlices()
}

// Crosshair handlers
function onAxialCrosshairMove(x: number, y: number) {
  if (!showCrosshairs.value) return
  crosshairAxial.value = { x, y }
  // Update other panes' crosshairs proportionally
  updateCrosshairsFromAxial(x, y)
  updateVoxelInfo('axial', x, y)
}

function onSagittalCrosshairMove(x: number, y: number) {
  if (!showCrosshairs.value) return
  crosshairSagittal.value = { x, y }
  updateVoxelInfo('sagittal', x, y)
}

function onCoronalCrosshairMove(x: number, y: number) {
  if (!showCrosshairs.value) return
  crosshairCoronal.value = { x, y }
  updateVoxelInfo('coronal', x, y)
}

function updateCrosshairsFromAxial(x: number, y: number) {
  // Map axial crosshair to sagittal/coronal panes
  // This is a simplified mapping - in a real viewer you'd use DICOM coordinates
  const axialCanvas = axialViewerRef.value?.canvas as HTMLCanvasElement | undefined
  const sagCanvas = sagittalViewerRef.value?.canvas as HTMLCanvasElement | undefined
  const corCanvas = coronalViewerRef.value?.canvas as HTMLCanvasElement | undefined

  if (sagCanvas) {
    const rect = sagCanvas.getBoundingClientRect()
    const axialRect = axialCanvas?.getBoundingClientRect()
    crosshairSagittal.value = { x: rect.width / 2, y: (x / (axialRect?.width || 1)) * rect.height }
  }
  if (corCanvas) {
    const rect = corCanvas.getBoundingClientRect()
    const axialRect = axialCanvas?.getBoundingClientRect()
    crosshairCoronal.value = { x: rect.width / 2, y: (y / (axialRect?.height || 1)) * rect.height }
  }
}

function updateVoxelInfo(pane: string, x: number, y: number) {
  let data: number[][] | null = null
  let label = ''
  let canvasEl: HTMLCanvasElement | undefined

  if (pane === 'axial') {
    data = axialData.value
    label = 'Axial'
    canvasEl = axialViewerRef.value?.canvas as HTMLCanvasElement | undefined
  } else if (pane === 'sagittal') {
    data = sagittalData.value
    label = 'Sagittal'
    canvasEl = sagittalViewerRef.value?.canvas as HTMLCanvasElement | undefined
  } else {
    data = coronalData.value
    label = 'Coronal'
    canvasEl = coronalViewerRef.value?.canvas as HTMLCanvasElement | undefined
  }

  if (!data || data.length === 0 || !canvasEl) return

  const rect = canvasEl.getBoundingClientRect()
  const scaleX = data[0]?.length || 1
  const scaleY = data.length

  const px = Math.floor((x / rect.width) * scaleX)
  const py = Math.floor((y / rect.height) * scaleY)

  if (px >= 0 && px < scaleX && py >= 0 && py < scaleY) {
    voxelInfo.value = { x: px, y: py, value: data[py][px], label }
  }
}

// Component refs for crosshair mapping
const axialViewerRef = ref<InstanceType<typeof ImageSliceViewer> | null>(null)
const sagittalViewerRef = ref<InstanceType<typeof ImageSliceViewer> | null>(null)
const coronalViewerRef = ref<InstanceType<typeof ImageSliceViewer> | null>(null)

function captureScreenshot() {
  const dataUrl = axialViewerRef.value?.captureScreenshot()
  if (!dataUrl) return
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = `slice_${appStore.selectedSeriesUid || 'unknown'}_${sliceIndex.value}.png`
  link.click()
}

function onPatientChange() {
  appStore.selectedSeriesUid = null
  axialData.value = null
  sagittalData.value = null
  coronalData.value = null
  seriesInfo.value = null
  structs.value = []
  doseList.value = []
  enabledStructOverlays.value.clear()
  enabledDoseOverlays.value.clear()
  structOverlayCache.value = {}
  doseOverlayCache.value = {}
}

function onSeriesSelect(uid: string) {
  appStore.selectSeries(uid)
}

// Rotation/flip
function rotateRight() {
  rotation.value = (rotation.value + 90) % 360
}

function rotateLeft() {
  rotation.value = (rotation.value - 90 + 360) % 360
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
