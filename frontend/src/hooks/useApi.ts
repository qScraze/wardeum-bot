import { useState, useEffect, useCallback } from 'react'

export function useApi<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      setData(await fn())
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err?.response?.data?.detail ?? err?.message ?? 'Ошибка сети')
    } finally {
      setLoading(false)
    }
  }, deps)

  useEffect(() => { fetch() }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useMutation<TData, TVar = void>(fn: (vars: TVar) => Promise<TData>) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutate = async (vars: TVar): Promise<TData | null> => {
    try {
      setLoading(true)
      setError(null)
      return await fn(vars)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      const msg = err?.response?.data?.detail ?? err?.message ?? 'Ошибка'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }

  return { mutate, loading, error, clearError: () => setError(null) }
}
