from django.db import models


class Alert(models.Model):
    """'Tell me when 1 BASE is above/below THRESHOLD QUOTE'. Owned by an anonymous browser id."""

    ABOVE, BELOW = "above", "below"

    client_id = models.CharField(max_length=64, db_index=True)
    base = models.CharField(max_length=3)
    quote = models.CharField(max_length=3)
    direction = models.CharField(max_length=5, choices=[(ABOVE, "above"), (BELOW, "below")])
    threshold = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    triggered_rate = models.FloatField(null=True, blank=True)
    triggered_on = models.DateField(null=True, blank=True, help_text="Rate date that crossed the threshold")

    class Meta:
        ordering = ["-created_at"]

    def is_hit(self, rate: float) -> bool:
        return rate > self.threshold if self.direction == self.ABOVE else rate < self.threshold
