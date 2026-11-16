import pytest

from modules.electricity_pricing.flexible_tariffs.ews_schoenau.config import EwsSchoenauTariffConfiguration
from modules.electricity_pricing.flexible_tariffs.ews_schoenau.tariff import URL, fetch_prices

RESPONSE = {
    "today": [
        {"startsAt": "2026-11-16T00:00:00.000+01:00", "total": 30.5},
        {"startsAt": "2026-11-16T00:15:00.000+01:00", "total": 29.0},
    ],
    "tomorrow": [
        {"startsAt": "2026-11-17T00:00:00.000+01:00", "total": 25.0},
    ],
}


def test_fetch_prices(requests_mock):
    requests_mock.get(URL, json=RESPONSE)

    prices = fetch_prices(EwsSchoenauTariffConfiguration(api_key="key"))

    assert prices == {"1794783600": 0.000305, "1794784500": 0.00029, "1794870000": 0.00025}
    assert requests_mock.last_request.headers["X-API-Key"] == "key"


def test_fetch_prices_without_tomorrow(requests_mock):
    requests_mock.get(URL, json={"today": RESPONSE["today"], "tomorrow": None})

    assert len(fetch_prices(EwsSchoenauTariffConfiguration(api_key="key"))) == 2


def test_fetch_prices_without_api_key():
    with pytest.raises(ValueError):
        fetch_prices(EwsSchoenauTariffConfiguration())
