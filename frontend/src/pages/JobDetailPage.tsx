import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useJob } from '@/api/jobs'
import JobStateBadge from '@/components/jobs/JobStateBadge'
import JobActions from '@/components/jobs/JobActions'
import LogViewer from '@/components/jobs/LogViewer'
import { formatSeconds, formatTimeAgo, formatBytes } from '@/lib/utils'
import { ArrowLeft } from 'lucide-react'

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const id = parseInt(jobId ?? '0')
  const { data, isLoading } = useJob(id)
  const [activeTab, setActiveTab] = useState<'log' | 'info'>('info')

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (!data?.data) return <div className="p-6 text-muted-foreground">Job not found.</div>

  const job = data.data

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
        <div className="grid grid-cols-2 gap-x-8 gap-y-2">
          {fields.map(({ label, value }) => (
            <div key={label} className="flex gap-2 py-1 border-b border-border/50 text-sm">
              <span className="text-muted-foreground w-32 shrink-0">{label}</span>
              <span className="font-mono break-all">{String(value)}</span>
            </div>
          ))}
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
