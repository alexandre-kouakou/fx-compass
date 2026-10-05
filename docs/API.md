# API

> Draft for team review. All example responses below are **real output** from our API on the local database (latest rate date 2026-10-02), captured on 2026-10-05. Long arrays are shortened with `…`; floats are shown as returned (unrounded).

Two parts:
1. **External APIs**: what our backend calls. Only the backend calls them, never the browser.
2. **Internal API**: our Django REST endpoints, which are the only thing the React app calls.

---

## 1. External APIs

### 1.1 Frankfurter (ECB daily reference rates): primary source

| | |
|---|---|
| Base URL | `https://api.frankfurter.dev/v1` (env `FRANKFURTER_URL`). The old `api.frankfurter.app` now 301-redirects here, so we call the new URL directly |
| Data | European Central Bank euro foreign exchange reference rates, published around 16:00 CET on ECB working days |
| Key / cost | None / free |
| Called from | `backend/rates/sources.py → fetch_frankfurter(start, end)` |
| Covers | 9 of our 10 currencies (USD, GBP, JPY, INR, CHF, CNY, AUD, CAD, plus EUR as the base). **Not AED** |

Request we send (always with an explicit end date, see below):

```
GET https://api.frankfurter.dev/v1/2026-09-30..2026-10-02?symbols=USD,INR
```

```json
{"amount":1.0,"base":"EUR","start_date":"2026-09-30","end_date":"2026-10-02",
 "rates":{"2026-09-30":{"INR":108.8205,"USD":1.1355},
          "2026-10-01":{"INR":108.832,"USD":1.1298},
          "2026-10-02":{"INR":108.1245,"USD":1.1225}}}
```

(The real request asks for all 8 symbols `USD,GBP,JPY,INR,CHF,CNY,AUD,CAD`.)

Behaviours we handle:
- **Weekends and holidays are missing** from the series (e.g. 2026-09-26/27). We store no row for them and never forward-fill.
- Frankfurter can return the business day *before* `start`; we drop anything earlier than what we asked for.
- An open-ended range starting on a weekend (`/2026-10-03..`) took ~13 s and timed out (we use a 10 s timeout). So we always send an explicit end date (today) and start from the last stored day (one day of overlap, re-saved harmlessly).

### 1.2 open.er-api.com (ExchangeRate-API open endpoint): live AED only

| | |
|---|---|
| URL | `https://open.er-api.com/v6/latest/USD` (env `AED_LIVE_URL`) |
| Key / cost | None / free. Updated once a day |
| Called from | `backend/rates/sources.py → fetch_aed_live()` |
| Attribution | Required by their terms. Shown in the dashboard footer and in `/api/status` as "Rates By Exchange Rate API" with a link to exchangerate-api.com |

Fields we use from the response (real values, 2026-10-05):

```json
{"result": "success", "base_code": "USD",
 "time_last_update_unix": 1791158551, "time_last_update_utc": "Mon, 05 Oct 2026 00:02:31 +0000",
 "rates": {"AED": 3.6725, "...": "…"}}
```

If `result` is not `"success"`, we treat it as a failure.

### 1.3 The AED problem and our solution

**Problem:** the ECB does not publish a UAE dirham rate, so Frankfurter has no AED at all, neither latest nor history.

**Solution:**
1. **History, derived from the peg.** The dirham has been pegged to the US dollar at **1 USD = 3.6725 AED** since 1997. For every ECB day we store
   `AED per EUR = 3.6725 × (USD per EUR from the ECB)`
   with `source = "derived_peg"`. Example for 2026-10-02: `3.6725 × 1.1225 = 4.12238125`.
2. **Latest day, live from open.er-api.com.** After each ECB fetch we overwrite AED on the latest stored date with
   `AED per EUR = (AED per USD from open.er-api) × (USD per EUR from the ECB, same date)`
   with `source = "er_api"`.
   We deliberately do *not* use open.er-api's own EUR rate: mixing two providers' EUR/USD created a fake ~0.2% jump in USD/AED.
3. **Labelled in the UI.** Every API response that involves AED carries the `source`. The dashboard shows a small **DERIVED** or **LIVE** badge with a tooltip, and the history chart adds "AED values before the latest day are derived from the USD peg."
4. **Consequence (stated openly):** USD/AED is a flat line at 3.6725, its volatility is ~0, and the forecast endpoint returns `verdict: "pegged"` for it.

### 1.4 Failure handling

