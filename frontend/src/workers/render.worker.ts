/**
 * OffscreenCanvas render worker.
 * Receives raw pixel data, applies window/level normalization,
 * and returns an ImageBitmap for the main thread to draw.
 */

interface RenderMessage {
  type: 'render'
  pixelData: Float32Array | Int16Array | Uint8Array
  width: number
  height: number
  windowCenter: number
  windowWidth: number
  canvasWidth: number
  canvasHeight: number
}

interface ResizeMessage {
  type: 'resize'
  width: number
  height: number
}

type WorkerMessage = RenderMessage | ResizeMessage

let offscreen: OffscreenCanvas | null = null
let offCtx: OffscreenCanvasRenderingContext2D | null = null

self.onmessage = (e: MessageEvent<WorkerMessage>) => {
  const msg = e.data

  if (msg.type === 'resize') {
    offscreen = new OffscreenCanvas(msg.width, msg.height)
    offCtx = offscreen.getContext('2d') as OffscreenCanvasRenderingContext2D
    return
  }

  if (msg.type === 'render' && offscreen && offCtx) {
    const { pixelData, width, height, windowCenter, windowWidth, canvasWidth, canvasHeight } = msg

    offscreen.width = width
    offscreen.height = height

    const imageData = offCtx.createImageData(width, height)
    const pixels = imageData.data

    const lower = windowCenter - windowWidth / 2
    const upper = windowCenter + windowWidth / 2
    const range = upper - lower || 1

    for (let i = 0; i < width * height; i++) {
      const val = pixelData[i]
      let normalized = (val - lower) / range
      normalized = normalized < 0 ? 0 : normalized > 1 ? 1 : normalized
      const gray = (normalized * 255 + 0.5) | 0
      const idx = i * 4
      pixels[idx] = gray
      pixels[idx + 1] = gray
      pixels[idx + 2] = gray
      pixels[idx + 3] = 255
    }

    offCtx.putImageData(imageData, 0, 0)

    // Create ImageBitmap from the offscreen canvas
    const bitmap = offscreen.transferToImageBitmap()

    // Send back the bitmap along with dimensions for drawing
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const workerSelf = self as any
    workerSelf.postMessage({ type: 'rendered', bitmap, width, height, canvasWidth, canvasHeight }, [bitmap])
  }
}
