import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'

export interface Job {
  job_id: number
  array_job_id: number | null
  array_task_id: number | null
  user: string
  account: string
  partition: string
  name: string
  state: string
  state_reason: string
  num_cpus: number
  num_nodes: number
  num_gpus: number
  memory_mb: number
  time_limit_seconds: number | null
  submit_time: string | null
  start_time: string | null
  end_time: string | null
  node_list: string
  work_dir: string
  std_out: string
  std_err: string
  qos: string
}

export interface JobsResponse {
  data: Job[]
  meta: { total: number; page: number; page_size: number; total_pages: number }
}

export interface JobFilters {
  state?: string
  user?: string
  partition?: string
  account?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
}

export interface JobSubmitPayload {
  job_name: string
  partition: string
  num_nodes: number
  num_cpus_per_task: number
  num_tasks: number
  num_gpus: number
  memory_mb: number
  time_limit_seconds: number
  account: string
  qos: string
  script_body: string
  env_vars: Record<string, string>
  std_out: string
  std_err: string
}

export function useJobs(filters: JobFilters = {}) {
  return useQuery<JobsResponse>({
    queryKey: ['jobs', filters],
    queryFn: async () => {
      const res = await api.get('/api/v1/jobs', { params: filters })
      return res.data
    },
    refetchInterval: 15_000,
  })
}

export function useJob(jobId: number) {
  return useQuery<{ data: Job }>({
    queryKey: ['jobs', jobId],
    queryFn: async () => {
      const res = await api.get(`/api/v1/jobs/${jobId}`)
      return res.data
    },
    refetchInterval: 10_000,
  })
}

export function useCancelJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (jobId: number) => api.post(`/api/v1/jobs/${jobId}/cancel`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useHoldJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (jobId: number) => api.post(`/api/v1/jobs/${jobId}/hold`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useRequeueJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (jobId: number) => api.post(`/api/v1/jobs/${jobId}/requeue`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useSignalJob() {
  return useMutation({
    mutationFn: ({ jobId, signal }: { jobId: number; signal: string }) =>
      api.post(`/api/v1/jobs/${jobId}/signal`, { signal }),
  })
}

export function useSubmitJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: JobSubmitPayload) => api.post('/api/v1/jobs/submit', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useJobStats(jobId: number, enabled: boolean) {
  return useQuery({
    queryKey: ['job-stats', jobId],
    queryFn: () => api.get(`/api/v1/jobs/${jobId}/stats`).then((r) => r.data),
    enabled,
    refetchInterval: 10_000,
  })
}
