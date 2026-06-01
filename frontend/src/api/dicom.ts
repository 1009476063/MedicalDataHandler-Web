import api from './client'

export interface UploadResponse {
  session_id: string
  patients: unknown[]
  file_count: number
}

export async function uploadDicom(files: File[], onProgress?: (p: number) => void): Promise<UploadResponse> {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  const res = await api.post('/dicom/upload', formData, {
    onUploadProgress: (e) => {
      if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100))
    },
  })
  return res.data.data ?? res.data
}

export async function uploadMedical(files: File[], onProgress?: (p: number) => void): Promise<UploadResponse> {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  const res = await api.post('/upload/medical', formData, {
    onUploadProgress: (e) => {
      if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100))
    },
  })
  return res.data.data ?? res.data
}

export async function getPatients(sessionId: string) {
  const res = await api.get(`/dicom/patients/${sessionId}`)
  return res.data.data ?? res.data
}

export async function getPatientDetail(sessionId: string, patientId: string) {
  const res = await api.get(`/dicom/patient/${sessionId}/${patientId}`)
  return res.data.data ?? res.data
}

export async function getFileMetadata(sessionId: string, fileId: string) {
  const res = await api.get(`/dicom/metadata/${sessionId}/${fileId}`)
  return res.data.data ?? res.data
}

export async function getSlice(params: {
  session_id: string; patient_id: string; series_uid: string
  orientation: string; slice_index: number
  window_center?: number | null; window_width?: number | null
}) {
  const res = await api.post('/dicom/slice', params)
  return res.data.data ?? res.data
}

export async function getSliceBinary(params: {
  session_id: string; patient_id: string; series_uid: string
  orientation: string; slice_index: number
  window_center?: number | null; window_width?: number | null
}) {
  return api.post('/dicom/slice-binary', params, { responseType: 'arraybuffer' })
}

export async function getVolumeBinary(params: {
  session_id: string; patient_id: string; series_uid: string
}) {
  return api.post('/dicom/volume-binary', params, { responseType: 'arraybuffer' })
}

export async function getSeriesInfo(sessionId: string, patientId: string, seriesUid: string) {
  const res = await api.get(`/dicom/series-info/${sessionId}/${patientId}/${seriesUid}`)
  return res.data.data ?? res.data
}

export async function getStructs(sessionId: string, patientId: string) {
  const res = await api.get(`/dicom/structs/${sessionId}/${patientId}`)
  return res.data.data ?? res.data
}

export async function getStructMask(sessionId: string, patientId: string, structKey: string, sliceIndex: number, orientation = 'axial') {
  const res = await api.get(
    `/dicom/struct-mask/${sessionId}/${patientId}/${structKey}/${sliceIndex}?orientation=${orientation}`
  )
  return res.data.data ?? res.data
}

export async function getDoseInfo(sessionId: string, patientId: string) {
  const res = await api.get(`/dicom/dose-info/${sessionId}/${patientId}`)
  return res.data.data ?? res.data
}

export async function getDoseSlice(sessionId: string, patientId: string, doseUid: string, sliceIndex: number, orientation = 'axial') {
  const res = await api.get(
    `/dicom/dose/${sessionId}/${patientId}/${doseUid}/${sliceIndex}?orientation=${orientation}`
  )
  return res.data.data ?? res.data
}

export async function getRoiBounds(sessionId: string, patientId: string, structKey: string) {
  const res = await api.get(`/dicom/roi-bounds/${sessionId}/${patientId}/${structKey}`)
  return res.data.data ?? res.data
}

export async function deleteSession(sessionId: string) {
  const res = await api.delete(`/dicom/session/${sessionId}`)
  return res.data.data ?? res.data
}

export async function getSegFiles(sessionId: string, patientId: string) {
  const res = await api.get(`/seg/list/${sessionId}/${patientId}`)
  return res.data.data ?? res.data
}

export async function getSegMask(sessionId: string, fileId: string, segmentNumber: number) {
  const res = await api.post('/seg/mask', { session_id: sessionId, file_id: fileId, segment_number: segmentNumber })
  return res.data.data ?? res.data
}

export async function get4DInfo(sessionId: string, patientId: string, seriesUid: string) {
  const res = await api.get(`/4d/info/${sessionId}/${patientId}/${seriesUid}`)
  return res.data.data ?? res.data
}

export async function get4DVolume(sessionId: string, patientId: string, seriesUid: string, timePoint?: number) {
  const res = await api.post('/4d/volume', {
    session_id: sessionId, patient_id: patientId, series_uid: seriesUid, time_point: timePoint,
  })
  return res.data.data ?? res.data
}

// --- AI Segmentation ---

export async function runAutoSegmentation(params: {
  session_id: string; patient_id: string; series_uid: string
  label_map_id: string; label: number; model_id?: string
}) {
  const res = await api.post('/ai/segment/auto', params)
  return res.data.data ?? res.data
}

export async function runTextSegmentation(params: {
  session_id: string; patient_id: string; series_uid: string
  text_prompt: string; label_map_id: string; label: number; model_id?: string
}) {
  const res = await api.post('/ai/segment/text', params)
  return res.data.data ?? res.data
}

export async function runReferenceSegmentation(params: {
  session_id: string; patient_id: string; series_uid: string
  ref_label_map_id: string; ref_label: number; label_map_id: string
  label: number; model_id?: string
}) {
  const res = await api.post('/ai/segment/reference', params)
  return res.data.data ?? res.data
}
