<template>
  <div class="space-y-6 animate-fade-in">
    <div>
      <h1 class="text-2xl font-bold text-accent-900 dark:text-white">{{ $t('settings.title') }}</h1>
      <p class="text-sm text-accent-500 dark:text-accent-400">{{ $t('settings.subtitle') }}</p>
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
              {{ $t('settings.defaultExportFormat') }}
            </label>
            <select
              v-model="defaultExportFormat"
              class="w-full px-3 py-2 bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="ct">{{ $t('export.formatCT') }}</option>
              <option value="red">{{ $t('export.formatRED') }}</option>
            </select>
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

      <!-- Session -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.session') }}</h2>
        <p class="text-sm text-accent-600 dark:text-accent-400 mb-4">
          {{ $t('settings.sessionId') }}: <code class="px-1.5 py-0.5 bg-accent-100 dark:bg-accent-800 rounded text-xs">{{ appStore.sessionId || $t('settings.notStarted') }}</code>
        </p>
        <p class="text-sm text-accent-600 dark:text-accent-400 mb-4">
          {{ $t('settings.patientsLoaded') }}: <span class="font-medium text-accent-900 dark:text-white">{{ appStore.patients.length }}</span>
        </p>
        <button
          class="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium transition-colors"
          @click="clearSession"
        >
          {{ $t('settings.clearSession') }}
        </button>
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

      <!-- About -->
      <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card">
        <h2 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">{{ $t('settings.about') }}</h2>
        <div class="space-y-2 text-sm text-accent-600 dark:text-accent-400">
          <p>{{ $t('settings.aboutTitle') }}</p>
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
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useTheme } from '@/composables/useTheme'
import { useSettings } from '@/composables/useSettings'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import i18n from '@/i18n'

const appStore = useAppStore()
const { isDark, toggle: toggleTheme } = useTheme()
const { t } = useI18n()

const settings = useSettings()
const { defaultWindow, defaultOrientation, scrollSensitivity, structOpacity, doseOpacity, orientationLabelColor, panSpeed, wlSensitivity, showOrientationLabels, showOverlayInfo, sidebarCollapsed, uploadConcurrency, defaultExportFormat, defaultAnonProfile } = settings

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
</script>
