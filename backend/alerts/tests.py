from django.test import TestCase

from analytics.series import load_frames, pair
from rates.testing import seed_random_walk


class AlertTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_random_walk(days=100)

    def setUp(self):
        self.client.defaults["HTTP_HOST"] = "localhost"
        values, _ = load_frames()
        self.rate = pair(values, "USD", "INR").iloc[-1]

    def create(self, direction, threshold, cid="client-aaaa"):
        return self.client.post("/api/alerts", {"client_id": cid, "base": "USD", "quote": "INR",
                                                "direction": direction, "threshold": threshold},
                                content_type="application/json")

    def test_triggers_only_when_crossed(self):
        self.assertIsNotNone(self.create("above", self.rate * 0.9).json()["triggered_at"])
        self.assertIsNone(self.create("above", self.rate * 1.1).json()["triggered_at"])
        self.assertIsNotNone(self.create("below", self.rate * 1.1).json()["triggered_at"])

    def test_clients_only_see_and_delete_their_own(self):
        pk = self.create("above", 1, cid="client-aaaa").json()["id"]
        self.assertEqual(len(self.client.get("/api/alerts?client_id=client-bbbb").json()["alerts"]), 0)
        self.assertEqual(self.client.delete(f"/api/alerts/{pk}?client_id=client-bbbb").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/alerts/{pk}?client_id=client-aaaa").status_code, 204)

    def test_rejects_same_currency(self):
        r = self.client.post("/api/alerts", {"client_id": "client-aaaa", "base": "USD", "quote": "USD",
                                             "direction": "above", "threshold": 1}, content_type="application/json")
        self.assertEqual(r.status_code, 400)
