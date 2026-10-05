import { useState } from 'react'
import { Line } from 'react-chartjs-2'
import { useApi } from '../api/useApi'
import { cssVar, fmtDate, fmtRate } from '../utils/format'
import { baseOptions } from './chartSetup'
import { Card, Stat, Tabs } from './ui'

const RANGES = ['1W', '1M', '6M', '1Y', '5Y']

export default function HistoryChart({ base, quote }) {
  const [range, setRange] = useState('1M')
  const { data, error, loading } = useApi('/history', { base, quote, range })
  const s = data?.stats
  const options = baseOptions({ yFormat: fmtRate })
  options.plugins.tooltip.callbacks.label = (c) => ` 1 ${base} = ${fmtRate(c.parsed.y)} ${quote}`
  const hasDerived = data?.points.some((p) => p.source === 'derived_peg')

  return (
    <Card
      title={`${base}/${quote} history`}
      insight={data?.insight}
      error={error}
      loading={loading}
      action={<Tabs options={RANGES} value={range} onChange={setRange} label="Chart range" />}
    >
      <div className="h-56 sm:h-64">
        {data && (
          <Line
            options={options}
            data={{
              labels: data.points.map((p) => p.date),
              datasets: [{
                data: data.points.map((p) => p.rate),
                borderColor: cssVar('--accent'),
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0,
              }],
            }}
          />
        )}
      </div>
      {s && (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Change" value={`${s.change_pct >= 0 ? '+' : '−'}${Math.abs(s.change_pct).toFixed(2)}%`} />
          <Stat label="Average" value={fmtRate(s.mean)} sub={`${s.trading_days} trading days`} />
          <Stat label="Low" value={fmtRate(s.min)} sub={fmtDate(s.min_date)} />
          <Stat label="High" value={fmtRate(s.max)} sub={fmtDate(s.max_date)} />
        </div>
      )}
      <p className="mt-3 text-[11px] text-ink-3">
        Weekends and ECB holidays have no rate and are skipped.
        {hasDerived && ' AED values before the latest day are derived from the USD peg.'}
      </p>
    </Card>
  )
}
