import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  username: string | null
  role: 'user' | 'admin' | null
  setTokens: (access: string, refresh: string) => void
  clear: () => void
}

function parseJwtPayload(token: string): Record<string, unknown> {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return {}
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      username: null,
      role: null,
      setTokens: (access, refresh) => {
        const payload = parseJwtPayload(access)
        set({
          accessToken: access,
          refreshToken: refresh,
          username: payload.sub as string,
          role: (payload.role as 'user' | 'admin') ?? 'user',
        })
      },
      clear: () =>
        set({ accessToken: null, refreshToken: null, username: null, role: null }),
    }),
    { name: 'slurmpp-auth' }
  )
)
