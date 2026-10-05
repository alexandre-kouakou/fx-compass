import math

import pandas as pd

from analytics import text
from analytics.series import load_frames, pair
from . import model
from .models import Forecast, ModelMetric


def _train_and_store(base, quote, s):
    data_until = s.index[-1].date()
    results, info = model.run(s)
    last = float(s.iloc[-1])
    dates = pd.bdate_range(s.index[-1] + pd.Timedelta(days=1), periods=model.HORIZON)
    for r, d in zip(results, dates):
        key = {"base": base, "quote": quote, "data_until": data_until, "horizon": r.horizon}
        ModelMetric.objects.update_or_create(**key, defaults={
            "model_name": model.MODEL_NAME,
            "model_mae_pct": r.model_mae_pct, "baseline_mae_pct": r.baseline_mae_pct,
            "model_rmse_pct": r.model_rmse_pct, "baseline_rmse_pct": r.baseline_rmse_pct,
            **info,
        })
        Forecast.objects.update_or_create(**key, defaults={
            "target_date": d.date(),
            "predicted": last * math.exp(r.pred_log_return),
            "low": last * math.exp(r.pred_log_return + r.err_lo),
            "high": last * math.exp(r.pred_log_return + r.err_hi),
            "baseline": last,
        })


def forecast(base: str, quote: str) -> dict:
    values, _ = load_frames()
    s = pair(values, base, quote)
    data_until = s.index[-1].date()
    key = {"base": base, "quote": quote, "data_until": data_until}
    if not Forecast.objects.filter(**key).exists():
        _train_and_store(base, quote, s)

    fc = list(Forecast.objects.filter(**key))
    metrics = list(ModelMetric.objects.filter(**key).order_by("horizon"))
    m_mae = sum(m.model_mae_pct for m in metrics) / len(metrics)
    b_mae = sum(m.baseline_mae_pct for m in metrics) / len(metrics)
    improvement = (1 - m_mae / b_mae) * 100 if b_mae > 1e-6 else 0.0
    last_fc = fc[-1]

    if b_mae < 1e-4:
        verdict = "pegged"
        insight = f"{base}/{quote} is pegged, so there is nothing to forecast: expect it to stay at {text.fmt_rate(last_fc.baseline)}."
    elif improvement > 1:
        verdict = "beats_baseline"
        insight = (
            f"The model expects {text.fmt_rate(last_fc.predicted)} by {last_fc.target_date:%d %b} "
            f"(80% range {text.fmt_rate(last_fc.low)}–{text.fmt_rate(last_fc.high)}). On recent unseen data it was "
            f"{improvement:.1f}% more accurate than simply assuming no change."
        )
    else:
        verdict = "no_better_than_baseline"
        insight = (
            f"Honest result: on recent unseen data the model was not more accurate than assuming no change "
            f"({abs(improvement):.1f}% {'worse' if improvement < 0 else 'better'}). Treat today's rate "
            f"({text.fmt_rate(last_fc.baseline)}) as the best guess; a 7-day 80% range is "
            f"{text.fmt_rate(last_fc.low)}–{text.fmt_rate(last_fc.high)}."
        )

    tail = s.iloc[-60:]
    m0 = metrics[0]
    return {
        "base": base, "quote": quote, "data_until": data_until,
        "model_name": m0.model_name,
        "history": [{"date": d.date().isoformat(), "rate": v} for d, v in tail.items()],
        "forecast": [
            {"date": f.target_date, "horizon": f.horizon, "predicted": f.predicted,
             "low": f.low, "high": f.high, "baseline": f.baseline}
            for f in fc
        ],
        "metrics": {
            "per_horizon": [
                {"horizon": m.horizon, "model_mae_pct": m.model_mae_pct, "baseline_mae_pct": m.baseline_mae_pct,
                 "model_rmse_pct": m.model_rmse_pct, "baseline_rmse_pct": m.baseline_rmse_pct}
                for m in metrics
            ],
            "avg_model_mae_pct": m_mae, "avg_baseline_mae_pct": b_mae,
            "improvement_pct": improvement,
            "test_start": m0.test_start, "test_end": m0.test_end,
            "n_train": m0.n_train, "n_test": m0.n_test,
        },
        "verdict": verdict,
        "insight": insight,
    }
