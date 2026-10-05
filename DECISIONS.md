# Decisions log

Technical choices, newest at the bottom. Format: date — decision — why — alternatives considered.

## 2026-10-05 — Frankfurter v1 at api.frankfurter.dev
- **Why:** `api.frankfurter.app` now 301-redirects to `api.frankfurter.dev/v1/`. Calling the new URL directly avoids a redirect hop and surprises.
- **Alternatives:** keep old URL and follow redirects (works, but fragile).

## 2026-10-05 — AED: live from open.er-api.com, history derived from the USD peg
- **Why:** verified that ECB/Frankfurter has no AED. open.er-api.com is free, needs no key, and returns AED daily. AED has been pegged at 3.6725 per USD since 1997, so `AED per X = 3.6725 × (USD per X)` is accurate for history. Derived rows are tagged `source="derived_peg"` and shown as "derived".
- **Detail:** for the latest day we store `AED per USD (open.er-api) × USD per EUR (ECB)`, not open.er-api's own AED/EUR. Mixing two providers' EUR/USD created a fake ~0.2% jump in USD/AED.
- **Alternatives:** drop AED (breaks scope); paid API with full AED history (needs a key, overkill).

## 2026-10-05 — Store everything with base EUR, compute crosses on the fly
- **Why:** ECB publishes everything against EUR. Storing one row per (date, currency) vs EUR keeps the table ~10× smaller than storing every pair, and any cross (e.g. INR per USD) is a simple division. Selectable base in the UI comes from this.
- **Alternatives:** store all 90 pairs per day (redundant, can drift out of sync).

## 2026-10-05 — Frontend never calls external APIs
- **Why:** the app must work offline/when an API is down; all data comes from our DB via Django REST Framework.

## 2026-10-05 — Refresh on request instead of a scheduler
- **Why:** no cron/Celery to set up for a laptop demo. Any `/api/rates/latest` call refreshes if the last ECB fetch attempt is older than `REFRESH_AFTER_HOURS` (6h). Failures are logged in `FetchLog` and cached data is served. `fetch_rates` command exists for manual/cron use.
- **Alternatives:** Celery beat / cron (more moving parts).

## 2026-10-05 — Backfill from 2018-01-01
- **Why:** 5Y chart needs 5 years; extra years give the ML more history. ~2,240 trading days × 10 currencies = ~22k rows, downloads in ~7s.

## 2026-10-05 — Forecast: Ridge regression on lagged log-returns, 7 trading days, vs naive baseline
- **Features (day t only, no look-ahead):** last 5 daily log-returns, 5/20-day mean return, 20-day volatility, distance from 20-day average. **Target:** log change from t to t+h, one model per h = 1..7.
- **Split:** last 5 years only; most recent 20% = test, never shuffled, 7-day gap so no training target overlaps the test period. Final forecast uses a model refit on all data.
- **Honesty:** metrics = MAE/RMSE in % of rate on the test period, vs baseline "rate stays the same". Verdict `beats_baseline` only if average MAE is >1% better; pegged pairs get `pegged`. Error range = 10th–90th percentile of test errors (an "80% range").
- **Result on 2026-10-02 data:** beats the baseline on 18/90 pairs, roughly ties elsewhere — consistent with FX being close to a random walk.
- **Alternatives:** ARIMA/Prophet/LSTM (slower, more fragile, unlikely to beat the baseline on daily FX either).
- **Note:** forecast dates are Mon–Fri business days; ECB holidays are not excluded.

## 2026-10-05 — Volatility = 30-trading-day annualised std of daily log-returns
- Levels: <5% low, 5–10% moderate, ≥10% high; also compared to the pair's own 1-year volatility (calmer / in line / more volatile than usual).

## 2026-10-05 — Alerts: anonymous browser id, checked on page load
- **Why:** no logins (agreed). The browser keeps a random `client_id` in localStorage; alerts are evaluated against the latest daily rate when listed or created. An alert whose condition is already true when created triggers immediately.

## 2026-10-05 — Insights generated server-side
- **Why:** one source of truth for the numbers and the sentence that explains them; frontend just displays `insight`.
