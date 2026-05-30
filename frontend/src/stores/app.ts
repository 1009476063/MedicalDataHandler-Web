import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Patient, SliceData, StructInfo, DoseInfo, SeriesInfo, VolumeInfo, SegFile } from '@/types'
import {
  uploadDicom, uploadMedical,
  getPatientDetail as apiGetPatientDetail,
  getFileMetadata as apiGetFileMetadata,
  getSlice as apiGetSlice, getSliceBinary as apiGetSliceBinary,
  getVolumeBinary as apiGetVolumeBinary, getSeriesInfo as apiGetSeriesInfo,
  getStructs as apiGetStructs, getStructMask as apiGetStructMask,
  getDoseInfo as apiGetDoseInfo, getDoseSlice as apiGetDoseSlice,
  getRoiBounds as apiGetRoiBounds,
  getSegFiles as apiGetSegFiles, getSegMask as apiGetSegMask,
  get4DInfo as apiGet4DInfo, get4DVolume as apiGet4DVolume,
} from '@/api/dicom'
import { exportNrrd as apiExportNrrd } from '@/api/export'
import {
  checkBackend,
  loadClientFiles as loadClientFilesRaw,
  getClientPatients,
  getSeriesMetadata,
  getFileMetadataById,
} from '@/composables/useClientMode'
import { cleanupSessionAction } from './session'
import { clientPatientToPatient, fetchPatients, loadClientPatients } from './patient'
import { buildClientSeriesInfo } from './viewer'

