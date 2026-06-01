import api from './client'

export async function exportNrrd(
  sessionId: string,
  patientId: string,
  seriesUid: string,
  format = 'ct',
  dtype = 'float32',
  unit = 'native',
): Promise<Blob> {
  const res = await api.get(
    `/export/nrrd/${sessionId}/${patientId}/${seriesUid}?format=${format}&dtype=${dtype}&unit=${unit}`,
    { responseType: 'blob' },
  )
  return res.data
}
