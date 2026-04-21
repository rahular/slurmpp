import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { formatDistanceToNow, formatDuration, intervalToDuration } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatSeconds(seconds: number | null | undefined): string {
  if (!seconds) return '—'
  const duration = intervalToDuration({ start: 0, end: seconds * 1000 })
  return formatDuration(duration, { format: ['days', 'hours', 'minutes'] }) || '0 minutes'
}

export function formatBytes(mb: number | null | undefined): string {
  if (!mb) return '—'
  if (mb >= 1024 * 1024) return `${(mb / (1024 * 1024)).toFixed(1)} TB`
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
}

export function formatTimeAgo(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true })
  } catch {
    return '—'
  }
}

export const JOB_STATE_COLORS: Record<string, string> = {
  RUNNING: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  PENDING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  COMPLETING: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  COMPLETED: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  FAILED: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  CANCELLED: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  TIMEOUT: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  NODE_FAIL: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  OUT_OF_MEMORY: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
}

export const NODE_STATE_COLORS: Record<string, string> = {
  idle: '#22c55e',      // green
  allocated: '#f97316', // orange
  mixed: '#eab308',     // yellow
  down: '#ef4444',      // red
  drain: '#a855f7',     // purple
  draining: '#a855f7',
  error: '#ef4444',
  unknown: '#6b7280',   // gray
}

export function getNodeColor(state: string): string {
  const lower = state.toLowerCase()
  for (const [key, color] of Object.entries(NODE_STATE_COLORS)) {
    if (lower.includes(key)) return color
  }
  return NODE_STATE_COLORS.unknown
}
