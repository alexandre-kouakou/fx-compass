from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Currency, FetchLog, Rate
from .services import last_success


@api_view(["GET"])
def currencies(request):
    return Response([
        {"code": c.code, "name": c.name, "symbol": c.symbol, "in_ecb": c.in_ecb}
        for c in Currency.objects.all()
    ])


@api_view(["GET"])
def status(request):
    ok = last_success()
    latest = Rate.objects.order_by("-date").values_list("date", flat=True).first()
    last_try = FetchLog.objects.filter(source="ecb").first()
    return Response({
        "latest_rate_date": latest,
        "last_successful_fetch": ok.created_at if ok else None,
        "last_fetch_failed": bool(last_try and not last_try.ok),
        "sources": [
            {"name": "European Central Bank daily reference rates via Frankfurter", "url": "https://frankfurter.dev"},
            {"name": "Rates By Exchange Rate API (live AED)", "url": "https://www.exchangerate-api.com"},
        ],
        "notes": [
            "Daily reference rates (published ~16:00 CET on ECB working days), not real-time quotes.",
            "AED history is derived from the USD peg (1 USD = 3.6725 AED); the latest AED comes from open.er-api.com.",
        ],
    })
