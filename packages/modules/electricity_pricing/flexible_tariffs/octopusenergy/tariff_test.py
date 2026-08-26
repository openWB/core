from datetime import datetime, timezone
from typing import Dict
from unittest.mock import MagicMock

import pytest

from modules.electricity_pricing.flexible_tariffs.octopusenergy import tariff
from modules.electricity_pricing.flexible_tariffs.octopusenergy.tariff import build_tariff_state, OctopusEnergyApiError


TEST_DATA = {'data': {'account': {'property': {'electricityMalos': [
    {'agreements': [{'id': 1,
                     'unitRateInformation': {'__typename': 'TimeOfUseProductUnitRateInformation',
                                             'rates': [{'latestGrossUnitRateCentsPerKwh': '20',
                                                        'timeslotActivationRules': [{'activeFromTime': '00:00:00',
                                                                                     'activeToTime': '05:00:00'}],
                                                        'timeslotName': 'GO'},
                                                       {'latestGrossUnitRateCentsPerKwh': '30',
                                                        'timeslotActivationRules': [{'activeFromTime': '05:00:00',
                                                                                     'activeToTime': '00:00:00'}],
                                                        'timeslotName': 'STANDARD'}]},
                     'validFrom': '2026-01-06T23:00:00+00:00',
                     'validTo': '2027-01-06T23:00:00+00:00'},
                    {'id': 2,
                     'unitRateInformation': {'__typename': 'SimpleProductUnitRateInformation',
                                             'latestGrossUnitRateCentsPerKwh': '26'},
                     'validFrom': '2026-01-01T23:00:00+00:00',
                     'validTo': '2026-01-06T23:00:00+00:00'}]}]}}}}

EXPECTED_PRICES_SUMMER_TIME = {'1775131200': 0.0003,  # 2026-04-02 14:00
                               '1775134800': 0.0003,  # 2026-04-02 15:00
                               '1775138400': 0.0003,  # 2026-04-02 16:00
                               '1775142000': 0.0003,  # 2026-04-02 17:00
                               '1775145600': 0.0003,  # 2026-04-02 18:00
                               '1775149200': 0.0003,  # 2026-04-02 19:00
                               '1775152800': 0.0003,  # 2026-04-02 20:00
                               '1775156400': 0.0003,  # 2026-04-02 21:00
                               '1775160000': 0.0003,  # 2026-04-02 22:00
                               '1775163600': 0.0003,  # 2026-04-02 23:00
                               '1775167200': 0.0002,  # 2026-04-03 00:00
                               '1775170800': 0.0002,  # 2026-04-03 01:00
                               '1775174400': 0.0002,  # 2026-04-03 02:00
                               '1775178000': 0.0002,  # 2026-04-03 03:00
                               '1775181600': 0.0002,  # 2026-04-03 04:00
                               '1775185200': 0.0003,  # 2026-04-03 05:00
                               '1775188800': 0.0003,  # 2026-04-03 06:00
                               '1775192400': 0.0003,  # 2026-04-03 07:00
                               '1775196000': 0.0003,  # 2026-04-03 08:00
                               '1775199600': 0.0003,  # 2026-04-03 09:00
                               '1775203200': 0.0003,  # 2026-04-03 10:00
                               '1775206800': 0.0003,  # 2026-04-03 11:00
                               '1775210400': 0.0003,  # 2026-04-03 12:00
                               '1775214000': 0.0003,  # 2026-04-03 13:00
                               '1775217600': 0.0003,  # 2026-04-03 14:00
                               '1775221200': 0.0003,  # 2026-04-03 15:00
                               '1775224800': 0.0003,  # 2026-04-03 16:00
                               '1775228400': 0.0003}  # 2026-04-03 17:00

