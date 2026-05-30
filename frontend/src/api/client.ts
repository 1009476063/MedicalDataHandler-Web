import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 429) {
      console.warn('Rate limited — retry after a moment')
    }
    if (error.response?.status === 401) {
      window.dispatchEvent(new Event('auth:logout'))
    }
    return Promise.reject(error)
  },
)

export default api
