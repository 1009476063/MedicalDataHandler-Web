import { ref, onBeforeUnmount } from 'vue'

// Lazy-loaded Cornerstone3D tools module — avoids pulling ~897KB into the ViewerView chunk
let csTools: typeof import('@cornerstonejs/tools') | null = null

async function loadCsTools(): Promise<typeof import('@cornerstonejs/tools')> {
  if (!csTools) {
    csTools = await import('@cornerstonejs/tools')
  }
  return csTools
}

export type ToolName = 'Length' | 'Angle' | 'RectangleROI' | 'EllipticalROI' | 'Probe' | 'ArrowAnnotate' | 'Crosshairs'

interface MeasurementItem {
  uid: string
  toolName: string
  label: string
  stats: Record<string, unknown>
}

const TOOL_GROUP_ID = 'mdh-measurement-tools'
const ALL_TOOLS = ['Length', 'Angle', 'RectangleROI', 'EllipticalROI', 'Probe', 'ArrowAnnotate'] as const

export function useTools() {
  const activeTool = ref<ToolName>('Length')
  const measurements = ref<MeasurementItem[]>([])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let toolGroup: any = null

  async function createToolGroup(engineId: string) {
    const tools = await loadCsTools()
    const { addTool, ToolGroupManager, LengthTool, AngleTool, RectangleROITool, EllipticalROITool, ProbeTool, ArrowAnnotateTool, CrosshairsTool, Enums } = tools

    // Destroy existing group if any
    if (toolGroup) {
      ToolGroupManager.destroyToolGroup(TOOL_GROUP_ID)
    }

    // Register all tools (idempotent — Cornerstone3D skips already-registered tools)
    for (const Tool of [LengthTool, AngleTool, RectangleROITool, EllipticalROITool, ProbeTool, ArrowAnnotateTool, CrosshairsTool]) {
      addTool(Tool)
    }

    toolGroup = ToolGroupManager.createToolGroup(TOOL_GROUP_ID)
    if (!toolGroup) return null

    // Add all tools
    for (const Tool of [LengthTool, AngleTool, RectangleROITool, EllipticalROITool, ProbeTool, ArrowAnnotateTool, CrosshairsTool]) {
      toolGroup.addTool(Tool.toolName)
    }

    // Enable crosshairs on all viewports
    toolGroup.setToolEnabled(CrosshairsTool.toolName)

    // Set Length as default active tool
    toolGroup.setToolActive(LengthTool.toolName, {
      bindings: [{ mouseButton: Enums.MouseBindings.Primary }],
    })

    return toolGroup
  }

  function addViewports(engineId: string, viewportIds: string[]) {
    if (!toolGroup) return
    for (const vpId of viewportIds) {
      toolGroup.addViewport(vpId, engineId)
    }
  }

  async function setActive(toolName: ToolName) {
    if (!toolGroup) return
    const tools = await loadCsTools()

    // Set all tools passive first
    for (const name of ALL_TOOLS) {
      toolGroup.setToolPassive(name, { removeAllBindings: true })
    }

    // Set selected tool active
    toolGroup.setToolActive(toolName, {
      bindings: [{ mouseButton: tools.Enums.MouseBindings.Primary }],
    })

    activeTool.value = toolName
  }

  async function refreshMeasurements(_engineId: string) {
    if (!toolGroup) return
    const tools = await loadCsTools()
    const items: MeasurementItem[] = []

    const viewportIds = toolGroup.getViewportIds()
    const selector = viewportIds[0] || ''

    for (const toolName of ALL_TOOLS) {
      const anns = tools.annotation.state.getAnnotations(toolName, selector)
      if (!anns) continue
      for (const ann of anns) {
        if (!ann.annotationUID) continue
        items.push({
          uid: ann.annotationUID,
          toolName,
          label: (ann.data?.label as string) || '',
          stats: (ann.data?.cachedStats as Record<string, unknown>) || {},
        })
      }
    }

    measurements.value = items
  }

  async function clearAll() {
    if (!toolGroup) return
    const tools = await loadCsTools()
    const viewportIds = toolGroup.getViewportIds()
    const selector = viewportIds[0] || ''

    for (const toolName of ALL_TOOLS) {
      const anns = tools.annotation.state.getAnnotations(toolName, selector)
      if (!anns) continue
      for (const ann of anns) {
        if (ann.annotationUID) {
          tools.annotation.state.removeAnnotation(ann.annotationUID)
        }
      }
    }
    measurements.value = []
  }

  function destroy() {
    if (toolGroup) {
      // Use cached module if available, otherwise skip (module may not be loaded yet)
      csTools?.ToolGroupManager?.destroyToolGroup(TOOL_GROUP_ID)
      toolGroup = null
    }
    measurements.value = []
  }

  onBeforeUnmount(() => {
    destroy()
  })

  return {
    activeTool,
    measurements,
    createToolGroup,
    addViewports,
    setActive,
    refreshMeasurements,
    clearAll,
    destroy,
  }
}
