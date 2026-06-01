import { ref } from 'vue'

let _clientLoader: typeof import('@/utils/clientDicomLoader') | null = null
async function getClientLoader() {
  if (!_clientLoader) {
    _clientLoader = await import('@/utils/clientDicomLoader')
  }
  return _clientLoader
}

const MAX_CLIENT_FILES = 500

const isClientMode = ref(false)
const backendAvailable = ref(true)
const clientFiles = ref<Array<{
  id: string
  buffer: ArrayBuffer
  metadata: Record<string, unknown>
}>>([])

export interface ClientPatient {
  patientId: string
  patientName: string
  studies: Map<string, ClientStudy>
}

export interface ClientStudy {
  studyUid: string
  description: string
  series: Map<string, ClientSeries>
}

export interface ClientSeries {
  seriesUid: string
  description: string
  modality: string
  files: Array<{ id: string; metadata: Record<string, unknown> }>
}

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
export async function enableClientMode() {
  const loader = await getClientLoader()
  loader.registerClientLoaders()
  isClientMode.value = true
}

/** Disable client-only mode and clear buffers. */
export async function disableClientMode() {
  isClientMode.value = false
  clientFiles.value = []
  const loader = await getClientLoader()
  loader.clearDicomBuffers()
}

/** Load DICOM files in client mode. Returns parsed metadata. */
export async function loadClientFiles(files: File[]) {
  const loader = await getClientLoader()
  loader.registerClientLoaders()
  isClientMode.value = true

  const results: Array<{
    id: string
    buffer: ArrayBuffer
    metadata: Record<string, unknown>
  }> = []

  for (const file of files) {
    const buffer = await file.arrayBuffer()
    const metadata = loader.parseDicomMetadata(buffer)
    const imageId = loader.storeDicomBuffer(buffer)
    results.push({
      id: imageId,
      buffer,
      metadata,
    })
  }

  clientFiles.value = [...clientFiles.value, ...results]

  // Evict oldest files if over limit
  while (clientFiles.value.length > MAX_CLIENT_FILES) {
    clientFiles.value.shift()
  }

  return results
}

/** Get unique patients from client files. */
export function getClientPatients(): ClientPatient[] {
  const patientMap = new Map<string, ClientPatient>()

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

/** Get imageIds for a specific series, sorted by instance number. */
export function getSeriesImageIds(seriesUid: string): string[] {
  const files = clientFiles.value.filter(
    f => (f.metadata as Record<string, string>).seriesInstanceUID === seriesUid
  )
  const sorted = files.sort((a, b) => {
    const instA = (a.metadata.instanceNumber as number) || 0
    const instB = (b.metadata.instanceNumber as number) || 0
    return instA - instB
  })
  return sorted.map(f => f.id)
}

/** Get metadata for all files in a series. */
export function getSeriesMetadata(seriesUid: string) {
  return clientFiles.value
    .filter(f => (f.metadata as Record<string, string>).seriesInstanceUID === seriesUid)
    .sort((a, b) => {
      const instA = (a.metadata.instanceNumber as number) || 0
      const instB = (b.metadata.instanceNumber as number) || 0
      return instA - instB
    })
    .map(f => f.metadata)
}

/** Get metadata for a specific file by imageId. */
export function getFileMetadataById(imageId: string): Record<string, unknown> | null {
  const file = clientFiles.value.find(f => f.id === imageId)
  return file ? file.metadata : null
}

/** Remove a single client file by imageId. */
export async function removeClientFile(imageId: string) {
  clientFiles.value = clientFiles.value.filter(f => f.id !== imageId)
}

/** Clear all client files and buffers. */
export async function clearClientFiles() {
  clientFiles.value = []
  const loader = await getClientLoader()
  loader.clearDicomBuffers()
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
    getSeriesImageIds,
    getSeriesMetadata,
    clearClientFiles,
    removeClientFile,
  }
}
