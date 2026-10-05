"""Plain-language formatting helpers for insight sentences."""

from rates.constants import CURRENCIES

SYMBOLS = {c[0]: c[2] for c in CURRENCIES}
NAMES = {c[0]: c[1] for c in CURRENCIES}
RANGE_WORDS = {"1W": "week", "1M": "month", "3M": "3 months", "6M": "6 months", "1Y": "year", "5Y": "5 years"}


def fmt_rate(v: float) -> str:
    if v >= 10:
        return f"{v:,.2f}"
    if v >= 0.1:
        return f"{v:,.4f}"
    return f"{v:.6f}"


def fmt_money(v: float, code: str) -> str:
    sign = "−" if v < 0 else ""
    return f"{sign}{abs(v):,.2f} {code}"


def fmt_pct(v: float, signed: bool = True) -> str:
    if signed:
        return f"{'+' if v >= 0 else '−'}{abs(v):.2f}%"
    return f"{v:.2f}%"


def period(range_key: str) -> str:
    return f"the past {RANGE_WORDS[range_key]}"