- Every call is logged in `FetchLog` (success or the error message).
- A failure never breaks a request: the API keeps serving cached rows, `/api/status` returns `last_fetch_failed: true`, and the header shows "Showing saved data from <date>. The ECB source could not be reached; we'll retry automatically."
- Retry timing: refresh at most every 6 h after a success (`REFRESH_AFTER_HOURS`), or 15 minutes after a failure.

---

## 2. Internal API (Django REST Framework)

- Base URL: `http://localhost:8000/api` (the frontend reads it from `VITE_API_URL`).
- JSON only. No authentication. CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` (env `CORS_ALLOWED_ORIGINS`).
- **No trailing slash** on paths (`/api/convert`, not `/api/convert/`).
- Currency codes: `USD, EUR, GBP, JPY, INR, AED, CHF, CNY, AUD, CAD` (case-insensitive in query params).
- Ranges: `1W` (7 calendar days), `1M` (31), `3M` (92), `6M` (183), `1Y` (365), `5Y` (1,827), counted back from the latest rate date.
- Every analytics endpoint returns an `insight` string: the one-line plain-language answer shown above the widget.
- `source` values: `ecb`, `derived_peg`, `er_api` (see 1.3). For a pair, it is AED's source if either side is AED, otherwise `ecb`.

### Error codes

| Status | When | Body |
|---|---|---|
| `400 Bad Request` | Invalid query parameter (unknown currency, same base and quote, bad range, non-numeric or non-positive amount, missing/short `client_id`) | `{"<param>": "<message>"}` |
| `400 Bad Request` | Invalid alert body (POST `/api/alerts`) | DRF serializer errors: `{"<field>": ["<message>", …]}` |
| `404 Not Found` | DELETE an alert that doesn't exist **or belongs to another `client_id`** | `{"detail": "No Alert matches the given query."}` |
| `405 Method Not Allowed` | Wrong HTTP method, e.g. `POST /api/forecast` | `{"detail": "Method \"POST\" not allowed."}` |
| `204 No Content` | Successful DELETE | empty |
| `500 Internal Server Error` | **Known gap:** the database has no rates yet (before `backfill_history` has run). The analytics code assumes data exists | Django error page |

Real error examples:

```
GET /api/history?base=USD&quote=USD   → 400 {"quote": "must differ from base"}
GET /api/history?range=2Y             → 400 {"range": "must be one of 1W, 1M, 3M, 6M, 1Y, 5Y"}
GET /api/convert?amount=-5            → 400 {"amount": "must be positive"}
GET /api/convert?amount=abc           → 400 {"amount": "must be a number"}
GET /api/convert?base=XYZ             → 400 {"base": "must be one of USD, EUR, GBP, JPY, INR, AED, CHF, CNY, AUD, CAD"}
GET /api/alerts                       → 400 {"client_id": "required (8-64 chars)"}
```

### Endpoint summary

| Method | Path | Parameters (default) | Purpose |
|---|---|---|---|
| GET | `/api/status` | | Data freshness, sources, honesty notes |
| GET | `/api/currencies` | | The 10 currencies |
| GET | `/api/rates/latest` | `base` (USD) | Latest daily rates vs base; **triggers refresh if stale** |
| GET | `/api/convert` | `base` (USD), `quote` (INR), `amount` (1000) | Conversion + comparison with 3-month average |
| GET | `/api/history` | `base`, `quote`, `range` (1M) | Time series + min/max/mean/change |
| GET | `/api/gain-loss` | `base`, `quote`, `amount` (10000), `range` (1M) | Daily value change of a holding |
| GET | `/api/volatility` | `base`, `quote` | 30-day vs 1-year annualised volatility, risk level |
| GET | `/api/heatmap` | `range` (1M) | 10×10 % change matrix + strength ranking |
| GET | `/api/forecast` | `base`, `quote` | 7-day forecast vs naive baseline + test metrics |
| GET | `/api/alerts` | `client_id` (required) | List this browser's alerts, evaluating them first |
| POST | `/api/alerts` | JSON body | Create an alert (evaluated immediately) |
| DELETE | `/api/alerts/<id>` | `client_id` (required) | Delete one of this browser's alerts |

---

### GET `/api/status`

Used by the header for "last updated" and the stale-data banner.

```
GET /api/status
```
```json
{
  "latest_rate_date": "2026-10-02",
  "last_successful_fetch": "2026-10-05T13:56:40.462739Z",
  "last_fetch_failed": false,
  "sources": [
    {"name": "European Central Bank daily reference rates via Frankfurter", "url": "https://frankfurter.dev"},
    {"name": "Rates By Exchange Rate API (live AED)", "url": "https://www.exchangerate-api.com"}
  ],
  "notes": [
    "Daily reference rates (published ~16:00 CET on ECB working days), not real-time quotes.",
    "AED history is derived from the USD peg (1 USD = 3.6725 AED); the latest AED comes from open.er-api.com."
  ]
}
```

### GET `/api/currencies`

```
GET /api/currencies
```
```json
[
  {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ", "in_ecb": false},
  {"code": "AUD", "name": "Australian Dollar", "symbol": "A$", "in_ecb": true},
  {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$", "in_ecb": true},
  "… 7 more, sorted by code"
]
```

### GET `/api/rates/latest?base=`

Latest rate of every other currency against `base`, with the % change since the previous trading day. Before answering, calls `refresh_if_stale()` (may fetch from Frankfurter/open.er-api; never fails the request).

```
GET /api/rates/latest?base=USD
```
```json
{
  "base": "USD",
  "date": "2026-10-02",
  "rates": [
    {"code": "EUR", "name": "Euro", "rate": 0.8908685968819599, "change_pct": 0.650334075723813, "source": "ecb"},
    {"code": "GBP", "name": "British Pound", "rate": 0.757532293986637, "change_pct": 0.24949172995003543, "source": "ecb"},
    {"code": "JPY", "name": "Japanese Yen", "rate": 157.67483296213808, "change_pct": -0.19551443743426322, "source": "ecb"},
    "… 6 more"
  ],
  "insight": "Since the previous trading day, 1 USD buys 0.65% more EUR (biggest gain) and 1.03% less CHF (biggest drop)."
}
```

### GET `/api/convert?base=&quote=&amount=`

`result = amount × rate`. `avg_3m` = mean of the last 63 trading days. The insight says "about the same" if within ±0.25% of that average.

```
GET /api/convert?base=USD&quote=INR&amount=1000
```
```json
{
  "amount": 1000.0, "base": "USD", "quote": "INR",
  "rate": 96.32472160356346, "result": 96324.72160356346, "date": "2026-10-02",
  "avg_3m": 95.6397099457951, "vs_avg_3m_pct": 0.7162418812819427,
  "source": "ecb",
  "insight": "Today's USD→INR rate is 0.72% above its 3-month average, so you get more INR than usual."
}
```

AED example (latest day comes from open.er-api, so `source` is `er_api`):

```
GET /api/convert?base=EUR&quote=AED&amount=500
```
```json
{
  "amount": 500.0, "base": "EUR", "quote": "AED",
  "rate": 4.12238125, "result": 2061.190625, "date": "2026-10-02",
  "avg_3m": 4.225083003968254, "vs_avg_3m_pct": -2.43076299026066,
  "source": "er_api",
  "insight": "Today's EUR→AED rate is 2.43% below its 3-month average, so you get less AED than usual."
}
```

### GET `/api/history?base=&quote=&range=`

One point per trading day in the range (no weekends), plus stats over those trading days.

```
GET /api/history?base=USD&quote=INR&range=1W
```
```json
{
  "base": "USD", "quote": "INR", "range": "1W",
  "points": [
    {"date": "2026-09-25", "rate": 95.81732877312986, "source": "ecb"},
    {"date": "2026-09-28", "rate": 95.983037440675, "source": "ecb"},
    {"date": "2026-09-29", "rate": 95.98502862175253, "source": "ecb"},
    {"date": "2026-09-30", "rate": 95.83487450462351, "source": "ecb"},
    {"date": "2026-10-01", "rate": 96.32855372632325, "source": "ecb"},
    {"date": "2026-10-02", "rate": 96.32472160356346, "source": "ecb"}
  ],
  "stats": {
    "start": 95.81732877312986, "end": 96.32472160356346, "change_pct": 0.5295418239376959,
    "min": 95.81732877312986, "min_date": "2026-09-25",
    "max": 96.32855372632325, "max_date": "2026-10-01",
    "mean": 96.0455907783446, "trading_days": 6
  },
  "insight": "Over the past week, 1 USD rose 0.53% against INR (95.82 → 96.32), ranging 95.82–96.33."
}
```

Note the jump from 2026-09-25 (Friday) to 2026-09-28 (Monday): the weekend has no data.

### GET `/api/gain-loss?base=&quote=&amount=&range=`

Value of holding `amount` of `base`, expressed in `quote`, each trading day. `daily_change` is `null` on the first day.

```
GET /api/gain-loss?base=USD&quote=INR&amount=10000&range=1W
```
```json
{
  "base": "USD", "quote": "INR", "amount": 10000.0, "range": "1W",
  "points": [
    {"date": "2026-09-25", "value": 958173.2877312986, "daily_change": null},
    {"date": "2026-09-28", "value": 959830.3744067501, "daily_change": 1657.0866754514864},
    {"date": "2026-09-29", "value": 959850.2862175254, "daily_change": 19.91181077528745},
    {"date": "2026-09-30", "value": 958348.7450462352, "daily_change": -1501.5411712902132},
    {"date": "2026-10-01", "value": 963285.5372632325, "daily_change": 4936.792216997361},
    {"date": "2026-10-02", "value": 963247.2160356346, "daily_change": -38.32122759788763}
  ],
  "total_change": 5073.928304336034, "total_change_pct": 0.5295418239376959,
  "up_days": 3, "down_days": 2,
  "insight": "10,000 USD held over the past week gained 5,073.93 INR (+0.53%). Best day 1 Oct: 4,936.79 INR; worst day 30 Sep: −1,501.54 INR."
}
```

### GET `/api/volatility?base=&quote=`

Volatility = standard deviation of daily log-returns × √252 × 100 (annualised %). `vol_30d` uses the last 30 returns, `vol_1y` the last 252. Level: < 5% `low`, 5–10% `moderate`, ≥ 10% `high`. `vs_norm`: ratio 30-day/1-year < 0.8 → "calmer than", > 1.25 → "more volatile than", otherwise "in line with". `rolling` = 30-day rolling volatility for the past ~252 trading days.

```
GET /api/volatility?base=USD&quote=INR
```
```json
{
  "base": "USD", "quote": "INR",
  "vol_30d": 3.6445288375315648, "vol_1y": 5.291542446918354,
  "typical_daily_move_pct": 0.2295837369074249,
  "level": "low", "vs_norm": "calmer than",
  "rolling": [{"date": "2025-10-08", "vol": 3.367508391447202}, {"date": "2025-10-09", "vol": 3.285305544648001}, "…"],
  "insight": "USD/INR risk is low: on a typical day it moves about ±0.23% (about ±23 INR on a 10,000 INR position), calmer than its usual level over the past year."
}
```

Pegged pair (`vol_1y < 0.5%` triggers a special sentence):

```
GET /api/volatility?base=USD&quote=AED
```
```json
{
  "vol_30d": 3.642409135490894e-13, "vol_1y": 2.934798302902239e-13, "level": "low", "vs_norm": "in line with",
  "insight": "USD/AED barely moves (the AED is pegged to the USD), so currency risk here is minimal.",
  "…": "…"
}
```

### GET `/api/heatmap?range=`

`matrix[i][j]` = % change over the range in the price of currency `i` measured in currency `j` (row strengthened if positive). Diagonal is `null`. `strength` = each currency's average of its row, sorted strongest first.

```
GET /api/heatmap?range=1M
```
```json
{
  "range": "1M",
  "currencies": ["USD", "EUR", "GBP", "JPY", "INR", "AED", "CHF", "CNY", "AUD", "CAD"],
  "matrix": [
    [null, 3.2516703786191536, 2.501888824997045, -1.5540961034757106, 1.4465007142578479, 0.0, 1.9876782460301223, -0.26289662532250624, 2.9081343219065525, 2.5332193918891965],
    [-3.1492666091458177, null, -0.72616893351235, -4.654420082960719, -1.748320058883135, -3.1492666091458177, -1.224185650415166, -3.4038839188304637, -0.3327171903881765, -0.6958250497017815],
    "… 8 more rows"
  ],
  "strength": [
    {"code": "JPY", "score": 3.200072218055746},
    {"code": "CNY", "score": 1.7201962715163808},
    "…",
    {"code": "EUR", "score": -2.120450455887047}
  ],
  "start_date": "2026-09-01", "end_date": "2026-10-02",
  "insight": "Over the past month, JPY was the strongest currency (+3.20% on average against the other nine) and EUR the weakest (−2.12%)."
}
```

### GET `/api/forecast?base=&quote=`

7-trading-day forecast from the Ridge model next to the naive baseline (`baseline` = last known rate), with an 80% error range and test metrics. Trained on first request for a given `data_until`, then cached in the DB. `verdict`:
- `beats_baseline`: average model MAE more than 1% lower than baseline MAE;
- `no_better_than_baseline`: otherwise;
- `pegged`: baseline error ≈ 0 (USD/AED, AED/USD).

`history` = the last 60 trading days, for the chart. Method details: [MODEL_REPORT.md](MODEL_REPORT.md).

```
GET /api/forecast?base=USD&quote=INR
```
```json
{
  "base": "USD", "quote": "INR", "data_until": "2026-10-02",
  "model_name": "Ridge(lagged returns)",
  "history": [{"date": "2026-07-13", "rate": 95.62106092436974}, {"date": "2026-07-14", "rate": 96.20473476545375}, "… 58 more"],
  "forecast": [
    {"date": "2026-10-05", "horizon": 1, "predicted": 96.33167002645575, "low": 95.9691834256758, "high": 96.73165885984722, "baseline": 96.32472160356346},
    {"date": "2026-10-06", "horizon": 2, "predicted": 96.31607116760243, "low": 95.79821866479328, "high": 96.90650646926213, "baseline": 96.32472160356346},
    "… horizons 3–7"
  ],
  "metrics": {
    "per_horizon": [
      {"horizon": 1, "model_mae_pct": 0.23857790909279858, "baseline_mae_pct": 0.23796302431128863, "model_rmse_pct": 0.33260136444605565, "baseline_rmse_pct": 0.3329673945672305},
      {"horizon": 2, "model_mae_pct": 0.3538287461681136, "baseline_mae_pct": 0.3581409957432769, "model_rmse_pct": 0.4724977327530331, "baseline_rmse_pct": 0.4789325966767099},
      "… horizons 3–7"
    ],
    "avg_model_mae_pct": 0.4791439577560129, "avg_baseline_mae_pct": 0.49809797300390046,
    "improvement_pct": 3.8052785345784157,
    "test_start": "2025-09-30", "test_end": "2026-09-23",
    "n_train": 996, "n_test": 251
  },
  "verdict": "beats_baseline",
  "insight": "The model expects 96.24 by 13 Oct (80% range 95.24–97.26). On recent unseen data it was 3.8% more accurate than simply assuming no change."
}
```

Other verdicts (real insights):

```
GET /api/forecast?base=EUR&quote=INR → "verdict": "no_better_than_baseline"
"Honest result: on recent unseen data the model was not more accurate than assuming no change (1.7% worse). Treat today's rate (108.12) as the best guess; a 7-day 80% range is 107.02–109.93."

GET /api/forecast?base=USD&quote=AED → "verdict": "pegged"
"USD/AED is pegged, so there is nothing to forecast: expect it to stay at 3.6725."
```

### Alerts

An alert = "tell me when 1 `base` is `above`/`below` `threshold` `quote`". Owned by an anonymous `client_id` (8–64 chars) that the browser generates and keeps in localStorage. Alerts are evaluated against the **latest daily rate** whenever they are created or listed; once triggered they stay triggered (`triggered_*` set once).

#### POST `/api/alerts`

```
POST /api/alerts
Content-Type: application/json

{"client_id": "doc-probe-1", "base": "USD", "quote": "INR", "direction": "above", "threshold": 80}
```
`201 Created` (already true on creation, so it triggers immediately):
```json
{
  "id": 3, "base": "USD", "quote": "INR", "direction": "above", "threshold": 80.0,
  "created_at": "2026-10-05T16:45:12.844243Z",
  "triggered_at": "2026-10-05T16:45:12.916065Z",
  "triggered_rate": 96.32472160356346,
  "triggered_on": "2026-10-02"
}
```
`client_id` is write-only (never returned). Validation errors → `400`:
```json
{"direction": ["\"sideways\" is not a valid choice."], "threshold": ["Ensure this value is greater than or equal to 0."]}
```
Same base and quote → `400 {"quote": ["must differ from base"]}`.

#### GET `/api/alerts?client_id=`

```
GET /api/alerts?client_id=doc-probe-1
```
```json
{
  "alerts": [
    {"id": 3, "base": "USD", "quote": "INR", "direction": "above", "threshold": 80.0,
     "created_at": "2026-10-05T16:45:12.844243Z", "triggered_at": "2026-10-05T16:45:12.916065Z",
     "triggered_rate": 96.32472160356346, "triggered_on": "2026-10-02"}
  ],
  "current_rates": {"USD/INR": 96.32472160356346},
  "insight": "1 of 1 alert(s) triggered. Latest: 1 USD went above 80.00 INR (rate 96.32 on 2026-10-02)."
}
```

#### DELETE `/api/alerts/<id>?client_id=`

```
DELETE /api/alerts/3?client_id=doc-probe-1   → 204 No Content
DELETE /api/alerts/3?client_id=someone-else  → 404 {"detail": "No Alert matches the given query."}
```

A client can only see and delete its own alerts. This is privacy-by-obscurity (anyone who knows an id could use it), which is acceptable for a no-login demo but not for production.
