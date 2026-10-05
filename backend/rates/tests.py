from datetime import date, datetime, timezone
from unittest import mock

from django.test import TestCase

from . import services
from .models import FetchLog, Rate


class StoreTests(TestCase):
    def setUp(self):
        services.ensure_currencies()

    def test_aed_history_is_derived_from_usd_peg(self):
        services.store_ecb_days({date(2026, 1, 5): {"USD": 1.2, "INR": 100.0}})
        aed = Rate.objects.get(date=date(2026, 1, 5), currency_id="AED")
        self.assertEqual(aed.source, Rate.SOURCE_DERIVED_PEG)
        self.assertAlmostEqual(float(aed.per_eur), 1.2 * 3.6725, places=8)
        self.assertEqual(float(Rate.objects.get(date=date(2026, 1, 5), currency_id="EUR").per_eur), 1)

    @mock.patch("rates.sources.fetch_aed_live", return_value=(3.6730, datetime(2026, 1, 6, tzinfo=timezone.utc)))
    def test_live_aed_uses_ecb_usd_for_consistency(self, _):
        services.store_ecb_days({date(2026, 1, 5): {"USD": 1.2}})
        services.update_aed_live()
        aed = Rate.objects.get(date=date(2026, 1, 5), currency_id="AED")
        self.assertEqual(aed.source, Rate.SOURCE_ER_API)
        self.assertAlmostEqual(float(aed.per_eur), 3.6730 * 1.2, places=8)

    @mock.patch("rates.sources.fetch_frankfurter", side_effect=ConnectionError("offline"))
    @mock.patch("rates.sources.fetch_aed_live", side_effect=ConnectionError("offline"))
    def test_network_failure_is_logged_not_raised(self, *_):
        services.refresh()
        self.assertTrue(FetchLog.objects.filter(source="ecb", ok=False).exists())
        self.assertIsNone(services.last_success())
