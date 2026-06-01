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

export interface VolumeInfo {
  shape: number[]
  spacing: number[]
  origin: number[]
  dtype: string
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

export interface MeasurementItem {
  uid: string
  toolName: string
  label: string
  stats: Record<string, unknown>
}

export interface SegSegment {
  segment_number: number
  label: string
  algorithm_type: string
  color: number[]
}

export interface SegFile {
  file_id: string
  filename: string
  series_uid: string
  segments: SegSegment[]
  frame_count: number
  description: string
}

export interface SegMask {
  segment_number: number
  shape: number[]
  origin: number[]
  spacing: number[]
  data: number[][][]
}

export interface QueueStatus {
  uploads_available: number
  conversions_available: number
  max_uploads: number
  max_conversions: number
}

export type Modality = 'CT' | 'MR' | 'RTDOSE' | 'RTSTRUCT' | 'RTPLAN' | 'PT' | 'NM' | string

export interface PetCtPair {
  ct_series_uid: string
  ct_description: string
  pt_series_uid: string
  pt_description: string
  study_uid: string
}

export interface SuvInfo {
  patient_weight: number | null
  total_dose: number | null
  half_life: number | null
  decay_correction: string | null
  suv_factor: number | null
}

export interface AIModel {
  id: string
  name: string
  description: string
  type: string
}

export interface AIJob {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  model_id: string
  created_at: string
  error?: string
}

export interface AIResult {
  job_id: string
  model_id: string
  masks: Array<{
    label: string
    shape: number[]
    origin: number[]
    spacing: number[]
    data: number[][][]
  }>
}

export interface ContentTreeNode {
  id: string
  relationship: string
  concept_name: string
  value_type: string
  value: string
  children: ContentTreeNode[]
}

export interface SrDocument {
  id: string
  patient_name: string
  patient_id: string
  study_date: string
  content_date: string
  modality: string
  sr_type: string
  title: string
  institution_name: string
  content_tree: ContentTreeNode[]
  file_path: string
  series_uid: string
  sop_instance_uid: string
}

export interface AiFinding {
  name: string
  value: string
  description?: string
}

export interface PrinterConfig {
  id: string
  name: string
  ae_title: string
  host: string
  port: number
  film_size: string
  orientation: string
  density: number
}

export interface PrintJob {
  id: string
  printer_id: string
  status: string
  film_size: string
  orientation: string
  created_at: string
}

export const MODALITY_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  CT: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', dot: 'bg-blue-500' },
  MR: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500' },
  RTDOSE: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500' },
  RTSTRUCT: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300', dot: 'bg-purple-500' },
  RTPLAN: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300', dot: 'bg-orange-500' },
  PT: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', dot: 'bg-yellow-500' },
  NM: { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-700 dark:text-pink-300', dot: 'bg-pink-500' },
}
