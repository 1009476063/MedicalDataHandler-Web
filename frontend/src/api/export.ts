import api from './client'

export async function exportNrrd(sessionId: string, patientId: string, seriesUid: string, format = 'ct'): Promise<Blob> {
  const res = await api.get(
    `/export/nrrd/${sessionId}/${patientId}/${seriesUid}?format=${format}`,
    { responseType: 'blob' },
  )
  return res.data
}
