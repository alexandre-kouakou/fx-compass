"""All dashboard numbers + the one-line insight shown above each widget."""

import math

import numpy as np
import pandas as pd

from rates.constants import CODES
from . import text
from .series import RANGES, load_frames, pair, pair_source, window

TRADING_DAYS_PER_YEAR = 252
AVG_3M_TRADING_DAYS = 63


def _d(ts) -> str:
    return pd.Timestamp(ts).date().isoformat()


def latest_rates(base: str) -> dict:
    values, sources = load_frames()
    rows = []
    for quote in CODES:
        if quote == base:
            continue
        s = pair(values, base, quote)
        rate, prev = s.iloc[-1], s.iloc[-2]
        rows.append({
            "code": quote,
            "name": text.NAMES[quote],
            "rate": rate,
            "change_pct": (rate / prev - 1) * 100,
            "source": pair_source(sources, base, quote).iloc[-1],
        })
    up = max(rows, key=lambda r: r["change_pct"])
    down = min(rows, key=lambda r: r["change_pct"])
    insight = (
        f"Since the previous trading day, 1 {base} buys {abs(up['change_pct']):.2f}% more {up['code']}"
        f" (biggest gain) and {abs(down['change_pct']):.2f}% less {down['code']} (biggest drop)."
    )
    return {"base": base, "date": _d(values.index[-1]), "rates": rows, "insight": insight}


def convert(amount: float, base: str, quote: str) -> dict:
    values, sources = load_frames()
    s = pair(values, base, quote)
    rate = s.iloc[-1]
    avg_3m = s.iloc[-AVG_3M_TRADING_DAYS:].mean()
    vs_avg = (rate / avg_3m - 1) * 100
    if abs(vs_avg) < 0.25:
        verdict = f"about the same as its 3-month average ({text.fmt_rate(avg_3m)})"
    elif vs_avg > 0:
        verdict = f"{text.fmt_pct(vs_avg, False)} above its 3-month average, so you get more {quote} than usual"
    else:
        verdict = f"{text.fmt_pct(-vs_avg, False)} below its 3-month average, so you get less {quote} than usual"
    return {
        "amount": amount, "base": base, "quote": quote,
        "rate": rate, "result": amount * rate, "date": _d(s.index[-1]),
        "avg_3m": avg_3m, "vs_avg_3m_pct": vs_avg,
        "source": pair_source(sources, base, quote).iloc[-1],
        "insight": f"Today's {base}→{quote} rate is {verdict}.",
    }


def history(base: str, quote: str, range_key: str) -> dict:
    values, sources = load_frames()
    full = pair(values, base, quote)
    s = window(full, range_key)
    src = pair_source(sources, base, quote).reindex(s.index)
    first, last = s.iloc[0], s.iloc[-1]
    change = (last / first - 1) * 100
    stats = {
        "start": first, "end": last, "change_pct": change,
        "min": s.min(), "min_date": _d(s.idxmin()),
        "max": s.max(), "max_date": _d(s.idxmax()),
        "mean": s.mean(), "trading_days": int(len(s)),
    }
    direction = "rose" if change >= 0 else "fell"
    insight = (
        f"Over {text.period(range_key)}, 1 {base} {direction} {text.fmt_pct(abs(change), False)} against {quote}"
        f" ({text.fmt_rate(first)} → {text.fmt_rate(last)}), ranging {text.fmt_rate(s.min())}–{text.fmt_rate(s.max())}."
    )
    return {
        "base": base, "quote": quote, "range": range_key,
        "points": [{"date": _d(d), "rate": v, "source": src[d]} for d, v in s.items()],
        "stats": stats, "insight": insight,
    }


