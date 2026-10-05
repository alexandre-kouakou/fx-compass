# FX Compass

**AI-powered Global Currency Intelligence Dashboard** — turns exchange-rate data into decisions: when to convert, how much risk, what the trend suggests.

FIN623 International Financial Management · Lovely Professional University · Group 2

## What it does

Every widget leads with a one-line plain-language answer, then shows the chart.

| Widget | Answers |
|---|---|
| Converter | "Is today a good day to convert?" — compares today's rate with its 3-month average |
| Daily reference rates | All 10 currencies against your chosen base, with day-on-day change |
| History (1W–5Y) | Trend, average, low/high over the period |
| AI forecast | 7-trading-day forecast **shown next to a naive "no change" baseline**, its error range, and how it scored on recent data it never saw |
| Daily gain/loss | What a holding (e.g. 10,000 USD) gained or lost in another currency, day by day |
| Volatility | Risk level (low/moderate/high), typical daily move, compared with its own past year |
| Strength heatmap | 10×10 % changes; which currency strengthened or weakened most |
| Rate alerts | "Tell me when 1 USD is above 97 INR" — shown on the dashboard when triggered |

Currencies: USD, EUR, GBP, JPY, INR, AED, CHF, CNY, AUD, CAD.

## Data and honesty notes

- **Daily reference rates**, not live ticks: European Central Bank rates via [Frankfurter](https://frankfurter.dev), published ~16:00 CET on ECB working days. Weekends/holidays have no data.
- **AED is not published by the ECB.** History is *derived* from the USD peg (1 USD = 3.6725 AED) and labelled "derived"; the latest value comes from [Rates By Exchange Rate API](https://www.exchangerate-api.com).
- All data is cached in our database, so the dashboard keeps working if the sources are down (it tells you how old the data is).
- **AI forecast:** Ridge regression on recent daily returns, trained with a time-based split (no shuffling). On data up to 2 Oct 2026 it beat the naive baseline on **18 of 90** currency pairs and roughly tied on the rest, which is what finance theory predicts for exchange rates (close to a random walk). The dashboard says this openly for each pair. Educational only, not financial advice.

## Tech stack

React (Vite) + Tailwind CSS + Chart.js · Django + Django REST Framework · SQLite (Postgres-ready) · scikit-learn / pandas

## How to run

See the **How to run** section in [CLAUDE.md](CLAUDE.md#how-to-run). Short version:

```bash
cp .env.example .env
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate && .venv/bin/python manage.py backfill_history
.venv/bin/python manage.py runserver          # terminal 1
cd ../frontend && npm install && npm run dev   # terminal 2 → http://localhost:5173
```

Technical decisions are logged in [DECISIONS.md](DECISIONS.md).

## Team

| Name | Registration no. |
|---|---|
| Bhushan | 12503370 |
| Manfe Ange Alexandre Kouakou | 12504161 |
| Neehar S | 12504547 |
| Ashutosh Tiwari | 12506700 |
| Belfi Essac | 12506860 |
