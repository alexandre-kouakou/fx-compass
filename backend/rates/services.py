"""Store rates in the DB. The frontend only ever reads from here (works offline)."""

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from . import sources
from .constants import CURRENCIES
from .models import Currency, FetchLog, Rate

log = logging.getLogger(__name__)


def ensure_currencies():
    for code, name, symbol, in_ecb in CURRENCIES:
        Currency.objects.update_or_create(
            code=code, defaults={"name": name, "symbol": symbol, "in_ecb": in_ecb}
        )


def _upsert(day, code, per_eur, source):
    Rate.objects.update_or_create(
        date=day,
        currency_id=code,
        defaults={"per_eur": Decimal(str(per_eur)).quantize(Decimal("1e-10")), "source": source},
    )


@transaction.atomic
def store_ecb_days(days: dict[date, dict[str, float]]) -> int:
    """Save ECB rows, EUR=1, and AED derived from the USD peg (AED isn't in ECB data)."""
    for day, values in days.items():
        _upsert(day, "EUR", 1, Rate.SOURCE_ECB)
        for code, value in values.items():
            _upsert(day, code, value, Rate.SOURCE_ECB)
        if "USD" in values:
            _upsert(day, "AED", values["USD"] * settings.AED_USD_PEG, Rate.SOURCE_DERIVED_PEG)
    return len(days)


def update_from_ecb(start: date) -> FetchLog:
    try:
        days = sources.fetch_frankfurter(start)
        n = store_ecb_days(days)
        latest = max(days) if days else None
        return FetchLog.objects.create(source="ecb", ok=True, rows=n, latest_date=latest)
    except Exception as exc:  # network down, API change... keep serving cached data
        log.warning("ECB fetch failed: %s", exc)
        return FetchLog.objects.create(source="ecb", ok=False, message=str(exc)[:500])


def update_aed_live() -> FetchLog:
    """Overwrite AED on the latest stored date with the live open.er-api.com value."""
    latest = Rate.objects.filter(currency_id="EUR").order_by("-date").values_list("date", flat=True).first()
    if latest is None:
        return FetchLog.objects.create(source="er_api", ok=False, message="no ECB data yet")
    try:
        aed_per_eur, updated = sources.fetch_aed_live()
        _upsert(latest, "AED", aed_per_eur, Rate.SOURCE_ER_API)
        return FetchLog.objects.create(
            source="er_api", ok=True, rows=1, latest_date=latest,
            message=f"provider updated {updated.isoformat()}",
        )
    except Exception as exc:
        log.warning("AED live fetch failed: %s", exc)
        return FetchLog.objects.create(source="er_api", ok=False, message=str(exc)[:500])


def refresh(full: bool = False):
    """Fetch everything new since the last stored day (or since HISTORY_START if full)."""
    ensure_currencies()
    last = Rate.objects.order_by("-date").values_list("date", flat=True).first()
    if full or last is None:
        start = date.fromisoformat(settings.HISTORY_START)
    else:
        start = last + timedelta(days=1)
    ecb_log = None
    if start <= timezone.now().date():
        ecb_log = update_from_ecb(start)
    aed_log = update_aed_live()
    return ecb_log, aed_log


def refresh_if_stale():
    """Called by API requests: refresh at most every REFRESH_AFTER_HOURS, never raise."""
    last_try = FetchLog.objects.filter(source="ecb").first()
    cutoff = timezone.now() - timedelta(hours=settings.REFRESH_AFTER_HOURS)
    if last_try is None or last_try.created_at < cutoff:
        try:
            refresh()
        except Exception as exc:
            log.warning("refresh failed: %s", exc)


def last_success():
    return FetchLog.objects.filter(source="ecb", ok=True).first()
