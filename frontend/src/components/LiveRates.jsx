import { useApi } from '../api/useApi'
import { fmtRate } from '../utils/format'
import { Card, Change, SourceBadge } from './ui'

export default function LiveRates({ base, quote, onPickQuote }) {
  const { data, error, loading } = useApi('/rates/latest', { base })
  return (
    <Card title={`Daily reference rates · 1 ${base} =`} insight={data?.insight} error={error} loading={loading}>
      <ul className="divide-y divide-line">
        {data?.rates.map((r) => (
          <li key={r.code}>
            <button
              onClick={() => onPickQuote(r.code)}
              className={`flex w-full items-center justify-between gap-2 px-1 py-2 text-left text-sm hover:bg-neutral ${
                r.code === quote ? 'font-semibold' : ''
              }`}
              aria-current={r.code === quote}
            >
              <span className="flex items-center">
                <span className="w-10">{r.code}</span>
                <span className="hidden text-ink-3 sm:inline">{r.name}</span>
                <SourceBadge source={r.source} />
              </span>
              <span className="flex items-center gap-3">
                <span className="tabular-nums">{fmtRate(r.rate)}</span>
                <span className="w-16 text-right text-xs"><Change value={r.change_pct} /></span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] text-ink-3">Tap a currency to analyse it. Change vs previous ECB trading day.</p>
    </Card>
  )
}
