import { volumeLoader } from '@cornerstonejs/core'
import type { Types } from '@cornerstonejs/core'
import axios from 'axios'

const MDH_SCHEME = 'mdh://volume'

/**
 * Custom Cornerstone3D volume loader that fetches raw 3D volume from
 * /api/dicom/volume-binary and constructs a cornerstone ImageVolume.
 */
function mdhVolumeLoader(
  volumeId: string,
  _options?: Record<string, unknown>
): { promise: Promise<Types.IImageVolume>; cancelFn?: () => void; decache?: () => void } {
  const promise = (async () => {
    // volumeId format: mdh://volume/{sessionId}/{patientId}/{seriesUid}
    const parts = volumeId.replace(`${MDH_SCHEME}/`, '').split('/')
    const [sessionId, patientId, seriesUid] = parts

    const res = await axios.post(
      '/api/dicom/volume-binary',
      { session_id: sessionId, patient_id: patientId, series_uid: seriesUid },
      { responseType: 'arraybuffer' }
    )

    const headers = res.headers
    const shape: number[] = JSON.parse(headers['x-volume-shape'] || '[]')
    const spacing: number[] = JSON.parse(headers['x-volume-spacing'] || '[1,1,1]')
    const origin: number[] = JSON.parse(headers['x-volume-origin'] || '[0,0,0]')
    const dtype = headers['x-volume-dtype'] || 'int16'

    // Convert ArrayBuffer to typed array based on dtype
    let scalarData: Types.PixelDataTypedArray
    if (dtype === 'float64') {
      scalarData = new Float64Array(res.data)
    } else if (dtype === 'float32') {
      scalarData = new Float32Array(res.data)
    } else if (dtype === 'uint8') {
      scalarData = new Uint8Array(res.data)
    } else if (dtype === 'int16') {
      scalarData = new Int16Array(res.data)
    } else if (dtype === 'uint16') {
      scalarData = new Uint16Array(res.data)
    } else if (dtype === 'int32') {
      scalarData = new Int32Array(res.data)
    } else {
      scalarData = new Int16Array(res.data)
    }

    const [numSlices, rows, cols] = shape
    const dimensions: [number, number, number] = [cols, rows, numSlices]
    const direction: Types.Mat3 = [
      1, 0, 0,
      0, 1, 0,
      0, 0, 1,
    ]

    const imageVolume: Types.IImageVolume = {
      volumeId,
      dataType: undefined as unknown as Types.PixelDataTypedArray,
      dimensions,
      spacing: [spacing[2], spacing[1], spacing[0]] as Types.Point3,
      origin: origin as Types.Point3,
      direction,
      scalarData,
      metadata: {
        BitsAllocated: 16,
        BitsStored: 16,
        HighBit: 15,
        PixelRepresentation: 1,
        Rows: rows,
        Columns: cols,
        NumberOfFrames: numSlices,
        Modality: 'CT',
      },
      numFrames: numSlices,
      imageIds: [],
      type: 'VOLUME' as const,
      loadStatus: { loaded: false, loading: false, cachedFrames: new Set() },
    } as unknown as Types.IImageVolume

    return imageVolume
  })()

  return { promise }
}

export function registerMdhVolumeLoader(): void {
  volumeLoader.registerVolumeLoader(MDH_SCHEME, mdhVolumeLoader as unknown as Types.VolumeLoaderFn)
}

export function buildVolumeId(sessionId: string, patientId: string, seriesUid: string): string {
  return `${MDH_SCHEME}/${sessionId}/${patientId}/${seriesUid}`
}
