from datetime import datetime, timezone
from typing import Optional

import pytest

from modules.electricity_pricing.flexible_tariffs.groupe_e import tariff
from modules.electricity_pricing.flexible_tariffs.groupe_e.config import GroupeETariffConfiguration

URL = "https://api.tariffs.groupe-e.ch/v2/tariffs"

# gekürzte Antwort der v2-API
RESPONSE = {
    "publication_timestamp": "2026-11-26T14:47:51+01:00",
    "prices": [
        {"start_timestamp": "2026-11-26T15:00:00+01:00", "end_timestamp": "2026-11-26T15:15:00+01:00",
         "grid": [{"unit": "CHF_kWh", "value": 0.1155}], "integrated": [{"unit": "CHF_kWh", "value": 0.235}]},
        {"start_timestamp": "2026-11-26T15:15:00+01:00", "end_timestamp": "2026-11-26T15:30:00+01:00",
         "grid": [{"unit": "CHF_kWh", "value": 0.1155}], "integrated": [{"unit": "CHF_kWh", "value": 0.24}]},
    ],
}


def _patch_now(monkeypatch: pytest.MonkeyPatch, now: datetime) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: Optional[timezone] = None):
            return now.astimezone(tz) if tz else now

    monkeypatch.setattr(tariff, "datetime", FixedDateTime)


def test_fetch_prices(monkeypatch: pytest.MonkeyPatch, requests_mock):
    _patch_now(monkeypatch, datetime(2026, 11, 26, 14, 20, 0, tzinfo=timezone.utc))
    requests_mock.get(URL, json=RESPONSE)

    prices = tariff.fetch_prices(GroupeETariffConfiguration())

    # 15:00 +01:00 = 14:00 UTC, CHF/kWh -> CHF/Wh
    assert prices == {"1795701600": pytest.approx(0.000235), "1795702500": pytest.approx(0.00024)}


def test_request_window_is_in_utc_and_starts_with_the_current_hour(monkeypatch: pytest.MonkeyPatch, requests_mock):
    # Sommerzeit: mit dem früheren festen Offset +01:00 hätte das Fenster eine Stunde zu spät begonnen
    _patch_now(monkeypatch, datetime(2026, 7, 1, 12, 20, 0, tzinfo=timezone.utc))
    requests_mock.get(URL, json=RESPONSE)

    tariff.fetch_prices(GroupeETariffConfiguration())

    query = requests_mock.last_request.qs
    assert query["start_timestamp"] == ["2026-07-01t12:00:00z"]
    assert query["end_timestamp"] == ["2026-07-03t12:00:00z"]
