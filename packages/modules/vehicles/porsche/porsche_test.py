import time

import pytest
import requests_mock

from modules.vehicles.porsche import api
from modules.vehicles.porsche.api import PorscheApiError, PorscheConnectApi


def make_api(monkeypatch, tmp_path):
    # Token-Persistenz in ein temporaeres Verzeichnis umlenken
    monkeypatch.setattr(api, "_DATA_PATH", tmp_path)
    client = PorscheConnectApi("mail@example.com", "secret", vehicle_id=0)
    # gueltiges Token vorsetzen -> OAuth-Flow wird uebersprungen
    client._token = {"access_token": "tok", "refresh_token": "ref",
                     "expires_at": int(time.time()) + 3600}
    return client


def status_sample():
    return {
        "vin": "WP0ZZZ12345678901",
        "modelName": "Macan 4",
        "measurements": [
            {"key": "BATTERY_LEVEL", "status": {"isEnabled": True, "updatedAt": "2026-08-26T10:00:00Z"},
             "value": {"percent": 72}},
            {"key": "E_RANGE", "status": {"isEnabled": True}, "value": {"kilometers": 310}},
            {"key": "MILEAGE", "status": {"isEnabled": True}, "value": {"kilometers": 12345}},
        ],
    }


def test_fetch_soc_parses_values(monkeypatch, tmp_path):
    client = make_api(monkeypatch, tmp_path)
    vin = "WP0ZZZ12345678901"
    with requests_mock.Mocker() as m:
        m.get(f"{api.API_BASE_URL}/connect/v1/vehicles/{vin}", json=status_sample())
        soc, range_km, soc_ts, odometer = client.fetch_soc(vin)
    assert soc == 72.0
    assert range_km == 310
    assert odometer == 12345
    assert soc_ts == pytest.approx(1787738400.0, abs=1)  # 2026-08-26T10:00:00Z


def test_fetch_soc_missing_battery_raises(monkeypatch, tmp_path):
    client = make_api(monkeypatch, tmp_path)
    vin = "WP0ZZZ12345678901"
    with requests_mock.Mocker() as m:
        m.get(f"{api.API_BASE_URL}/connect/v1/vehicles/{vin}",
              json={"vin": vin, "measurements": []})
        with pytest.raises(PorscheApiError):
            client.fetch_soc(vin)


def test_resolve_vin_uses_configured(monkeypatch, tmp_path):
    client = make_api(monkeypatch, tmp_path)
    # kein HTTP noetig, wenn VIN konfiguriert ist
    assert client.resolve_vin("wp0zzz12345678901") == "WP0ZZZ12345678901"


def test_resolve_vin_single_vehicle(monkeypatch, tmp_path):
    client = make_api(monkeypatch, tmp_path)
    with requests_mock.Mocker() as m:
        m.get(f"{api.API_BASE_URL}/connect/v1/vehicles",
              json=[{"vin": "WP0ZZZ12345678901"}])
        assert client.resolve_vin(None) == "WP0ZZZ12345678901"


def test_resolve_vin_multiple_requires_config(monkeypatch, tmp_path):
    client = make_api(monkeypatch, tmp_path)
    with requests_mock.Mocker() as m:
        m.get(f"{api.API_BASE_URL}/connect/v1/vehicles",
              json=[{"vin": "WP0AAA"}, {"vin": "WP0BBB"}])
        with pytest.raises(PorscheApiError):
            client.resolve_vin(None)


def test_direct_charge_polls_until_done(monkeypatch, tmp_path):
    monkeypatch.setattr(api.time, "sleep", lambda *_: None)  # nicht wirklich warten
    client = make_api(monkeypatch, tmp_path)
    vin = "WP0ZZZ12345678901"
    with requests_mock.Mocker() as m:
        m.post(f"{api.API_BASE_URL}/connect/v1/vehicles/{vin}/commands",
               json={"status": {"id": "cmd1", "result": "ACCEPTED"}})
        m.get(f"{api.API_BASE_URL}/connect/v1/vehicles/{vin}/commands/cmd1",
              json={"status": {"result": "SUCCESS"}})
        result = client.direct_charge(vin, on=True)
    assert result == "SUCCESS"


def test_direct_charge_error_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(api.time, "sleep", lambda *_: None)
    client = make_api(monkeypatch, tmp_path)
    vin = "WP0ZZZ12345678901"
    with requests_mock.Mocker() as m:
        m.post(f"{api.API_BASE_URL}/connect/v1/vehicles/{vin}/commands",
               json={"status": {"id": "cmd1", "result": "ACCEPTED"}})
        m.get(f"{api.API_BASE_URL}/connect/v1/vehicles/{vin}/commands/cmd1",
              json={"status": {"result": "ERROR"}})
        with pytest.raises(api.PorscheApiError):
            client.direct_charge(vin, on=False)


def test_expired_token_triggers_refresh(monkeypatch, tmp_path):
    client = make_api(monkeypatch, tmp_path)
    client._token["expires_at"] = int(time.time()) - 10  # abgelaufen
    vin = "WP0ZZZ12345678901"
    with requests_mock.Mocker() as m:
        m.post(api.TOKEN_URL, json={"access_token": "new", "refresh_token": "ref2",
                                    "expires_in": 3600})
        m.get(f"{api.API_BASE_URL}/connect/v1/vehicles/{vin}", json=status_sample())
        soc, *_ = client.fetch_soc(vin)
    assert soc == 72.0
    assert client._token["access_token"] == "new"
