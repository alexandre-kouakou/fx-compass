from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Alert
from .serializers import AlertSerializer
from .services import evaluate, insight


def _client_id(request):
    cid = request.query_params.get("client_id", "")
    if not 8 <= len(cid) <= 64:
        raise ValidationError({"client_id": "required (8-64 chars)"})
    return cid


@api_view(["GET", "POST"])
def alert_list(request):
    if request.method == "POST":
        ser = AlertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        alert = ser.save()
        evaluate([alert])
        return Response(AlertSerializer(alert).data, status=status.HTTP_201_CREATED)

    alerts = list(Alert.objects.filter(client_id=_client_id(request)))
    current = evaluate(alerts)
    return Response({
        "alerts": AlertSerializer(alerts, many=True).data,
        "current_rates": current,
        "insight": insight(alerts, current),
    })


@api_view(["DELETE"])
def alert_detail(request, pk):
    get_object_or_404(Alert, pk=pk, client_id=_client_id(request)).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
