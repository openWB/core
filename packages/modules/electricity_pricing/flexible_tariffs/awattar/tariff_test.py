from datetime import datetime

from modules.electricity_pricing.flexible_tariffs.awattar import tariff
from modules.electricity_pricing.flexible_tariffs.awattar.config import AwattarTariffConfiguration
from modules.electricity_pricing.flexible_tariffs.awattar.tariff import fetch_prices


def test_fetch_prices(requests_mock):
    # setup
    config = AwattarTariffConfiguration(country="de")
    requests_mock.get('https://api.awattar.de/v1/marketdata', json=SAMPLE_DATA)

    # execution
    prices = fetch_prices(config)

    # evaluation
    assert prices == EXPECTED_PRICES


def test_request_covers_the_current_hour_until_two_days_ahead(monkeypatch, requests_mock):
    # ohne Zeitraum liefert die API nur die nächsten 24 Stunden, tomorrow wäre am Abend nicht vollständig
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 26, 16, 30, 0)

    monkeypatch.setattr(tariff, "datetime", FixedDateTime)
    requests_mock.get('https://api.awattar.de/v1/marketdata', json=SAMPLE_DATA)

    fetch_prices(AwattarTariffConfiguration(country="de"))

    query = requests_mock.last_request.qs
    start = int(datetime(2026, 11, 26, 16, 0, 0).timestamp() * 1000)
    assert query["start"] == [str(start)]
    assert query["end"] == [str(start + 48 * 3600 * 1000)]


SAMPLE_DATA = {
    "object": "list",
    "data": [
        {
            "start_timestamp": 1698310800000,
            "end_timestamp": 1698314400000,
            "marketprice": 140,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698314400000,
            "end_timestamp": 1698318000000,
            "marketprice": 131.11,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698318000000,
            "end_timestamp": 1698321600000,
            "marketprice": 120.09,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698321600000,
            "end_timestamp": 1698325200000,
            "marketprice": 119.6,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698325200000,
            "end_timestamp": 1698328800000,
            "marketprice": 120.01,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698328800000,
            "end_timestamp": 1698332400000,
            "marketprice": 131.14,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698332400000,
            "end_timestamp": 1698336000000,
            "marketprice": 142.91,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698336000000,
            "end_timestamp": 1698339600000,
            "marketprice": 150.95,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698339600000,
            "end_timestamp": 1698343200000,
            "marketprice": 150.99,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698343200000,
            "end_timestamp": 1698346800000,
            "marketprice": 130.72,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698346800000,
            "end_timestamp": 1698350400000,
            "marketprice": 119.06,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698350400000,
            "end_timestamp": 1698354000000,
            "marketprice": 117.06,
            "unit": "Eur/MWh"
        },
        {
            "start_timestamp": 1698354000000,
            "end_timestamp": 1698357600000,
            "marketprice": 104.85,
            "unit": "Eur/MWh"
        }
    ],
    "url": "/de/v1/marketdata"
}

EXPECTED_PRICES = {
    "1698310800": 0.00014,
    "1698314400": 0.00013111,
    "1698318000": 0.00012009,
    "1698321600": 0.0001196,
    "1698325200": 0.00012001000000000001,
    "1698328800": 0.00013114,
    "1698332400": 0.00014291,
    "1698336000": 0.00015094999999999998,
    "1698339600": 0.00015099000000000002,
    "1698343200": 0.00013072,
    "1698346800": 0.00011906,
    "1698350400": 0.00011706000000000001,
    "1698354000": 0.00010485
}
