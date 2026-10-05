import { useEffect, useState } from 'react'
import { useApi } from '../api/useApi'
import Alerts from '../components/Alerts'
import Converter from '../components/Converter'
import Footer from '../components/Footer'
import Forecast from '../components/Forecast'
import GainLoss from '../components/GainLoss'
import Header from '../components/Header'
import Heatmap from '../components/Heatmap'
import HistoryChart from '../components/HistoryChart'
import LiveRates from '../components/LiveRates'
import Volatility from '../components/Volatility'

function usePersisted(key, initial) {
  const [value, setValue] = useState(() => {
    try { return localStorage.getItem(key) || initial } catch { return initial }
  })
  useEffect(() => {
    try { localStorage.setItem(key, value) } catch { /* private mode: fine */ }
  }, [key, value])
  return [value, setValue]
}

export default function Dashboard() {
  const { data: currencies, error } = useApi('/currencies', {})
  const [base, setBase] = usePersisted('fx-base', 'USD')
  const [quote, setQuote] = usePersisted('fx-quote', 'INR')

  if (error) {
    return (
      <main className="mx-auto max-w-xl p-6 text-sm text-ink-2">
        <h1 className="mb-2 text-xl font-semibold text-ink">FX Compass</h1>
        Can’t reach the FX Compass API. Is the Django server running on port 8000? ({error.message})
      </main>
    )
  }
  if (!currencies) return <main className="p-6 text-sm text-ink-3">Loading…</main>

  const pick = (code) => (code === base ? setBase(quote) : setQuote(code))
  const props = { base, quote }

  return (
    <main className="mx-auto max-w-6xl px-4 py-5 sm:px-6">
      <Header currencies={currencies} base={base} quote={quote} setBase={setBase} setQuote={setQuote} />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="min-w-0 space-y-4 lg:col-span-2">
          <Converter {...props} />
          <HistoryChart {...props} />
          <Forecast {...props} />
          <GainLoss {...props} />
        </div>
        <div className="min-w-0 space-y-4">
          <LiveRates {...props} onPickQuote={pick} />
          <Volatility {...props} />
          <Alerts {...props} />
        </div>
        <div className="min-w-0 lg:col-span-3">
          <Heatmap />
        </div>
      </div>
      <Footer />
    </main>
  )
}
