import { Server, Cpu, Play, Clock } from 'lucide-react'
import type { ClusterOverview } from '@/api/cluster'

interface Props {
  overview: ClusterOverview
}

export default function ClusterStats({ overview }: Props) {
  const cards = [
    {
      label: 'Nodes Online',
      value: `${overview.total_nodes - overview.down_nodes} / ${overview.total_nodes}`,
      sub: `${overview.down_nodes} down`,
      icon: Server,
      color: 'text-green-500',
    },
    {
      label: 'CPU Utilization',
      value: overview.total_cpus > 0
        ? `${Math.round((overview.allocated_cpus / overview.total_cpus) * 100)}%`
        : '—',
      sub: `${overview.allocated_cpus} / ${overview.total_cpus} cores`,
      icon: Cpu,
      color: 'text-blue-500',
    },
    {
      label: 'Running Jobs',
      value: overview.running_jobs.toString(),
      sub: `${overview.completing_jobs} completing`,
      icon: Play,
      color: 'text-green-500',
    },
    {
      label: 'Pending Jobs',
      value: overview.pending_jobs.toString(),
      sub: 'waiting in queue',
      icon: Clock,
      color: 'text-yellow-500',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">{card.label}</span>
            <card.icon className={`w-4 h-4 ${card.color}`} />
          </div>
          <div className="text-2xl font-bold">{card.value}</div>
          <div className="text-xs text-muted-foreground mt-1">{card.sub}</div>
        </div>
      ))}
    </div>
  )
}
