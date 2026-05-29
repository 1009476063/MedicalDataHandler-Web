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

  // Parse files in parallel batches of 20 for performance
  const BATCH_SIZE = 20
  for (let i = 0; i < files.length; i += BATCH_SIZE) {
    const batch = files.slice(i, i + BATCH_SIZE)
    const results = await Promise.all(batch.map(f => parseDicomFile(f)))

    for (let j = 0; j < results.length; j++) {
      const meta = results[j]
      const file = batch[j]
      totalSize += file.size

      if (!meta) {
        failedCount++
        continue
      }
      parsedCount++

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
  }

  return {
    patients,
    totalFiles: files.length,
    totalSize,
    parsedCount,
    failedCount,
  }
}
