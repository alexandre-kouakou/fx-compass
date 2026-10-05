import { useState } from 'react'
import { Line } from 'react-chartjs-2'
import { useApi } from '../api/useApi'
import { cssVar, fmtDate, fmtRate } from '../utils/format'
import { baseOptions } from './chartSetup'
import { Card, StatusPill } from './ui'

const VERDICT = {
  beats_baseline: ['good', 'Beats naive baseline'],
  no_better_than_baseline: ['warning', 'No better than naive'],
  pegged: ['good', 'Pegged currency'],
}

function withAlpha(hex, a) {
  const n = parseInt(hex.slice(1), 16)
  return `rgba(${n >> 16}, ${(n >> 8) & 255}, ${n & 255}, ${a})`
}

export default function Forecast({ base, quote }) {
  const { data, error, loading } = useApi('/forecast', { base, quote })
  const [showDetails, setShowDetails] = useState(false)
  const [status, label] = VERDICT[data?.verdict] || []

  let chart = null
  if (data) {
    const hist = data.history
    const fc = data.forecast
    const pad = (arr, before) => [...Array(before).fill(null), ...arr]
    const lastIdx = hist.length - 1
    const last = hist[lastIdx].rate
    const orange = cssVar('--forecast')
    const options = baseOptions({ yFormat: fmtRate, legend: true })
    options.plugins.legend.labels.filter = (item) => !item.text.startsWith('_')
    options.plugins.tooltip.filter = (item) => !item.dataset.label.startsWith('_') && item.parsed.y != null
    options.plugins.tooltip.callbacks.label = (c) => ` ${c.dataset.label}: ${fmtRate(c.parsed.y)}`
    chart = {
      options,
      data: {
        labels: [...hist.map((p) => p.date), ...fc.map((p) => p.date)],
        datasets: [
          { label: 'Actual', data: hist.map((p) => p.rate), borderColor: cssVar('--accent'), borderWidth: 2, pointRadius: 0, pointHoverRadius: 4 },
          { label: 'Model forecast', data: pad([last, ...fc.map((p) => p.predicted)], lastIdx), borderColor: orange, borderWidth: 2, pointRadius: 0, pointHoverRadius: 4 },
          { label: 'Naive (no change)', data: pad([last, ...fc.map((p) => p.baseline)], lastIdx), borderColor: cssVar('--ink-3'), borderWidth: 2, borderDash: [4, 4], pointRadius: 0, pointHoverRadius: 3 },
          { label: '_low', data: pad([last, ...fc.map((p) => p.low)], lastIdx), borderWidth: 0, pointRadius: 0, pointHoverRadius: 0 },
          { label: '80% range', data: pad([last, ...fc.map((p) => p.high)], lastIdx), borderWidth: 0, pointRadius: 0, pointHoverRadius: 0, fill: '-1', backgroundColor: withAlpha(orange, 0.15) },
        ],
      },
    }
  }

  const m = data?.metrics
  return (
    <Card title={`AI forecast · next 7 trading days`} insight={data?.insight} error={error} loading={loading}
      action={status && <StatusPill status={status}>{label}</StatusPill>}>
      <div className="h-56 sm:h-64">{chart && <Line {...chart} />}</div>
      {m && (
        <>
          <div className="mt-4 grid grid-cols-2 gap-3 rounded-xl bg-neutral p-3 text-sm">
            <div>
              <div className="text-xs text-ink-3">Model avg. error</div>
              <div className="font-semibold">{m.avg_model_mae_pct.toFixed(3)}%</div>
            </div>
            <div>
              <div className="text-xs text-ink-3">Naive avg. error</div>
              <div className="font-semibold">{m.avg_baseline_mae_pct.toFixed(3)}%</div>
            </div>
          </div>
          <button onClick={() => setShowDetails((v) => !v)} className="mt-3 text-xs font-medium text-accent">
            {showDetails ? 'Hide' : 'Show'} how this was tested
          </button>
          {showDetails && (
            <div className="mt-2 space-y-2 text-xs text-ink-2">
              <p>
                {data.model_name}, trained on {m.n_train} trading days and tested on the {m.n_test} most recent days it
                never saw ({fmtDate(m.test_start)} – {fmtDate(m.test_end)}). Time-ordered split, no shuffling. Error =
                mean absolute error as % of the rate. The shaded band is where 80% of past test errors fell.
              </p>
              <table className="w-full text-left tabular-nums">
                <thead className="text-ink-3">
                  <tr><th className="font-normal">Days ahead</th><th className="font-normal">Model MAE</th><th className="font-normal">Naive MAE</th></tr>
                </thead>
                <tbody>
                  {m.per_horizon.map((h) => (
                    <tr key={h.horizon}>
                      <td>{h.horizon}</td><td>{h.model_mae_pct.toFixed(3)}%</td><td>{h.baseline_mae_pct.toFixed(3)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="mt-3 text-[11px] text-ink-3">Educational model, not financial advice. Exchange rates are hard to predict.</p>
        </>
      )}
    </Card>
  )
}
