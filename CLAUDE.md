# FX Compass — project guide for Claude

AI-powered Global Currency Intelligence Dashboard.
Course: FIN623 International Financial Management, LPU — Group 2.
**Deadline: 2026-10-05 (today). Prefer working and simple over clever.**

## Working agreement

- The user is a vibe coder who owns the product vision and decisions. Claude owns the engineering.
- Explain choices in plain language. No jargon without a one-line explanation.
- Never hide mocks, shortcuts, stubbed data or failing tests. Say so plainly in the reply and in the code (`# MOCK:` / `// MOCK:` comments).
- **Ask before any decision that changes what the user sees** (layout, wording, which numbers appear, colours, feature cuts). Engineering-only choices don't need approval but go in `DECISIONS.md`.

## Product vision

Turn exchange-rate data into decisions: when to convert, how much risk, what the trend suggests.

Personas:
- **Gurpreet**, a Ludhiana textile exporter invoicing in USD/EUR, worried about rupee swings → volatility, alerts, forecast.
- **Aïcha**, an international student receiving money from abroad: "is this a good week to convert?" → converter, gain/loss, comparison with the 3-month average.
- **Rahul**, a finance student who needs evidence on currency strength and risk → heatmap, history, honest model metrics.

Principles:
1. **Answer first, then the chart.** Every widget shows a one-line plain-language insight above its visual (e.g. "INR is 1.2% weaker than its 3-month average").
2. **Honest AI.** Every forecast is shown next to a naive baseline (tomorrow = today) with its error range and test metrics. If the model doesn't beat the baseline, we say so.
3. **Mobile-first.** Design for a phone screen, then scale up.
4. **Calm financial design.** Neutral palette, no flashing red/green, no hype.

## Scope

Currencies (10): USD, EUR, GBP, JPY, INR, AED, CHF, CNY, AUD, CAD.

Features:
- Live rates with a selectable base currency
- Converter
- Daily gain/loss over a chosen period
- Interactive charts: 1W / 1M / 6M / 1Y / 5Y
- Historical stats (min, max, average, change)
- Volatility indicator
- AI forecast (vs naive baseline, with error range)
- 10×10 currency strength heatmap
- Threshold alerts (in-app)
- Responsive design

Stretch only (do not start until everything above works): news sentiment.

## Stack

- Frontend: React (Vite) + Tailwind CSS + Chart.js (via `react-chartjs-2`)
- Backend: Django + Django REST Framework
- Database: SQLite now, Postgres-ready (no SQLite-only features; DB settings read from env)
- ML: scikit-learn (+ pandas, numpy)
- Data: Frankfurter API (ECB reference rates) as primary source

## Data facts (verified 2026-10-05)

- Frankfurter base URL is now `https://api.frankfurter.dev/v1/` (the old `api.frankfurter.app` 301-redirects there). Always follow redirects.
- Frankfurter supports 9 of our 10 currencies. **AED is not in ECB data.**
- Weekends/holidays are simply missing from Frankfurter time series (e.g. 2026-09-26/27 absent).
- `https://open.er-api.com/v6/latest/USD` (ExchangeRate-API open endpoint, free, no key) returns AED (3.6725), updated once a day. Attribution to exchangerate-api.com is required by their terms.

## Known traps and how we handle them

- **AED**: live AED from open.er-api.com; historical AED derived from the USD peg (1 USD = 3.6725 AED) times the ECB USD cross rate. Every derived value is stored with `source="derived_peg"` and labelled **"derived"** in the UI.
- **Daily, not tick-level**: always call them "daily reference rates". Always show "last updated <date>". Never say "real-time".
- **Offline**: all rates are cached in the database. The frontend only talks to our Django API, never to external APIs. If an external API fails we serve the last cached data and say how old it is.
- **Gaps**: weekends/holidays have no rows. Charts skip them; stats use trading days. Do not forward-fill silently — if we ever fill, mark it.
- **ML**: time-based train/test split only (train on past, test on most recent period). Never shuffle. No future data in features (no leakage).
- **Secrets**: none in the repo. Use `.env` (git-ignored) and commit `.env.example`.

## Conventions

- **Conventional commits**: `feat:`, `fix:`, `docs:`, `test:` (plus `chore:` / `refactor:` when needed). Example: `feat: add currency converter endpoint`.
- **Small commits**: one logical change per commit.
- **DECISIONS.md**: log every technical choice (date, decision, why, alternatives). Newest at the bottom.
- **"How to run" section below must stay up to date** — update it in the same commit as any change to setup or commands.
- Python: Black-style formatting, type hints where cheap. JS: functional React components + hooks.
- Tests: Django `TestCase` for API endpoints and the ML split; keep them fast and offline (no real network calls in tests).
- Money/rates: store as `Decimal` in the DB, round only for display.

## Folder structure (planned)

```
fx-compass/
├── CLAUDE.md, DECISIONS.md, README.md, .env.example, .gitignore
├── backend/
│   ├── manage.py, requirements.txt
│   ├── fxcompass/            # Django project settings, urls
│   ├── rates/                # models, fetchers (Frankfurter, open.er-api), API views
│   │   └── management/commands/  # fetch_rates, backfill_history
│   ├── analytics/            # stats, volatility, heatmap, gain/loss
│   ├── forecasting/          # scikit-learn model, baseline, metrics, train command
│   └── alerts/               # threshold alerts
└── frontend/
    ├── package.json, vite.config.js, tailwind.config.js
    └── src/
        ├── api/              # one small client for our Django API
        ├── components/       # widgets (RateCard, Converter, Chart, Heatmap, ...)
        ├── pages/            # Dashboard
        └── utils/            # formatting, insight sentences
```

## How to run

_Not runnable yet — no app code written. This section will be filled in as soon as the backend and frontend skeletons exist._

## Team

| Name | Reg. no. |
|---|---|
| Bhushan | 12503370 |
| Manfe Ange Alexandre Kouakou | 12504161 |
| Neehar S | 12504547 |
| Ashutosh Tiwari | 12506700 |
| Belfi Essac | 12506860 |
