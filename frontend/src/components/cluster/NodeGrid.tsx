import { useState } from 'react'
import type { NodeInfo } from '@/api/cluster'

interface Props {
  nodes: NodeInfo[]
}

function getNodeDisplayColor(node: NodeInfo): string {
  const lower = node.state.toLowerCase()
  if (lower.includes('down') || lower.includes('error')) return '#ef4444'
  if (lower.includes('drain')) return '#a855f7'
  if (lower.includes('idle')) return '#22c55e'
  // For allocated/mix nodes, use utilization ratio
  if (node.cpus_total > 0) {
    const ratio = node.cpus_allocated / node.cpus_total
    if (ratio >= 0.9) return '#f97316'       // orange - mostly full
    if (ratio >= 0.5) return '#eab308'       // yellow - partial
    if (ratio > 0) return '#84cc16'          // lime green - lightly used
  }
  if (lower.includes('alloc') || lower.includes('mix')) return '#f97316'
  return '#6b7280'
}

export default function NodeGrid({ nodes }: Props) {
  const [hovered, setHovered] = useState<NodeInfo | null>(null)

  if (!nodes.length) return (
    <div className="text-muted-foreground text-sm">No node data available.</div>
  )

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-1">
        {nodes.map((node) => (
          <div
            key={node.name}
            className="w-5 h-5 rounded-sm cursor-pointer transition-transform hover:scale-125"
            style={{ backgroundColor: getNodeDisplayColor(node) }}
            title={`${node.name} — ${node.state} (${node.cpus_allocated}/${node.cpus_total} CPUs)`}
            onMouseEnter={() => setHovered(node)}
            onMouseLeave={() => setHovered(null)}
          />
        ))}
      </div>
      {hovered && (
        <div className="mt-3 p-3 bg-card border border-border rounded-md text-sm max-w-xs">
          <div className="font-medium">{hovered.name}</div>
          <div className="text-muted-foreground">State: {hovered.state}</div>
          {hovered.reason && <div className="text-muted-foreground">Reason: {hovered.reason}</div>}
          <div className="text-muted-foreground">CPUs: {hovered.cpus_allocated}/{hovered.cpus_total}</div>
          {hovered.gpus_total > 0 && (
            <div className="text-muted-foreground">GPUs: {hovered.gpus_allocated}/{hovered.gpus_total}</div>
          )}
          <div className="text-muted-foreground">Partitions: {hovered.partitions.join(', ') || '—'}</div>
        </div>
      )}
      {/* Legend */}
      <div className="flex gap-4 mt-3 flex-wrap">
        {[
          { label: 'idle', color: '#22c55e' },
          { label: 'light use (<50%)', color: '#84cc16' },
          { label: 'partial (50-90%)', color: '#eab308' },
          { label: 'full (>90%)', color: '#f97316' },
          { label: 'down', color: '#ef4444' },
          { label: 'drain', color: '#a855f7' },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1 text-xs text-muted-foreground">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}
