/**
 * DICOM parsing WebWorker.
 * Parses DICOM files off the main thread to avoid blocking the UI.
 * Receives ArrayBuffers, returns structured metadata.
 */

import dicomParser from 'dicom-parser'

interface ParseRequest {
  type: 'parse-batch'
  id: number
  files: { name: string; buffer: ArrayBuffer }[]
}

interface ParseSingleRequest {
  type: 'parse-single'
  id: number
  buffer: ArrayBuffer
}

type WorkerMessage = ParseRequest | ParseSingleRequest

function getTagString(dataSet: dicomParser.DataSet, tag: string): string {
  try {
    return dataSet.string(tag) || ''
  } catch {
    return ''
  }
}

function getTagFloat(dataSet: dicomParser.DataSet, tag: string): number {
  try {
    return dataSet.floatString(tag) || 0
  } catch {
    return 0
  }
}

function parseSingle(buffer: ArrayBuffer) {
  const byteArray = new Uint8Array(buffer)
  const dataSet = dicomParser.parseDicom(byteArray)

  return {
    patientName: getTagString(dataSet, 'x00100010'),
    patientId: getTagString(dataSet, 'x00100020'),
    modality: getTagString(dataSet, 'x00080060'),
    studyDescription: getTagString(dataSet, 'x00081030'),
    seriesDescription: getTagString(dataSet, 'x0008103e'),
    studyDate: getTagString(dataSet, 'x00080020'),
    seriesInstanceUID: getTagString(dataSet, 'x0020000e'),
    sopInstanceUID: getTagString(dataSet, 'x00080018'),
    instanceNumber: getTagFloat(dataSet, 'x00200013'),
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const workerSelf = self as any

workerSelf.onmessage = (e: MessageEvent<WorkerMessage>) => {
  const msg = e.data

  if (msg.type === 'parse-single') {
    try {
      const meta = parseSingle(msg.buffer)
      workerSelf.postMessage({ type: 'parsed', id: msg.id, result: meta })
    } catch {
      workerSelf.postMessage({ type: 'parsed', id: msg.id, result: null })
    }
    return
  }

  if (msg.type === 'parse-batch') {
    const results: (object | null)[] = []
    for (const file of msg.files) {
      try {
        results.push(parseSingle(file.buffer))
      } catch {
        results.push(null)
      }
    }
    workerSelf.postMessage({ type: 'batch-parsed', id: msg.id, results })
  }
}
