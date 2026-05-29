import { ref } from 'vue'
import axios from 'axios'

export interface AnonProfile {
  key: string
  name: string
  description: string
}

export interface AnonChange {
  tag: string
  original: string
  action: string
  new_value?: string
}

export interface AnonPreview {
  changes: AnonChange[]
  total: number
}

export interface AnonResult {
  files: Array<{ original_uid: string; anonymized_path: string; changes: number }>
  errors: string[]
  total_changes: number
  output_dir: string
  audit_log: string
}

export function useAnonymization() {
  const profiles = ref<AnonProfile[]>([])
  const preview = ref<AnonPreview | null>(null)
  const result = ref<AnonResult | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function fetchProfiles() {
    const resp = await axios.get('/api/anonymization/profiles')
    profiles.value = resp.data
  }

  async function previewAnonymization(
    sessionId: string,
    patientId: string,
    profile: string,
    customRules?: Record<string, string>,
    dateOffsetDays?: number,
    seed?: string,
  ) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.post('/api/anonymization/preview', {
        session_id: sessionId,
        patient_id: patientId,
        profile,
        custom_rules: customRules || null,
        date_offset_days: dateOffsetDays ?? null,
        seed: seed || '',
      })
      preview.value = resp.data
      return resp.data as AnonPreview
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Preview failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function applyAnonymization(
    sessionId: string,
    patientId: string,
    profile: string,
    customRules?: Record<string, string>,
    dateOffsetDays?: number,
    seed?: string,
  ) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.post('/api/anonymization/apply', {
        session_id: sessionId,
        patient_id: patientId,
        profile,
        custom_rules: customRules || null,
        date_offset_days: dateOffsetDays ?? null,
        seed: seed || null,
      })
      result.value = resp.data
      return resp.data as AnonResult
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Anonymization failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function getAuditLog(sessionId: string, patientId: string) {
    const resp = await axios.get(`/api/anonymization/audit/${sessionId}/${patientId}`)
    return resp.data
  }

  return {
    profiles,
    preview,
    result,
    loading,
    error,
    fetchProfiles,
    previewAnonymization,
    applyAnonymization,
    getAuditLog,
  }
}
