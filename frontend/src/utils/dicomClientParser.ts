import dicomParser from 'dicom-parser'

export interface ClientDicomMetadata {
  patientName: string
  patientId: string
  modality: string
  studyDescription: string
  seriesDescription: string
  studyDate: string
  seriesInstanceUID: string
  sopInstanceUID: string
  instanceNumber: number
}

export interface PatientPreview {
  name: string
  patientId: string
  studies: Map<string, StudyPreview>
}

export interface StudyPreview {
  description: string
  date: string
  series: Map<string, SeriesPreview>
}

export interface SeriesPreview {
  description: string
  modality: string
  fileCount: number
  seriesUID: string
}

export interface ParseResult {
  patients: Map<string, PatientPreview>
  totalFiles: number
  totalSize: number
  parsedCount: number
  failedCount: number
}

// WebWorker for background DICOM parsing (falls back to main thread)
let parseWorker: Worker | null = null
let workerReady = false

try {
  parseWorker = new Worker(new URL('../workers/dicom-parse.worker.ts', import.meta.url), { type: 'module' })
  workerReady = true
} catch {
  parseWorker = null
}

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

export async function parseDicomFile(file: File): Promise<ClientDicomMetadata | null> {
  try {
    const buffer = await file.arrayBuffer()
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
  } catch {
    return null
  }
}

export async function parseDicomFiles(files: File[]): Promise<ParseResult> {
  const patients = new Map<string, PatientPreview>()
  let totalSize = 0
  let parsedCount = 0
  let failedCount = 0

  // Use WebWorker for batch parsing if available
  if (workerReady && parseWorker && files.length > 5) {
    const BATCH_SIZE = 50
    for (let i = 0; i < files.length; i += BATCH_SIZE) {
      const batch = files.slice(i, i + BATCH_SIZE)
      const buffers = await Promise.all(batch.map(async f => ({
        name: f.name,
        buffer: await f.arrayBuffer(),
      })))

      const results = await new Promise<(ClientDicomMetadata | null)[]>((resolve, reject) => {
        const id = Date.now() + i
        const timeout = setTimeout(() => {
          parseWorker!.removeEventListener('message', handler)
          reject(new Error(`Worker batch ${id} timed out`))
        }, 30000)
        const handler = (e: MessageEvent) => {
          if (e.data.type === 'batch-parsed' && e.data.id === id) {
            clearTimeout(timeout)
            parseWorker!.removeEventListener('message', handler)
            resolve(e.data.results)
          }
        }
        parseWorker!.addEventListener('message', handler)
        parseWorker!.postMessage({ type: 'parse-batch', id, files: buffers })
      }).catch(() => [] as (ClientDicomMetadata | null)[])

      for (let j = 0; j < results.length; j++) {
        const meta = results[j]
        totalSize += batch[j].size
        if (!meta) { failedCount++; continue }
        parsedCount++
        addToPreview(patients, meta)
      }
    }
  } else {
    // Fallback: main thread parsing in batches
    const BATCH_SIZE = 20
    for (let i = 0; i < files.length; i += BATCH_SIZE) {
      const batch = files.slice(i, i + BATCH_SIZE)
      const results = await Promise.all(batch.map(f => parseDicomFile(f)))

      for (let j = 0; j < results.length; j++) {
        const meta = results[j]
        totalSize += batch[j].size
        if (!meta) { failedCount++; continue }
        parsedCount++
        addToPreview(patients, meta)
      }
    }
  }

  return {
    patients,
    totalFiles: files.length,
    totalSize,
    parsedCount,
    failedCount,
  }
}

function addToPreview(patients: Map<string, PatientPreview>, meta: ClientDicomMetadata) {
  const pid = meta.patientId || 'unknown'
  if (!patients.has(pid)) {
    patients.set(pid, {
      name: meta.patientName || 'Unknown',
      patientId: pid,
      studies: new Map(),
    })
  }
  const patient = patients.get(pid)!

  const studyKey = meta.studyDescription || 'Unknown Study'
  if (!patient.studies.has(studyKey)) {
    patient.studies.set(studyKey, {
      description: meta.studyDescription,
      date: meta.studyDate,
      series: new Map(),
    })
  }
  const study = patient.studies.get(studyKey)!

  const seriesKey = meta.seriesInstanceUID || meta.seriesDescription || 'unknown'
  if (!study.series.has(seriesKey)) {
    study.series.set(seriesKey, {
      description: meta.seriesDescription,
      modality: meta.modality,
      fileCount: 0,
      seriesUID: meta.seriesInstanceUID,
    })
  }
  study.series.get(seriesKey)!.fileCount++
}
