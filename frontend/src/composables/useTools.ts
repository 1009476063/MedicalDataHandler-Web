import { ref, onBeforeUnmount } from 'vue'
import {
  addTool,
  ToolGroupManager,
  LengthTool,
  AngleTool,
  RectangleROITool,
  EllipticalROITool,
  ProbeTool,
  ArrowAnnotateTool,
  CrosshairsTool,
  annotation,
  Enums as ToolsEnums,
} from '@cornerstonejs/tools'

export type ToolName = 'Length' | 'Angle' | 'RectangleROI' | 'EllipticalROI' | 'Probe' | 'ArrowAnnotate' | 'Crosshairs'

interface MeasurementItem {
  uid: string
  toolName: string
  label: string
  stats: Record<string, unknown>
}

let toolsInitialized = false
const TOOL_GROUP_ID = 'mdh-measurement-tools'

function ensureToolsInit() {
  if (toolsInitialized) return
  addTool(LengthTool)
  addTool(AngleTool)
  addTool(RectangleROITool)
  addTool(EllipticalROITool)
  addTool(ProbeTool)
  addTool(ArrowAnnotateTool)
  addTool(CrosshairsTool)
  toolsInitialized = true
}

export function useTools() {
  const activeTool = ref<ToolName>('Length')
  const measurements = ref<MeasurementItem[]>([])
  let toolGroup: ReturnType<typeof ToolGroupManager.createToolGroup> | null = null

  function createToolGroup(engineId: string) {
    ensureToolsInit()

    // Destroy existing group if any
    if (toolGroup) {
      ToolGroupManager.destroyToolGroup(TOOL_GROUP_ID)
    }

    toolGroup = ToolGroupManager.createToolGroup(TOOL_GROUP_ID)
    if (!toolGroup) return null

    // Add all tools
    toolGroup.addTool(LengthTool.toolName)
    toolGroup.addTool(AngleTool.toolName)
    toolGroup.addTool(RectangleROITool.toolName)
    toolGroup.addTool(EllipticalROITool.toolName)
    toolGroup.addTool(ProbeTool.toolName)
    toolGroup.addTool(ArrowAnnotateTool.toolName)
    toolGroup.addTool(CrosshairsTool.toolName)

    // Enable crosshairs on all viewports
    toolGroup.setToolEnabled(CrosshairsTool.toolName)

    // Set Length as default active tool
    toolGroup.setToolActive(LengthTool.toolName, {
      bindings: [{ mouseButton: ToolsEnums.MouseBindings.Primary }],
    })

    return toolGroup
  }

  function addViewports(engineId: string, viewportIds: string[]) {
    if (!toolGroup) return
    for (const vpId of viewportIds) {
      toolGroup.addViewport(vpId, engineId)
    }
  }

  function setActive(toolName: ToolName) {
    if (!toolGroup) return

    // Set all tools passive first
    for (const name of ['Length', 'Angle', 'RectangleROI', 'EllipticalROI', 'Probe', 'ArrowAnnotate'] as ToolName[]) {
      toolGroup.setToolPassive(name, { removeAllBindings: true })
    }

    // Set selected tool active
    toolGroup.setToolActive(toolName, {
      bindings: [{ mouseButton: ToolsEnums.MouseBindings.Primary }],
    })

    activeTool.value = toolName
  }

  function refreshMeasurements(engineId: string) {
    if (!toolGroup) return
    const items: MeasurementItem[] = []

    const viewportIds = toolGroup.getViewportIds()
    const selector = viewportIds[0] || ''

    for (const toolName of ['Length', 'Angle', 'RectangleROI', 'EllipticalROI', 'Probe', 'ArrowAnnotate'] as ToolName[]) {
      const anns = annotation.state.getAnnotations(toolName, selector)
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

  function clearAll() {
    if (!toolGroup) return
    const viewportIds = toolGroup.getViewportIds()
    const selector = viewportIds[0] || ''

    for (const toolName of ['Length', 'Angle', 'RectangleROI', 'EllipticalROI', 'Probe', 'ArrowAnnotate'] as ToolName[]) {
      const anns = annotation.state.getAnnotations(toolName, selector)
      if (!anns) continue
      for (const ann of anns) {
        if (ann.annotationUID) {
          annotation.state.removeAnnotation(ann.annotationUID)
        }
      }
    }
    measurements.value = []
  }

  function destroy() {
    if (toolGroup) {
      ToolGroupManager.destroyToolGroup(TOOL_GROUP_ID)
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
