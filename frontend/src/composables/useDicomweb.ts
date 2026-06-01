import { ref } from 'vue'
import axios from 'axios'

interface PacsConnection {
  name: string
  base_url: string
}

export interface PacsStudy {
  [key: string]: { vr: string; Value?: string[] } | undefined
}

export interface PacsSeries {
  [key: string]: { vr: string; Value?: string[] } | undefined
}

function extractTag(tag: Record<string, unknown>, key: string): string {
  const field = tag[key] as { Value?: string[] } | undefined
  return field?.Value?.[0] || ''
}

// Module-level singleton state — survives component mount/unmount cycles
const connections = ref<PacsConnection[]>([])
const studies = ref<PacsStudy[]>([])
const series = ref<PacsSeries[]>([])
const loading = ref(false)
const error = ref('')
const connectionsReady = ref(false)

export function useDicomweb() {

  async function fetchConnections(force = false) {
    if (connectionsReady.value && !force) return
    const resp = await axios.get('/api/dicomweb/connections')
    connections.value = resp.data.data ?? resp.data
    connectionsReady.value = true
  }

  async function connect(name: string, baseUrl: string, token?: string) {
    loading.value = true
    error.value = ''
    try {
      await axios.post('/api/dicomweb/connect', {
        name,
        base_url: baseUrl,
        auth_token: token || null,
      })
      await fetchConnections(true)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Connection failed'
    } finally {
      loading.value = false
    }
  }

  async function disconnect(name: string) {
    await axios.delete(`/api/dicomweb/connections/${name}`)
    await fetchConnections(true)
  }

  async function searchStudies(connection: string, params?: Record<string, string>) {
    loading.value = true
    try {
      const resp = await axios.get('/api/dicomweb/studies', { params: { connection, ...params } })
      studies.value = resp.data.data ?? resp.data
    } finally {
      loading.value = false
    }
  }

  async function searchSeries(connection: string, studyUid: string) {
    loading.value = true
    try {
      const resp = await axios.get(`/api/dicomweb/studies/${studyUid}/series`, { params: { connection } })
      series.value = resp.data.data ?? resp.data
    } finally {
      loading.value = false
    }
  }

  function studyName(s: PacsStudy): string {
    return extractTag(s, '00100010') || extractTag(s, '00081030') || 'Unknown'
  }

  function studyDate(s: PacsStudy): string {
    return extractTag(s, '00080020') || ''
  }

  function studyUid(s: PacsStudy): string {
    return extractTag(s, '0020000D') || ''
  }

  function seriesModality(s: PacsSeries): string {
    return extractTag(s, '00080060') || ''
  }

  function seriesDescription(s: PacsSeries): string {
    return extractTag(s, '0008103E') || ''
  }

  function seriesUid(s: PacsSeries): string {
    return extractTag(s, '0020000E') || ''
  }

  function reset() {
    connections.value = []
    connectionsReady.value = false
    studies.value = []
    series.value = []
    loading.value = false
    error.value = ''
  }

  return {
    connections,
    connectionsReady,
    studies,
    series,
    loading,
    error,
    fetchConnections,
    connect,
    disconnect,
    searchStudies,
    searchSeries,
    studyName,
    studyDate,
    studyUid,
    seriesModality,
    seriesDescription,
    seriesUid,
    reset,
  }
}
