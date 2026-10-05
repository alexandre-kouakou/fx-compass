from unittest import mock

from django.test import TestCase

from rates.testing import seed_random_walk
from .series import load_frames, pair


@mock.patch("analytics.views.refresh_if_stale")  # tests must never hit the network
class AnalyticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_random_walk(days=400)

    def setUp(self):
        self.client.defaults["HTTP_HOST"] = "localhost"

    def test_cross_rate_is_ratio_of_eur_rates(self, _refresh):
        values, _ = load_frames()
        s = pair(values, "USD", "INR")
        self.assertAlmostEqual(s.iloc[-1], values["INR"].iloc[-1] / values["USD"].iloc[-1])

    def test_endpoints_return_insight(self, _refresh):
        for url in [
            "/api/rates/latest?base=INR",
            "/api/convert?base=USD&quote=INR&amount=100",
            "/api/history?base=USD&quote=JPY&range=6M",
            "/api/gain-loss?base=EUR&quote=INR&amount=5000&range=1M",
            "/api/volatility?base=USD&quote=INR",
            "/api/heatmap?range=1M",
        ]:
            with self.subTest(url=url):
                r = self.client.get(url)
                self.assertEqual(r.status_code, 200, r.content)
                self.assertTrue(r.json()["insight"])

    def test_converter_math(self, _refresh):
        d = self.client.get("/api/convert?base=USD&quote=INR&amount=250").json()
        self.assertAlmostEqual(d["result"], 250 * d["rate"])

    def test_heatmap_is_antisymmetric_in_sign(self, _refresh):
        d = self.client.get("/api/heatmap?range=1M").json()
        m = d["matrix"]
        self.assertEqual(len(m), 10)
        self.assertIsNone(m[0][0])
        self.assertEqual(m[0][4] > 0, m[4][0] < 0)

    def test_usd_aed_is_pegged(self, _refresh):
        d = self.client.get("/api/history?base=USD&quote=AED&range=1Y").json()
        self.assertAlmostEqual(d["stats"]["min"], 3.6725)
        self.assertEqual(d["points"][0]["source"], "derived_peg")

    def test_bad_params_are_400(self, _refresh):
        for url in ["/api/history?base=USD&quote=USD", "/api/history?range=2Y", "/api/convert?amount=-5"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)
