from unittest.mock import Mock
from datetime import datetime
from helpermodules import timecheck
from modules.electricity_tariffs.dynamic_tariffs.tibber.config import TibberTariffConfiguration
from modules.electricity_tariffs.dynamic_tariffs.tibber.tariff import fetch_prices
import pytest


SAMPLE_DATA_TODAY = {
    "data": {
        "viewer": {
            "home": {"currentSubscription": {
                "priceInfo": {"today": [
                    {"total": 0.8724, "startsAt": "2023-10-27T00:00:00.000+02:00"},
                    {"total": 0.8551, "startsAt": "2023-10-27T01:00:00.000+02:00"},
                    {"total": 0.8552, "startsAt": "2023-10-27T01:15:00.000+02:00"},
                    {"total": 0.8553, "startsAt": "2023-10-27T01:30:00.000+02:00"},
                    {"total": 0.8554, "startsAt": "2023-10-27T01:45:00.000+02:00"},
                    {"total": 0.8389, "startsAt": "2023-10-27T02:00:00.000+02:00"},
                    {"total": 0.8189, "startsAt": "2023-10-27T03:00:00.000+02:00"},
                    {"total": 0.8544, "startsAt": "2023-10-27T04:00:00.000+02:00"},
                    {"total": 0.8473, "startsAt": "2023-10-27T05:00:00.000+02:00"},
                    {"total": 1.1724, "startsAt": "2023-10-27T06:00:00.000+02:00"},
                    {"total": 1.6862, "startsAt": "2023-10-27T07:00:00.000+02:00"},
                    {"total": 2.3264, "startsAt": "2023-10-27T08:00:00.000+02:00"},
                    {"total": 2.3024, "startsAt": "2023-10-27T09:00:00.000+02:00"},
                    {"total": 2.3124, "startsAt": "2023-10-27T09:15:00.000+02:00"},
                    {"total": 2.3224, "startsAt": "2023-10-27T09:30:00.000+02:00"},
                    {"total": 2.3324, "startsAt": "2023-10-27T09:45:00.000+02:00"},
                    {"total": 1.7204, "startsAt": "2023-10-27T10:00:00.000+02:00"},
                    {"total": 1.7213, "startsAt": "2023-10-27T11:00:00.000+02:00"},
                    {"total": 1.8697, "startsAt": "2023-10-27T12:00:00.000+02:00"},
                    {"total": 1.69, "startsAt": "2023-10-27T13:00:00.000+02:00"},
                    {"total": 1.5725, "startsAt": "2023-10-27T14:00:00.000+02:00"},
                    {"total": 1.2997, "startsAt": "2023-10-27T15:00:00.000+02:00"},
                    {"total": 1.4289, "startsAt": "2023-10-27T16:00:00.000+02:00"},
                    {"total": 1.9176, "startsAt": "2023-10-27T17:00:00.000+02:00"},
                    {"total": 2.1175, "startsAt": "2023-10-27T18:00:00.000+02:00"},
                    {"total": 1.8902, "startsAt": "2023-10-27T19:00:00.000+02:00"},
                    {"total": 1.2104, "startsAt": "2023-10-27T20:00:00.000+02:00"},
                    {"total": 1.1332, "startsAt": "2023-10-27T21:00:00.000+02:00"},
                    {"total": 0.8015, "startsAt": "2023-10-27T22:00:00.000+02:00"},
                    {"total": 0.7698, "startsAt": "2023-10-27T23:00:00.000+02:00"}
                ], "tomorrow": []}}}}}}

EXPECTED_PRICES_TODAY = {
    '1698357600': 0.0008724,
    '1698361200': 0.0008551,
    '1698362100': 0.0008552,
    '1698363000': 0.0008552999999999999,
    '1698363900': 0.0008554000000000001,
    '1698364800': 0.0008389,
    '1698368400': 0.0008189,
    '1698372000': 0.0008544000000000001,
    '1698375600': 0.0008473,
    '1698379200': 0.0011724,
    "1698382800": 0.0016862,
    "1698386400": 0.0023264,
    "1698390000": 0.0023024,
    "1698390900": 0.0023123999999999996,
    "1698391800": 0.0023224,
    "1698392700": 0.0023323999999999997,
    "1698393600": 0.0017204,
    "1698397200": 0.0017213,
    "1698400800": 0.0018697,
    "1698404400": 0.0016899999999999999,
    "1698408000": 0.0015725000000000001,
    "1698411600": 0.0012997,
    "1698415200": 0.0014289,
    "1698418800": 0.0019176,
    "1698422400": 0.0021175,
    "1698426000": 0.0018902,
    "1698429600": 0.0012104,
    "1698433200": 0.0011332,
    "1698436800": 0.0008015,
    "1698440400": 0.0007698000000000001,
}


@pytest.mark.parametrize(
    "now, tibber_response, expected",
    [
        pytest.param(datetime.fromisoformat('2023-10-27T07:00:00.000+02:00'),
                     SAMPLE_DATA_TODAY,
                     EXPECTED_PRICES_TODAY,
                     id="return all prices, outdated will be filtered in ConfigurableElectricityTariff"),
    ]
)
def test_fetch_prices(now, tibber_response, expected, monkeypatch, requests_mock):
    # setup
    config = TibberTariffConfiguration(token="5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE",
                                       home_id="96a14971-525a-4420-aae9-e5aedaa129ff")
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=int(now.timestamp())))
    requests_mock.post('https://api.tibber.com/v1-beta/gql', json=tibber_response)

    # execution
    prices = fetch_prices(config)

    # evaluation
    assert prices == expected
