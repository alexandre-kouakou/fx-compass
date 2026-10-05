from rest_framework import serializers

from rates.constants import CODES
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    base = serializers.ChoiceField(choices=CODES)
    quote = serializers.ChoiceField(choices=CODES)
    client_id = serializers.CharField(min_length=8, max_length=64, write_only=True)
    threshold = serializers.FloatField(min_value=0, max_value=1e9)

    class Meta:
        model = Alert
        fields = ["id", "client_id", "base", "quote", "direction", "threshold",
                  "created_at", "triggered_at", "triggered_rate", "triggered_on"]
        read_only_fields = ["created_at", "triggered_at", "triggered_rate", "triggered_on"]

    def validate(self, data):
        if data["base"] == data["quote"]:
            raise serializers.ValidationError({"quote": "must differ from base"})
        return data
