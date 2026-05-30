import api from './client'

export async function listConfigs() {
  const res = await api.get('/config/')
  return res.data.data ?? res.data
}

export async function getConfig(configName: string) {
  const res = await api.get(`/config/${configName}`)
  return res.data.data ?? res.data
}

export async function updateConfig(configName: string, rules: Record<string, unknown>) {
  const res = await api.put(`/config/${configName}`, { rules })
  return res.data.data ?? res.data
}

export async function resetConfig(configName: string) {
  const res = await api.post(`/config/${configName}/reset`)
  return res.data.data ?? res.data
}
