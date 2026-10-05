"""Thin clients for the external rate APIs. Return plain dicts; no DB access here."""

from datetime import date, datetime, timezone

import requests
from django.conf import settings

from .constants import ECB_SYMBOLS


def fetch_frankfurter(start: date, end: date | None = None) -> dict[date, dict[str, float]]:
    """ECB daily reference rates (base EUR) for every business day in [start, end]."""
    span = f"{start.isoformat()}..{end.isoformat() if end else ''}"
    resp = requests.get(
        f"{settings.FRANKFURTER_URL}/{span}",
        params={"symbols": ",".join(ECB_SYMBOLS)},
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        date.fromisoformat(day): values
        for day, values in data["rates"].items()
        # Frankfurter may include the business day *before* start; keep only what we asked for.
        if date.fromisoformat(day) >= start
    }


def fetch_aed_live() -> tuple[float, datetime]:
    """Latest AED per USD from open.er-api.com (free, no key, updated daily)."""
    resp = requests.get(settings.AED_LIVE_URL, timeout=settings.HTTP_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()
    if data.get("result") != "success":
        raise ValueError(f"open.er-api.com returned {data.get('result')}")
    updated = datetime.fromtimestamp(data["time_last_update_unix"], tz=timezone.utc)
    return float(data["rates"]["AED"]), updated
