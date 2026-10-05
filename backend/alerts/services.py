from django.utils import timezone

from analytics import text
from analytics.series import load_frames, pair
from .models import Alert


def evaluate(alerts: list[Alert]) -> dict:
    """Trigger any untriggered alert whose pair crossed its threshold on the latest day."""
    values, _ = load_frames()
    current = {}
    for a in alerts:
        key = (a.base, a.quote)
        if key not in current:
            s = pair(values, a.base, a.quote)
            current[key] = (float(s.iloc[-1]), s.index[-1].date())
        rate, day = current[key]
        if a.triggered_at is None and a.is_hit(rate):
            a.triggered_at, a.triggered_rate, a.triggered_on = timezone.now(), rate, day
            a.save(update_fields=["triggered_at", "triggered_rate", "triggered_on"])
    return {f"{b}/{q}": r for (b, q), (r, _) in current.items()}


def insight(alerts: list[Alert], current: dict) -> str:
    if not alerts:
        return "No alerts yet. Set a level and we'll flag it here when the daily rate crosses it."
    hit = [a for a in alerts if a.triggered_at]
    if not hit:
        return f"None of your {len(alerts)} alert(s) have triggered yet."
    a = hit[0]
    return (
        f"{len(hit)} of {len(alerts)} alert(s) triggered. Latest: 1 {a.base} went {a.direction} "
        f"{text.fmt_rate(a.threshold)} {a.quote} (rate {text.fmt_rate(a.triggered_rate)} on {a.triggered_on})."
    )
