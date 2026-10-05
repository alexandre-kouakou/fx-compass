export function fmtRate(v) {
  if (v == null || Number.isNaN(v)) return '–'
  const a = Math.abs(v)
  const digits = a >= 10 ? 2 : a >= 0.1 ? 4 : 6
  return v.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function fmtMoney(v, code) {
  if (v == null) return '–'
  return `${v.toLocaleString('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 2 })} ${code}`
}

export function fmtPct(v, signed = true) {
  if (v == null) return '–'
  const s = `${Math.abs(v).toFixed(2)}%`
  if (!signed) return s
  return (v >= 0 ? '+' : '−') + s
}

export function fmtDate(iso, opts = { day: 'numeric', month: 'short', year: 'numeric' }) {
  if (!iso) return '–'
  return new Date(iso + (iso.length === 10 ? 'T00:00:00' : '')).toLocaleDateString('en-GB', opts)
}

export function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

export const SOURCE_LABEL = { ecb: 'ECB', er_api: 'live (open.er-api)', derived_peg: 'derived' }
