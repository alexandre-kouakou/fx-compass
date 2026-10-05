from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=64)
    symbol = models.CharField(max_length=8)
    in_ecb = models.BooleanField(default=True, help_text="False if ECB publishes no rate (AED)")

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.code


class Rate(models.Model):
    """One daily reference rate: how many units of `currency` one EUR buys on `date`."""

    SOURCE_ECB = "ecb"
    SOURCE_ER_API = "er_api"
    SOURCE_DERIVED_PEG = "derived_peg"
    SOURCE_CHOICES = [
        (SOURCE_ECB, "ECB via Frankfurter"),
        (SOURCE_ER_API, "open.er-api.com"),
        (SOURCE_DERIVED_PEG, "Derived from USD peg"),
    ]

    date = models.DateField(db_index=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="rates")
    per_eur = models.DecimalField(max_digits=20, decimal_places=10)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "currency"]
        constraints = [
            models.UniqueConstraint(fields=["date", "currency"], name="unique_rate_per_day")
        ]

    def __str__(self):
        return f"{self.date} EUR/{self.currency_id}={self.per_eur} ({self.source})"


class FetchLog(models.Model):
    """Every attempt to pull data from an external source. Drives 'last updated'."""

    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=16)
    ok = models.BooleanField()
    rows = models.IntegerField(default=0)
    latest_date = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
