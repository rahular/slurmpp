import { useQuery } from '@tanstack/react-query'
import { api } from './client'

export interface ClusterOverview {
  total_nodes: number
  allocated_nodes: number
  idle_nodes: number
  down_nodes: number
  drain_nodes: number
  total_cpus: number
  allocated_cpus: number
  running_jobs: number
  pending_jobs: number
  completing_jobs: number
  polled_at: string | null
  source: string
}

export interface NodeInfo {
  name: string
  state: string
  reason: string
  cpus_total: number
  cpus_allocated: number
  memory_mb: number
  memory_allocated_mb: number
  gpus_total: number
  gpus_allocated: number
  partitions: string[]
}

export interface PartitionInfo {
  name: string
  state: string
  total_nodes: number
  total_cpus: number
  max_time_seconds: number | null
  has_gpus: boolean
}

export function useClusterOverview() {
  return useQuery<ClusterOverview>({
    queryKey: ['cluster', 'overview'],
    queryFn: async () => {
      const res = await api.get('/api/v1/cluster/overview')
      return res.data
    },
    refetchInterval: 15_000,
  })
}

export function useNodes() {
  return useQuery<{ data: NodeInfo[] }>({
    queryKey: ['cluster', 'nodes'],
    queryFn: async () => {
      const res = await api.get('/api/v1/cluster/nodes')
      return res.data
    },
    refetchInterval: 30_000,
  })
}

export function usePartitions() {
  return useQuery<{ data: PartitionInfo[] }>({
    queryKey: ['cluster', 'partitions'],
    queryFn: async () => {
      const res = await api.get('/api/v1/cluster/partitions')
      return res.data
    },
    refetchInterval: 60_000,
  })
}
