from unittest.mock import Mock
from helpermodules import timecheck
from modules.electricity_tariffs.tibber.config import TibberTariffConfiguration
from modules.electricity_tariffs.tibber.tariff import fetch_prices


def test_fetch_prices(monkeypatch, requests_mock):
    # setup
    config = TibberTariffConfiguration(token="5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE",
                                       home_id="96a14971-525a-4420-aae9-e5aedaa129ff")
    mock_create_unix_timestamp_current_full_hour = Mock(return_value=1698382800)
    monkeypatch.setattr(timecheck, "create_unix_timestamp_current_full_hour",
                        mock_create_unix_timestamp_current_full_hour)
    requests_mock.post('https://api.tibber.com/v1-beta/gql', json=SAMPLE_DATA)

    # execution
    prices = fetch_prices(config)

    # evaluation
    assert prices == EXPECTED_PRICES


SAMPLE_DATA = {"data":
               {"viewer":
                {"home":
                 {"currentSubscription":
                  {"priceInfo":
                   {"today": [{"total": 0.8724, "startsAt": "2023-10-27T00:00:00.000+02:00"},
                              {"total": 0.8551, "startsAt": "2023-10-27T01:00:00.000+02:00"},
                              {"total": 0.8389, "startsAt": "2023-10-27T02:00:00.000+02:00"},
                              {"total": 0.8189, "startsAt": "2023-10-27T03:00:00.000+02:00"},
                              {"total": 0.8544, "startsAt": "2023-10-27T04:00:00.000+02:00"},
                              {"total": 0.8473, "startsAt": "2023-10-27T05:00:00.000+02:00"},
                              {"total": 1.1724, "startsAt": "2023-10-27T06:00:00.000+02:00"},
                              {"total": 1.6862, "startsAt": "2023-10-27T07:00:00.000+02:00"},
                              {"total": 2.3264, "startsAt": "2023-10-27T08:00:00.000+02:00"},
                              {"total": 2.3024, "startsAt": "2023-10-27T09:00:00.000+02:00"},
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
                              ],
                    "tomorrow": []}}}}}}

EXPECTED_PRICES = {
    "1698382800": 0.0016862,
    "1698386400": 0.0023264,
    "1698390000": 0.0023024,
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
