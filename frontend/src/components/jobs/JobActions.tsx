import { useCancelJob, useHoldJob, useRequeueJob, useSignalJob } from '@/api/jobs'
import { useState } from 'react'

interface Props {
  jobId: number
  state: string
}

export default function JobActions({ jobId, state }: Props) {
  const cancel = useCancelJob()
  const hold = useHoldJob()
  const requeue = useRequeueJob()
  const signal = useSignalJob()
  const [signalVal, setSignalVal] = useState('SIGUSR1')

  const isActive = ['RUNNING', 'COMPLETING'].includes(state)
  const isPending = state === 'PENDING'

  return (
    <div className="flex flex-wrap gap-2">
      {(isActive || isPending) && (
        <button
          onClick={() => cancel.mutate(jobId)}
          disabled={cancel.isPending}
          className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
        >
          {cancel.isPending ? 'Cancelling…' : 'Cancel'}
        </button>
      )}
      {isPending && (
        <>
          <button
            onClick={() => hold.mutate(jobId)}
            disabled={hold.isPending}
            className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
          >
            Hold
          </button>
          <button
            onClick={() => requeue.mutate(jobId)}
            disabled={requeue.isPending}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Requeue
          </button>
        </>
      )}
      {isActive && (
        <div className="flex items-center gap-1">
          <select
            value={signalVal}
            onChange={(e) => setSignalVal(e.target.value)}
            className="text-sm border border-border rounded px-2 py-1.5 bg-background"
          >
            {['SIGUSR1', 'SIGUSR2', 'SIGTERM', 'SIGINT', 'SIGCONT', 'SIGSTOP'].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button
            onClick={() => signal.mutate({ jobId, signal: signalVal })}
            disabled={signal.isPending}
            className="px-3 py-1.5 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
          >
            Send Signal
          </button>
        </div>
      )}
    </div>
  )
}
