# Model report: 7-day exchange-rate forecast

> Draft for team review. All numbers are real: they come from the `ModelMetric` table after running `train_forecasts` on data up to **2026-10-02** (trained 2026-10-05). Code: `backend/forecasting/model.py` and `services.py`.

## 1. Question and honesty rule

**Question:** given daily reference rates up to today, what will a currency pair's rate be 1 to 7 trading days from now?

**Honesty rule:** a forecast only means something if it beats the simplest possible guess. Our yardstick is the **naive baseline: "tomorrow = today"** (the rate stays where it is). Finance theory (the random-walk view of exchange rates, see Meese & Rogoff 1983 and the efficient-markets discussion in Eun & Resnick) says this baseline is very hard to beat at short horizons. The dashboard always shows the model next to the baseline and states the verdict for each pair.

## 2. Data

| Item | Value |
|---|---|
| Source | ECB euro foreign exchange reference rates via Frankfurter (one rate per ECB working day, ~16:00 CET) |
| Currencies | USD, EUR, GBP, JPY, INR, CHF, CNY, AUD, CAD from the ECB; AED derived from the USD peg (1 USD = 3.6725 AED) |
| Stored history | 2018-01-02 → 2026-10-02, 2,241 trading days × 10 currencies = 22,410 rows |
| Used for the model | The **last 5 years** of each pair (`LOOKBACK_YEARS = 5`), i.e. from about 2021-10-02 |
| Pairs | 90 ordered pairs (10 × 9), each modelled separately |
| Frequency | Daily, trading days only. Weekends and ECB holidays are absent and **not filled** |

## 3. Preprocessing

1. **Cross rates.** Every rate is stored against EUR. A pair is computed as `quote per base = per_eur[quote] / per_eur[base]` (`analytics/series.pair`). Days where either side is missing are dropped.
2. **Log prices and log-returns.** `lp = log(rate)`, `r_t = lp_t − lp_{t−1}`. Log-returns are roughly symmetric and scale-free, so one recipe works for USD/INR (~96) and EUR/GBP (~0.85) alike.
3. **Five-year window**, as above.
4. **Drop incomplete rows.** The first 20 rows (rolling windows not yet full) and the last 7 rows (target not yet known) are removed. For every pair this left **1,254 usable samples**.
5. **Standardisation** (`StandardScaler`) is fitted inside the pipeline, **on the training rows only**, so test-set statistics never leak into training.

## 4. Features

All features for day *t* use only data **up to and including day *t*** (no look-ahead; proven by `test_features_do_not_look_ahead`).

| Feature | Definition | Idea |
|---|---|---|
| `ret_lag0` … `ret_lag4` | Last 5 daily log-returns `r_t, r_{t−1}, …, r_{t−4}` | Short-term momentum / reversal |
| `mean_ret_5` | Mean of the last 5 returns | 1-week trend |
| `mean_ret_20` | Mean of the last 20 returns | ~1-month trend |
| `vol_20` | Std of the last 20 returns | Recent risk regime |
| `dist_from_ma20` | `lp_t − mean(lp over last 20 days)` | How stretched the rate is from its 1-month average (mean reversion) |

**Targets:** for each horizon *h* = 1…7 trading days, `y_h = lp_{t+h} − lp_t` (the log change from today to *h* days ahead).

## 5. Models

| | Naive baseline | Ridge regression (our model) |
|---|---|---|
| Prediction | `y_h = 0` (rate unchanged) | Linear combination of the 9 features |
| Library | n/a | scikit-learn `make_pipeline(StandardScaler(), Ridge(alpha=10.0))` |
| Fitted | No | One model **per horizon** (7 models per pair, 630 in total) |

**Why Ridge:** it is fast (all 90 pairs train in ~10 s on a laptop), stable with correlated features (the lagged returns overlap with the rolling means), its L2 penalty (`alpha=10`) pulls coefficients towards zero, so when there's no signal it falls back to roughly the baseline, and it's easy to explain. ARIMA, Prophet and LSTM were considered and rejected as slower, more fragile, and not expected to beat a random walk on daily FX either (see `DECISIONS.md`).

## 6. Train / test split

- **Time-based, never shuffled** (`model.time_split`). The most recent 20% of samples are the test set; everything before is training.
- **7-day gap** between the last training sample and the first test sample, so no training *target* (which looks up to 7 days ahead) overlaps the test period.
- For every pair:

