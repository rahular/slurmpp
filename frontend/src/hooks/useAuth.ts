import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/authStore'

export function useAuth() {
  const { accessToken, username, role, setTokens, clear } = useAuthStore()
  const navigate = useNavigate()

  const login = useCallback(
    async (username: string, password: string) => {
      const res = await api.post('/auth/login', { username, password })
      setTokens(res.data.access_token, res.data.refresh_token)
      navigate('/')
    },
    [setTokens, navigate]
  )

  const logout = useCallback(() => {
    clear()
    navigate('/login')
  }, [clear, navigate])

  return {
    isAuthenticated: !!accessToken,
    isAdmin: role === 'admin',
    username,
    role,
    login,
    logout,
  }
}
