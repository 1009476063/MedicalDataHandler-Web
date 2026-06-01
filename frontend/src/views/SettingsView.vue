<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-accent-900 dark:text-white">{{ $t('settings.title') }}</h1>
        <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('settings.subtitle') }}</p>
      </div>
      <button
        class="flex items-center gap-2 px-4 py-2 bg-accent-100 dark:bg-accent-800 hover:bg-accent-200 dark:hover:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg text-sm font-medium transition-colors"
        @click="showChangelog = true"
      >
        <ClockIcon class="w-4 h-4" />
        {{ $t('settings.changelog') }}
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Appearance -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.appearance') }}</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.language') }}
            </label>
            <select
              v-model="currentLanguage"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              @change="changeLanguage"
            >
              <option value="en">English</option>
              <option value="zh-CN">简体中文</option>
            </select>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-accent-900 dark:text-white">{{ $t('settings.darkMode') }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t('settings.darkModeDesc') }}</p>
            </div>
            <button
              :class="[
                'relative w-11 h-6 rounded-full transition-colors',
                isDark ? 'bg-primary-500' : 'bg-accent-300 dark:bg-accent-600',
              ]"
              @click="toggleTheme"
            >
              <span
                :class="[
                  'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  isDark ? 'translate-x-5' : '',
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-accent-900 dark:text-white">{{ $t('settings.sidebarCollapsed') }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t('settings.sidebarCollapsedDesc') }}</p>
            </div>
            <button
              :class="[
                'relative w-11 h-6 rounded-full transition-colors',
                sidebarCollapsed ? 'bg-primary-500' : 'bg-accent-300 dark:bg-accent-600',
              ]"
              @click="sidebarCollapsed = !sidebarCollapsed"
            >
              <span
                :class="[
                  'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  sidebarCollapsed ? 'translate-x-5' : '',
                ]"
              />
            </button>
          </div>
        </div>
      </div>

      <!-- Viewer Defaults -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.viewerDefaults') }}</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.defaultWindowLevel') }}
            </label>
            <select
              v-model="defaultWindow"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="auto">{{ $t('settings.windowAuto') }}</option>
              <option value="ct">{{ $t('settings.windowCT') }}</option>
              <option value="mri">{{ $t('settings.windowMRI') }}</option>
              <option value="bone">{{ $t('settings.windowBone') }}</option>
              <option value="lung">{{ $t('settings.windowLung') }}</option>
              <option value="soft_tissue">{{ $t('settings.windowSoftTissue') }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.defaultOrientation') }}
            </label>
            <select
              v-model="defaultOrientation"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="axial">{{ $t('settings.axial') }}</option>
              <option value="sagittal">{{ $t('settings.sagittal') }}</option>
              <option value="coronal">{{ $t('settings.coronal') }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.sliceSensitivity') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="scrollSensitivity"
                type="range"
                :min="1"
                :max="5"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ scrollSensitivity }}</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.contourThickness') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="contourThickness"
                type="range"
                :min="0"
                :max="5"
                step="0.5"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ contourThickness }}</span>
            </div>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.contourThicknessDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.defaultTool') }}
            </label>
            <select
              v-model="defaultTool"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="Length">Length</option>
              <option value="Angle">Angle</option>
              <option value="Probe">Probe</option>
              <option value="RectangleROI">Rectangle ROI</option>
              <option value="EllipticalROI">Elliptical ROI</option>
            </select>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.defaultToolDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.playbackFps') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="playbackFps"
                type="range"
                :min="1"
                :max="30"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ playbackFps }} fps</span>
            </div>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.playbackFpsDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.fourDPlaybackMode') }}
            </label>
            <select
              v-model="fourDPlaybackMode"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="loop">{{ $t('settings.fourDLoop') }}</option>
              <option value="once">{{ $t('settings.fourDOnce') }}</option>
              <option value="pingPong">{{ $t('settings.fourDPingPong') }}</option>
            </select>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.fourDPlaybackModeDesc') }}</p>
          </div>
        </div>
      </div>

      <!-- Overlay Settings -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.overlayDefaults') }}</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.structOpacity') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="structOpacity"
                type="range"
                :min="0.05"
                :max="1"
                step="0.05"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ Math.round(structOpacity * 100) }}%</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.doseOpacity') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="doseOpacity"
                type="range"
                :min="0.05"
                :max="1"
                step="0.05"
                class="flex-1 h-1.5 accent-red-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ Math.round(doseOpacity * 100) }}%</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.segmentOpacity') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="segmentOpacity"
                type="range"
                :min="0.1"
                :max="1"
                step="0.05"
                class="flex-1 h-1.5 accent-purple-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-12 text-right">{{ Math.round(segmentOpacity * 100) }}%</span>
            </div>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.segmentOpacityDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.defaultSegmentPalette') }}
            </label>
            <select
              v-model="defaultSegmentPalette"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="vivid">{{ $t('settings.paletteVivid') }}</option>
              <option value="pastel">{{ $t('settings.palettePastel') }}</option>
              <option value="highContrast">{{ $t('settings.paletteHighContrast') }}</option>
            </select>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.defaultSegmentPaletteDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.orientationColor') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model="orientationLabelColor"
                type="color"
                class="w-8 h-8 rounded border-0 cursor-pointer"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400">{{ orientationLabelColor }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Interaction Settings -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.interaction') }}</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.panSpeed') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="panSpeed"
                type="range"
                :min="0.5"
                :max="3"
                step="0.25"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ panSpeed }}x</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.windowSensitivity') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="wlSensitivity"
                type="range"
                :min="0.5"
                :max="5"
                step="0.25"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ wlSensitivity }}x</span>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-accent-900 dark:text-white">{{ $t('settings.showOrientation') }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t('settings.showOrientationDesc') }}</p>
            </div>
            <button
              :class="[
                'relative w-11 h-6 rounded-full transition-colors',
                showOrientationLabels ? 'bg-primary-500' : 'bg-accent-300 dark:bg-accent-600',
              ]"
              @click="showOrientationLabels = !showOrientationLabels"
            >
              <span
                :class="[
                  'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  showOrientationLabels ? 'translate-x-5' : '',
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-accent-900 dark:text-white">{{ $t('settings.showOverlayInfo') }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t('settings.showOverlayInfoDesc') }}</p>
            </div>
            <button
              :class="[
                'relative w-11 h-6 rounded-full transition-colors',
                showOverlayInfo ? 'bg-primary-500' : 'bg-accent-300 dark:bg-accent-600',
              ]"
              @click="showOverlayInfo = !showOverlayInfo"
            >
              <span
                :class="[
                  'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                  showOverlayInfo ? 'translate-x-5' : '',
                ]"
              />
            </button>
          </div>
        </div>
      </div>

      <!-- Upload & Export -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.uploadExport') }}</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.uploadConcurrency') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="uploadConcurrency"
                type="range"
                :min="1"
                :max="8"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ uploadConcurrency }}</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.exportDtype') }}
            </label>
            <select
              v-model="exportDtype"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="float32">float32</option>
              <option value="float64">float64</option>
              <option value="int16">int16</option>
              <option value="int32">int32</option>
            </select>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.exportDtypeDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.exportUnit') }}
            </label>
            <select
              v-model="exportUnit"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="native">Native</option>
              <option value="hu">HU (Hounsfield Units)</option>
              <option value="red">RED (Relative Electron Density)</option>
              <option value="suv">SUV (Standardized Uptake Value)</option>
            </select>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.exportUnitDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.defaultAnonProfile') }}
            </label>
            <select
              v-model="defaultAnonProfile"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="research">Research</option>
              <option value="clinical">Clinical</option>
              <option value="education">Education</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Analysis & Detection -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.analysisSettings') }}</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.analysisConfidenceThreshold') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="analysisConfidenceThreshold"
                type="range"
                :min="0.3"
                :max="0.9"
                step="0.05"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-10 text-right">{{ analysisConfidenceThreshold }}</span>
            </div>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.analysisConfidenceThresholdDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.dceMinFileCount') }}
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="dceMinFileCount"
                type="range"
                :min="5"
                :max="50"
                step="5"
                class="flex-1 h-1.5 accent-primary-500"
              />
              <span class="text-xs text-accent-600 dark:text-accent-400 w-10 text-right">{{ dceMinFileCount }}</span>
            </div>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.dceMinFileCountDesc') }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.defaultModality') }}
            </label>
            <select
              v-model="defaultModality"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="auto">{{ $t('settings.autoDetect') || 'Auto-detect' }}</option>
              <option value="MR">MR</option>
              <option value="CT">CT</option>
              <option value="MG">MG</option>
              <option value="US">US</option>
              <option value="PT">PT</option>
            </select>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.defaultModalityDesc') }}</p>
          </div>
        </div>
      </div>

      <!-- Session -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.session') }}</h2>
        <p class="text-sm text-accent-600 dark:text-accent-400 mb-4">
          {{ $t('settings.sessionId') }}: <code class="px-1.5 py-0.5 bg-accent-100 dark:bg-accent-800 rounded text-xs">{{ appStore.sessionId || $t('settings.notStarted') }}</code>
        </p>
        <p class="text-sm text-accent-600 dark:text-accent-400 mb-4">
          {{ $t('settings.patientsLoaded') }}: <span class="font-medium text-accent-900 dark:text-white">{{ appStore.patients.length }}</span>
        </p>

        <div class="mb-4">
          <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
            {{ $t('settings.recentPatientsCount') }}
          </label>
          <div class="flex items-center gap-3">
            <input
              v-model.number="recentPatientsCount"
              type="range"
              :min="3"
              :max="20"
              class="flex-1 h-1.5 accent-primary-500"
            />
            <span class="text-xs text-accent-600 dark:text-accent-400 w-8 text-right">{{ recentPatientsCount }}</span>
          </div>
          <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">{{ $t('settings.recentPatientsCountDesc') }}</p>
        </div>
        <button
          class="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium transition-colors"
          @click="clearSession"
        >
          {{ $t('settings.clearSession') }}
        </button>
      </div>

      <!-- AI Configuration -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-1">{{ $t('settings.aiConfig') }}</h2>
        <p class="text-xs text-accent-500 dark:text-accent-400 mb-4">{{ $t('settings.aiConfigDesc') }}</p>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.aiApiBase') }}
            </label>
            <input
              v-model="aiApiBase"
              type="text"
              :placeholder="$t('settings.aiApiBaseDesc')"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.aiApiKey') }}
            </label>
            <input
              v-model="aiApiKey"
              type="password"
              :placeholder="$t('settings.aiApiKeyDesc')"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>

          <!-- Connection check + fetch models buttons -->
          <div class="flex items-center gap-2">
            <button
              :disabled="aiCheckStatus === 'checking'"
              class="flex items-center gap-1.5 px-3 py-1.5 bg-accent-100 dark:bg-accent-800 hover:bg-accent-200 dark:hover:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
              @click="checkConnection"
            >
              <template v-if="aiCheckStatus === 'checking'">
                <svg class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25" /><path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="3" stroke-linecap="round" /></svg>
                {{ $t('settings.aiChecking') }}
              </template>
              <template v-else>
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                {{ $t('settings.aiCheckConnection') }}
              </template>
            </button>

            <button
              :disabled="aiModelsLoading"
              class="flex items-center gap-1.5 px-3 py-1.5 bg-accent-100 dark:bg-accent-800 hover:bg-accent-200 dark:hover:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
              @click="fetchModels"
            >
              <template v-if="aiModelsLoading">
                <svg class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25" /><path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="3" stroke-linecap="round" /></svg>
                ...
              </template>
              <template v-else>
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                {{ $t('settings.aiFetchModels') }}
              </template>
            </button>

            <!-- Connection status indicator -->
            <span v-if="aiCheckStatus === 'ok'" class="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
              {{ aiCheckMessage }}
            </span>
            <span v-else-if="aiCheckStatus === 'error'" class="text-xs text-red-500 flex items-center gap-1">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>
              {{ aiCheckMessage }}
            </span>
          </div>

          <div class="relative">
            <label class="block text-sm font-medium text-accent-700 dark:text-accent-300 mb-1.5">
              {{ $t('settings.aiDefaultModel') }}
            </label>
            <div class="relative">
              <input
                v-model="aiDefaultModel"
                type="text"
                :placeholder="$t('settings.aiDefaultModelDesc')"
                class="w-full px-3 py-2 pr-8 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                @focus="aiModelDropdownOpen = true"
                @click="aiModelDropdownOpen = true"
              />
              <button
                v-if="aiModels.length > 0"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-accent-400 hover:text-accent-600 dark:hover:text-accent-200"
                @click="aiModelDropdownOpen = !aiModelDropdownOpen"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9" /></svg>
              </button>
            </div>
            <div
              v-if="aiModelDropdownOpen && aiModels.length > 0"
              class="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg shadow-lg"
            >
              <button
                v-for="m in aiModels"
                :key="m.id"
                class="w-full text-left px-3 py-2 text-sm text-accent-900 dark:text-white hover:bg-accent-100 dark:hover:bg-accent-700 transition-colors"
                :class="{ 'bg-primary-50 dark:bg-primary-900/30': aiDefaultModel === m.id }"
                @mousedown.prevent="aiDefaultModel = m.id; aiModelDropdownOpen = false"
              >
                <span class="font-medium">{{ m.id }}</span>
                <span v-if="m.name && m.name !== m.id" class="text-accent-400 ml-1">— {{ m.name }}</span>
              </button>
            </div>
            <p v-if="aiModels.length > 0" class="text-xs text-accent-400 mt-1">{{ $t('settings.aiModelsFetched', { count: aiModels.length }) }}</p>
          </div>

          <div class="flex items-center justify-between pt-2">
            <p v-if="aiConfigSaved" class="text-xs text-green-600 dark:text-green-400">{{ $t('settings.aiConfigSaved') }}</p>
            <p v-else-if="aiConfigError" class="text-xs text-red-500">{{ $t('settings.aiConfigFailed') }}</p>
            <button
              class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors ml-auto"
              @click="saveAiConfig"
            >
              {{ $t('settings.save') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Config Files -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.configFileSection') }}</h2>
        <p class="text-sm text-accent-600 dark:text-accent-400 mb-4">
          {{ $t('settings.configDesc') }}
        </p>

        <div class="space-y-3">
          <div class="flex items-center justify-between p-3 bg-accent-50 dark:bg-accent-800/50 rounded-lg">
            <div>
              <p class="text-sm font-medium text-accent-900 dark:text-white">{{ $t('settings.tg263Naming') }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t('settings.tg263Desc') }}</p>
            </div>
            <div class="flex items-center gap-2">
              <button
                class="px-3 py-1.5 text-xs font-medium bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
                @click="editConfig('tg263')"
              >
                {{ $t('settings.edit') }}
              </button>
              <button
                class="px-3 py-1.5 text-xs font-medium bg-accent-200 dark:bg-accent-700 hover:bg-accent-300 dark:hover:bg-accent-600 text-accent-700 dark:text-accent-300 rounded-lg transition-colors"
                @click="resetConfig('tg263')"
              >
                {{ $t('settings.reset') }}
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-3 bg-accent-50 dark:bg-accent-800/50 rounded-lg">
            <div>
              <p class="text-sm font-medium text-accent-900 dark:text-white">{{ $t('settings.organMatching') }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ $t('settings.organDesc') }}</p>
            </div>
            <div class="flex items-center gap-2">
              <button
                class="px-3 py-1.5 text-xs font-medium bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
                @click="editConfig('organ_matching')"
              >
                {{ $t('settings.edit') }}
              </button>
              <button
                class="px-3 py-1.5 text-xs font-medium bg-accent-200 dark:bg-accent-700 hover:bg-accent-300 dark:hover:bg-accent-600 text-accent-700 dark:text-accent-300 rounded-lg transition-colors"
                @click="resetConfig('organ_matching')"
              >
                {{ $t('settings.reset') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Config Editor Modal -->
      <Teleport to="body">
        <div v-if="editingConfig" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div class="bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col mx-4">
            <div class="flex items-center justify-between px-6 py-4 border-b border-accent-200 dark:border-accent-700">
              <h3 class="text-lg font-semibold text-accent-900 dark:text-white">
                {{ editingConfig === 'tg263' ? $t('settings.editTg263') : $t('settings.editOrgan') }}
              </h3>
              <button @click="editingConfig = null" class="text-accent-400 hover:text-accent-600">
                <XMarkIcon class="w-5 h-5" />
              </button>
            </div>
            <div class="flex-1 overflow-y-auto p-6">
              <p class="text-xs text-accent-500 dark:text-accent-400 mb-3">
                {{ $t('settings.editorHint') }}
              </p>
              <textarea
                v-model="configEditorContent"
                class="w-full h-96 px-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-xs font-mono text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50 resize-none"
                spellcheck="false"
              />
              <p v-if="configError" class="text-xs text-red-500 mt-2">{{ configError }}</p>
            </div>
            <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-accent-200 dark:border-accent-700">
              <button
                class="px-4 py-2 text-sm font-medium bg-accent-200 dark:bg-accent-700 hover:bg-accent-300 dark:hover:bg-accent-600 text-accent-700 dark:text-accent-300 rounded-lg transition-colors"
                @click="editingConfig = null"
              >
                {{ $t('settings.cancel') }}
              </button>
              <button
                class="px-4 py-2 text-sm font-medium bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
                @click="saveConfig"
              >
                {{ $t('settings.save') }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Changelog Modal -->
      <Teleport to="body">
        <div v-if="showChangelog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showChangelog = false">
          <div class="bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col mx-4">
            <div class="flex items-center justify-between px-6 py-4 border-b border-accent-200 dark:border-accent-700">
              <h3 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('settings.changelog') }}</h3>
              <button @click="showChangelog = false" class="text-accent-400 hover:text-accent-600">
                <XMarkIcon class="w-5 h-5" />
              </button>
            </div>
            <div class="flex-1 overflow-y-auto p-6 space-y-4">
              <div v-for="release in changelog" :key="release.version" class="border border-accent-200 dark:border-accent-700 rounded-lg overflow-hidden">
                <button
                  class="w-full flex items-center justify-between px-4 py-3 bg-accent-50 dark:bg-accent-800/50 hover:bg-accent-100 dark:hover:bg-accent-800 transition-colors text-left"
                  @click="toggleRelease(release.version)"
                >
                  <div class="flex items-center gap-3">
                    <span class="text-sm font-bold text-accent-900 dark:text-white">v{{ release.version }}</span>
                    <span class="text-xs text-accent-500 dark:text-accent-400">{{ release.date }}</span>
                  </div>
                  <ChevronDownIcon
                    :class="['w-4 h-4 text-accent-400 transition-transform', expandedVersions.has(release.version) ? 'rotate-180' : '']"
                  />
                </button>
                <div v-if="expandedVersions.has(release.version)" class="px-4 py-3 space-y-2">
                  <div v-for="(change, idx) in release.changes" :key="idx" class="flex items-start gap-2">
                    <span
                      :class="[
                        'inline-block px-1.5 py-0.5 rounded text-[10px] font-medium uppercase shrink-0 mt-0.5',
                        change.type === 'feature' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        change.type === 'fix' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                      ]"
                    >{{ change.type }}</span>
                    <span class="text-sm text-accent-700 dark:text-accent-300">{{ currentLocale === 'zh-CN' ? change.text_zh : change.text_en }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- DICOM Printers -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('print.settingsTitle') }}</h2>
          <button
            class="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
            @click="showAddPrinter = true"
          >
            <PlusIcon class="w-4 h-4" />
            {{ $t('print.addPrinter') }}
          </button>
        </div>

        <!-- Printer list -->
        <div v-if="print.printers.value.length === 0" class="text-sm text-accent-500 dark:text-accent-400 py-4 text-center">
          {{ $t('print.noPrinters') }}
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="p in print.printers.value"
            :key="p.id"
            class="flex items-center justify-between p-3 bg-accent-50 dark:bg-accent-800 rounded-lg"
          >
            <div>
              <p class="text-sm font-medium text-accent-900 dark:text-white">{{ p.name }}</p>
              <p class="text-xs text-accent-500 dark:text-accent-400">{{ p.ae_title }}@{{ p.host }}:{{ p.port }}</p>
            </div>
            <button
              class="p-1.5 text-accent-400 hover:text-red-500 transition-colors"
              @click="removePrinter(p.id)"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Add printer form -->
        <div v-if="showAddPrinter" class="mt-4 p-4 bg-accent-50 dark:bg-accent-800 rounded-lg space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <input
              v-model="newPrinter.name"
              :placeholder="$t('print.printerName')"
              class="px-3 py-2 text-sm bg-white dark:bg-accent-900 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white"
            />
            <input
              v-model="newPrinter.ae_title"
              :placeholder="$t('print.aeTitle')"
              class="px-3 py-2 text-sm bg-white dark:bg-accent-900 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white"
            />
            <input
              v-model="newPrinter.host"
              :placeholder="$t('print.host')"
              class="px-3 py-2 text-sm bg-white dark:bg-accent-900 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white"
            />
            <input
              v-model.number="newPrinter.port"
              :placeholder="$t('print.port')"
              type="number"
              class="px-3 py-2 text-sm bg-white dark:bg-accent-900 border border-accent-200 dark:border-accent-700 rounded-lg text-accent-900 dark:text-white"
            />
          </div>
          <div class="flex justify-end gap-2">
            <button
              class="px-3 py-1.5 text-sm text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-700 rounded-lg transition-colors"
              @click="showAddPrinter = false"
            >
              {{ $t('settings.cancel') }}
            </button>
            <button
              class="px-3 py-1.5 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50"
              :disabled="!newPrinter.name || !newPrinter.ae_title || !newPrinter.host"
              @click="addPrinter"
            >
              {{ $t('print.addPrinter') }}
            </button>
          </div>
        </div>
      </div>

      <!-- About -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.about') }}</h2>
        <div class="space-y-2 text-sm text-accent-600 dark:text-accent-400">
          <p class="text-base font-semibold text-accent-900 dark:text-white">MedVista v2.0.0</p>
          <p>{{ $t('settings.aboutDesc') }}</p>
          <a
            href="https://github.com/1009476063/MedVista"
            target="_blank"
            class="text-primary-500 hover:text-primary-600 transition-colors"
          >
            {{ $t('settings.viewGithub') }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useTheme } from '@/composables/useTheme'
