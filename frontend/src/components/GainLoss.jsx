import { useState } from 'react'
import { Bar } from 'react-chartjs-2'
import { useApi } from '../api/useApi'
import { cssVar, fmtMoney } from '../utils/format'
import { baseOptions } from './chartSetup'
import { Card, Stat, Tabs } from './ui'

const RANGES = ['1W', '1M', '6M', '1Y']

export default function GainLoss({ base, quote }) {
  const [range, setRange] = useState('1M')
  const [amount, setAmount] = useState('10000')
  const valid = Number(amount) > 0
  const { data, error, loading } = useApi('/gain-loss', { base, quote, range, amount: valid ? amount : 1 })
  const points = data?.points.slice(1) || [] // first day has no previous day
  const up = cssVar('--up')
  const down = cssVar('--down')
  const options = baseOptions({ yFormat: (v) => v.toLocaleString('en-US', { maximumFractionDigits: 0 }) })
  options.plugins.tooltip.callbacks.label = (c) => ` Daily change: ${fmtMoney(c.parsed.y, quote)}`

  return (
    <Card
      title="Daily gain / loss"
      insight={data?.insight}
      error={error}
      loading={loading}
      action={<Tabs options={RANGES} value={range} onChange={setRange} label="Gain/loss period" />}
    >
      <label className="mb-3 flex items-center gap-2 text-xs text-ink-3">
        If I hold
        <input
          type="number" min="0" value={amount} onChange={(e) => setAmount(e.target.value)}
          className="w-28 rounded-lg border border-line bg-surface px-2 py-1.5 text-sm font-medium text-ink"
        />
        {base}, valued in {quote}
      </label>
      <div className="h-44 sm:h-52">
        {data && (
          <Bar
            options={options}
            data={{
              labels: points.map((p) => p.date),
              datasets: [{
                data: points.map((p) => p.daily_change),
                backgroundColor: points.map((p) => (p.daily_change >= 0 ? up : down)),
                borderRadius: 4,
                borderSkipped: 'start',
                categoryPercentage: 0.9,
                barPercentage: 0.9,
              }],
            }}
          />
        )}
      </div>
      {data && (
        <div className="mt-4 grid grid-cols-3 gap-3">
          <Stat label="Total" value={fmtMoney(data.total_change, quote)} sub={`${data.total_change_pct >= 0 ? '+' : '−'}${Math.abs(data.total_change_pct).toFixed(2)}%`} />
          <Stat label="Up days" value={<><span aria-hidden style={{ color: up }}>▲</span> {data.up_days}</>} />
          <Stat label="Down days" value={<><span aria-hidden style={{ color: down }}>▼</span> {data.down_days}</>} />
        </div>
      )}
    </Card>
  )
}
