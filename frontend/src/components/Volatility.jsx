import { Line } from 'react-chartjs-2'
import { useApi } from '../api/useApi'
import { cssVar } from '../utils/format'
import { baseOptions } from './chartSetup'
import { Card, Stat, StatusPill } from './ui'

const LEVEL = { low: ['good', 'Low risk'], moderate: ['warning', 'Moderate risk'], high: ['serious', 'High risk'] }

export default function Volatility({ base, quote }) {
  const { data, error, loading } = useApi('/volatility', { base, quote })
  const options = baseOptions({ yFormat: (v) => `${v.toFixed(1)}%` })
  options.plugins.tooltip.callbacks.label = (c) => ` 30-day volatility: ${c.parsed.y.toFixed(2)}% a year`
  const [status, label] = LEVEL[data?.level] || []

  return (
    <Card title="Volatility (risk)" insight={data?.insight} error={error} loading={loading}
      action={status && <StatusPill status={status}>{label}</StatusPill>}>
      {data && (
        <>
          <div className="mb-3 grid grid-cols-3 gap-3">
            <Stat label="Last 30 days" value={`${data.vol_30d.toFixed(1)}%`} sub="annualised" />
            <Stat label="Past year" value={`${data.vol_1y.toFixed(1)}%`} sub="annualised" />
            <Stat label="Typical day" value={`±${data.typical_daily_move_pct.toFixed(2)}%`} />
          </div>
          <div className="h-28">
            <Line
              options={options}
              data={{
                labels: data.rolling.map((p) => p.date),
                datasets: [{ data: data.rolling.map((p) => p.vol), borderColor: cssVar('--accent'), borderWidth: 2, pointRadius: 0, pointHoverRadius: 4 }],
              }}
            />
          </div>
          <p className="mt-2 text-[11px] text-ink-3">
            30-day rolling volatility over the past year. Under 5% = low, 5–10% = moderate, over 10% = high.
          </p>
        </>
      )}
    </Card>
  )
}
