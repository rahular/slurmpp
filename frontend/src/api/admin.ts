import { useQuery } from '@tanstack/react-query'
import { api } from './client'

export function useAdminUsers(days = 30) {
  return useQuery({
    queryKey: ['admin', 'users', days],
    queryFn: async () => {
      const res = await api.get('/api/v1/admin/users', { params: { days } })
      return res.data
    },
  })
}

export function useAdminHeatmap(days = 30) {
  return useQuery({
    queryKey: ['admin', 'heatmap', days],
    queryFn: async () => {
      const res = await api.get('/api/v1/admin/heatmap', { params: { days } })
      return res.data
    },
  })
}
