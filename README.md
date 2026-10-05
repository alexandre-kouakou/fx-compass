# FX Compass

**AI-powered Global Currency Intelligence Dashboard.** It turns exchange-rate data into decisions: when to convert, how much risk you carry, and what the trend suggests, with an AI forecast that is always shown next to a naive baseline and says honestly when it doesn't beat it.

FIN623 International Financial Management · Lovely Professional University · Group 2

## The pitch

Exchange-rate sites show numbers; people need answers. A textile exporter in Ludhiana wants to know whether to convert this week's dollar invoice or wait. A student abroad wants to know whether today is a good day to receive money. FX Compass puts a **one-line plain-language answer above every chart** ("Today's USD→INR rate is 0.72% above its 3-month average, so you get more INR than usual"), covers 10 major currencies with 8+ years of European Central Bank data, and is honest about what AI can and can't predict.

## Who it's for

| Persona | Need | Widgets that answer it |
|---|---|---|
| **Gurpreet**, textile exporter in Ludhiana, invoices in USD/EUR | "How much could the rupee move against me before I get paid?" | Volatility, rate alerts, AI forecast + error range, gain/loss |
| **Aïcha**, international student receiving money from abroad | "Is this a good week to convert?" | Converter with comparison to the 3-month average, daily gain/loss |
| **Rahul**, finance student | "Show me evidence on currency strength and risk" | Strength heatmap, 5-year history and stats, honest model metrics |

## Features

Every widget leads with a one-line plain-language answer, then shows the chart.

| Widget | Answers |
|---|---|
| Currency selector | Any of the 10 currencies as base ("From") or quote ("To"); remembered in the browser |
| Converter | "Is today a good day to convert?": compares today's rate with its 3-month average |
| Daily reference rates | All 10 currencies against your chosen base, with day-on-day change |
| History (1W / 1M / 6M / 1Y / 5Y) | Trend, average, low/high with dates, % change over the period |
| AI forecast | 7-trading-day forecast **next to a naive "no change" baseline**, its 80% error range, and how it scored on the most recent year of data it never saw |
| Daily gain/loss | What a holding (e.g. 10,000 USD) gained or lost in another currency, day by day |
| Volatility | Risk level (low/moderate/high), typical daily move, compared with its own past year |
| Strength heatmap | 10×10 % changes and a strongest→weakest ranking |
| Rate alerts | "Tell me when 1 USD is above 97 INR": shown on the dashboard when triggered |
| Responsive, calm design | Phone-first layout, light/dark mode, no flashing colours; status colours always come with an icon and a label |

Currencies: USD, EUR, GBP, JPY, INR, AED, CHF, CNY, AUD, CAD.

## Data and honesty notes

- **Daily reference rates**, not live ticks: European Central Bank rates via [Frankfurter](https://frankfurter.dev), published ~16:00 CET on ECB working days. Weekends/holidays have no data and are never filled in.
- **AED is not published by the ECB.** History is *derived* from the USD peg (1 USD = 3.6725 AED) and labelled "derived"; the latest value comes from [Rates By Exchange Rate API](https://www.exchangerate-api.com).
- All data is cached in our database, so the dashboard keeps working if the sources are down (it tells you how old the data is). The browser only ever talks to our own API.
- **AI forecast:** Ridge regression on recent daily returns, trained with a time-based split (no shuffling). On data up to 2 Oct 2026 it beat the naive baseline by more than 1% on **18 of 90** currency pairs, was within ±1% on 30, was more than 1% worse on 40, and had nothing to forecast on the 2 pegged USD/AED pairs. That is what finance theory predicts for exchange rates (close to a random walk). The dashboard says this openly for each pair. Educational only, not financial advice.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 (Vite 8) · Tailwind CSS 4 · Chart.js 4 via react-chartjs-2 |
| Backend | Django 6.1 · Django REST Framework 3.18 · django-cors-headers |
| Database | SQLite (Postgres-ready via `DB_ENGINE=postgres`) |
| ML / data | scikit-learn 1.9 · pandas 3.0 · NumPy 2.5 |
| Data sources | Frankfurter (ECB reference rates) · open.er-api.com (live AED) |

## Quick start (how to run)

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

## Documentation

| Document | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, frontend/backend/DB/ML, data flow |
| [docs/DATABASE.md](docs/DATABASE.md) | Schema tables and ER diagram |
| [docs/API.md](docs/API.md) | External APIs (and the AED solution), every internal endpoint with real examples and error codes |
| [docs/UML.md](docs/UML.md) | Use case, class, sequence and activity diagrams |
| [docs/TESTING.md](docs/TESTING.md) | Testing approach and latest results |
| [docs/USER_MANUAL.md](docs/USER_MANUAL.md) | Installation and how to use each widget |
| [docs/MODEL_REPORT.md](docs/MODEL_REPORT.md) | Forecast model: data, features, split, real metrics, limitations |
| [DECISIONS.md](DECISIONS.md) | Log of technical decisions |

## Team

| Name | Registration no. |
|---|---|
| Bhushan | 12503370 |
| Manfe Ange Alexandre Kouakou | 12504161 |
| Neehar S | 12504547 |
| Ashutosh Tiwari | 12506700 |
| Belfi Essac | 12506860 |

## Citations

**Textbook and literature**
- Eun, C. S., & Resnick, B. G. *International Financial Management*. McGraw-Hill Education. *(Team: add the edition and year of the copy used in FIN623.)* Used for exchange-rate determination, currency risk and exposure, and exchange-rate forecasting (efficient-market / random-walk view).
- Meese, R. A., & Rogoff, K. (1983). Empirical exchange rate models of the seventies: Do they fit out of sample? *Journal of International Economics*, 14(1–2), 3–24. The classic result that a random walk is hard to beat, which is why every forecast is compared with a naive baseline.

**Data sources**
- European Central Bank, *Euro foreign exchange reference rates*. https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/
- Frankfurter, open-source API for ECB reference rates. https://frankfurter.dev
- Rates By Exchange Rate API, open access endpoint (`open.er-api.com`), used for live AED. https://www.exchangerate-api.com (attribution required by its terms)

**Libraries**
- Django. https://www.djangoproject.com
- Django REST Framework. https://www.django-rest-framework.org
- django-cors-headers. https://github.com/adamchainz/django-cors-headers
- Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. https://scikit-learn.org
- McKinney, W. (2010). Data Structures for Statistical Computing in Python. *Proceedings of the 9th Python in Science Conference*, 56–61. https://pandas.pydata.org
- Harris, C. R. et al. (2020). Array programming with NumPy. *Nature*, 585, 357–362. https://numpy.org
- Requests. https://requests.readthedocs.io · python-dotenv. https://github.com/theskumar/python-dotenv
- React. https://react.dev · Vite. https://vite.dev · Tailwind CSS. https://tailwindcss.com
- Chart.js. https://www.chartjs.org · react-chartjs-2. https://react-chartjs-2.js.org
