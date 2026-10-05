from rest_framework.decorators import api_view
from rest_framework.response import Response

from analytics import params
from . import services


@api_view(["GET"])
def forecast(request):
    base, quote = params.pair(request)
    return Response(services.forecast(base, quote))
