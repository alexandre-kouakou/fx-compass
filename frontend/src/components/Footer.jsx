const TEAM = [
  ['Bhushan', '12503370'],
  ['Manfe Ange Alexandre Kouakou', '12504161'],
  ['Neehar S', '12504547'],
  ['Ashutosh Tiwari', '12506700'],
  ['Belfi Essac', '12506860'],
]

export default function Footer() {
  return (
    <footer className="mt-8 space-y-2 border-t border-line pt-4 text-[11px] leading-relaxed text-ink-3">
      <p>
        Data: European Central Bank daily reference rates via{' '}
        <a className="underline" href="https://frankfurter.dev" target="_blank" rel="noreferrer">Frankfurter</a>, published
        around 16:00 CET on ECB working days, so these are not real-time quotes. AED is not published by the ECB: its
        history is derived from the USD peg (1 USD = 3.6725 AED) and the latest value uses{' '}
        <a className="underline" href="https://www.exchangerate-api.com" target="_blank" rel="noreferrer">Rates By Exchange Rate API</a>.
      </p>
      <p>For education only. Not financial advice.</p>
      <p>
        FIN623 International Financial Management · LPU · Group 2 —{' '}
        {TEAM.map(([n, id]) => `${n} (${id})`).join(', ')}
      </p>
    </footer>
  )
}
