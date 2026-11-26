from datetime import datetime, timezone
from typing import Optional

import pytest

from modules.electricity_pricing.flexible_tariffs.ostrom import tariff
from modules.electricity_pricing.flexible_tariffs.ostrom.config import OstromTariffConfiguration

TOKEN_URL = "https://auth.production.ostrom-api.io/oauth2/token"
PRICES_URL = "https://production.ostrom-api.io/spot-prices"


def _patch_now(monkeypatch: pytest.MonkeyPatch, now: datetime) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: Optional[timezone] = None):
            return now.astimezone(tz) if tz else now

    monkeypatch.setattr(tariff, "datetime", FixedDateTime)


def test_fetch_prices_requests_two_days(monkeypatch: pytest.MonkeyPatch, requests_mock):
    # bei nur einem Tag fehlt morgen Abend
    _patch_now(monkeypatch, datetime(2026, 11, 26, 14, 20, 0, tzinfo=timezone.utc))
    requests_mock.post(TOKEN_URL, json={"access_token": "token"})
    requests_mock.get(PRICES_URL, json={"data": [
        {"date": "2026-11-26T14:00:00.000Z", "grossKwhPrice": 20.0, "grossKwhTaxAndLevies": 5.0}]})

    prices = tariff.fetch_prices(OstromTariffConfiguration(client_id="id", client_secret="secret"))

    query = requests_mock.last_request.qs
    assert query["startdate"] == ["2026-11-26t14:00:00.000z"]
    assert query["enddate"] == ["2026-11-28t14:00:00.000z"]
    assert prices == {"1795701600": pytest.approx(0.00025)}
