import { useCallback, useEffect, useState } from 'react'
import { api } from './client'

/** GET `path` with `params`; refetches when params change. */
export function useApi(path, params) {
  const key = JSON.stringify(params)
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    api
      .get(path, JSON.parse(key))
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState({ data: null, error, loading: false }))
    return () => {
      alive = false
    }
  }, [path, key, nonce])

  const reload = useCallback(() => setNonce((n) => n + 1), [])
  return { ...state, reload }
}
