import { useState } from 'react'
import { useAdminUsers, useAdminHeatmap } from '@/api/admin'

export default function AdminPage() {
  const [days, setDays] = useState(30)
  const { data: usersData } = useAdminUsers(days)
  const { data: heatmapData } = useAdminHeatmap(Math.min(days, 30))

  const users = usersData?.data ?? []
  const heatmap: Record<string, Record<string, number>> = heatmapData?.data ?? {}

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
                    <span className={u.avg_efficiency < 50 ? 'text-red-500' : u.avg_efficiency < 75 ? 'text-yellow-500' : 'text-green-500'}>
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
    </div>
  )
}
