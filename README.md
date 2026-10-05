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
- **AI forecast:** Ridge regression on recent daily returns, trained with a time-based split (no shuffling). On data up to 2 Oct 2026 it beat the naive baseline by more than 1% on **18 of 90** currency pairs, was within ±1% on 30, was more than 1% worse on 40, and had nothing to forecast on the 2 pegged USD/AED pairs. That is what finance theory predicts for exchange rates (close to a random walk). The dashboard says this openly for each pair. Educational only, not financial advice.

## Tech stack

React (Vite) + Tailwind CSS + Chart.js · Django + Django REST Framework · SQLite (Postgres-ready) · scikit-learn / pandas

## How to run

Prerequisites: Python 3.12+ (tested on 3.14), Node 20+ (tested on 22).

```bash
# 0. config (once)
cp .env.example .env          # then set DJANGO_SECRET_KEY to any long random string

# 1. backend (once)
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py backfill_history    # downloads ~8 years of daily rates (~10s)
.venv/bin/python manage.py train_forecasts     # optional: pre-trains all 90 pairs (~10s)

# 2. backend (every time)
.venv/bin/python manage.py runserver           # API on http://localhost:8000/api/

# tests (offline, no network)
.venv/bin/python manage.py test
```

Useful commands: `fetch_rates` (pull new days + live AED; also happens automatically every 6h when the dashboard is opened).

API endpoints (all GET unless noted): `/api/status`, `/api/currencies`, `/api/rates/latest?base=`, `/api/convert?base=&quote=&amount=`, `/api/history?base=&quote=&range=1W|1M|3M|6M|1Y|5Y`, `/api/gain-loss?base=&quote=&amount=&range=`, `/api/volatility?base=&quote=`, `/api/heatmap?range=`, `/api/forecast?base=&quote=`, `/api/alerts?client_id=` (GET, POST), `/api/alerts/<id>?client_id=` (DELETE).

```bash
# 3. frontend (once), in a second terminal
cd frontend
npm install

# 4. frontend (every time, with the backend running)
npm run dev                                    # dashboard on http://localhost:5173
npm run build                                  # production build into frontend/dist
```

The frontend reads `VITE_API_URL` from the root `.env` (default `http://localhost:8000/api`).

Technical decisions are logged in [DECISIONS.md](DECISIONS.md).

## Team

| Name | Registration no. |
|---|---|
| Bhushan | 12503370 |
| Manfe Ange Alexandre Kouakou | 12504161 |
| Neehar S | 12504547 |
| Ashutosh Tiwari | 12506700 |
| Belfi Essac | 12506860 |
