# Testing

> Draft for team review. **Note:** there is no `tests/RESULTS.md` file in the repository. The results below come from a fresh run of the test suite, the frontend lint and the build on **2026-10-05** (Python 3.14.7, Node 22.23.2, macOS).

## Approach

1. **Automated backend tests (Django `TestCase`)** for every API endpoint and for the ML split. Each app has a `tests.py`.
2. **Offline by design.** Tests never call Frankfurter or open.er-api:
   - fetchers are replaced with `unittest.mock.patch` (including a simulated network failure);
   - analytics tests patch `refresh_if_stale` so `/api/rates/latest` can't reach the network;
   - price data comes from `rates/testing.py → seed_random_walk()`: a seeded (reproducible) random walk of 100–600 business days for the 8 ECB currencies, stored through the real `store_ecb_days()` code path, so AED is derived from the peg exactly as in production.
3. **Fast.** Django creates a throw-away in-memory SQLite database; the whole suite runs in ~2.4 s.
4. **Test the promises we make to users**, not only "returns 200": the AED peg, the converter maths, the heatmap sign symmetry, alert ownership, and above all the **no-leakage, no-shuffle** rules of the forecast.
5. **Frontend:** no automated tests (time constraint). Checked with the `oxlint` linter, a production build, and manual testing in the browser on desktop and phone widths.
6. **Manual API check** against the real local database: every endpoint and every documented error code was called once on 2026-10-05; the responses are the examples in [API.md](API.md).

Run:

```bash
cd backend
.venv/bin/python manage.py test          # add -v 2 to list each test
```

## Results: backend (2026-10-05)

```
Ran 16 tests in 2.411s

OK
```

**16 / 16 passed, 0 failed, 0 skipped.** (The line `ECB fetch failed: offline` printed during the run is expected: it is the warning logged by the simulated network failure test.)

| # | App | Test | What it proves | Result |
|---|---|---|---|---|
| 1 | rates | `test_aed_history_is_derived_from_usd_peg` | Storing an ECB day with USD=1.2 creates AED = 1.2 × 3.6725 tagged `derived_peg`, and EUR = 1 | ✅ |
| 2 | rates | `test_live_aed_uses_ecb_usd_for_consistency` | Live AED = open.er-api AED/USD × **ECB** USD/EUR, tagged `er_api` (no mixing of providers' EUR/USD) | ✅ |
| 3 | rates | `test_network_failure_is_logged_not_raised` | If both external APIs are down, `refresh()` does not crash; a failed `FetchLog` is written and there is no "last success" | ✅ |
| 4 | analytics | `test_cross_rate_is_ratio_of_eur_rates` | USD/INR = (INR per EUR) ÷ (USD per EUR) | ✅ |
| 5 | analytics | `test_endpoints_return_insight` | `/rates/latest`, `/convert`, `/history`, `/gain-loss`, `/volatility`, `/heatmap` all return 200 and a non-empty `insight` (6 sub-tests) | ✅ |
| 6 | analytics | `test_converter_math` | `result == amount × rate` | ✅ |
| 7 | analytics | `test_heatmap_is_antisymmetric_in_sign` | Matrix is 10×10, diagonal is empty, and if USD rose vs INR then INR fell vs USD | ✅ |
| 8 | analytics | `test_usd_aed_is_pegged` | USD/AED history min is exactly 3.6725 and points are labelled `derived_peg` | ✅ |
| 9 | analytics | `test_bad_params_are_400` | Same base/quote, range `2Y`, amount `-5` → 400 (3 sub-tests) | ✅ |
| 10 | forecasting | `test_time_split_train_strictly_before_test_with_gap` | Train indices all come before test, with a 7-day gap; both are contiguous (**not shuffled**); test ends at the last sample | ✅ |
| 11 | forecasting | `test_features_do_not_look_ahead` | Multiplying only the *future* prices (from day 60 on) by 5 leaves features for days 0–59 identical (**no leakage**) | ✅ |
| 12 | forecasting | `test_forecast_has_baseline_range_and_metrics` | `/api/forecast` returns 7 points, each with `low ≤ high` and a `baseline`; test set is non-empty; verdict is one of the two honest values | ✅ |
| 13 | forecasting | `test_pegged_pair` | USD/AED forecast verdict is `pegged` | ✅ |
| 14 | alerts | `test_triggers_only_when_crossed` | "above 90% of rate" triggers, "above 110%" doesn't, "below 110%" does | ✅ |
| 15 | alerts | `test_clients_only_see_and_delete_their_own` | Another `client_id` sees 0 alerts and gets 404 on delete; the owner gets 204 | ✅ |
| 16 | alerts | `test_rejects_same_currency` | Alert with base = quote → 400 | ✅ |

## Results: frontend (2026-10-05)

| Check | Command | Result |
|---|---|---|
| Lint | `npm run lint` (oxlint) | **0 errors, 3 warnings** (see below) |
| Production build | `npm run build` | ✅ built in 131 ms. JS 424.5 kB (139.3 kB gzipped), CSS 15.0 kB (4.1 kB gzipped) |
| Automated UI tests | | **None** |

The 3 lint warnings (not fixed; behaviour is correct, they are React style rules):
- `Header.jsx`: `Date.now()` called during render (used to compute how many days old the data is).
- `useApi.js` and `Alerts.jsx`: `setState` called inside `useEffect` (loading flag; pre-filling the alert threshold).

## Manual API checks (2026-10-05, real local data up to 2026-10-02)

| Check | Result |
|---|---|
| All 11 GET/POST endpoint calls return 200/201 with sensible values (successful DELETE → 204 is covered by test #15) | ✅ |
| `GET /api/history?base=USD&quote=USD` | 400 `{"quote": "must differ from base"}` ✅ |
| `GET /api/history?range=2Y` | 400 ✅ |
| `GET /api/convert?amount=-5` / `amount=abc` / `base=XYZ` | 400 ✅ |
| `GET /api/alerts` without `client_id` | 400 ✅ |
| `DELETE /api/alerts/999999?client_id=…` | 404 ✅ |
| `POST /api/forecast` | 405 ✅ |
| Weekend gap: 1W history goes 2026-09-25 (Fri) → 2026-09-28 (Mon), no filled rows | ✅ |
| EUR/AED latest = 3.6725 × 1.1225 = 4.12238125, `source: er_api` | ✅ |
| `train_forecasts` over all 90 pairs (see [MODEL_REPORT.md](MODEL_REPORT.md)) | ✅ 18 beat baseline, 2 pegged, rest reported honestly |

## Known gaps (honest list)

- **No frontend tests.** Widgets were only checked by hand.
- **Empty database → HTTP 500.** If the API is called before `backfill_history` has ever succeeded, the analytics endpoints crash (verified by simulating an empty table). The setup steps in the README always run the backfill first, but the API should return a friendly 503 instead.
- **The real external APIs are not tested automatically** (deliberately, to keep tests offline). A change in Frankfurter's or open.er-api's response format would only show up as a failed `FetchLog` entry and the "showing saved data" banner.
- **Volatility and gain/loss values are only checked for "returns an insight"**, not against hand-computed numbers.
- **No load/performance test.** Every request reads the whole `rates_rate` table into pandas (~22k rows, fast on a laptop, but it would not scale to many users).
- **Synthetic test data.** The random walk skips weekends (business days only) but has no ECB holidays and no real market behaviour.
