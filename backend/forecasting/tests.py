import numpy as np
import pandas as pd
from django.test import TestCase

from rates.testing import seed_random_walk
from . import model


class SplitAndLeakageTests(TestCase):
    def test_time_split_train_strictly_before_test_with_gap(self):
        train, test = model.time_split(1000)
        self.assertEqual(train.max() + 1 + model.HORIZON, test.min())
        self.assertEqual(test.max(), 999)
        self.assertTrue((np.diff(train) == 1).all() and (np.diff(test) == 1).all())  # not shuffled

    def test_features_do_not_look_ahead(self):
        idx = pd.bdate_range("2024-01-01", periods=100)
        s = pd.Series(np.linspace(1, 2, 100), index=idx)
        changed = s.copy()
        changed.iloc[60:] *= 5  # change the future only
        a, b = model.make_features(s), model.make_features(changed)
        pd.testing.assert_frame_equal(a.iloc[:60], b.iloc[:60])


class ForecastApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_random_walk(days=500)

    def setUp(self):
        self.client.defaults["HTTP_HOST"] = "localhost"

    def test_forecast_has_baseline_range_and_metrics(self):
        d = self.client.get("/api/forecast?base=USD&quote=INR").json()
        self.assertEqual(len(d["forecast"]), model.HORIZON)
        for f in d["forecast"]:
            self.assertLessEqual(f["low"], f["high"])
            self.assertIn("baseline", f)
        self.assertGreater(d["metrics"]["n_test"], 0)
        self.assertIn(d["verdict"], {"beats_baseline", "no_better_than_baseline"})

    def test_pegged_pair(self):
        self.assertEqual(self.client.get("/api/forecast?base=USD&quote=AED").json()["verdict"], "pegged")
