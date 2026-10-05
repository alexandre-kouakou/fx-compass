"""Ridge regression on recent log-returns vs a naive 'no change' baseline.

Honesty rules (see CLAUDE.md):
- time-based split, never shuffled: test = most recent TEST_FRACTION of samples
- a GAP of HORIZON days between train and test so no training target overlaps the test period
- features at day t only use data up to and including day t (no look-ahead)
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HORIZON = 7  # trading days
TEST_FRACTION = 0.2
LOOKBACK_YEARS = 5
MODEL_NAME = "Ridge(lagged returns)"


def make_features(series: pd.Series) -> pd.DataFrame:
    lp = np.log(series)
    r = lp.diff()
    feats = {f"ret_lag{k}": r.shift(k) for k in range(5)}
    feats["mean_ret_5"] = r.rolling(5).mean()
    feats["mean_ret_20"] = r.rolling(20).mean()
    feats["vol_20"] = r.rolling(20).std()
    feats["dist_from_ma20"] = lp - lp.rolling(20).mean()
    return pd.DataFrame(feats)


def make_targets(series: pd.Series) -> pd.DataFrame:
    lp = np.log(series)
    return pd.DataFrame({h: lp.shift(-h) - lp for h in range(1, HORIZON + 1)})


def time_split(n: int, gap: int = HORIZON, test_fraction: float = TEST_FRACTION):
    """Index ranges: train = [0, train_end), test = [test_start, n). Train is strictly earlier."""
    test_start = int(n * (1 - test_fraction))
    train_end = test_start - gap
    return np.arange(0, train_end), np.arange(test_start, n)


def _model():
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0))


@dataclass
class HorizonResult:
    horizon: int
    model_mae_pct: float
    baseline_mae_pct: float
    model_rmse_pct: float
    baseline_rmse_pct: float
    err_lo: float  # log-return error quantiles on the test set
    err_hi: float
    pred_log_return: float  # forecast from the latest day, model refit on all data


def run(series: pd.Series):
    series = series[series.index >= series.index[-1] - pd.DateOffset(years=LOOKBACK_YEARS)]
    X_all = make_features(series)
    Y_all = make_targets(series)
    usable = X_all.notna().all(axis=1) & Y_all.notna().all(axis=1)
    X, Y = X_all[usable], Y_all[usable]
    train_idx, test_idx = time_split(len(X))
    x_last = X_all.iloc[[-1]]

    results = []
    for h in range(1, HORIZON + 1):
        y = Y[h].to_numpy()
        m = _model().fit(X.iloc[train_idx], y[train_idx])
        pred = m.predict(X.iloc[test_idx])
        err = y[test_idx] - pred
        base_err = y[test_idx]  # baseline predicts 0 change
        final = _model().fit(X, y)
        results.append(HorizonResult(
            horizon=h,
            model_mae_pct=float(np.mean(np.abs(err)) * 100),
            baseline_mae_pct=float(np.mean(np.abs(base_err)) * 100),
            model_rmse_pct=float(np.sqrt(np.mean(err**2)) * 100),
            baseline_rmse_pct=float(np.sqrt(np.mean(base_err**2)) * 100),
            err_lo=float(np.quantile(err, 0.1)),
            err_hi=float(np.quantile(err, 0.9)),
            pred_log_return=float(final.predict(x_last)[0]),
        ))
    info = {
        "n_train": len(train_idx), "n_test": len(test_idx),
        "test_start": X.index[test_idx[0]].date(), "test_end": X.index[test_idx[-1]].date(),
    }
    return results, info
