import { useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar } from 'recharts'
import { useUsageStats, useFairshare, useBurnRate, useEfficiency } from '@/api/analytics'
import { useAuthStore } from '@/stores/authStore'

const PERIODS = [7, 30, 90] as const

export default function AnalyticsPage() {
  const { username } = useAuthStore()
  const [days, setDays] = useState<number>(30)

  const { data: usageData } = useUsageStats(days)
  const { data: fairshareData } = useFairshare()
  const { data: burnRateData } = useBurnRate()
  const { data: effData } = useEfficiency(days)

  const usage = usageData?.data ?? []
  const fs = fairshareData?.data?.fairshare_factor
  const burnRate = burnRateData?.data
  const efficiency = effData?.data

  // Aggregate by date for chart
  const chartData = usage.reduce((acc: Record<string, { date: string; cpu_hours: number; gpu_hours: number }>, s: { date: string; cpu_hours: number; gpu_hours: number }) => {
    if (!acc[s.date]) acc[s.date] = { date: s.date, cpu_hours: 0, gpu_hours: 0 }
    acc[s.date].cpu_hours += s.cpu_hours
    acc[s.date].gpu_hours += s.gpu_hours
    return acc
  }, {})
  const sortedChart = (Object.values(chartData) as { date: string; cpu_hours: number; gpu_hours: number }[]).sort((a, b) => a.date.localeCompare(b.date))

  const fsPct = fs != null ? Math.round(fs * 100) : null
  const fsColor = fsPct == null ? '#6b7280' : fsPct < 25 ? '#ef4444' : fsPct < 50 ? '#f97316' : '#22c55e'

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Analytics — {username}</h1>
        <div className="flex gap-1">
          {PERIODS.map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                days === d ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-accent'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">CPU-hours / day</div>
          <div className="text-2xl font-bold">{burnRate?.cpu_hours_per_day ?? '—'}</div>
          <div className="text-xs text-muted-foreground mt-1">{days}d avg</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">GPU-hours / day</div>
          <div className="text-2xl font-bold">{burnRate?.gpu_hours_per_day ?? '—'}</div>
          <div className="text-xs text-muted-foreground mt-1">{days}d avg</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Avg CPU Efficiency</div>
          <div className="text-2xl font-bold">
            {efficiency?.avg_cpu_efficiency != null ? `${efficiency.avg_cpu_efficiency}%` : '—'}
          </div>
          <div className="text-xs text-muted-foreground mt-1">{efficiency?.total_jobs ?? 0} jobs</div>
        </div>
      </div>

      {/* Usage chart */}
      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="text-base font-semibold mb-4">CPU-hours Over Time</h2>
        {sortedChart.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={sortedChart}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="cpu_hours" stroke="#3b82f6" fill="#bfdbfe" name="CPU-hours" />
              {sortedChart.some((d) => d.gpu_hours > 0) && (
                <Area type="monotone" dataKey="gpu_hours" stroke="#8b5cf6" fill="#ddd6fe" name="GPU-hours" />
              )}
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-muted-foreground text-sm">No usage data for this period.</div>
        )}
      </div>

      {/* Fairshare + partition table */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="text-base font-semibold mb-4">Fairshare Factor</h2>
          {fsPct != null ? (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width={100} height={100}>
                <RadialBarChart innerRadius={30} outerRadius={50} data={[{ value: fsPct }]} startAngle={90} endAngle={-270}>
                  <RadialBar dataKey="value" fill={fsColor} background />
                </RadialBarChart>
              </ResponsiveContainer>
              <div>
                <div className="text-3xl font-bold" style={{ color: fsColor }}>{fsPct}%</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {fsPct < 25 ? 'Low — jobs will be deprioritized' :
                   fsPct < 50 ? 'Below average' : 'Good standing'}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-muted-foreground text-sm">Fairshare data unavailable.</div>
          )}
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="text-base font-semibold mb-3">By Partition</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-muted-foreground text-xs">
                <th className="text-left pb-2">Partition</th>
                <th className="text-right pb-2">CPU-h</th>
                <th className="text-right pb-2">Jobs</th>
                <th className="text-right pb-2">Eff %</th>
              </tr>
            </thead>
            <tbody>
              {(efficiency?.by_partition ?? []).map((p: { partition: string; cpu_hours: number; job_count: number; avg_efficiency: number }) => (
                <tr key={p.partition} className="border-t border-border/50">
                  <td className="py-1 font-mono">{p.partition}</td>
                  <td className="py-1 text-right">{p.cpu_hours}</td>
                  <td className="py-1 text-right">{p.job_count}</td>
                  <td className="py-1 text-right">{p.avg_efficiency}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
