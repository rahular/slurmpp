import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { useNavigate } from 'react-router-dom'
import type { Job } from '@/api/jobs'
import JobStateBadge from './JobStateBadge'
import { formatSeconds, formatTimeAgo } from '@/lib/utils'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const col = createColumnHelper<Job>()

const columns = [
  col.accessor('job_id', { header: 'Job ID', cell: (i) => <span className="font-mono">{i.getValue()}</span> }),
  col.accessor('name', { header: 'Name', cell: (i) => <span className="max-w-[160px] truncate block">{i.getValue() || '—'}</span> }),
  col.accessor('state', { header: 'State', cell: (i) => <JobStateBadge state={i.getValue()} /> }),
  col.accessor('user', { header: 'User' }),
  col.accessor('partition', { header: 'Partition' }),
  col.accessor('num_cpus', { header: 'CPUs' }),
  col.accessor('num_nodes', { header: 'Nodes' }),
  col.accessor('submit_time', { header: 'Submitted', cell: (i) => formatTimeAgo(i.getValue()) }),
  col.accessor('start_time', { header: 'Started', cell: (i) => formatTimeAgo(i.getValue()) }),
  col.accessor('time_limit_seconds', { header: 'Time Limit', cell: (i) => formatSeconds(i.getValue()) }),
]

interface Props {
  data: Job[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function JobsTable({ data, total, page, pageSize, totalPages, onPageChange }: Props) {
  const navigate = useNavigate()
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((h) => (
                  <th key={h.id} className="px-3 py-2 text-left font-medium text-muted-foreground whitespace-nowrap">
                    {flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-t border-border hover:bg-accent/40 cursor-pointer"
                onClick={() => navigate(`/jobs/${row.original.job_id}`)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
            {!data.length && (
              <tr>
                <td colSpan={columns.length} className="text-center py-8 text-muted-foreground">
                  No jobs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-3 text-sm text-muted-foreground">
        <span>{total} total jobs</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="p-1 rounded hover:bg-accent disabled:opacity-40"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span>Page {page} of {totalPages || 1}</span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="p-1 rounded hover:bg-accent disabled:opacity-40"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
