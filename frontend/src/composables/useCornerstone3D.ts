import { ref, onBeforeUnmount, shallowRef } from 'vue'
import {
  init,
  RenderingEngine,
  Enums,
  type Types,
} from '@cornerstonejs/core'
import { registerMdhVolumeLoader, buildVolumeId } from '@/utils/cornerstoneVolumeLoader'

let initialized = false
let renderingEngine: Types.IRenderingEngine | null = null

function ensureInit() {
  if (!initialized) {
    init()
    registerMdhVolumeLoader()
    initialized = true
  }
}

export function useCornerstone3D() {
  const isReady = ref(false)
  const engine = shallowRef<Types.IRenderingEngine | null>(null)

  function createEngine(engineId: string) {
    ensureInit()
    renderingEngine = new RenderingEngine(engineId)
    engine.value = renderingEngine
    isReady.value = true
    return renderingEngine
  }

  function enableViewport(
    viewportId: string,
    element: HTMLDivElement,
    type: Enums.ViewportType = Enums.ViewportType.ORTHOGRAPHIC
  ) {
    if (!renderingEngine) return
    renderingEngine.setViewports([
      {
        viewportId,
        element,
        type,
        defaultOptions: {
          background: [0, 0, 0] as Types.Point3,
        },
      },
    ])
  }

  async function loadVolume(
    viewportId: string,
    sessionId: string,
    patientId: string,
    seriesUid: string,
    options?: { voi?: { windowWidth: number; windowCenter: number } }
  ) {
    if (!renderingEngine) return
    const volumeId = buildVolumeId(sessionId, patientId, seriesUid)

    const viewport = renderingEngine.getViewport(viewportId)
    if (!viewport) return

    await (viewport as Types.IBaseVolumeViewport).setVolumes([
      {
        volumeId,
        callback: () => {
          if (options?.voi) {
            const ww = options.voi.windowWidth
            const wc = options.voi.windowCenter
            ;(viewport as Types.IBaseVolumeViewport).setProperties({
              voiRange: {
                upper: wc + ww / 2,
                lower: wc - ww / 2,
              },
            })
          }
        },
      },
    ])

    renderingEngine.render()
  }

  function setWindowLevel(viewportId: string, windowWidth: number, windowCenter: number) {
    if (!renderingEngine) return
    const viewport = renderingEngine.getViewport(viewportId)
    if (viewport) {
      ;(viewport as Types.IBaseVolumeViewport).setProperties({
        voiRange: {
          upper: windowCenter + windowWidth / 2,
          lower: windowCenter - windowWidth / 2,
        },
      })
      renderingEngine.render()
    }
  }

  function render() {
    renderingEngine?.render()
  }

  function destroy() {
    if (renderingEngine) {
      renderingEngine.destroy()
      renderingEngine = null
      engine.value = null
      isReady.value = false
    }
  }

  onBeforeUnmount(() => {
    destroy()
  })

  return {
    isReady,
    engine,
    createEngine,
    enableViewport,
    loadVolume,
    setWindowLevel,
    render,
    destroy,
  }
}
