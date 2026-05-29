/**
 * Auth composable — manages login/logout, token storage, and user info.
 * When OIDC is not configured (backend returns enabled: false), auth is transparent.
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

interface AuthConfig {
  enabled: boolean
  authorizationEndpoint: string
  clientId: string
  redirectUri: string
}

interface UserInfo {
  sub: string
  name: string
  email: string
  isAuthenticated: boolean
}

const accessToken = ref<string | null>(localStorage.getItem('mdh_access_token'))
const refreshToken = ref<string | null>(localStorage.getItem('mdh_refresh_token'))
const user = ref<UserInfo | null>(null)
const authConfig = ref<AuthConfig | null>(null)
const loading = ref(false)

export function useAuth() {
  const router = useRouter()

  const isAuthenticated = computed(() => !!accessToken.value)
  const authEnabled = computed(() => authConfig.value?.enabled ?? false)

  async function fetchAuthConfig() {
    try {
      const resp = await fetch('/api/auth/config')
      authConfig.value = await resp.json()
    } catch {
      authConfig.value = { enabled: false, authorizationEndpoint: '', clientId: '', redirectUri: '' }
    }
  }

  async function fetchUser() {
    if (!accessToken.value) {
      user.value = null
      return
    }
    try {
      const resp = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${accessToken.value}` },
      })
      if (resp.ok) {
        user.value = await resp.json()
      } else {
        logout()
      }
    } catch {
      user.value = null
    }
  }

  function loginWithRedirect() {
    if (!authConfig.value?.enabled) return
    const params = new URLSearchParams({
      client_id: authConfig.value.clientId,
      redirect_uri: authConfig.value.redirectUri,
      response_type: 'code',
      scope: 'openid profile email',
    })
    window.location.href = `${authConfig.value.authorizationEndpoint}?${params}`
  }

  async function handleCallback(code: string) {
    loading.value = true
    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      if (!resp.ok) throw new Error('Login failed')
      const data = await resp.json()
      setTokens(data.accessToken, data.refreshToken)
      await fetchUser()
      router.push('/')
    } finally {
      loading.value = false
    }
  }

  async function loginLocally() {
    loading.value = true
    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: 'local' }),
      })
      if (!resp.ok) throw new Error('Login failed')
      const data = await resp.json()
      setTokens(data.accessToken, data.refreshToken)
      await fetchUser()
    } finally {
      loading.value = false
    }
  }

  async function tryRefresh() {
    if (!refreshToken.value) return false
    try {
      const resp = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: refreshToken.value }),
      })
      if (!resp.ok) return false
      const data = await resp.json()
      setTokens(data.accessToken, data.refreshToken)
      return true
    } catch {
      return false
    }
  }

  function setTokens(access: string, refresh: string | null) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('mdh_access_token', access)
    if (refresh) localStorage.setItem('mdh_refresh_token', refresh)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('mdh_access_token')
    localStorage.removeItem('mdh_refresh_token')
    fetch('/api/auth/logout', { method: 'POST' }).catch(() => {})
  }

  function getAuthHeaders(): Record<string, string> {
    if (!accessToken.value) return {}
    return { Authorization: `Bearer ${accessToken.value}` }
  }

  return {
    accessToken,
    refreshToken,
    user,
    authConfig,
    loading,
    isAuthenticated,
    authEnabled,
    fetchAuthConfig,
    fetchUser,
    loginWithRedirect,
    handleCallback,
    loginLocally,
    tryRefresh,
    logout,
    getAuthHeaders,
  }
}
