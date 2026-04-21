import { useQuery } from '@tanstack/react-query'
import { api } from './client'

export function useUsageStats(days = 30, partition?: string, account?: string) {
  return useQuery({
    queryKey: ['analytics', 'usage', days, partition, account],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/usage', { params: { days, partition, account } })
      return res.data
    },
  })
}

export function useFairshare() {
  return useQuery({
    queryKey: ['analytics', 'fairshare'],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/fairshare')
      return res.data
    },
    refetchInterval: 60_000,
  })
}

export function useBurnRate() {
  return useQuery({
    queryKey: ['analytics', 'burn-rate'],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/burn-rate')
      return res.data
    },
    refetchInterval: 300_000,
  })
}

export function useEfficiency(days = 30) {
  return useQuery({
    queryKey: ['analytics', 'efficiency', days],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/efficiency', { params: { days } })
      return res.data
    },
  })
}
