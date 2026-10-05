import { useEffect, useState } from 'react'
import { api, clientId } from '../api/client'
import { useApi } from '../api/useApi'
import { fmtDate, fmtRate } from '../utils/format'
import { Card } from './ui'

export default function Alerts({ base, quote }) {
  const cid = clientId()
  const { data, error, loading, reload } = useApi('/alerts', { client_id: cid })
  const current = data?.current_rates?.[`${base}/${quote}`]
  const [direction, setDirection] = useState('above')
  const [threshold, setThreshold] = useState('')
  const [formError, setFormError] = useState(null)

  // Prefill with the latest rate for the selected pair.
  const { data: conv } = useApi('/convert', { base, quote, amount: 1 })
  useEffect(() => {
    if (conv) setThreshold(fmtRate(conv.rate).replace(/,/g, ''))
  }, [conv])

  async function add(e) {
    e.preventDefault()
    setFormError(null)
    try {
      await api.post('/alerts', { client_id: cid, base, quote, direction, threshold: Number(threshold) })
      reload()
    } catch (err) {
      setFormError(err.message)
    }
  }

  async function remove(id) {
    await api.del(`/alerts/${id}`, { client_id: cid })
    reload()
  }

  return (
    <Card title="Rate alerts" insight={data?.insight} error={error} loading={loading}>
      <form onSubmit={add} className="flex flex-wrap items-end gap-2 text-sm">
        <span className="pb-2 text-ink-2">Tell me when 1 {base} is</span>
        <select value={direction} onChange={(e) => setDirection(e.target.value)}
          className="rounded-lg border border-line bg-surface px-2 py-2">
          <option value="above">above</option>
          <option value="below">below</option>
        </select>
        <input type="number" step="any" min="0" required value={threshold} onChange={(e) => setThreshold(e.target.value)}
          className="w-28 rounded-lg border border-line bg-surface px-2 py-2" aria-label="Threshold" />
        <span className="pb-2 text-ink-2">{quote}</span>
        <button className="rounded-lg bg-ink px-3 py-2 font-medium text-surface">Add alert</button>
      </form>
      {formError && <p className="mt-2 text-xs text-ink-2">{formError}</p>}
      {current != null && <p className="mt-2 text-xs text-ink-3">Latest daily rate: {fmtRate(current)} {quote}</p>}
      <ul className="mt-4 divide-y divide-line">
        {data?.alerts.map((a) => (
          <li key={a.id} className="flex items-center justify-between gap-2 py-2 text-sm">
            <span>
              <span aria-hidden style={{ color: a.triggered_at ? 'var(--warning)' : 'var(--ink-3)' }}>
                {a.triggered_at ? '▲' : '○'}
              </span>{' '}
              1 {a.base} {a.direction} {fmtRate(a.threshold)} {a.quote}
              <span className="block pl-4 text-xs text-ink-3">
                {a.triggered_at
                  ? `Triggered: ${fmtRate(a.triggered_rate)} on ${fmtDate(a.triggered_on)}`
                  : 'Waiting – checked against each new daily rate'}
              </span>
            </span>
            <button onClick={() => remove(a.id)} className="text-xs text-ink-3 hover:text-ink" aria-label="Delete alert">
              Remove
            </button>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] text-ink-3">Alerts are stored for this browser only and shown here when you open the dashboard.</p>
    </Card>
  )
}
