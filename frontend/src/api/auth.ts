import api from './client'

export async function getAuthConfig() {
  const res = await api.get('/auth/config')
  return res.data.data ?? res.data
}

export async function login(code: string) {
  const res = await api.post('/auth/login', { code })
  return res.data.data ?? res.data
}

export async function refresh(refreshToken: string) {
  const res = await api.post('/auth/refresh', { refreshToken })
  return res.data.data ?? res.data
}

export async function getMe() {
  const res = await api.get('/auth/me')
  return res.data.data ?? res.data
}

export async function logout() {
  const res = await api.post('/auth/logout')
  return res.data.data ?? res.data
}
