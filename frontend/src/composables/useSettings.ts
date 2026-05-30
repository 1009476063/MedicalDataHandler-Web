import { ref, watch } from 'vue'

const PREFIX = 'mdh_'

function load<T>(key: string, defaultValue: T): T {
  try {
    const stored = localStorage.getItem(`${PREFIX}${key}`)
    return stored !== null ? JSON.parse(stored) : defaultValue
  } catch {
    return defaultValue
  }
}

function save(key: string, value: unknown) {
  localStorage.setItem(`${PREFIX}${key}`, JSON.stringify(value))
}

const defaultWindow = ref(load('defaultWindow', 'auto'))
const defaultOrientation = ref(load('defaultOrientation', 'axial'))
const scrollSensitivity = ref(load('scrollSensitivity', 1))
const structOpacity = ref(load('structOpacity', 0.4))
const doseOpacity = ref(load('doseOpacity', 0.35))
const orientationLabelColor = ref(load('orientationLabelColor', '#00ff00'))
const panSpeed = ref(load('panSpeed', 1))
const wlSensitivity = ref(load('wlSensitivity', 2))
const showOrientationLabels = ref(load('showOrientationLabels', true))
const showOverlayInfo = ref(load('showOverlayInfo', true))
const sidebarCollapsed = ref(load('sidebarCollapsed', false))
const uploadConcurrency = ref(load('uploadConcurrency', 3))
const defaultExportFormat = ref(load('defaultExportFormat', 'ct'))
const defaultAnonProfile = ref(load('defaultAnonProfile', 'research'))

const allRefs = {
  defaultWindow,
  defaultOrientation,
  scrollSensitivity,
  structOpacity,
  doseOpacity,
  orientationLabelColor,
  panSpeed,
  wlSensitivity,
  showOrientationLabels,
  showOverlayInfo,
  sidebarCollapsed,
  uploadConcurrency,
  defaultExportFormat,
  defaultAnonProfile,
}

Object.entries(allRefs).forEach(([key, r]) => {
  watch(r, (v) => save(key, v))
})

export function useSettings() {
  return allRefs
}
