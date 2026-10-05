"""Load cached rates into pandas and build cross rates for any base/quote pair."""

from datetime import timedelta

import pandas as pd

from rates.models import Rate

RANGES = {"1W": 7, "1M": 31, "3M": 92, "6M": 183, "1Y": 365, "5Y": 1827}


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(values, sources): one row per trading day, one column per currency, values per EUR."""
    rows = list(Rate.objects.values_list("date", "currency_id", "per_eur", "source"))
    if not rows:
        return pd.DataFrame(), pd.DataFrame()
    df = pd.DataFrame(rows, columns=["date", "code", "per_eur", "source"])
    df["date"] = pd.to_datetime(df["date"])
    df["per_eur"] = df["per_eur"].astype(float)
    values = df.pivot(index="date", columns="code", values="per_eur").sort_index()
    sources = df.pivot(index="date", columns="code", values="source").sort_index()
    return values, sources


def pair(values: pd.DataFrame, base: str, quote: str) -> pd.Series:
    """Units of `quote` per 1 `base`, for each trading day (gaps = weekends/holidays, not filled)."""
    return (values[quote] / values[base]).dropna()


def pair_source(sources: pd.DataFrame, base: str, quote: str) -> pd.Series:
    """'ecb' unless one leg is AED, in which case AED's source (derived_peg / er_api)."""
    if "AED" in (base, quote):
        return sources["AED"]
    return pd.Series("ecb", index=sources.index)


def window(series: pd.Series, range_key: str) -> pd.Series:
    start = series.index[-1] - timedelta(days=RANGES[range_key])
    return series[series.index >= start]