export const useAppStore = defineStore('app', () => {
  const sessionId = ref<string | null>(null)
  const patients = ref<Patient[]>([])
  const selectedPatientId = ref<string | null>(null)
  const selectedSeriesUid = ref<string | null>(null)
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const isClientMode = ref(false)

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

    const backendUp = await checkBackend()

    if (!backendUp || hasMedicalFormat && !backendUp) {
      await loadClientFilesAction(files)
      uploading.value = false
      return
    }

    const uploadFn = hasMedicalFormat ? uploadMedical : uploadDicom

    try {
      const result = await uploadFn(files, (p) => {
        uploadProgress.value = p
        onProgress?.(p)
      })
      sessionId.value = result.session_id
      patients.value = result.patients as Patient[]
      isClientMode.value = false
      if (patients.value.length > 0) {
        selectedPatientId.value = patients.value[0].patient_id
      }
    } catch {
      await loadClientFilesAction(files)
    } finally {
      uploading.value = false
    }
  }

  async function loadClientFilesAction(files: File[]) {
    await loadClientFilesRaw(files)
    isClientMode.value = true
    patients.value = loadClientPatients()
    if (patients.value.length > 0) {
      selectedPatientId.value = patients.value[0].patient_id
    }
  }

  async function refreshPatients() {
    if (!sessionId.value) return
    patients.value = await fetchPatients(sessionId.value)
  }

  async function cleanupSession(): Promise<boolean> {
    if (!sessionId.value) return false
    const ok = await cleanupSessionAction(sessionId.value)
    if (ok) {
      sessionId.value = null
      patients.value = []
      selectedPatientId.value = null
      selectedSeriesUid.value = null
    }
    return ok
  }

  async function getSlice(
    seriesUid: string, orientation: string, sliceIndex: number,
    windowCenter?: number, windowWidth?: number
  ): Promise<SliceData | null> {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      return await apiGetSlice({
        session_id: sessionId.value,
        patient_id: selectedPatientId.value,
        series_uid: seriesUid,
        orientation,
        slice_index: sliceIndex,
        window_center: windowCenter ?? null,
        window_width: windowWidth ?? null,
      })
    } catch {
      return null
    }
  }

  async function getSeriesInfo(seriesUid: string): Promise<SeriesInfo | null> {
    if (isClientMode.value) {
      const meta = getSeriesMetadata(seriesUid)
      return buildClientSeriesInfo(meta as Record<string, unknown>[], meta.length)
    }
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      return await apiGetSeriesInfo(sessionId.value, selectedPatientId.value, seriesUid)
    } catch {
      return null
    }
  }

  async function getStructs(): Promise<StructInfo[]> {
    if (!sessionId.value || !selectedPatientId.value) return []
    try {
      const result = await apiGetStructs(sessionId.value, selectedPatientId.value)
      return result.structures
    } catch {
      return []
    }
  }

  async function getStructMask(structKey: string, sliceIndex: number, orientation = 'axial') {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      return await apiGetStructMask(sessionId.value, selectedPatientId.value, structKey, sliceIndex, orientation)
    } catch {
      return null
    }
  }

  async function getDoseInfo(): Promise<DoseInfo[]> {
    if (!sessionId.value || !selectedPatientId.value) return []
    try {
      const result = await apiGetDoseInfo(sessionId.value, selectedPatientId.value)
      return result.doses
    } catch {
      return []
    }
  }

  async function getDoseSlice(doseUid: string, sliceIndex: number, orientation = 'axial') {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      return await apiGetDoseSlice(sessionId.value, selectedPatientId.value, doseUid, sliceIndex, orientation)
    } catch {
      return null
    }
  }

  async function getSliceBinary(
    seriesUid: string, orientation: string, sliceIndex: number,
    windowCenter?: number, windowWidth?: number
  ): Promise<SliceData | null> {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      const res = await apiGetSliceBinary({
        session_id: sessionId.value,
        patient_id: selectedPatientId.value,
        series_uid: seriesUid,
        orientation,
        slice_index: sliceIndex,
        window_center: windowCenter ?? null,
        window_width: windowWidth ?? null,
      })

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
      const res = await apiGetVolumeBinary({
        session_id: sessionId.value,
        patient_id: selectedPatientId.value,
        series_uid: seriesUid,
      })

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
      const result = await apiGetSegFiles(sessionId.value, selectedPatientId.value)
      return result.segments
    } catch {
      return []
    }
  }

  async function getSegMask(fileId: string, segmentNumber: number) {
    if (!sessionId.value) return null
    try {
      return await apiGetSegMask(sessionId.value, fileId, segmentNumber)
    } catch {
      return null
    }
  }

  async function getFileMetadata(fileId: string): Promise<Record<string, unknown> | null> {
    if (isClientMode.value) {
      return getFileMetadataById(fileId)
    }
    if (!sessionId.value) return null
    try {
      return await apiGetFileMetadata(sessionId.value, fileId)
    } catch {
      return null
    }
  }

  async function getPatientDetail(patientId: string): Promise<{ id: string; filename: string; modality: string; series_uid: string }[]> {
    if (isClientMode.value) {
      const allPatients = getClientPatients()
      const patientData = allPatients.find(p => p.patientId === patientId)
      if (!patientData) return []
      const files: { id: string; filename: string; modality: string; series_uid: string }[] = []
      for (const study of patientData.studies.values()) {
        for (const series of study.series.values()) {
          for (const f of series.files) {
            files.push({
              id: f.id,
              filename: (f.metadata.seriesDescription as string) || f.id,
              modality: series.modality,
              series_uid: series.seriesUid,
            })
          }
        }
      }
      return files
    }
    if (!sessionId.value) return []
    try {
      const result = await apiGetPatientDetail(sessionId.value, patientId)
      return result.files || []
    } catch {
      return []
    }
  }

  async function getRoiBounds(structKey: string) {
    if (!sessionId.value || !selectedPatientId.value) return null
    try {
      return await apiGetRoiBounds(sessionId.value, selectedPatientId.value, structKey) as { name: string; bounds: { x: number[]; y: number[]; z: number[] }; center: { x: number; y: number; z: number } }
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
    return await apiExportNrrd(sessionId.value, patientId, seriesUid, format)
  }

  async function get4DInfo(patientId: string, seriesUid: string) {
    if (!sessionId.value) throw new Error('No active session')
    return await apiGet4DInfo(sessionId.value, patientId, seriesUid) as { is_4d: boolean; time_point_count: number; time_points: Array<{ position: number; file_count: number; shape: number[] }> }
  }

  async function get4DVolume(patientId: string, seriesUid: string, timePoint?: number) {
    if (!sessionId.value) throw new Error('No active session')
    return await apiGet4DVolume(sessionId.value, patientId, seriesUid, timePoint) as { volumes: Record<string, { data: number[][][]; shape: number[]; spacing: number[]; origin: number[]; dtype: string; min: number; max: number; mean: number }> }
  }

  return {
    sessionId, patients, selectedPatientId, selectedSeriesUid,
    uploading, uploadProgress, currentPatient, currentSeries,
    isClientMode,
    uploadFiles, loadClientFilesAction, refreshPatients, getSlice, getSeriesInfo,
    getStructs, getStructMask, getDoseInfo, getDoseSlice,
    selectPatient: (id: string) => { selectedPatientId.value = id; selectedSeriesUid.value = null },
    selectSeries: (uid: string) => { selectedSeriesUid.value = uid },
    getFileMetadata, getPatientDetail, getRoiBounds, exportNrrd,
    getSliceBinary, getVolumeBinary, cleanupSession,
    getSegFiles, getSegMask, get4DInfo, get4DVolume,
  }
})
