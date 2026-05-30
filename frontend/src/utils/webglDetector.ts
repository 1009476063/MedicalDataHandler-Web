export interface WebGLCapability {
  webgl2: boolean
  webgl1: boolean
  renderer: string
  vendor: string
  maxTextureSize: number
  maxViewportDims: number
}

export interface BrowserRecommendation {
  browser: string
  reason: string
  url: string
}

const BROWSER_RECOMMENDATIONS: BrowserRecommendation[] = [
  { browser: 'Google Chrome', reason: '最佳 WebGL2 和 GPU 加速支持，Cornerstone3D 官方推荐', url: 'https://www.google.com/chrome/' },
  { browser: 'Microsoft Edge', reason: '基于 Chromium，同样支持 WebGL2 和硬件加速', url: 'https://www.microsoft.com/edge' },
  { browser: 'Mozilla Firefox', reason: '独立 WebGL 实现，支持 WebGPU，兼容性良好', url: 'https://www.mozilla.org/firefox/' },
]

export function detectWebGL(): WebGLCapability {
  const canvas = document.createElement('canvas')
  const gl2 = canvas.getContext('webgl2')
  const gl1 = !gl2 ? canvas.getContext('webgl') : null

  const result: WebGLCapability = {
    webgl2: !!gl2,
    webgl1: !!gl1 || !!gl2,
    renderer: '',
    vendor: '',
    maxTextureSize: 0,
    maxViewportDims: 0,
  }

  const gl = gl2 || gl1
  if (gl) {
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
    if (debugInfo) {
      result.renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
      result.vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
    }
    result.maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE)
    const dims = gl.getParameter(gl.MAX_VIEWPORT_DIMS)
    result.maxViewportDims = Array.isArray(dims) ? dims[0] : dims
    const loseCtx = gl.getExtension('WEBGL_lose_context')
    loseCtx?.loseContext()
  }

  return result
}

export function getBrowserRecommendations(): BrowserRecommendation[] {
  return BROWSER_RECOMMENDATIONS
}
