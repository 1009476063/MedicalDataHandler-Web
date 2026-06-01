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

export interface ComplianceViolation {
  tag: string
  value: string
  message: string
}

export interface ComplianceResult {
  compliant: boolean
  violations: ComplianceViolation[]
  checked_tags: number
  passed: number
  failed: number
  profile: string
  standard: string
}

export interface BurnedInResult {
  has_burned_in: boolean
  method: string
  details: string
}

export interface AIBurnedInResult {
  detected: boolean
  regions: Array<{ type: string; description: string; confidence: number }>
  confidence: number
  raw_response: string
}

export interface AIComplianceResult {
  compliant: boolean
  risks: Array<{ tag: string; risk: string; severity: string }>
  summary: string
}

export function useAnonymization() {
  const profiles = ref<AnonProfile[]>([])
  const preview = ref<AnonPreview | null>(null)
  const result = ref<AnonResult | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function fetchProfiles() {
    const resp = await axios.get('/api/anonymization/profiles')
    profiles.value = resp.data.data || resp.data
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
      preview.value = resp.data.data || resp.data
      return preview.value as AnonPreview
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
      result.value = resp.data.data || resp.data
      return result.value as AnonResult
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Anonymization failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function getAuditLog(sessionId: string, patientId: string) {
    const resp = await axios.get(`/api/anonymization/audit/${sessionId}/${patientId}`)
    return resp.data.data || resp.data
  }

  async function validateCompliance(
    sessionId: string,
    patientId: string,
    profile: string,
    fileId?: string,
  ): Promise<ComplianceResult> {
    const resp = await axios.post('/api/anonymization/validate', {
      session_id: sessionId,
      patient_id: patientId,
      file_id: fileId || null,
      profile,
    })
    return (resp.data.data || resp.data) as ComplianceResult
  }

  async function detectBurnedIn(
    sessionId: string,
    patientId: string,
    fileId?: string,
  ): Promise<BurnedInResult> {
    const resp = await axios.post('/api/anonymization/detect-burned-in', {
      session_id: sessionId,
      patient_id: patientId,
      file_id: fileId || null,
    })
    return (resp.data.data || resp.data) as BurnedInResult
  }

  async function detectBurnedInAi(
    sessionId: string,
    patientId: string,
    fileId?: string,
    modelId?: string,
  ): Promise<AIBurnedInResult> {
    const resp = await axios.post('/api/anonymization/detect-burned-in-ai', {
      session_id: sessionId,
      patient_id: patientId,
      file_id: fileId || null,
      model_id: modelId || 'gpt-4o-mini',
    })
    return (resp.data.data || resp.data) as AIBurnedInResult
  }

  async function validateComplianceAi(
    sessionId: string,
    patientId: string,
    profile: string,
    modelId?: string,
  ): Promise<AIComplianceResult> {
    const resp = await axios.post('/api/anonymization/validate-ai', {
      session_id: sessionId,
      patient_id: patientId,
      profile,
      model_id: modelId || 'gpt-4o-mini',
    })
    return (resp.data.data || resp.data) as AIComplianceResult
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
    validateCompliance,
    detectBurnedIn,
    detectBurnedInAi,
    validateComplianceAi,
  }
}
