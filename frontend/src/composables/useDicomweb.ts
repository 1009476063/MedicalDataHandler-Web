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

export function useDicomweb() {
  const connections = ref<PacsConnection[]>([])
  const studies = ref<PacsStudy[]>([])
  const series = ref<PacsSeries[]>([])
  const loading = ref(false)
  const error = ref('')

  async function fetchConnections() {
    const resp = await axios.get('/api/dicomweb/connections')
    connections.value = resp.data
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
      await fetchConnections()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Connection failed'
    } finally {
      loading.value = false
    }
  }

  async function disconnect(name: string) {
    await axios.delete(`/api/dicomweb/connections/${name}`)
    await fetchConnections()
  }

  async function searchStudies(connection: string, params?: Record<string, string>) {
    loading.value = true
    try {
      const resp = await axios.get('/api/dicomweb/studies', { params: { connection, ...params } })
      studies.value = resp.data
    } finally {
      loading.value = false
    }
  }

  async function searchSeries(connection: string, studyUid: string) {
    loading.value = true
    try {
      const resp = await axios.get(`/api/dicomweb/studies/${studyUid}/series`, { params: { connection } })
      series.value = resp.data
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

  return {
    connections,
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
  }
}
