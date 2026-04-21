import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSubmitJob } from '@/api/jobs'
import { usePartitions } from '@/api/cluster'
import ScriptEditor from '@/components/submit/ScriptEditor'
import EnvVarEditor from '@/components/submit/EnvVarEditor'
import SubmitPreview from '@/components/submit/SubmitPreview'

const DEFAULT_SCRIPT = `#!/bin/bash
echo "Job started on $(hostname)"
echo "Date: $(date)"

# Your commands here
`

const STEPS = ['Resources', 'Script', 'Review']

export default function SubmitPage() {
  const navigate = useNavigate()
  const { data: partitionsData } = usePartitions()
  const submit = useSubmitJob()
  const [step, setStep] = useState(0)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [jobName, setJobName] = useState('my-job')
  const [partition, setPartition] = useState('')
  const [numNodes, setNumNodes] = useState(1)
  const [numTasks, setNumTasks] = useState(1)
  const [numCpus, setNumCpus] = useState(1)
  const [numGpus, setNumGpus] = useState(0)
  const [memoryMb, setMemoryMb] = useState(0)
  const [hours, setHours] = useState(1)
  const [minutes, setMinutes] = useState(0)
  const [account, setAccount] = useState('')
  const [qos, setQos] = useState('')
  const [scriptBody, setScriptBody] = useState(DEFAULT_SCRIPT)
  const [envVars, setEnvVars] = useState<Record<string, string>>({})

  const timeLimitSeconds = (hours * 3600) + (minutes * 60)
  const partitions = partitionsData?.data ?? []
  const selectedPartition = partitions.find((p) => p.name === partition)

  async function handleSubmit() {
    setError(null)
    try {
      const res = await submit.mutateAsync({
        job_name: jobName,
        partition,
        num_nodes: numNodes,
        num_tasks: numTasks,
        num_cpus_per_task: numCpus,
        num_gpus: numGpus,
        memory_mb: memoryMb,
        time_limit_seconds: timeLimitSeconds,
        account,
        qos,
        script_body: scriptBody,
        env_vars: envVars,
        std_out: '',
        std_err: '',
      })
      navigate(`/jobs/${res.data.job_id}`)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: { message?: string } | string } } })?.response?.data?.detail
      setError(typeof msg === 'string' ? msg : (msg as { message?: string })?.message ?? 'Submission failed')
    }
  }

  return (
    <div className="p-6 max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold">Submit Job</h1>

      {/* Step indicator */}
      <div className="flex items-center gap-0">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center">
            <button
              onClick={() => i < step && setStep(i)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                i === step
                  ? 'bg-primary text-primary-foreground'
                  : i < step
                  ? 'text-primary cursor-pointer hover:bg-accent'
                  : 'text-muted-foreground cursor-default'
              }`}
            >
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs border ${
                i === step ? 'border-primary-foreground bg-primary-foreground text-primary' :
                i < step ? 'border-primary text-primary' : 'border-muted-foreground text-muted-foreground'
              }`}>{i + 1}</span>
              {s}
            </button>
            {i < STEPS.length - 1 && <div className="w-8 h-px bg-border mx-1" />}
          </div>
        ))}
      </div>

      <div className="bg-card border border-border rounded-xl p-6">
        {step === 0 && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium block mb-1">Job Name</label>
              <input value={jobName} onChange={(e) => setJobName(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Partition</label>
              <select value={partition} onChange={(e) => setPartition(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm">
                <option value="">Select partition…</option>
                {partitions.map((p) => (
                  <option key={p.name} value={p.name}>{p.name} ({p.total_nodes} nodes)</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Nodes</label>
              <input type="number" min={1} value={numNodes} onChange={(e) => setNumNodes(+e.target.value)}
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Tasks</label>
              <input type="number" min={1} value={numTasks} onChange={(e) => setNumTasks(+e.target.value)}
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">CPUs per Task</label>
              <input type="number" min={1} value={numCpus} onChange={(e) => setNumCpus(+e.target.value)}
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
            </div>
            {selectedPartition?.has_gpus !== false && (
              <div>
                <label className="text-sm font-medium block mb-1">GPUs</label>
                <input type="number" min={0} value={numGpus} onChange={(e) => setNumGpus(+e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
              </div>
            )}
            <div>
              <label className="text-sm font-medium block mb-1">Memory (MB, 0=default)</label>
              <input type="number" min={0} step={256} value={memoryMb} onChange={(e) => setMemoryMb(+e.target.value)}
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Wall Time</label>
              <div className="flex gap-2">
                <input type="number" min={0} value={hours} onChange={(e) => setHours(+e.target.value)}
                  className="w-20 px-3 py-2 border border-border rounded bg-background text-sm" />
                <span className="text-muted-foreground self-center text-sm">h</span>
                <input type="number" min={0} max={59} value={minutes} onChange={(e) => setMinutes(+e.target.value)}
                  className="w-20 px-3 py-2 border border-border rounded bg-background text-sm" />
                <span className="text-muted-foreground self-center text-sm">m</span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Account</label>
              <input value={account} onChange={(e) => setAccount(e.target.value)}
                placeholder="optional"
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">QOS</label>
              <input value={qos} onChange={(e) => setQos(e.target.value)}
                placeholder="optional"
                className="w-full px-3 py-2 border border-border rounded bg-background text-sm" />
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Generated #SBATCH header</label>
                <span className="text-xs text-muted-foreground">Live preview</span>
              </div>
              <SubmitPreview params={{ jobName, partition, numNodes, numTasks, numCpusPerTask: numCpus,
                numGpus, memoryMb, timeLimitSeconds, account, qos }} />
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Script Body</label>
              <ScriptEditor value={scriptBody} onChange={setScriptBody} />
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Environment Variables</label>
              <EnvVarEditor vars={envVars} onChange={setEnvVars} />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-base font-semibold">Review & Submit</h3>
            <SubmitPreview params={{ jobName, partition, numNodes, numTasks, numCpusPerTask: numCpus,
              numGpus, memoryMb, timeLimitSeconds, account, qos }} />
            <div className="bg-gray-950 text-green-400 font-mono text-xs rounded-lg p-3">
              {scriptBody.split('\n').map((l, i) => <div key={i}>{l || '\u00A0'}</div>)}
            </div>
            {Object.keys(envVars).length > 0 && (
              <div className="text-sm">
                <div className="font-medium mb-1">Environment Variables</div>
                {Object.entries(envVars).map(([k, v]) => (
                  <div key={k} className="font-mono text-xs">{k}={v}</div>
                ))}
              </div>
            )}
            {error && <p className="text-sm text-red-500">{error}</p>}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setStep((s) => s - 1)}
          disabled={step === 0}
          className="px-4 py-2 text-sm border border-border rounded-md disabled:opacity-40 hover:bg-accent"
        >
          Previous
        </button>
        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep((s) => s + 1)}
            disabled={step === 0 && !partition}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md disabled:opacity-50 hover:opacity-90"
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submit.isPending}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-md disabled:opacity-50 hover:bg-green-700"
          >
            {submit.isPending ? 'Submitting…' : 'Submit Job'}
          </button>
        )}
      </div>
    </div>
  )
}
