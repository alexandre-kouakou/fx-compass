from django.db import models


class ModelMetric(models.Model):
    """How the model did on the held-out most-recent period, vs the naive baseline."""

    base = models.CharField(max_length=3)
    quote = models.CharField(max_length=3)
    data_until = models.DateField(help_text="Last rate date the model saw")
    horizon = models.PositiveSmallIntegerField(help_text="Trading days ahead")
    model_name = models.CharField(max_length=64)
    model_mae_pct = models.FloatField()
    baseline_mae_pct = models.FloatField()
    model_rmse_pct = models.FloatField()
    baseline_rmse_pct = models.FloatField()
    test_start = models.DateField()
    test_end = models.DateField()
    n_train = models.IntegerField()
    n_test = models.IntegerField()
    trained_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["base", "quote", "data_until", "horizon"], name="unique_metric")
        ]


class Forecast(models.Model):
    base = models.CharField(max_length=3)
    quote = models.CharField(max_length=3)
    data_until = models.DateField()
    horizon = models.PositiveSmallIntegerField()
    target_date = models.DateField()
    predicted = models.FloatField()
    low = models.FloatField(help_text="10th percentile of past test errors applied to the prediction")
    high = models.FloatField(help_text="90th percentile")
    baseline = models.FloatField(help_text="Naive forecast: last known rate")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["horizon"]
        constraints = [
            models.UniqueConstraint(fields=["base", "quote", "data_until", "horizon"], name="unique_forecast")
        ]