| | Samples | Period (sample dates *t*) |
|---|---|---|
| Train | 996 | ≈ 2021-10 → 2025-09 |
| Gap | 7 | |
| Test | 251 | **2025-09-30 → 2026-09-23** (targets reach 2026-10-02) |

- After scoring, a final model per horizon is **refit on all 1,254 samples** and used to forecast from the latest day (2026-10-02). The reported metrics always come from the train-only model on the unseen test year.

## 7. Metrics

Measured on the test period, in **% of the rate** (errors are log differences × 100, which ≈ percentage error):

- **MAE** (mean absolute error): the average size of a miss. The headline number, also used for the verdict.
- **RMSE** (root mean squared error): punishes big misses more.
- **Improvement** = `1 − (model MAE ÷ baseline MAE)`, averaged over the 7 horizons.
- **Verdict:** `beats_baseline` if improvement > 1%; `pegged` if the baseline error is ~0; otherwise `no_better_than_baseline`.
- **80% error range:** the 10th and 90th percentiles of the test-set errors, added to the forecast (shaded band on the chart).

## 8. Results (data up to 2026-10-02)

### 8.1 Scorecard across all 90 pairs

| Outcome | Ordered pairs | Unordered pairs* |
|---|---|---|
| Model beats baseline by > 1% (MAE) | **18** | 9 |
| Within ±1% of baseline | 30 | 15 |
| Model worse by > 1% | 40 | 20 |
| Pegged (USD/AED, AED/USD): nothing to forecast | 2 | 1 |
| **Total** | **90** | **45** |

\*X/Y and Y/X give **identical** errors: their log-returns are exact negatives, and a linear model with standardised inputs simply flips the sign of its prediction. So there are really 45 distinct results, not 90. Also, because AED moves exactly with USD, every AED/X pair duplicates USD/X, so **only 36 pairs carry independent information** (the 9 ECB currencies taken two at a time).

Other summary numbers (88 non-pegged ordered pairs):
- Median improvement: **−0.42%**; mean −2.01%; best +4.02% (GBP/JPY); worst −15.6% (GBP/CHF).
- Model RMSE lower than baseline RMSE on 30 of 88.
- Average MAE across all pairs and horizons: **model 0.581% vs baseline 0.572%.**

### 8.2 Error by horizon (average over the 88 non-pegged pairs)

| Days ahead | Model MAE | Naive MAE | Model RMSE | Naive RMSE |
|---|---|---|---|---|
| 1 | 0.283% | 0.280% | 0.382% | 0.378% |
| 2 | 0.413% | 0.409% | 0.547% | 0.541% |
| 3 | 0.514% | 0.507% | 0.671% | 0.661% |
| 4 | 0.605% | 0.595% | 0.782% | 0.769% |
| 5 | 0.685% | 0.674% | 0.878% | 0.862% |
| 6 | 0.756% | 0.743% | 0.962% | 0.944% |
| 7 | 0.811% | 0.797% | 1.025% | 1.005% |

On average the model is ~1–2% *worse* than the baseline at every horizon. Errors grow roughly with √horizon, as expected for a random walk.

### 8.3 Unordered pairs, ranked by MAE improvement

| Pair | Model MAE | Naive MAE | Improvement |
|---|---|---|---|
| GBP/JPY | 0.624% | 0.651% | **+4.0%** |
| INR/USD (= AED/INR) | 0.479% | 0.498% | **+3.8%** |
| CNY/INR | 0.504% | 0.519% | **+3.1%** |
| CNY/JPY | 0.709% | 0.730% | **+3.0%** |
| EUR/JPY | 0.586% | 0.601% | **+2.5%** |
| CAD/GBP | 0.423% | 0.433% | **+2.2%** |
| CAD/CNY | 0.447% | 0.457% | **+2.1%** |
| CNY/GBP | 0.496% | 0.501% | **+1.00%** |
| EUR/USD (= AED/EUR) | 0.516% | 0.521% | +0.99% (just under the 1% bar) |
| … 13 more within ±1% … | | | |
| CHF/INR | 0.738% | 0.731% | −0.9% |
| EUR/INR | 0.667% | 0.656% | −1.7% |
| EUR/GBP | 0.293% | 0.283% | −3.6% |
| AUD/USD (= AED/AUD) | 0.776% | 0.735% | −5.7% |
| CNY/USD (= AED/CNY) | 0.214% | 0.190% | −12.4% |
| AUD/EUR | 0.610% | 0.540% | −12.9% |
| AUD/CHF | 0.654% | 0.577% | −13.4% |
| CHF/GBP | 0.459% | 0.397% | −15.6% |

