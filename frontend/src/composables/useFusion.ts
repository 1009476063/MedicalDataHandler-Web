import { ref, shallowRef } from 'vue'
import type { Types } from '@cornerstonejs/core' // type-only: zero bundle cost
import { buildVolumeId } from '@/utils/cornerstoneVolumeLoader'
import type { PetCtPair, SuvInfo } from '@/types'
import axios from 'axios'

// Lazy-loaded Cornerstone3D core module — avoids pulling ~2MB into the ViewerView chunk
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let csCore: any = null
async function loadCsCore() {
  if (!csCore) {
    csCore = await import('@cornerstonejs/core')
  }
  return csCore
}

// Cornerstone3D v4.22 BlendModes enum doesn't include ADDITIVE/DEFAULT,
// but the runtime API supports them. Cast numeric values directly.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const BLEND_ADDITIVE = 6 as any // additive blend for PET overlay

// Cornerstone3D v4.22 types don't expose blendMode/opacity on VolumeViewportProperties,
// but the runtime API supports them on BaseVolumeViewport.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyProps = Record<string, any>

export function useFusion() {
  const fusionEnabled = ref(false)
  const ctSeriesUid = ref<string | null>(null)
  const ptSeriesUid = ref<string | null>(null)
  const fusionOpacity = ref(0.5)
  const blendMode = ref<'default' | 'additive'>('additive')
  const showSuv = ref(false)
  const suvInfo = shallowRef<SuvInfo | null>(null)
  const petCtPairs = ref<PetCtPair[]>([])
  const currentSessionId = ref<string>('')
  const currentPatientId = ref<string>('')

  async function findPetCtPairs(sessionId: string, patientId: string): Promise<PetCtPair[]> {
    try {
      const res = await axios.get(`/api/dicom/find-pt-series/${sessionId}/${patientId}`)
      const pairs = res.data?.data?.pairs || []
      petCtPairs.value = pairs
      return pairs
    } catch {
      petCtPairs.value = []
      return []
    }
  }

  async function fetchSuvInfo(sessionId: string, patientId: string, seriesUid: string): Promise<SuvInfo | null> {
    try {
      const res = await axios.get(`/api/dicom/suv-info/${sessionId}/${patientId}/${seriesUid}`)
      const info = res.data?.data || null
      suvInfo.value = info
      return info
    } catch {
      suvInfo.value = null
      return null
    }
  }

  async function enableFusion(
    renderingEngine: Types.IRenderingEngine | null,
    viewportIds: string[],
    sessionId: string,
    patientId: string,
    ctUid: string,
    ptUid: string,
  ) {
    if (!renderingEngine) return
    const core = await loadCsCore()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const blendDefault = core.Enums.BlendModes.COMPOSITE as any

    currentSessionId.value = sessionId
    currentPatientId.value = patientId
    ctSeriesUid.value = ctUid
    ptSeriesUid.value = ptUid
    fusionEnabled.value = true

    for (const viewportId of viewportIds) {
      const viewport = renderingEngine.getViewport(viewportId)
      if (!viewport) continue

      const ctVolumeId = buildVolumeId(sessionId, patientId, ctUid)
      const ptVolumeId = buildVolumeId(sessionId, patientId, ptUid)

      ;(viewport as Types.IBaseVolumeViewport).setVolumes([
        { volumeId: ctVolumeId },
        {
          volumeId: ptVolumeId,
          callback: () => {
            ;(viewport as Types.IBaseVolumeViewport).setProperties({
              blendMode: blendMode.value === 'additive'
                ? BLEND_ADDITIVE
                : blendDefault,
              opacity: fusionOpacity.value,
            } as AnyProps)
          },
        },
      ])
    }
    renderingEngine.render()
  }

  function setFusionOpacity(
    renderingEngine: Types.IRenderingEngine | null,
    viewportIds: string[],
    opacity: number,
  ) {
    if (!renderingEngine) return
    fusionOpacity.value = opacity

    for (const viewportId of viewportIds) {
      const viewport = renderingEngine.getViewport(viewportId)
      if (!viewport) continue
      ;(viewport as Types.IBaseVolumeViewport).setProperties({ opacity } as AnyProps)
    }
    renderingEngine.render()
  }

  async function setBlendMode(
    renderingEngine: Types.IRenderingEngine | null,
    viewportIds: string[],
    mode: 'default' | 'additive',
  ) {
    if (!renderingEngine) return
    const core = await loadCsCore()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const blendDefault = core.Enums.BlendModes.COMPOSITE as any
    blendMode.value = mode

    for (const viewportId of viewportIds) {
      const viewport = renderingEngine.getViewport(viewportId)
      if (!viewport) continue
      ;(viewport as Types.IBaseVolumeViewport).setProperties({
        blendMode: mode === 'additive'
          ? BLEND_ADDITIVE
          : blendDefault,
      } as AnyProps)
    }
    renderingEngine.render()
  }

  async function disableFusion(
    renderingEngine: Types.IRenderingEngine | null,
    viewportIds: string[],
  ) {
    if (!renderingEngine) return
    const core = await loadCsCore()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const blendDefault = core.Enums.BlendModes.COMPOSITE as any
    fusionEnabled.value = false
    ctSeriesUid.value = null
    ptSeriesUid.value = null
    suvInfo.value = null

    // Reload just the CT volume (remove PT overlay)
    for (const viewportId of viewportIds) {
      const viewport = renderingEngine.getViewport(viewportId)
      if (!viewport) continue
      ;(viewport as Types.IBaseVolumeViewport).setProperties({
        blendMode: blendDefault,
        opacity: 1.0,
      } as AnyProps)
    }
    renderingEngine.render()
  }

  return {
    fusionEnabled,
    ctSeriesUid,
    ptSeriesUid,
    fusionOpacity,
    blendMode,
    showSuv,
    suvInfo,
    petCtPairs,
    currentSessionId,
    currentPatientId,
    findPetCtPairs,
    fetchSuvInfo,
    enableFusion,
    setFusionOpacity,
    setBlendMode,
    disableFusion,
  }
}
