/**
 * Client-side DICOM loader — parses DICOM files in the browser without a backend.
 * Uses dicom-parser and registers Cornerstone3D image loaders.
 */
import dicomParser from 'dicom-parser'
import {
  imageLoader,
  Enums,
  type Types,
} from '@cornerstonejs/core'

let registered = false

/** Register Cornerstone3D image loaders for client-side DICOM parsing. */
export function registerClientLoaders() {
  if (registered) return
  registered = true

  // Register a custom image loader for DICOM files loaded via dicom-parser
  imageLoader.registerImageLoader('mdh-client-dcm', loadClientDicomImage)
}

function loadClientDicomImage(
  imageId: string,
): { promise: Promise<Types.IImage> } {
  const promise = (async (): Promise<Types.IImage> => {
    // imageId format: mdh-client-dcm:<arrayBufferIndex>
    const bufferIndex = parseInt(imageId.split(':')[1], 10)
    const buffer = clientDicomBuffers.get(bufferIndex)
    if (!buffer) {
      throw new Error(`No DICOM buffer found for index ${bufferIndex}`)
    }

    const dataSet = dicomParser.parseDicom(new Uint8Array(buffer))

    const rows = dataSet.uint16('x00280010') || 0
    const cols = dataSet.uint16('x00280011') || 0
    const bitsAllocated = dataSet.uint16('x00280100') || 16
    const pixelRepresentation = dataSet.uint16('x00280103') || 0
    const pixelDataElement = dataSet.elements.x7FE00010

    if (!pixelDataElement) {
      throw new Error('No pixel data found in DICOM file')
    }

    const pixelData = dataSet.byteArray.slice(
      pixelDataElement.dataOffset,
      pixelDataElement.dataOffset + pixelDataElement.length,
    )

    let floatData: Float32Array
    if (bitsAllocated === 16) {
      const intData = new Int16Array(pixelData.buffer, pixelData.byteOffset, rows * cols)
      floatData = new Float32Array(intData.length)
      for (let i = 0; i < intData.length; i++) {
        floatData[i] = intData[i]
      }
    } else if (bitsAllocated === 8) {
      floatData = new Float32Array(rows * cols)
      for (let i = 0; i < rows * cols; i++) {
        floatData[i] = pixelData[i]
      }
    } else {
      const intData = new Int32Array(pixelData.buffer, pixelData.byteOffset, rows * cols)
      floatData = new Float32Array(intData.length)
      for (let i = 0; i < intData.length; i++) {
        floatData[i] = intData[i]
      }
    }

    const windowCenter = dataSet.floatString('x00281050') ?? 0
    const windowWidth = dataSet.floatString('x00281051') ?? 0
    const rescaleSlope = dataSet.floatString('x00281053') ?? 1
    const rescaleIntercept = dataSet.floatString('x00281052') ?? 0

    if (rescaleSlope !== 1 || rescaleIntercept !== 0) {
      for (let i = 0; i < floatData.length; i++) {
        floatData[i] = floatData[i] * rescaleSlope + rescaleIntercept
      }
    }

    const photometric = dataSet.string('x00280004') ?? 'MONOCHROME2'
    const invert = photometric === 'MONOCHROME1'
    const pixelSpacing = [
      dataSet.floatString('x00280030') ?? 1,
      dataSet.floatString('x00280030', 1) ?? 1,
    ]

    const image: Types.IImage = {
      imageId,
      getPixelData: () => new Float32Array(floatData.buffer),
      getCanvas: () => {
        const canvas = document.createElement('canvas')
        canvas.width = cols
        canvas.height = rows
        const ctx = canvas.getContext('2d')!
        const imgData = ctx.createImageData(cols, rows)
        const pixelArr = new Float32Array(floatData.buffer)
        const min = pixelRepresentation === 0 ? -32768 : 0
        const max = pixelRepresentation === 0 ? 32767 : 65535
        const range = max - min || 1
        for (let i = 0; i < pixelArr.length; i++) {
          const val = Math.round(((pixelArr[i] - min) / range) * 255)
          imgData.data[i * 4] = val
          imgData.data[i * 4 + 1] = val
          imgData.data[i * 4 + 2] = val
          imgData.data[i * 4 + 3] = 255
        }
        ctx.putImageData(imgData, 0, 0)
        return canvas
      },
      rows,
      columns: cols,
      height: rows,
      width: cols,
      color: false,
      rgba: false,
      invert,
      windowCenter,
      windowWidth,
      minPixelValue: pixelRepresentation === 0 ? -32768 : 0,
      maxPixelValue: pixelRepresentation === 0 ? 32767 : 65535,
      slope: rescaleSlope,
      intercept: rescaleIntercept,
      sizeInBytes: floatData.byteLength,
      dataType: 'Float32Array' as Types.PixelDataTypedArrayString,
      voiLUTFunction: Enums.VOILUTFunctionType.LINEAR,
      numberOfComponents: 1,
      rowPixelSpacing: pixelSpacing[0],
      columnPixelSpacing: pixelSpacing[1],
      calibration: undefined as unknown as Types.IImageCalibration,
    }

    return image
  })()

  return { promise }
}

// Store DICOMArrayBuffers keyed by index for loader lookup
const clientDicomBuffers: Map<number, ArrayBuffer> = new Map()
let nextBufferIndex = 0

/** Store a DICOM ArrayBuffer and return its imageId. */
export function storeDicomBuffer(buffer: ArrayBuffer): string {
  const idx = nextBufferIndex++
  clientDicomBuffers.set(idx, buffer)
  return `mdh-client-dcm:${idx}`
}

/** Clear all stored buffers. */
export function clearDicomBuffers() {
  clientDicomBuffers.clear()
  nextBufferIndex = 0
}

/** Get metadata from a DICOM ArrayBuffer. */
export function parseDicomMetadata(buffer: ArrayBuffer): Record<string, unknown> {
  const ds = dicomParser.parseDicom(new Uint8Array(buffer))
  return {
    patientId: ds.string('x00100020') ?? '',
    patientName: ds.string('x00100010') ?? '',
    studyDescription: ds.string('x00081030') ?? '',
    seriesDescription: ds.string('x0008103e') ?? '',
    modality: ds.string('x00080060') ?? '',
    studyInstanceUID: ds.string('x0020000d') ?? '',
    seriesInstanceUID: ds.string('x0020000e') ?? '',
    instanceNumber: ds.intString('x00200013') ?? 0,
    sliceLocation: ds.floatString('x00201041') ?? 0,
    imagePositionPatient: [
      ds.floatString('x00200032') ?? 0,
      ds.floatString('x00200032', 1) ?? 0,
      ds.floatString('x00200032', 2) ?? 0,
    ],
    pixelSpacing: [
      ds.floatString('x00280030') ?? 1,
      ds.floatString('x00280030', 1) ?? 1,
    ],
    rows: ds.uint16('x00280010') ?? 0,
    columns: ds.uint16('x00280011') ?? 0,
    bitsAllocated: ds.uint16('x00280100') ?? 16,
    windowCenter: ds.floatString('x00281050') ?? 0,
    windowWidth: ds.floatString('x00281051') ?? 0,
    rescaleSlope: ds.floatString('x00281053') ?? 1,
    rescaleIntercept: ds.floatString('x00281052') ?? 0,
  }
}