(The full list is printed by `python manage.py train_forecasts`.)

### 8.4 Persona pairs

| Pair | Model MAE | Naive MAE | Improvement | Verdict shown |
|---|---|---|---|---|
| USD/INR (Gurpreet, Aïcha) | 0.479% | 0.498% | +3.8% | Beats naive baseline |
| EUR/INR (Gurpreet) | 0.667% | 0.656% | −1.7% | No better than naive |
| GBP/INR | 0.713% | 0.715% | +0.3% | No better than naive |
| USD/AED | 0 | 0 | n/a | Pegged |

USD/INR per horizon: the model's edge grows with the horizon, from none at 1 day (0.239% vs 0.238%) to 0.657% vs 0.705% at 7 days.

Latest USD/INR forecast (from 2026-10-02, rate 96.32): **96.24 by 13 Oct**, 80% range 95.24–97.26.

## 9. Interpretation

- **Exchange rates are close to a random walk at a 1–7 day horizon.** Our model beats "no change" by a meaningful margin on only 9 of 45 distinct pairs, and only by 1–4%. On average it is slightly worse. This matches the classic finding (Meese & Rogoff, 1983) that structural and statistical models struggle to beat a random walk out of sample, and it fits the weak-form efficient-market idea: if past prices predicted future prices reliably, traders would already have used it.
- **Where the model helps** (USD/INR, CNY/INR, CNY/JPY, GBP/JPY) the rates were trending or managed in the test year, so the trend and mean-reversion features carry a little signal. The RBI's and PBoC's management of INR and CNY is a plausible reason, but we did not test it.
- **Where it hurts most** (CHF/GBP, AUD/CHF, AUD/EUR, CNY/USD) a pattern learned in 2021–2025 did not hold in 2025–26. CNY/USD is tightly managed, so the baseline error is already tiny (0.19%) and any small model error looks large in relative terms.
- **The most useful output is the error range, not the point forecast.** For USD/INR, a 7-day 80% range of about ±1% (~95.2–97.3) tells an exporter like Gurpreet how much a week's delay could cost, and that is useful even when the point forecast is no better than "no change".
- **What we tell users:** for each pair the dashboard shows the verdict ("Beats naive baseline" / "No better than naive" / "Pegged"), both errors, the test dates, and a per-horizon table. If the model doesn't beat the baseline, the insight says "Treat today's rate as the best guess".

## 10. Limitations

1. **One test window.** The scores come from a single test year (2025-09-30 → 2026-09-23). A walk-forward evaluation over several years would be more reliable, and with 251 test days a 1–4% MAE difference may not be statistically significant (we ran no Diebold–Mariano test).
2. **Verdict threshold is arbitrary.** "> 1% better" is our choice, not a statistical test.
3. **Only past prices.** No interest-rate differentials, inflation, trade balance, central-bank events or news. These drive currencies in theory (interest rate parity, PPP), but they're not in the model.
4. **The error range is not independently validated.** It's taken from the same test errors it's reported on, then applied to a model refit on all data, so real-world coverage may be below 80%.
5. **The final model has also seen the test year** (refit on all data). That's standard practice, but the live forecast itself has no out-of-sample score until the future arrives.
6. **Forecast dates are Mon–Fri business days;** ECB holidays are not excluded, so a "7-day" target date can land on a holiday.
7. **AED is synthetic.** Its history comes from the peg, so AED pairs carry no information beyond USD pairs, and a de-pegging event could not be anticipated.
8. **Daily reference rates, not tradable prices.** No bid/ask spread or bank margin; real conversions cost more than the rate shown.
9. **Retraining only on demand.** A pair is retrained the first time it's requested after a new rate day; old rows stay in the DB (no cleanup).
10. **Educational only, not financial advice.**

## 11. How to reproduce

```bash
cd backend
.venv/bin/python manage.py backfill_history    # data up to the latest ECB day
.venv/bin/python manage.py train_forecasts     # prints model vs baseline MAE for all 90 pairs
.venv/bin/python manage.py test forecasting    # split and leakage tests
```

The numbers will change slightly once newer ECB days are added (`data_until` moves forward).
