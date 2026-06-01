import api from './client'

export interface CreateLabelMapParams {
  session_id: string
  patient_id: string
  series_uid: string
  name?: string
  labels?: Array<{ id: number; name: string; color: string; opacity?: number }>
}

export interface PaintParams {
  label_map_id: string
  label: number
  slice_index: number
  orientation: string
  points: number[][]
  radius: number
}

export interface ShapeParams {
  label_map_id: string
  label: number
  slice_index: number
  orientation: string
  shape_type: 'polygon' | 'rectangle' | 'ellipse'
  points: number[][]
}

export interface MagicWandParams {
  label_map_id: string
  label: number
  slice_index: number
  orientation: string
  seed_x: number
  seed_y: number
  pixel_data: number[][]
  threshold?: number
}

export interface SliceMaskParams {
  label_map_id: string
  slice_index: number
  orientation: string
}

export interface ExportNiftiParams {
  label_map_id: string
}

export interface ExportDicomSegParams {
  label_map_id: string
  patient_id: string
  study_uid: string
  labels: Array<{ id: number; name: string; color: number[] }>
}

export interface ImportNiftiParams {
  session_id: string
  patient_id: string
  series_uid: string
  name?: string
}

export async function createLabelMap(params: CreateLabelMapParams) {
  const res = await api.post('/roi/create', params)
  return res.data.data ?? res.data
}

export async function listLabelMaps(sessionId: string, patientId: string) {
  const res = await api.get(`/roi/list/${sessionId}/${patientId}`)
  return res.data.data ?? res.data
}

export async function getLabelMap(labelMapId: string) {
  const res = await api.get(`/roi/${labelMapId}`)
  return res.data.data ?? res.data
}

export async function deleteLabelMap(labelMapId: string) {
  const res = await api.delete(`/roi/${labelMapId}`)
  return res.data.data ?? res.data
}

export async function addLabel(labelMapId: string, labelId: number, name: string, color: string, opacity = 0.4) {
  const res = await api.post('/roi/add-label', { label_map_id: labelMapId, label_id: labelId, name, color, opacity })
  return res.data.data ?? res.data
}

export async function removeLabel(labelMapId: string, labelId: number) {
  const res = await api.post('/roi/remove-label', { label_map_id: labelMapId, label_id: labelId })
  return res.data.data ?? res.data
}

export async function renameLabel(labelMapId: string, labelId: number, name: string) {
  const res = await api.post('/roi/rename-label', { label_map_id: labelMapId, label_id: labelId, name })
  return res.data.data ?? res.data
}

export async function paintStroke(params: PaintParams) {
  const res = await api.post('/roi/paint', params)
  return res.data.data ?? res.data
}

export async function fillShape(params: ShapeParams) {
  const res = await api.post('/roi/shape', params)
  return res.data.data ?? res.data
}

export async function magicWand(params: MagicWandParams) {
  const res = await api.post('/roi/magic-wand', params)
  return res.data.data ?? res.data
}

export async function clearLabel(labelMapId: string, label: number) {
  const res = await api.post('/roi/clear-label', { label_map_id: labelMapId, label })
  return res.data.data ?? res.data
}

export async function erode(labelMapId: string, label: number, iterations = 1) {
  const res = await api.post('/roi/erode', { label_map_id: labelMapId, label, iterations })
  return res.data.data ?? res.data
}

export async function dilate(labelMapId: string, label: number, iterations = 1) {
  const res = await api.post('/roi/dilate', { label_map_id: labelMapId, label, iterations })
  return res.data.data ?? res.data
}

export async function smooth(labelMapId: string, label: number, sigma = 1.0) {
  const res = await api.post('/roi/smooth', { label_map_id: labelMapId, label, sigma })
  return res.data.data ?? res.data
}

export async function getSliceMask(params: SliceMaskParams) {
  const res = await api.post('/roi/slice-mask', params)
  return res.data.data ?? res.data
}

export async function getSliceAllMasks(params: SliceMaskParams) {
  const res = await api.post('/roi/slice-all', params)
  return res.data.data ?? res.data
}

export async function undo(labelMapId: string) {
  const res = await api.post('/roi/undo', { label_map_id: labelMapId })
  return res.data.data ?? res.data
}

export async function redo(labelMapId: string) {
  const res = await api.post('/roi/redo', { label_map_id: labelMapId })
  return res.data.data ?? res.data
}

export async function exportNifti(params: ExportNiftiParams) {
  return api.post('/roi/export/nifti', params, { responseType: 'blob' })
}

export async function exportDicomSeg(params: ExportDicomSegParams) {
  return api.post('/roi/export/dicom-seg', params, { responseType: 'blob' })
}

export async function importNifti(sessionId: string, patientId: string, seriesUid: string, file: File, name?: string) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('session_id', sessionId)
  formData.append('patient_id', patientId)
  formData.append('series_uid', seriesUid)
  if (name) formData.append('name', name)
  const res = await api.post('/roi/import/nifti', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data.data ?? res.data
}
