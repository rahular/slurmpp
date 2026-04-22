import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

export const api = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401, try refresh; on failure, clear auth and redirect to login
let refreshing = false

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry && !refreshing) {
      original._retry = true
      refreshing = true
      const { refreshToken, setTokens, clear } = useAuthStore.getState()
      if (refreshToken) {
        try {
          const res = await axios.post('/auth/refresh', { refresh_token: refreshToken })
          setTokens(res.data.access_token, res.data.refresh_token)
          original.headers.Authorization = `Bearer ${res.data.access_token}`
          refreshing = false
          return api(original)
        } catch {
          clear()
          refreshing = false
          window.location.href = '/login'
          return Promise.reject(error)
        }
      } else {
        clear()
        refreshing = false
        window.location.href = '/login'
      }
    }
    refreshing = false
    return Promise.reject(error)
  }
)
