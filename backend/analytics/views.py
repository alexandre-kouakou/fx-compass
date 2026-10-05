from rest_framework.decorators import api_view
from rest_framework.response import Response

from rates.services import refresh_if_stale
from . import params, services


@api_view(["GET"])
def latest(request):
    refresh_if_stale()
    return Response(services.latest_rates(params.currency(request, "base", "USD")))


@api_view(["GET"])
def convert(request):
    base, quote = params.pair(request)
    return Response(services.convert(params.amount(request), base, quote))


@api_view(["GET"])
def history(request):
    base, quote = params.pair(request)
    return Response(services.history(base, quote, params.range_key(request)))


@api_view(["GET"])
def gain_loss(request):
    base, quote = params.pair(request)
    return Response(services.gain_loss(base, quote, params.amount(request, "10000"), params.range_key(request)))


@api_view(["GET"])
def volatility(request):
    base, quote = params.pair(request)
    return Response(services.volatility(base, quote))


@api_view(["GET"])
def heatmap(request):
    return Response(services.heatmap(params.range_key(request)))
