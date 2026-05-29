import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Patient, SliceData, StructInfo, DoseInfo, SeriesInfo, VolumeInfo, SegFile } from '@/types'
import axios from 'axios'

export const useAppStore = defineStore('app', () => {
  const sessionId = ref<string | null>(null)
  const patients = ref<Patient[]>([])
  const selectedPatientId = ref<string | null>(null)
  const selectedSeriesUid = ref<string | null>(null)
  const uploading = ref(false)
  const uploadProgress = ref(0)

  const currentPatient = computed(() =>
    patients.value.find(p => p.patient_id === selectedPatientId.value)
  )

  const currentSeries = computed(() => {
    if (!currentPatient.value || !selectedSeriesUid.value) return null
    for (const study of currentPatient.value.studies) {
      const s = study.series.find(sr => sr.series_uid === selectedSeriesUid.value)
      if (s) return s
    }
    return null
  })

  const MEDICAL_FORMATS = /\.(nii\.gz|nii|nrrd|nhdr|mha|mhd)$/i

  async function uploadFiles(files: File[], onProgress?: (p: number) => void) {
    uploading.value = true
    uploadProgress.value = 0

    const hasMedicalFormat = files.some(f => MEDICAL_FORMATS.test(f.name))
    const endpoint = hasMedicalFormat ? '/api/upload/medical' : '/api/dicom/upload'

    const formData = new FormData()
    files.forEach(f => formData.append('files', f))

    try {
      const res = await axios.post(endpoint, formData, {
        onUploadProgress: (e) => {
          if (e.total) {
            const p = Math.round((e.loaded / e.total) * 100)
            uploadProgress.value = p
            onProgress?.(p)
          }
        },
      })
      sessionId.value = res.data.session_id
      patients.value = res.data.patients
      if (patients.value.length > 0) {
        selectedPatientId.value = patients.value[0].patient_id
      }
    } finally {
      uploading.value = false
    }
  }

  async function refreshPatients() {
    if (!sessionId.value) return
    const res = await axios.get(`/api/dicom/patients/${sessionId.value}`)
    patients.value = res.data.patients
  }

  async function getSlice(
    seriesUid: string, orientation: string, sliceIndex: number,
    windowCenter?: number, windowWidth?: number
  ): Promise<SliceData | null> {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await axios.post('/api/dicom/slice', {
        session_id: sessionId.value,
        patient_id: selectedPatientId.value,
        series_uid: seriesUid,
        orientation,
        slice_index: sliceIndex,
        window_center: windowCenter ?? null,
        window_width: windowWidth ?? null,
      })
      return res.data
    } catch {
      return null
    }
  }

  async function getSeriesInfo(seriesUid: string): Promise<SeriesInfo | null> {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await axios.get(
        `/api/dicom/series-info/${sessionId.value}/${selectedPatientId.value}/${seriesUid}`
      )
      return res.data
    } catch {
      return null
    }
  }

  async function getStructs(): Promise<StructInfo[]> {
    if (!sessionId.value || !selectedPatientId.value) return []
    try {
      const res = await axios.get(
        `/api/dicom/structs/${sessionId.value}/${selectedPatientId.value}`
      )
      return res.data.structures
    } catch {
      return []
    }
  }

  async function getStructMask(structKey: string, sliceIndex: number, orientation = 'axial') {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await axios.get(
        `/api/dicom/struct-mask/${sessionId.value}/${selectedPatientId.value}/${structKey}/${sliceIndex}?orientation=${orientation}`
      )
      return res.data
    } catch {
      return null
    }
  }

  async function getDoseInfo(): Promise<DoseInfo[]> {
    if (!sessionId.value || !selectedPatientId.value) return []
    try {
      const res = await axios.get(
        `/api/dicom/dose-info/${sessionId.value}/${selectedPatientId.value}`
      )
      return res.data.doses
    } catch {
      return []
    }
  }

  async function getDoseSlice(doseUid: string, sliceIndex: number, orientation = 'axial') {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await axios.get(
        `/api/dicom/dose/${sessionId.value}/${selectedPatientId.value}/${doseUid}/${sliceIndex}?orientation=${orientation}`
      )
      return res.data
    } catch {
      return null
    }
  }

  function selectPatient(patientId: string) {
    selectedPatientId.value = patientId
    selectedSeriesUid.value = null
  }

  function selectSeries(seriesUid: string) {
    selectedSeriesUid.value = seriesUid
  }

  async function getSliceBinary(
    seriesUid: string, orientation: string, sliceIndex: number,
    windowCenter?: number, windowWidth?: number
  ): Promise<SliceData | null> {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await axios.post('/api/dicom/slice-binary', {
        session_id: sessionId.value,
        patient_id: selectedPatientId.value,
        series_uid: seriesUid,
        orientation,
        slice_index: sliceIndex,
        window_center: windowCenter ?? null,
        window_width: windowWidth ?? null,
      }, { responseType: 'arraybuffer' })

      const headers = res.headers
      const shape: number[] = JSON.parse(headers['x-slice-shape'] || '[]')
      const binaryData = new Uint8Array(res.data)
      const data: number[][] = []
      const [rows, cols] = shape
      for (let r = 0; r < rows; r++) {
        const row: number[] = []
        for (let c = 0; c < cols; c++) {
          row.push(binaryData[r * cols + c])
        }
        data.push(row)
      }

      return {
        data,
        shape,
        orientation: headers['x-slice-orientation'] || orientation,
        slice_index: parseInt(headers['x-slice-index'] || '0'),
        max_slice: parseInt(headers['x-slice-maxslice'] || '0'),
        spacing: JSON.parse(headers['x-slice-spacing'] || '[1,1,1]'),
        window_center: (() => { const v = parseFloat(headers['x-slice-windowcenter']); return Number.isFinite(v) ? v : null; })(),
        window_width: (() => { const v = parseFloat(headers['x-slice-windowwidth']); return Number.isFinite(v) ? v : null; })(),
      }
    } catch {
      return null
    }
  }

  async function getVolumeBinary(
    seriesUid: string
  ): Promise<{ data: ArrayBuffer; info: VolumeInfo } | null> {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await axios.post('/api/dicom/volume-binary', {
        session_id: sessionId.value,
        patient_id: selectedPatientId.value,
        series_uid: seriesUid,
      }, { responseType: 'arraybuffer' })

      const headers = res.headers
      return {
        data: res.data,
        info: {
          shape: JSON.parse(headers['x-volume-shape'] || '[]'),
          spacing: JSON.parse(headers['x-volume-spacing'] || '[1,1,1]'),
          origin: JSON.parse(headers['x-volume-origin'] || '[0,0,0]'),
          dtype: headers['x-volume-dtype'] || 'int16',
        },
      }
    } catch {
      return null
    }
  }

  async function getSegFiles(): Promise<SegFile[]> {
    if (!sessionId.value || !selectedPatientId.value) return []
    try {
      const res = await axios.get(`/api/seg/list/${sessionId.value}/${selectedPatientId.value}`)
      return res.data.segments
    } catch {
      return []
    }
  }

  async function getSegMask(fileId: string, segmentNumber: number) {
    if (!sessionId.value) return null
    try {
      const res = await axios.post('/api/seg/mask', {
        session_id: sessionId.value,
        file_id: fileId,
        segment_number: segmentNumber,
      })
      return res.data
    } catch {
      return null
    }
  }

  async function cleanupSession(): Promise<boolean> {
    if (!sessionId.value) return false
    try {
      await axios.delete(`/api/dicom/session/${sessionId.value}`)
      sessionId.value = null
      patients.value = []
      selectedPatientId.value = null
      selectedSeriesUid.value = null
      return true
    } catch {
      return false
    }
  }

  async function getFileMetadata(fileId: string): Promise<Record<string, unknown> | null> {
    if (!sessionId.value) return null
    try {
      const res = await axios.get(`/api/dicom/metadata/${sessionId.value}/${fileId}`)
      return res.data
    } catch {
      return null
    }
  }

  async function getPatientDetail(patientId: string): Promise<{ id: string; filename: string; modality: string; series_uid: string }[]> {
    if (!sessionId.value) return []
    try {
      const res = await axios.get(`/api/dicom/patient/${sessionId.value}/${patientId}`)
      return res.data.files || []
    } catch {
      return []
    }
  }

  async function getRoiBounds(structKey: string) {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await axios.get(
        `/api/dicom/roi-bounds/${sessionId.value}/${selectedPatientId.value}/${structKey}`
      )
      return res.data as { name: string; bounds: { x: number[]; y: number[]; z: number[] }; center: { x: number; y: number; z: number } }
    } catch {
      return null
    }
  }

  async function exportNrrd(
    patientId: string,
    seriesUid: string,
    format: string = 'ct'
  ): Promise<Blob> {
    if (!sessionId.value) throw new Error('No active session')
    const res = await axios.get(
      `/api/export/nrrd/${sessionId.value}/${patientId}/${seriesUid}?format=${format}`,
      { responseType: 'blob' }
    )
    return res.data
  }

  async function get4DInfo(patientId: string, seriesUid: string) {
    if (!sessionId.value) throw new Error('No active session')
    const res = await axios.get(`/api/4d/info/${sessionId.value}/${patientId}/${seriesUid}`)
    return res.data as { is_4d: boolean; time_point_count: number; time_points: Array<{ position: number; file_count: number; shape: number[] }> }
  }

  async function get4DVolume(patientId: string, seriesUid: string, timePoint?: number) {
    if (!sessionId.value) throw new Error('No active session')
    const res = await axios.post('/api/4d/volume', {
      session_id: sessionId.value,
      patient_id: patientId,
      series_uid: seriesUid,
      time_point: timePoint,
    })
    return res.data as { volumes: Record<string, { data: number[][][]; shape: number[]; spacing: number[]; origin: number[]; dtype: string; min: number; max: number; mean: number }> }
  }

  return {
    sessionId, patients, selectedPatientId, selectedSeriesUid,
    uploading, uploadProgress, currentPatient, currentSeries,
    uploadFiles, refreshPatients, getSlice, getSeriesInfo,
    getStructs, getStructMask, getDoseInfo, getDoseSlice,
    selectPatient, selectSeries, getFileMetadata, getPatientDetail, getRoiBounds, exportNrrd, getSliceBinary, getVolumeBinary, cleanupSession,
    getSegFiles, getSegMask, get4DInfo, get4DVolume,
  }
})
