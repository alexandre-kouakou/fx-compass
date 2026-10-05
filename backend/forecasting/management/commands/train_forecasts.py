from itertools import permutations

from django.core.management.base import BaseCommand

from forecasting.services import forecast
from rates.constants import CODES


class Command(BaseCommand):
    help = "Train and cache forecasts for all 90 currency pairs; print the honest scorecard."

    def handle(self, *args, **opts):
        beats = 0
        for base, quote in permutations(CODES, 2):
            res = forecast(base, quote)
            m = res["metrics"]
            beats += res["verdict"] == "beats_baseline"
            self.stdout.write(
                f"{base}/{quote}: model MAE {m['avg_model_mae_pct']:.3f}% vs baseline "
                f"{m['avg_baseline_mae_pct']:.3f}% -> {res['verdict']}"
            )
        self.stdout.write(f"Model beats the naive baseline on {beats}/90 pairs.")
