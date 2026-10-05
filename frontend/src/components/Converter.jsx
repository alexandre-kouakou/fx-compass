import { useState } from 'react'
import { useApi } from '../api/useApi'
import { fmtDate, fmtRate } from '../utils/format'
import { Card, SourceBadge, Stat } from './ui'

export default function Converter({ base, quote }) {
  const [amount, setAmount] = useState('1000')
  const valid = Number(amount) > 0
  const { data, error, loading } = useApi('/convert', { base, quote, amount: valid ? amount : 1 })
  return (
    <Card title="Converter" insight={data?.insight} error={error} loading={loading}>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-ink-3">
          Amount in {base}
          <input
            type="number" min="0" inputMode="decimal" value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-36 rounded-lg border border-line bg-surface px-3 py-2 text-lg font-semibold text-ink"
          />
        </label>
        <div className="pb-1">
          <div className="text-xs text-ink-3">= {quote}</div>
          <div className="text-2xl font-semibold tabular-nums">
            {valid && data ? data.result.toLocaleString('en-US', { maximumFractionDigits: 2 }) : '–'}
          </div>
        </div>
      </div>
      {data && (
        <div className="mt-4 grid grid-cols-3 gap-3">
          <Stat label="Rate" value={<>{fmtRate(data.rate)}<SourceBadge source={data.source} /></>} sub={fmtDate(data.date)} />
          <Stat label="3-month avg" value={fmtRate(data.avg_3m)} />
          <Stat label="vs average" value={`${data.vs_avg_3m_pct >= 0 ? '+' : '−'}${Math.abs(data.vs_avg_3m_pct).toFixed(2)}%`} />
        </div>
      )}
    </Card>
  )
}