import { useSettings } from '@/composables/useSettings'
import { usePrint } from '@/composables/usePrint'
import { XMarkIcon, ChevronDownIcon, ClockIcon, PlusIcon, TrashIcon } from '@heroicons/vue/24/outline'
import i18n from '@/i18n'
import changelogData from '@/data/changelog.json'

const appStore = useAppStore()
const { isDark, toggle: toggleTheme } = useTheme()
const { t } = useI18n()

const settings = useSettings()
const { defaultWindow, defaultOrientation, scrollSensitivity, structOpacity, doseOpacity, orientationLabelColor, panSpeed, wlSensitivity, showOrientationLabels, showOverlayInfo, sidebarCollapsed, uploadConcurrency, exportDtype, exportUnit, defaultAnonProfile, contourThickness, defaultTool, playbackFps, segmentOpacity, recentPatientsCount, analysisConfidenceThreshold, dceMinFileCount, defaultModality, fourDPlaybackMode, defaultSegmentPalette } = settings

const currentLanguage = ref(localStorage.getItem('mdh_language') || 'en')

function changeLanguage() {
  i18n.global.locale.value = currentLanguage.value as 'en' | 'zh-CN'
  localStorage.setItem('mdh_language', currentLanguage.value)
}

function clearSession() {
  appStore.sessionId = ''
  appStore.patients = []
  appStore.selectedPatientId = ''
  appStore.selectedSeriesUid = ''
}

