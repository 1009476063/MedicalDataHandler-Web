import { ref } from 'vue'
import axios from 'axios'

export interface MwlItem {
  id: string
  patient_name: string
  patient_id: string
  accession_number: string
  study_date: string
  modality: string
  referring_physician: string
  scheduled_step_status: string
  study_instance_uid: string
  scheduled_station_ae_title: string
  requested_procedure_description: string
  institution_name: string
  station_name: string
}

export function useWorklist() {
  const items = ref<MwlItem[]>([])
  const searchQuery = ref('')
  const loading = ref(false)
  const error = ref('')

  async function search(sessionId: string, query: string = '') {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.get('/api/mwl/search', {
        params: { session_id: sessionId, q: query },
      })
      items.value = resp.data.data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Search failed'
    } finally {
      loading.value = false
    }
  }

  async function importCsv(sessionId: string, file: File) {
    loading.value = true
    error.value = ''
    try {
      const formData = new FormData()
      formData.append('file', file)
      const resp = await axios.post('/api/mwl/import', formData, {
        params: { session_id: sessionId },
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      await search(sessionId)
      return resp.data.data.count as number
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Import failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function exportCsv(sessionId: string): Promise<string> {
    const resp = await axios.get('/api/mwl/export', {
      params: { session_id: sessionId },
    })
    return resp.data.data.csv as string
  }

  async function addItem(sessionId: string, item: Partial<MwlItem>) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.post('/api/mwl/items', {
        session_id: sessionId,
        ...item,
      })
      items.value.push(resp.data.data)
      return resp.data.data as MwlItem
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Add failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateItem(sessionId: string, itemId: string, updates: Partial<MwlItem>) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.put(`/api/mwl/items/${itemId}`, {
        session_id: sessionId,
        ...updates,
      })
      const idx = items.value.findIndex(i => i.id === itemId)
      if (idx >= 0) items.value[idx] = resp.data.data
      return resp.data.data as MwlItem
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Update failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteItem(sessionId: string, itemId: string) {
    loading.value = true
    error.value = ''
    try {
      await axios.delete(`/api/mwl/items/${itemId}`, {
        params: { session_id: sessionId },
      })
      items.value = items.value.filter(i => i.id !== itemId)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Delete failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function remoteQuery(config: {
    base_url: string
    auth_token?: string
    patient_name?: string
    patient_id?: string
    accession_number?: string
    study_date?: string
  }) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.post('/api/mwl/remote-query', config)
      return resp.data.data as MwlItem[]
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Remote query failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    searchQuery,
    loading,
    error,
    search,
    importCsv,
    exportCsv,
    addItem,
    updateItem,
    deleteItem,
    remoteQuery,
  }
}
