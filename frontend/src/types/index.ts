export interface Patient {
  patient_id: string
  name: string
  birth_date: string
  sex: string
  studies: Study[]
}

export interface Study {
  study_uid: string
  description: string
  date: string
  series: Series[]
}

export interface Series {
  series_uid: string
  description: string
  modality: string
  series_number: string
  file_count: number
}

export interface DicomFile {
  id: string
  filename: string
  modality: string
  patient_id: string
  study_uid: string
  series_uid: string
  metadata: Record<string, string>
  all_tags: Record<string, { name: string; value: string; vr: string }>
}

export interface SliceData {
  data: number[][]
  shape: number[]
  orientation: string
  slice_index: number
  max_slice: number
  spacing: number[]
  window_center: number | null
  window_width: number | null
}

export interface StructInfo {
  key: string
  name: string
  file_id: string
}

export interface DoseInfo {
  file_id: string
  filename: string
  metadata: Record<string, string>
}

export interface SeriesInfo {
  shape: number[]
  spacing: number[]
  origin: number[]
  min: number
  max: number
  mean: number
}

export interface PlanInfo {
  plan_label: string
  patient_id: string
  file_count: number
  info: Record<string, string>
  beams?: Array<{
    name: string
    energy: string
    gantry_angle: string
    weight: string
  }>
  fractions?: {
    number: string
    dose_per_fraction: string
    total_dose: string
  }
}

export interface OverlaySettings {
  structOpacity: number
  doseOpacity: number
  enabledStructs: string[]
  enabledDoses: string[]
}

export type Modality = 'CT' | 'MR' | 'RTDOSE' | 'RTSTRUCT' | 'RTPLAN' | 'PT' | 'NM' | string

export const MODALITY_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  CT: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', dot: 'bg-blue-500' },
  MR: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500' },
  RTDOSE: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500' },
  RTSTRUCT: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300', dot: 'bg-purple-500' },
  RTPLAN: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300', dot: 'bg-orange-500' },
  PT: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', dot: 'bg-yellow-500' },
  NM: { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-700 dark:text-pink-300', dot: 'bg-pink-500' },
}
