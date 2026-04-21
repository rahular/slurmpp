import ClusterStats from '@/components/cluster/ClusterStats'
import NodeGrid from '@/components/cluster/NodeGrid'
import { useClusterOverview, useNodes } from '@/api/cluster'
import { RefreshCw } from 'lucide-react'

export default function DashboardPage() {
  const { data: overview, isLoading: ovLoading, dataUpdatedAt } = useClusterOverview()
  const { data: nodesData, isLoading: nodesLoading } = useNodes()

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Cluster Dashboard</h1>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className="w-3 h-3" />
          {dataUpdatedAt ? `Updated ${new Date(dataUpdatedAt).toLocaleTimeString()}` : 'Loading…'}
        </div>
      </div>

      {ovLoading ? (
        <div className="text-muted-foreground">Loading cluster overview…</div>
      ) : overview ? (
        <ClusterStats overview={overview} />
      ) : null}

      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="text-base font-semibold mb-4">Node Status</h2>
        {nodesLoading ? (
          <div className="text-muted-foreground text-sm">Loading nodes…</div>
        ) : (
          <NodeGrid nodes={nodesData?.data ?? []} />
        )}
      </div>
    </div>
  )
}
