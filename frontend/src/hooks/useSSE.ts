import { useEffect, useRef, useState } from 'react'
import { useAuthStore } from '@/stores/authStore'

export function useSSE(url: string | null, follow = false) {
  const [lines, setLines] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!url) return
    setLines([])
    setError(null)
    setDone(false)

    const token = useAuthStore.getState().accessToken
    const fullUrl = `${url}?follow=${follow}${token ? `&token=${encodeURIComponent(token)}` : ''}`

    // Note: EventSource doesn't support custom headers; token sent as query param
    // Backend should accept token query param as fallback (future enhancement)
    const es = new EventSource(fullUrl)
    esRef.current = es

    es.onmessage = (e) => {
      setLines((prev) => [...prev, e.data])
    }

    es.onerror = () => {
      setDone(true)
      es.close()
    }

    return () => {
      es.close()
      esRef.current = null
    }
  }, [url, follow])

  return { lines, error, done }
}
