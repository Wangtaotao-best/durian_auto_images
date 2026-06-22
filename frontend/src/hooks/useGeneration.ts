import { useState, useCallback, useRef } from 'react'
import { generateAndWait } from '@/api/client'
import type { GenerateRequest, TaskStatus } from '@/api/types'

export function useGeneration() {
  const [status, setStatus] = useState<TaskStatus | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const start = useCallback(async (req: GenerateRequest) => {
    setError(null)
    setStatus(null)
    setIsRunning(true)
    abortRef.current = new AbortController()
    try {
      const final = await generateAndWait(
        req,
        (s) => setStatus(s),
        abortRef.current.signal,
      )
      if (final.status === 'failed') setError(final.error || '未知错误')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(msg)
    } finally {
      setIsRunning(false)
    }
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setIsRunning(false)
  }, [])

  const reset = useCallback(() => {
    setStatus(null)
    setError(null)
  }, [])

  return { status, isRunning, error, start, cancel, reset }
}
