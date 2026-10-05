// Small shared building blocks: card, tabs, selects, badges.

export function Card({ title, insight, loading, error, children, action, className = '' }) {
  return (
    <section className={`rounded-2xl border border-line bg-surface p-4 sm:p-5 ${className}`}>
      <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-3">{title}</h2>
        {action}
      </header>
      {error ? (
        <p className="text-sm text-ink-2">Couldn’t load this widget: {error.message}</p>
      ) : (
        <>
          {/* Answer first: the plain-language insight comes before the chart. */}
          <p className={`mb-4 text-[15px] leading-snug text-ink ${loading && !insight ? 'animate-pulse' : ''}`}>
            {insight || (loading ? 'Loading…' : '')}
          </p>
          <div className={loading ? 'opacity-60 transition-opacity' : 'transition-opacity'}>{children}</div>
        </>
      )}
    </section>
  )
}

export function Tabs({ options, value, onChange, label }) {
  return (
    <div role="tablist" aria-label={label} className="inline-flex rounded-lg border border-line p-0.5 text-xs">
      {options.map((o) => (
        <button
          key={o}
          role="tab"
          aria-selected={o === value}
          onClick={() => onChange(o)}
          className={`min-w-9 rounded-md px-2 py-1.5 font-medium ${
            o === value ? 'bg-ink text-surface' : 'text-ink-2 hover:bg-neutral'
          }`}
        >
          {o}
        </button>
      ))}
    </div>
  )
}

export function CurrencySelect({ value, onChange, currencies, label, exclude }) {
  return (
    <label className="flex min-w-0 flex-1 flex-col gap-1 text-xs text-ink-3 sm:w-52 sm:flex-none">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-line bg-surface px-2 py-2 text-sm font-medium text-ink"
      >
        {currencies.map((c) => (
          <option key={c.code} value={c.code} disabled={c.code === exclude}>
            {c.code} – {c.name}
          </option>
        ))}
      </select>
    </label>
  )
}

export function SourceBadge({ source }) {
  if (!source || source === 'ecb') return null
  const text = source === 'derived_peg' ? 'derived' : 'live'
  const title =
    source === 'derived_peg'
      ? 'AED is not published by the ECB. Derived from the USD peg (1 USD = 3.6725 AED).'
      : 'AED from open.er-api.com, combined with the ECB USD rate.'
  return (
    <span title={title} className="ml-1 rounded border border-line px-1 text-[10px] font-medium uppercase text-ink-3">
      {text}
    </span>
  )
}

const STATUS = {
  good: { color: 'var(--good)', icon: '●' },
  warning: { color: 'var(--warning)', icon: '▲' },
  serious: { color: 'var(--serious)', icon: '◆' },
  critical: { color: 'var(--critical)', icon: '■' },
}

/** Status colour always comes with an icon and a text label. */
export function StatusPill({ status, children }) {
  const s = STATUS[status]
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-line px-2.5 py-1 text-xs font-medium text-ink">
      <span aria-hidden style={{ color: s.color }}>{s.icon}</span>
      {children}
    </span>
  )
}

export function Change({ value }) {
  if (value == null) return null
  if (Math.abs(value) < 0.005) return <span className="whitespace-nowrap text-ink-3">– 0.00%</span>
  const up = value >= 0
  return (
    <span className="whitespace-nowrap text-ink-2">
      <span aria-hidden style={{ color: up ? 'var(--up)' : 'var(--down)' }}>{up ? '▲' : '▼'}</span>{' '}
      {Math.abs(value).toFixed(2)}%
    </span>
  )
}

export function Stat({ label, value, sub }) {
  return (
    <div>
      <div className="text-xs text-ink-3">{label}</div>
      <div className="text-sm font-semibold text-ink">{value}</div>
      {sub && <div className="text-[11px] text-ink-3">{sub}</div>}
    </div>
  )
}
