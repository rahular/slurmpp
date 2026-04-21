import { useEffect, useRef } from 'react'
import { useSSE } from '@/hooks/useSSE'

interface Props {
  jobId: number
  follow?: boolean
}

export default function LogViewer({ jobId, follow = false }: Props) {
  const { lines, done } = useSSE(`/api/v1/jobs/${jobId}/output`, follow)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (follow) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [lines, follow])

  return (
    <div className="bg-gray-950 text-green-400 font-mono text-xs rounded-lg p-4 overflow-auto max-h-96 relative">
      {!lines.length && !done && (
        <div className="text-gray-500">Loading log output…</div>
      )}
      {lines.map((line, i) => (
        <div key={i} className="whitespace-pre-wrap leading-relaxed">{line || '\u00A0'}</div>
      ))}
      {done && lines.length === 0 && (
        <div className="text-gray-500">Log file not available or empty.</div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
