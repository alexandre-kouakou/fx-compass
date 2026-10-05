import { useState } from 'react'
import { useApi } from '../api/useApi'
import { cssVar, fmtDate } from '../utils/format'
import { Card, Tabs } from './ui'

const RANGES = ['1W', '1M', '3M', '1Y']

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16)
  return [n >> 16, (n >> 8) & 255, n & 255]
}

/** Diverging scale: down-colour ← neutral grey → up-colour. */
function cellColor(v, max) {
  if (v == null) return 'transparent'
  const t = Math.min(Math.abs(v) / max, 1)
  const a = hexToRgb(cssVar('--neutral'))
  const b = hexToRgb(cssVar(v >= 0 ? '--up' : '--down'))
  const mix = a.map((x, i) => Math.round(x + (b[i] - x) * t))
  return `rgb(${mix.join(',')})`
}

export default function Heatmap() {
  const [range, setRange] = useState('1M')
  const { data, error, loading } = useApi('/heatmap', { range })
  const max = data ? Math.max(...data.matrix.flat().filter((v) => v != null).map(Math.abs)) || 1 : 1

  return (
    <Card title="Currency strength heatmap" insight={data?.insight} error={error} loading={loading}
      action={<Tabs options={RANGES} value={range} onChange={setRange} label="Heatmap period" />}>
      {data && (
        <>
          <div className="-mx-1 overflow-x-auto">
            <table className="w-full min-w-[480px] border-separate border-spacing-0.5 text-[11px] tabular-nums">
              <caption className="sr-only">% change in the price of each row currency measured in each column currency</caption>
              <thead>
                <tr>
                  <th className="text-left font-normal text-ink-3">1 ↓ in →</th>
                  {data.currencies.map((c) => <th key={c} scope="col" className="font-semibold text-ink-2">{c}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.currencies.map((row, i) => (
                  <tr key={row}>
                    <th scope="row" className="pr-1 text-left font-semibold text-ink-2">{row}</th>
                    {data.matrix[i].map((v, j) => {
                      const strong = v != null && Math.abs(v) / max > 0.6
                      return (
                        <td
                          key={j}
                          title={v == null ? '' : `1 ${row} in ${data.currencies[j]}: ${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(2)}%`}
                          style={{ background: cellColor(v, max) }}
                          className={`h-8 rounded text-center ${strong ? 'text-white' : 'text-ink'}`}
                        >
                          {v == null ? '' : `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(1)}`}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-ink-3">
            <span><span aria-hidden style={{ color: 'var(--up)' }}>■</span> row currency strengthened</span>
            <span><span aria-hidden style={{ color: 'var(--down)' }}>■</span> row currency weakened</span>
            <span>% change, {fmtDate(data.start_date)} – {fmtDate(data.end_date)}</span>
          </div>
          <ol className="mt-3 flex flex-wrap gap-1.5 text-xs">
            {data.strength.map((s, i) => (
              <li key={s.code} className="rounded-full border border-line px-2 py-0.5 text-ink-2">
                {i + 1}. {s.code} {s.score >= 0 ? '+' : '−'}{Math.abs(s.score).toFixed(2)}%
              </li>
            ))}
          </ol>
        </>
      )}
    </Card>
  )
}
