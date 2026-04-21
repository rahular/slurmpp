import { useState, useEffect } from 'react'
import { useAdminUsers, useAdminHeatmap } from '@/api/admin'
import { api } from '@/api/client'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

function LowEfficiencyPanel() {
  const { data: jobsData } = useQuery({
    queryKey: ['admin', 'running-jobs'],
    queryFn: () => api.get('/api/v1/jobs?state=RUNNING&page_size=50').then((r) => r.data),
    refetchInterval: 30_000,
  })
  const { data: statsCache, refetch: refetchStats } = useQuery({
    queryKey: ['admin', 'job-stats-batch'],
    queryFn: async () => {
      const jobs = jobsData?.data ?? []
      const results: Record<number, { cpu_efficiency: number | null; memory_rss_mb: number | null; gpu_util_pct: number | null }> = {}
      await Promise.all(jobs.slice(0, 10).map(async (j: { job_id: number }) => {
        try {
          const r = await api.get(`/api/v1/jobs/${j.job_id}/stats`)
          results[j.job_id] = r.data.data
        } catch { /* ignore */ }
      }))
      return results
    },
    enabled: (jobsData?.data?.length ?? 0) > 0,
    refetchInterval: 30_000,
  })

  const jobs = jobsData?.data ?? []

  if (!jobs.length) return <div className="text-sm text-muted-foreground">No running jobs.</div>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted-foreground text-xs border-b border-border">
            <th className="text-left pb-2">Job</th>
            <th className="text-left pb-2">User</th>
            <th className="text-left pb-2">Partition</th>
            <th className="text-right pb-2">CPUs</th>
            <th className="text-right pb-2">CPU Eff.</th>
            <th className="text-right pb-2">Mem RSS</th>
            <th className="text-right pb-2">GPU</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((j: { job_id: number; name: string; user: string; partition: string; num_cpus: number; memory_mb: number; num_gpus: number }) => {
            const s = statsCache?.[j.job_id]
            const isLowEff = s?.cpu_efficiency != null && s.cpu_efficiency < 50
            return (
              <tr key={j.job_id} className={`border-t border-border/50 hover:bg-accent/30 ${isLowEff ? 'bg-red-500/5' : ''}`}>
                <td className="py-1.5">
                  <Link to={`/jobs/${j.job_id}`} className="font-mono text-primary hover:underline">{j.job_id}</Link>
                  <span className="text-muted-foreground ml-1 text-xs">{j.name}</span>
                </td>
                <td className="py-1.5 font-mono">{j.user}</td>
                <td className="py-1.5">{j.partition}</td>
                <td className="py-1.5 text-right">{j.num_cpus}</td>
                <td className="py-1.5 text-right">
                  {s?.cpu_efficiency != null
                    ? <span className={`font-medium ${s.cpu_efficiency < 50 ? 'text-red-500' : s.cpu_efficiency < 75 ? 'text-yellow-500' : 'text-green-500'}`}>
                        {isLowEff && '⚠ '}{s.cpu_efficiency.toFixed(1)}%
                      </span>
                    : <span className="text-muted-foreground text-xs">—</span>}
                </td>
                <td className="py-1.5 text-right text-xs">
                  {s?.memory_rss_mb != null ? `${s.memory_rss_mb >= 1024 ? (s.memory_rss_mb / 1024).toFixed(1) + ' GB' : s.memory_rss_mb + ' MB'}` : '—'}
                </td>
                <td className="py-1.5 text-right text-xs">
                  {s?.gpu_util_pct != null ? `${s.gpu_util_pct.toFixed(0)}%` : j.num_gpus ? '—' : 'N/A'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

interface ManagedUser {
  username: string
  role: string
}

export default function AdminPage() {
  const [days, setDays] = useState(30)
  const { data: usersData } = useAdminUsers(days)
  const { data: heatmapData } = useAdminHeatmap(Math.min(days, 30))

  const users = usersData?.data ?? []
  const heatmap: Record<string, Record<string, number>> = heatmapData?.data ?? {}

  // User management state
  const [managedUsers, setManagedUsers] = useState<ManagedUser[]>([])
  const [newUsername, setNewUsername] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newRole, setNewRole] = useState('user')
  const [userMgmtError, setUserMgmtError] = useState<string | null>(null)
  const [userMgmtLoading, setUserMgmtLoading] = useState(false)

  const fetchUsers = async () => {
    try {
      const res = await api.get('/api/v1/admin/list-users')
      setManagedUsers(res.data.data)
    } catch {
      // silently fail
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setUserMgmtError(null)
    setUserMgmtLoading(true)
    try {
      await api.post('/api/v1/admin/users', { username: newUsername, password: newPassword, role: newRole })
      setNewUsername('')
      setNewPassword('')
      setNewRole('user')
      await fetchUsers()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setUserMgmtError(detail ?? 'Failed to create user')
    } finally {
      setUserMgmtLoading(false)
    }
  }

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`Delete user "${username}"?`)) return
    try {
      await api.delete(`/api/v1/admin/users/${username}`)
      await fetchUsers()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      alert(detail ?? 'Failed to delete user')
    }
  }

  // Build ordered list of dates and hours
  const dates = Object.keys(heatmap).sort().slice(-14) // last 14 days
  const hours = Array.from({ length: 24 }, (_, i) => i)

  function getColor(pct: number) {
    const opacity = Math.min(pct / 100, 1)
    return `rgba(59, 130, 246, ${opacity})`
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <div className="flex gap-1">
          {[7, 30, 90].map((d) => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1 text-sm rounded-md ${days === d ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-accent'}`}>
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* Utilization Heatmap */}
      <div className="bg-card border border-border rounded-lg p-5 overflow-x-auto">
        <h2 className="text-base font-semibold mb-4">Cluster Utilization (last 14 days, by hour)</h2>
        {dates.length > 0 ? (
          <div className="text-xs">
            <div className="flex gap-1 mb-1">
              <div className="w-20" />
              {hours.filter((h) => h % 4 === 0).map((h) => (
                <div key={h} className="w-5 text-muted-foreground">{h}h</div>
              ))}
            </div>
            {dates.map((date) => (
              <div key={date} className="flex gap-1 mb-0.5 items-center">
                <div className="w-20 text-muted-foreground shrink-0">{date.slice(5)}</div>
                {hours.map((h) => {
                  const pct = heatmap[date]?.[h] ?? 0
                  return (
                    <div key={h} className="w-5 h-4 rounded-sm" style={{ backgroundColor: getColor(pct) }}
                      title={`${date} ${h}:00 — ${pct.toFixed(0)}%`} />
                  )
                })}
              </div>
            ))}
            <div className="flex items-center gap-2 mt-3">
              <span className="text-muted-foreground">0%</span>
              <div className="flex gap-0.5">
                {[0, 25, 50, 75, 100].map((p) => (
                  <div key={p} className="w-5 h-3 rounded-sm" style={{ backgroundColor: getColor(p) }} />
                ))}
              </div>
              <span className="text-muted-foreground">100%</span>
            </div>
          </div>
        ) : (
          <div className="text-muted-foreground text-sm">No utilization data available.</div>
        )}
      </div>

      {/* User Usage Table */}
      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="text-base font-semibold mb-3">User Usage ({days} days)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-muted-foreground text-xs border-b border-border">
                <th className="text-left pb-2">User</th>
                <th className="text-right pb-2">Jobs</th>
                <th className="text-right pb-2">CPU-hours</th>
                <th className="text-right pb-2">GPU-hours</th>
                <th className="text-right pb-2">Avg Efficiency</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: { user: string; job_count: number; cpu_hours: number; gpu_hours: number; avg_efficiency: number }) => (
                <tr key={u.user} className="border-t border-border/50 hover:bg-accent/30">
                  <td className="py-1.5 font-mono">{u.user}</td>
                  <td className="py-1.5 text-right">{u.job_count}</td>
                  <td className="py-1.5 text-right">{u.cpu_hours.toFixed(1)}</td>
                  <td className="py-1.5 text-right">{u.gpu_hours.toFixed(1)}</td>
                  <td className="py-1.5 text-right">
                    <span className={`inline-flex items-center gap-1 ${u.avg_efficiency < 50 ? 'text-red-500' : u.avg_efficiency < 75 ? 'text-yellow-500' : 'text-green-500'}`}>
                      {u.avg_efficiency < 50 && (
                        <span className="px-1 py-0.5 text-xs bg-red-500/10 border border-red-500/30 rounded text-red-500">low</span>
                      )}
                      {u.avg_efficiency.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
              {!users.length && (
                <tr><td colSpan={5} className="text-center py-6 text-muted-foreground">No data.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Low-Efficiency Running Jobs */}
      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="text-base font-semibold mb-1">Running Jobs — Resource Efficiency</h2>
        <p className="text-xs text-muted-foreground mb-3">Live CPU/memory utilization for all running jobs. Users below 50% efficiency are flagged.</p>
        <LowEfficiencyPanel />
      </div>

      {/* User Management */}
      <div className="bg-card border border-border rounded-lg p-5 space-y-4">
        <h2 className="text-base font-semibold">Manage Users</h2>

        {/* Create User Form */}
        <form onSubmit={handleCreateUser} className="flex flex-wrap gap-2 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Username</label>
            <input
              type="text"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              required
              placeholder="username"
              className="px-2 py-1.5 text-sm rounded-md border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary w-36"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              placeholder="password"
              className="px-2 py-1.5 text-sm rounded-md border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary w-36"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Role</label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="px-2 py-1.5 text-sm rounded-md border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={userMgmtLoading}
            className="px-3 py-1.5 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            Add User
          </button>
          {userMgmtError && <span className="text-xs text-red-500">{userMgmtError}</span>}
        </form>

        {/* User List */}
        <table className="w-full text-sm">
          <thead>
            <tr className="text-muted-foreground text-xs border-b border-border">
              <th className="text-left pb-2">Username</th>
              <th className="text-left pb-2">Role</th>
              <th className="text-right pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {managedUsers.map((u) => (
              <tr key={u.username} className="border-t border-border/50 hover:bg-accent/30">
                <td className="py-1.5 font-mono">{u.username}</td>
                <td className="py-1.5">
                  <span className={`px-1.5 py-0.5 text-xs rounded ${u.role === 'admin' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                    {u.role}
                  </span>
                </td>
                <td className="py-1.5 text-right">
                  <button
                    onClick={() => handleDeleteUser(u.username)}
                    className="text-xs px-2 py-1 rounded text-red-500 hover:bg-red-500/10 border border-red-500/30"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {!managedUsers.length && (
              <tr><td colSpan={3} className="text-center py-4 text-muted-foreground text-sm">No users found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
