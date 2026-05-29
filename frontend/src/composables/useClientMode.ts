import { ref } from 'vue'
import {
  registerClientLoaders,
  storeDicomBuffer,
  parseDicomMetadata,
  clearDicomBuffers,
} from '@/utils/clientDicomLoader'

const isClientMode = ref(false)
const backendAvailable = ref(true)
const clientFiles = ref<Array<{
  id: string
  buffer: ArrayBuffer
  metadata: Record<string, unknown>
}>>([])

/** Check if the backend server is reachable. */
export async function checkBackend(): Promise<boolean> {
  try {
    const res = await fetch('/api/health', { signal: AbortSignal.timeout(3000) })
    backendAvailable.value = res.ok
  } catch {
    backendAvailable.value = false
  }
  return backendAvailable.value
}

/** Enable client-only mode. */
export function enableClientMode() {
  registerClientLoaders()
  isClientMode.value = true
}

/** Disable client-only mode and clear buffers. */
export function disableClientMode() {
  isClientMode.value = false
  clientFiles.value = []
  clearDicomBuffers()
}

/** Load DICOM files in client mode. Returns parsed metadata. */
export async function loadClientFiles(files: File[]) {
  registerClientLoaders()
  isClientMode.value = true

  const results: Array<{
    id: string
    buffer: ArrayBuffer
    metadata: Record<string, unknown>
  }> = []

  for (const file of files) {
    const buffer = await file.arrayBuffer()
    const metadata = parseDicomMetadata(buffer)
    const imageId = storeDicomBuffer(buffer)
    results.push({
      id: imageId,
      buffer,
      metadata,
    })
  }

  clientFiles.value = [...clientFiles.value, ...results]
  return results
}

/** Get unique patients from client files. */
export function getClientPatients() {
  const patientMap = new Map<string, {
    patientId: string
    patientName: string
    studies: Map<string, {
      studyUid: string
      description: string
      series: Map<string, {
        seriesUid: string
        description: string
        modality: string
        files: Array<{ id: string; metadata: Record<string, unknown> }>
      }>
    }>
  }>()

  for (const file of clientFiles.value) {
    const meta = file.metadata as Record<string, string>
    const pid = meta.patientId || 'unknown'
    const pName = meta.patientName || 'Unknown'
    const studyUid = meta.studyInstanceUID || 'unknown'
    const studyDesc = meta.studyDescription || ''
    const seriesUid = meta.seriesInstanceUID || 'unknown'
    const seriesDesc = meta.seriesDescription || ''
    const modality = meta.modality || 'OT'

    if (!patientMap.has(pid)) {
      patientMap.set(pid, {
        patientId: pid,
        patientName: pName,
        studies: new Map(),
      })
    }
    const patient = patientMap.get(pid)!

    if (!patient.studies.has(studyUid)) {
      patient.studies.set(studyUid, {
        studyUid,
        description: studyDesc,
        series: new Map(),
      })
    }
    const study = patient.studies.get(studyUid)!

    if (!study.series.has(seriesUid)) {
      study.series.set(seriesUid, {
        seriesUid,
        description: seriesDesc,
        modality,
        files: [],
      })
    }
    study.series.get(seriesUid)!.files.push({ id: file.id, metadata: file.metadata })
  }

  return Array.from(patientMap.values())
}

export function useClientMode() {
  return {
    isClientMode,
    backendAvailable,
    clientFiles,
    checkBackend,
    enableClientMode,
    disableClientMode,
    loadClientFiles,
    getClientPatients,
  }
}
