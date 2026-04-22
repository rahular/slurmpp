interface ResourceParams {
  jobName: string
  partition: string
  numNodes: number
  numTasks: number
  numCpusPerTask: number
  numGpus: number
  memoryMb: number
  timeLimitSeconds: number
  account: string
  qos: string
}

function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export default function SubmitPreview({ params }: { params: ResourceParams }) {
  const lines = [
    `#!/bin/bash`,
    `#SBATCH --job-name=${params.jobName || 'job'}`,
    `#SBATCH --partition=${params.partition || '<partition>'}`,
    `#SBATCH --nodes=${params.numNodes}`,
    `#SBATCH --ntasks=${params.numTasks}`,
    `#SBATCH --cpus-per-task=${params.numCpusPerTask}`,
    params.memoryMb > 0 ? `#SBATCH --mem=${params.memoryMb}M` : null,
    `#SBATCH --time=${formatTime(params.timeLimitSeconds)}`,
    params.account ? `#SBATCH --account=${params.account}` : null,
    params.qos ? `#SBATCH --qos=${params.qos}` : null,
    params.numGpus > 0 ? `#SBATCH --gres=gpu:${params.numGpus}` : null,
  ].filter(Boolean)

  return (
    <div className="bg-gray-950 text-green-400 font-mono text-xs rounded-lg p-3 overflow-x-auto">
      {lines.map((line, i) => (
        <div key={i} className={line?.startsWith('#SBATCH') ? 'text-blue-400' : 'text-green-400'}>
          {line}
        </div>
      ))}
    </div>
  )
}