def gain_loss(base: str, quote: str, amount: float, range_key: str) -> dict:
    """Holding `amount` of base: what is it worth in quote each day, and how much did it change?"""
    values, _ = load_frames()
    s = window(pair(values, base, quote), range_key)
    worth = s * amount
    daily = worth.diff()
    total = worth.iloc[-1] - worth.iloc[0]
    pct = (worth.iloc[-1] / worth.iloc[0] - 1) * 100
    best, worst = daily.idxmax(), daily.idxmin()
    word = "gained" if total >= 0 else "lost"
    insight = (
        f"{amount:,.0f} {base} held over {text.period(range_key)} {word} {text.fmt_money(abs(total), quote)}"
        f" ({text.fmt_pct(pct)}). Best day {best:%-d %b}: {text.fmt_money(daily[best], quote)};"
        f" worst day {worst:%-d %b}: {text.fmt_money(daily[worst], quote)}."
    )
    return {
        "base": base, "quote": quote, "amount": amount, "range": range_key,
        "points": [
            {"date": _d(d), "value": worth[d], "daily_change": None if math.isnan(daily[d]) else daily[d]}
            for d in worth.index
        ],
        "total_change": total, "total_change_pct": pct,
        "up_days": int((daily > 0).sum()), "down_days": int((daily < 0).sum()),
        "insight": insight,
    }


def _annualised_vol(returns: pd.Series) -> float:
    return float(returns.std() * math.sqrt(TRADING_DAYS_PER_YEAR) * 100)


def volatility(base: str, quote: str) -> dict:
    """30-trading-day annualised volatility vs the pair's own 1-year norm."""
    values, _ = load_frames()
    s = pair(values, base, quote)
    r = np.log(s).diff().dropna()
    vol_30 = _annualised_vol(r.iloc[-30:])
    vol_1y = _annualised_vol(r.iloc[-TRADING_DAYS_PER_YEAR:])
    rolling = (r.rolling(30).std() * math.sqrt(TRADING_DAYS_PER_YEAR) * 100).dropna().iloc[-TRADING_DAYS_PER_YEAR:]
    daily_move = vol_30 / math.sqrt(TRADING_DAYS_PER_YEAR)

    if vol_30 < 5:
        level = "low"
    elif vol_30 < 10:
        level = "moderate"
    else:
        level = "high"
    ratio = vol_30 / vol_1y if vol_1y > 0 else 1
    trend = "calmer than" if ratio < 0.8 else "more volatile than" if ratio > 1.25 else "in line with"

    if vol_1y < 0.5:
        insight = f"{base}/{quote} barely moves (the AED is pegged to the USD), so currency risk here is minimal."
    else:
        insight = (
            f"{base}/{quote} risk is {level}: on a typical day it moves about ±{daily_move:.2f}%"
            f" (about ±{10_000 * daily_move / 100:,.0f} {quote} on a 10,000 {quote} position), {trend} its usual level over the past year."
        )
    return {
        "base": base, "quote": quote,
        "vol_30d": vol_30, "vol_1y": vol_1y, "typical_daily_move_pct": daily_move,
        "level": level, "vs_norm": trend,
        "rolling": [{"date": _d(d), "vol": v} for d, v in rolling.items()],
        "insight": insight,
    }


def heatmap(range_key: str) -> dict:
    """matrix[i][j] = % change in the price of currency i measured in currency j."""
    values, _ = load_frames()
    w = values[CODES]
    w = w[w.index >= w.index[-1] - pd.Timedelta(days=RANGES[range_key])]
    first, last = w.iloc[0], w.iloc[-1]
    matrix, strength = [], {}
    for i in CODES:
        row = []
        for j in CODES:
            if i == j:
                row.append(None)
            else:
                # price of i in j = per_eur[j] / per_eur[i]
                row.append(((last[j] / last[i]) / (first[j] / first[i]) - 1) * 100)
        matrix.append(row)
        strength[i] = float(np.mean([v for v in row if v is not None]))
    ranked = sorted(strength, key=strength.get, reverse=True)
    top, bottom = ranked[0], ranked[-1]
    insight = (
        f"Over {text.period(range_key)}, {top} was the strongest currency ({text.fmt_pct(strength[top])} on average"
        f" against the other nine) and {bottom} the weakest ({text.fmt_pct(strength[bottom])})."
    )
    return {
        "range": range_key, "currencies": CODES, "matrix": matrix,
        "strength": [{"code": c, "score": strength[c]} for c in ranked],
        "start_date": _d(w.index[0]), "end_date": _d(w.index[-1]),
        "insight": insight,
    }
