// The only place that talks to the network – and only to our own Django API.
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

async function request(path, { params, method = 'GET', body } = {}) {
  const url = new URL(API + path)
  Object.entries(params || {}).forEach(([k, v]) => url.searchParams.set(k, v))
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = Object.values(data).flat().join(' ') || `Request failed (${res.status})`
    throw new Error(msg)
  }
  return data
}

export const api = {
  get: (path, params) => request(path, { params }),
  post: (path, body, params) => request(path, { method: 'POST', body, params }),
  del: (path, params) => request(path, { method: 'DELETE', params }),
}

// Anonymous id so alerts survive a page reload without logins.
export function clientId() {
  try {
    let id = localStorage.getItem('fx-client-id')
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem('fx-client-id', id)
    }
    return id
  } catch {
    return 'session-' + (window.__fxId ||= Math.random().toString(36).slice(2, 12))
  }
}