// Config management
const editingConfig = ref<string | null>(null)
const configEditorContent = ref('')
const configError = ref('')

async function editConfig(name: string) {
  try {
    const res = await fetch(`/api/config/${name}`)
    const data = await res.json()
    editingConfig.value = name
    configEditorContent.value = JSON.stringify(data.rules || {}, null, 2)
    configError.value = ''
  } catch {
    configError.value = t('settings.loadConfigFailed')
  }
}

async function saveConfig() {
  if (!editingConfig.value) return
  try {
    const rules = JSON.parse(configEditorContent.value)
    const res = await fetch(`/api/config/${editingConfig.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rules }),
    })
    if (res.ok) {
      editingConfig.value = null
    } else {
      configError.value = t('settings.saveConfigFailed')
    }
  } catch {
    configError.value = t('settings.invalidJson')
  }
}

async function resetConfig(name: string) {
  try {
    await fetch(`/api/config/${name}/reset`, { method: 'POST' })
  } catch {
    // silently ignore
  }
}

// AI Config
interface AIModelItem { id: string; name: string; description: string; type: string }

const aiApiBase = ref('')
const aiApiKey = ref('')
const aiDefaultModel = ref('')
const aiConfigSaved = ref(false)
const aiConfigError = ref(false)
const aiCheckStatus = ref<'idle' | 'checking' | 'ok' | 'error'>('idle')
const aiCheckMessage = ref('')
const aiModels = ref<AIModelItem[]>([])
const aiModelsLoading = ref(false)
const aiModelDropdownOpen = ref(false)

async function loadAiConfig() {
  try {
    const res = await fetch('/api/ai/config')
    const data = await res.json()
    if (data.success && data.data) {
      aiApiBase.value = data.data.api_base || ''
      aiApiKey.value = data.data.api_key || ''
      aiDefaultModel.value = data.data.default_model || ''
    }
  } catch {
    // silently ignore
  }
}

async function saveAiConfig() {
  try {
    aiConfigSaved.value = false
    aiConfigError.value = false
    const res = await fetch('/api/ai/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_base: aiApiBase.value || null,
        api_key: aiApiKey.value || null,
        default_model: aiDefaultModel.value || null,
      }),
    })
    if (res.ok) {
      aiConfigSaved.value = true
      setTimeout(() => { aiConfigSaved.value = false }, 3000)
    } else {
      aiConfigError.value = true
    }
  } catch {
    aiConfigError.value = true
  }
}

async function checkConnection() {
  aiCheckStatus.value = 'checking'
  aiCheckMessage.value = ''

  try {
    const body = JSON.stringify({
      api_base: aiApiBase.value || null,
      api_key: aiApiKey.value || null,
    })
    const res = await fetch('/api/ai/check', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
    let data: any = null
    try { data = await res.json() } catch { /* not JSON */ }

    if (res.ok && data?.success && data?.data) {
      const d = data.data
      aiCheckStatus.value = 'ok'
      aiCheckMessage.value = `${d.latency_ms}ms · ${d.model_count} models`
    } else if (data?.error) {
      aiCheckStatus.value = 'error'
      aiCheckMessage.value = String(data.error).slice(0, 120)
    } else {
      aiCheckStatus.value = 'error'
      aiCheckMessage.value = `HTTP ${res.status} — ${data?.detail || '请求失败'}`
    }
  } catch (e: any) {
    aiCheckStatus.value = 'error'
    aiCheckMessage.value = e?.message || '网络请求失败'
  }
}

async function fetchModels() {
  aiModelsLoading.value = true
  try {
    const body = JSON.stringify({
      api_base: aiApiBase.value || null,
      api_key: aiApiKey.value || null,
    })
    const res = await fetch('/api/ai/models', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    })
    const data = await res.json()
    if (data.success && Array.isArray(data.data)) {
      aiModels.value = data.data
    }
  } catch {
    // silently ignore
  } finally {
    aiModelsLoading.value = false
  }
}

// Load AI config on mount
loadAiConfig()

// DICOM Printers
const print = usePrint()
const showAddPrinter = ref(false)
const newPrinter = ref({ name: '', ae_title: '', host: '', port: 104 })

async function addPrinter() {
  try {
    await print.addPrinter({
      ...newPrinter.value,
      film_size: '8X10',
      orientation: 'PORTRAIT',
      density: 15,
    })
    showAddPrinter.value = false
    newPrinter.value = { name: '', ae_title: '', host: '', port: 104 }
  } catch {
    // error handled by composable
  }
}

async function removePrinter(id: string) {
  await print.removePrinter(id)
}

onMounted(() => {
  print.fetchPrinters()
  document.addEventListener('click', handleModelDropdownClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleModelDropdownClickOutside)
})

function handleModelDropdownClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.relative')) {
    aiModelDropdownOpen.value = false
  }
}

// Changelog
const changelog = computed(() => changelogData as Array<{ version: string; date: string; changes: Array<{ type: string; text_zh: string; text_en: string }> }>)
const currentLocale = computed(() => i18n.global.locale.value)
const expandedVersions = ref<Set<string>>(new Set())
const showChangelog = ref(false)

function toggleRelease(version: string) {
  if (expandedVersions.value.has(version)) {
    expandedVersions.value.delete(version)
  } else {
    expandedVersions.value.add(version)
  }
  // trigger reactivity
  expandedVersions.value = new Set(expandedVersions.value)
}
</script>
