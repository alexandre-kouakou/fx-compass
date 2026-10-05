"""Synthetic rate data for offline tests (never used by the app itself)."""

import numpy as np
import pandas as pd

from .constants import ECB_SYMBOLS
from .services import ensure_currencies, store_ecb_days

START_LEVELS = {"USD": 1.1, "GBP": 0.85, "JPY": 160.0, "INR": 95.0, "CHF": 0.95,
                "CNY": 7.8, "AUD": 1.6, "CAD": 1.5}


def seed_random_walk(days: int = 600, seed: int = 0):
    ensure_currencies()
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2023-01-02", periods=days)
    data = {}
    levels = dict(START_LEVELS)
    for d in dates:
        for code in ECB_SYMBOLS:
            levels[code] *= float(np.exp(rng.normal(0, 0.004)))
        data[d.date()] = dict(levels)
    store_ecb_days(data)
    return dates
