import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useJob, useJobStats } from '@/api/jobs'
import JobStateBadge from '@/components/jobs/JobStateBadge'
import JobActions from '@/components/jobs/JobActions'
import LogViewer from '@/components/jobs/LogViewer'
import { formatSeconds, formatTimeAgo, formatBytes } from '@/lib/utils'
import { ArrowLeft, Copy } from 'lucide-react'

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const id = parseInt(jobId ?? '0')
  const { data, isLoading } = useJob(id)
  const { data: statsData } = useJobStats(id, !isLoading)
  const [activeTab, setActiveTab] = useState<'log' | 'info'>('info')
  const navigate = useNavigate()

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (!data?.data) return <div className="p-6 text-muted-foreground">Job not found.</div>

  const job = data.data
  const stats = statsData?.data

  const handleClone = () => {
    const params = new URLSearchParams({
      partition: job.partition || '',
      num_nodes: String(job.num_nodes || 1),
      num_cpus: String(job.num_cpus || 1),
      num_gpus: String(job.num_gpus || 0),
      memory_mb: String(job.memory_mb || 4096),
      time_limit: String(job.time_limit_seconds || 3600),
      job_name: `${job.name}-clone`,
      account: job.account || '',
      qos: job.qos || '',
    })
    navigate(`/submit?${params.toString()}`)
  }

  const fields = [
    { label: 'Job ID', value: job.job_id },
    { label: 'Name', value: job.name || '—' },
    { label: 'User', value: job.user },
    { label: 'Account', value: job.account || '—' },
    { label: 'Partition', value: job.partition },
    { label: 'QOS', value: job.qos || '—' },
    { label: 'CPUs', value: job.num_cpus },
    { label: 'Nodes', value: job.num_nodes },
    { label: 'GPUs', value: job.num_gpus || '—' },
    { label: 'Memory', value: formatBytes(job.memory_mb) },
    { label: 'Time Limit', value: formatSeconds(job.time_limit_seconds) },
    { label: 'Node List', value: job.node_list || '—' },
    { label: 'Working Dir', value: job.work_dir || '—' },
    { label: 'Submitted', value: formatTimeAgo(job.submit_time) },
    { label: 'Started', value: formatTimeAgo(job.start_time) },
    { label: 'Ended', value: job.end_time ? formatTimeAgo(job.end_time) : '—' },
    { label: 'Reason', value: job.state_reason || '—' },
  ]

  return (
    <div className="p-6 space-y-5 max-w-4xl">
      <div className="flex items-center gap-3">
        <Link to="/jobs" className="text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold">Job {job.job_id}</h1>
        <JobStateBadge state={job.state} />
        <button
          onClick={handleClone}
          className="ml-auto flex items-center gap-1 px-3 py-1.5 text-sm rounded-md bg-muted hover:bg-accent text-muted-foreground border border-border"
        >
          <Copy className="w-4 h-4" />
          Clone Job
        </button>
      </div>

      <JobActions jobId={job.job_id} state={job.state} />

      {/* Tabs */}
      <div className="border-b border-border flex gap-4">
        {(['info', 'log'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab === 'info' ? 'Details' : 'Output Log'}
          </button>
        ))}
      </div>

      {activeTab === 'info' && (
        <div className="space-y-4">
          {/* Live Resource Utilization (only for running jobs) */}
          {job.state === 'RUNNING' && stats && (
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Live Resource Utilization</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-muted-foreground mb-1">CPU Efficiency</div>
                  {stats.cpu_efficiency != null ? (
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{
                          width: `${Math.min(stats.cpu_efficiency, 100)}%`,
                          backgroundColor: stats.cpu_efficiency < 50 ? '#ef4444' : stats.cpu_efficiency < 75 ? '#eab308' : '#22c55e'
                        }} />
                      </div>
                      <span className={`text-sm font-medium ${stats.cpu_efficiency < 50 ? 'text-red-500' : stats.cpu_efficiency < 75 ? 'text-yellow-500' : 'text-green-500'}`}>
                        {stats.cpu_efficiency.toFixed(1)}%
                      </span>
                    </div>
                  ) : <span className="text-xs text-muted-foreground">N/A</span>}
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Memory (RSS)</div>
                  {stats.memory_rss_mb != null ? (
                    <div>
                      <span className="text-sm font-medium">{stats.memory_rss_mb >= 1024 ? `${(stats.memory_rss_mb / 1024).toFixed(1)} GB` : `${stats.memory_rss_mb} MB`}</span>
                      {job.memory_mb > 0 && <span className="text-xs text-muted-foreground"> / {formatBytes(job.memory_mb)}</span>}
                    </div>
                  ) : <span className="text-xs text-muted-foreground">N/A</span>}
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">GPU Utilization</div>
                  {stats.gpu_util_pct != null ? (
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div className="h-full rounded-full bg-blue-500" style={{ width: `${Math.min(stats.gpu_util_pct, 100)}%` }} />
                      </div>
                      <span className="text-sm font-medium">{stats.gpu_util_pct.toFixed(1)}%</span>
                    </div>
                  ) : <span className="text-xs text-muted-foreground">{job.num_gpus ? 'N/A' : 'No GPUs'}</span>}
                </div>
              </div>
            </div>
          )}
          <div className="grid grid-cols-2 gap-x-8 gap-y-2">
            {fields.map(({ label, value }) => (
              <div key={label} className="flex gap-2 py-1 border-b border-border/50 text-sm">
                <span className="text-muted-foreground w-32 shrink-0">{label}</span>
                <span className="font-mono break-all">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'log' && (
        <div>
          <p className="text-sm text-muted-foreground mb-2">
            Streaming from: <code className="font-mono">{job.std_out || 'unknown'}</code>
          </p>
          <LogViewer jobId={job.job_id} follow={['RUNNING', 'COMPLETING'].includes(job.state)} />
        </div>
      )}
    </div>
  )
}
