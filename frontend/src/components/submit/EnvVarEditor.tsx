import { Plus, Trash2 } from 'lucide-react'

interface Props {
  vars: Record<string, string>
  onChange: (vars: Record<string, string>) => void
}

export default function EnvVarEditor({ vars, onChange }: Props) {
  const entries = Object.entries(vars)

  function update(index: number, key: string, val: string) {
    const newEntries = [...entries]
    newEntries[index] = [key, val]
    onChange(Object.fromEntries(newEntries))
  }

  function remove(index: number) {
    const newEntries = entries.filter((_, i) => i !== index)
    onChange(Object.fromEntries(newEntries))
  }

  function add() {
    onChange({ ...vars, '': '' })
  }

  return (
    <div className="space-y-2">
      {entries.map(([k, v], i) => (
        <div key={i} className="flex gap-2 items-center">
          <input
            value={k}
            onChange={(e) => update(i, e.target.value, v)}
            placeholder="KEY"
            className="flex-1 px-2 py-1.5 text-sm border border-border rounded bg-background font-mono"
          />
          <span className="text-muted-foreground">=</span>
          <input
            value={v}
            onChange={(e) => update(i, k, e.target.value)}
            placeholder="value"
            className="flex-1 px-2 py-1.5 text-sm border border-border rounded bg-background font-mono"
          />
          <button
            type="button"
            onClick={() => remove(i)}
            className="p-1 text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="flex items-center gap-1 text-sm text-primary hover:underline"
      >
        <Plus className="w-4 h-4" />
        Add variable
      </button>
    </div>
  )
}
