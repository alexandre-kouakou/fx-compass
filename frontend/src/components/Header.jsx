import { useApi } from '../api/useApi'
import { fmtDate } from '../utils/format'
import { CurrencySelect } from './ui'

export default function Header({ currencies, base, quote, setBase, setQuote }) {
  const { data: status } = useApi('/status', {})
  const ageDays = status?.latest_rate_date
    ? Math.floor((Date.now() - new Date(status.latest_rate_date + 'T16:00:00Z')) / 86400000)
    : 0
  const stale = status && (status.last_fetch_failed || ageDays > 4)

  return (
    <header className="mb-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">FX Compass</h1>
          <p className="text-xs text-ink-3">
            Daily reference rates · last updated {status ? fmtDate(status.latest_rate_date) : '…'}
          </p>
        </div>
        <div className="flex w-full items-end gap-2 sm:w-auto">
          <CurrencySelect label="From" value={base} onChange={setBase} currencies={currencies} exclude={quote} />
          <button
            onClick={() => { setBase(quote); setQuote(base) }}
            className="mb-0.5 rounded-lg border border-line px-2 py-2 text-sm text-ink-2 hover:bg-neutral"
            aria-label="Swap currencies"
          >⇄</button>
          <CurrencySelect label="To" value={quote} onChange={setQuote} currencies={currencies} exclude={base} />
        </div>
      </div>
      {stale && (
        <p className="mt-3 rounded-lg border border-line bg-surface px-3 py-2 text-xs text-ink-2">
          <span aria-hidden style={{ color: 'var(--warning)' }}>▲</span> Showing saved data from{' '}
          {fmtDate(status.latest_rate_date)}. {status.last_fetch_failed ? 'The ECB source could not be reached; we’ll retry automatically.' : ''}
        </p>
      )}
    </header>
  )
}
