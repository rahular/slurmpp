import { cn, JOB_STATE_COLORS } from '@/lib/utils'

interface Props {
  state: string
}

export default function JobStateBadge({ state }: Props) {
  const cls = JOB_STATE_COLORS[state] ?? 'bg-gray-100 text-gray-700'
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', cls)}>
      {state}
    </span>
  )
}
