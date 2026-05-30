import type { Patient } from '@/types'
import { getPatients } from '@/api/dicom'
import {
  getClientPatients,
  type ClientPatient,
} from '@/composables/useClientMode'

/** Convert ClientPatient (Map-based) to store Patient type. */
export function clientPatientToPatient(cp: ClientPatient): Patient {
  const studies = Array.from(cp.studies.values()).map(study => ({
    study_uid: study.studyUid,
    description: study.description,
    series: Array.from(study.series.values()).map(s => ({
      series_uid: s.seriesUid,
      description: s.description,
      modality: s.modality,
      file_count: s.files.length,
    })),
  }))
  return {
    patient_id: cp.patientId,
    name: cp.patientName,
    studies,
  } as Patient
}

export async function fetchPatients(sessionId: string): Promise<Patient[]> {
  const result = await getPatients(sessionId)
  return result.patients
}

export function loadClientPatients(): Patient[] {
  return getClientPatients().map(clientPatientToPatient)
}