EXPECTED_PRICES_WINTER_TIME = {'1793624400': 0.0003,  # 2026-11-02 14:00
                               '1793628000': 0.0003,  # 2026-11-02 15:00
                               '1793631600': 0.0003,  # 2026-11-02 16:00
                               '1793635200': 0.0003,  # 2026-11-02 17:00
                               '1793638800': 0.0003,  # 2026-11-02 18:00
                               '1793642400': 0.0003,  # 2026-11-02 19:00
                               '1793646000': 0.0003,  # 2026-11-02 20:00
                               '1793649600': 0.0003,  # 2026-11-02 21:00
                               '1793653200': 0.0003,  # 2026-11-02 22:00
                               '1793656800': 0.0003,  # 2026-11-02 23:00
                               '1793660400': 0.0002,  # 2026-11-03 00:00
                               '1793664000': 0.0002,  # 2026-11-03 01:00
                               '1793667600': 0.0002,  # 2026-11-03 02:00
                               '1793671200': 0.0002,  # 2026-11-03 03:00
                               '1793674800': 0.0002,  # 2026-11-03 04:00
                               '1793678400': 0.0003,  # 2026-11-03 05:00
                               '1793682000': 0.0003,  # 2026-11-03 06:00
                               '1793685600': 0.0003,  # 2026-11-03 07:00
                               '1793689200': 0.0003,  # 2026-11-03 08:00
                               '1793692800': 0.0003,  # 2026-11-03 09:00
                               '1793696400': 0.0003,  # 2026-11-03 10:00
                               '1793700000': 0.0003,  # 2026-11-03 11:00
                               '1793703600': 0.0003,  # 2026-11-03 12:00
                               '1793707200': 0.0003,  # 2026-11-03 13:00
                               '1793710800': 0.0003,  # 2026-11-03 14:00
                               '1793714400': 0.0003,  # 2026-11-03 15:00
                               '1793718000': 0.0003,  # 2026-11-03 16:00
                               '1793721600': 0.0003}  # 2026-11-03 17:00


@pytest.mark.parametrize(
    "now, expected_prices",
    [
        # 2 Stunden früher wegen UTC
        pytest.param(datetime(2026, 4, 2, 12, 3, 0, tzinfo=timezone.utc), EXPECTED_PRICES_SUMMER_TIME),
        # 1 Stunde früher wegen UTC
        pytest.param(datetime(2026, 11, 2, 13, 3, 0, tzinfo=timezone.utc), EXPECTED_PRICES_WINTER_TIME)
    ])
def test_build_tariff_state(now: datetime, expected_prices: Dict[str, float], monkeypatch):
    # setup
    datetime_mock = MagicMock(wraps=datetime)
    datetime_mock.now.return_value = now
    monkeypatch.setattr(tariff, "datetime", datetime_mock)

    # execution
    prices = build_tariff_state(TEST_DATA["data"])

    # assert
    assert prices == expected_prices


# --- Zusätzliche Tests für die Fehlerbehandlung bei fehlenden/kaputten API-Daten ---

def test_build_tariff_state_raises_on_missing_property():
    # setup: 'property' ist None, z.B. wenn die API keine gültige Property zurückgibt
    data = {'account': {'property': None}}

    # execution & assert
    with pytest.raises(OctopusEnergyApiError, match="Property"):
        build_tariff_state(data)


def test_build_tariff_state_raises_on_missing_account():
    # setup: 'account' fehlt komplett in der Antwort
    data = {}

    # execution & assert
    with pytest.raises(OctopusEnergyApiError, match="Property"):
        build_tariff_state(data)


def test_build_tariff_state_raises_on_empty_malos():
    # setup: 'electricityMalos' ist leer, z.B. Zählpunkt noch nicht verknüpft
    data = {'account': {'property': {'electricityMalos': []}}}

    # execution & assert
    with pytest.raises(OctopusEnergyApiError, match="electricityMalos"):
        build_tariff_state(data)


def test_graphql_request_raises_on_graphql_errors(monkeypatch):
    # setup: HTTP 200, aber GraphQL liefert ein 'errors'-Array statt 'data'
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "errors": [{"message": "Token invalid or expired"}]
    }
    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    monkeypatch.setattr(tariff.req, "get_http_session", lambda: mock_session)

    # execution & assert: Authentifizierung im Konstruktor schlägt fehl
    with pytest.raises(OctopusEnergyApiError, match="Token invalid or expired"):
        tariff.OctopusEnergyClient(email="test@example.com", password="secret")


def test_graphql_request_raises_on_missing_data_field(monkeypatch):
    # setup: HTTP 200, aber weder 'data' noch 'errors' im Body (unerwartetes Format)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    monkeypatch.setattr(tariff.req, "get_http_session", lambda: mock_session)

    # execution & assert
    with pytest.raises(OctopusEnergyApiError, match="data"):
        tariff.OctopusEnergyClient(email="test@example.com", password="secret")
