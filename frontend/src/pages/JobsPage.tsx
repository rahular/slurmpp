import { useState } from 'react'
import { useJobs } from '@/api/jobs'
import JobsTable from '@/components/jobs/JobsTable'
import { useAuthStore } from '@/stores/authStore'
import { Search } from 'lucide-react'

const STATES = ['', 'RUNNING', 'PENDING', 'COMPLETING', 'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT']

export default function JobsPage() {
  const { role, username } = useAuthStore()
  const [state, setState] = useState('')
  const [userFilter, setUserFilter] = useState(role === 'admin' ? '' : (username ?? ''))
  const [partition, setPartition] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useJobs({
    state: state || undefined,
    user: userFilter || undefined,
    partition: partition || undefined,
    page,
    page_size: 50,
  })

  return (
    <div className="p-6 space-y-4 max-w-7xl">
      <h1 className="text-2xl font-bold">Jobs</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">State</label>
          <select
            value={state}
            onChange={(e) => { setState(e.target.value); setPage(1) }}
            className="text-sm border border-border rounded px-2 py-1.5 bg-background"
          >
            {STATES.map((s) => (
              <option key={s} value={s}>{s || 'All states'}</option>
            ))}
          </select>
        </div>

        {role === 'admin' && (
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">User</label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                value={userFilter}
                onChange={(e) => { setUserFilter(e.target.value); setPage(1) }}
                placeholder="all users"
                className="text-sm border border-border rounded pl-6 pr-2 py-1.5 bg-background w-32"
              />
            </div>
          </div>
        )}

        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Partition</label>
          <input
            value={partition}
            onChange={(e) => { setPartition(e.target.value); setPage(1) }}
            placeholder="all"
            className="text-sm border border-border rounded px-2 py-1.5 bg-background w-28"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-muted-foreground text-sm">Loading jobs…</div>
      ) : (
        <JobsTable
          data={data?.data ?? []}
          total={data?.meta.total ?? 0}
          page={page}
          pageSize={50}
          totalPages={data?.meta.total_pages ?? 1}
          onPageChange={setPage}
        />
      )}
    </div>
  )
}
