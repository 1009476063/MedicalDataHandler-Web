import { ref, watch, type Ref } from 'vue'

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

const defaults: Record<string, unknown> = {
  defaultWindow: 'auto',
  defaultOrientation: 'axial',
  scrollSensitivity: 1,
  structOpacity: 0.4,
  doseOpacity: 0.35,
  orientationLabelColor: '#00ff00',
  panSpeed: 1,
  wlSensitivity: 2,
  showOrientationLabels: true,
  showOverlayInfo: true,
  sidebarCollapsed: false,
  uploadConcurrency: 3,
  exportDtype: 'float32',
  exportUnit: 'native',
  defaultAnonProfile: 'research',
  contourThickness: 1,
  defaultTool: 'Length',
  playbackFps: 4,
  segmentOpacity: 0.4,
  recentPatientsCount: 5,
  analysisConfidenceThreshold: 0.5,
  dceMinFileCount: 10,
  defaultModality: 'auto',
  fourDPlaybackMode: 'loop',
  defaultSegmentPalette: 'vivid',
  defaultFusionOpacity: 0.5,
  defaultBlendMode: 'additive',
}

let _refs: Record<string, Ref> | null = null

function initRefs(): Record<string, Ref> {
  const keys = Object.keys(defaults)
  const refs: Record<string, Ref> = {}
  for (const key of keys) {
    refs[key] = ref(load(key, defaults[key]))
    watch(refs[key], (v) => save(key, v))
  }
  return refs
}

export function useSettings() {
  if (!_refs) {
    _refs = initRefs()
  }
  return _refs as {
    defaultWindow: Ref<string>
    defaultOrientation: Ref<string>
    scrollSensitivity: Ref<number>
    structOpacity: Ref<number>
    doseOpacity: Ref<number>
    orientationLabelColor: Ref<string>
    panSpeed: Ref<number>
    wlSensitivity: Ref<number>
    showOrientationLabels: Ref<boolean>
    showOverlayInfo: Ref<boolean>
    sidebarCollapsed: Ref<boolean>
    uploadConcurrency: Ref<number>
    exportDtype: Ref<string>
    exportUnit: Ref<string>
    defaultAnonProfile: Ref<string>
    contourThickness: Ref<number>
    defaultTool: Ref<string>
    playbackFps: Ref<number>
    segmentOpacity: Ref<number>
    recentPatientsCount: Ref<number>
    analysisConfidenceThreshold: Ref<number>
    dceMinFileCount: Ref<number>
    defaultModality: Ref<string>
    fourDPlaybackMode: Ref<string>
    defaultSegmentPalette: Ref<string>
    defaultFusionOpacity: Ref<number>
    defaultBlendMode: Ref<string>
  }
}
