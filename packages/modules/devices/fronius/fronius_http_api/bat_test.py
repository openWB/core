from unittest.mock import Mock

import pytest

from dataclass_utils import dataclass_from_dict
from modules.common.store._api import LoggingValueStore
from modules.conftest import SAMPLE_IP
from modules.devices.fronius.fronius_http_api import bat
from modules.devices.fronius.fronius_http_api.config import FroniusBatSetup, FroniusConfiguration


def test_update(monkeypatch, mock_simcount):
    component_config = FroniusBatSetup()
    device_config = FroniusConfiguration()
    device_config.ip_address = SAMPLE_IP
    assert component_config.configuration.meter_id == 0
    battery = bat.FroniusBat(component_config, device_config=dataclass_from_dict(
        FroniusConfiguration, device_config), device_id=0)
    battery.initialize()

    mock = Mock(return_value=None)
    monkeypatch.setattr(LoggingValueStore, "set", mock)
    mock_simcount.return_value = 0, 0

    battery.update(json)

    # mock_valuestore.assert_called_once()
    battery_state = mock.call_args[0][0]
    assert battery_state.exported == 0
    assert battery_state.imported == 0
    assert battery_state.power == -2288
    assert battery_state.soc == 60.8


def test_update_connection_error_raises(monkeypatch, mock_simcount):
    # Anders als beim Wechselrichter ist ein "keine Antwort" beim Speicher kein normaler
    # Nachtmodus-Zustand (der Speicher entlädt weiterhin) -- die Komponente muss fehlerhaft werden,
    # statt falsche 0-Werte zu melden.
    component_config = FroniusBatSetup()
    device_config = FroniusConfiguration()
    device_config.ip_address = SAMPLE_IP
    battery = bat.FroniusBat(component_config, device_config=dataclass_from_dict(
        FroniusConfiguration, device_config), device_id=0)
    battery.initialize()

    mock = Mock(return_value=None)
    monkeypatch.setattr(LoggingValueStore, "set", mock)
    mock_simcount.return_value = 0, 0

    with pytest.raises(ConnectionError):
        battery.update(ConnectionError("no response"))


def test_power_limit_controllable_without_credentials():
    component_config = FroniusBatSetup()
    device_config = FroniusConfiguration()
    device_config.ip_address = SAMPLE_IP
    battery = bat.FroniusBat(component_config, device_config=dataclass_from_dict(
        FroniusConfiguration, device_config), device_id=0)
    battery.initialize()

    assert battery.power_limit_controllable() is False


def test_power_limit_controllable_with_credentials():
    component_config = FroniusBatSetup()
    component_config.configuration.username = "installer"
    component_config.configuration.password = "secret"
    device_config = FroniusConfiguration()
    device_config.ip_address = SAMPLE_IP
    battery = bat.FroniusBat(component_config, device_config=dataclass_from_dict(
        FroniusConfiguration, device_config), device_id=0)
    battery.initialize()

    assert battery.power_limit_controllable() is True


def test_set_power_limit_without_credentials_does_not_connect(monkeypatch):
    # Ohne Zugangsdaten darf gar nicht erst versucht werden, eine Verbindung aufzubauen -- das würde
    # mit ungültigen Zugangsdaten fehlschlagende Login-Versuche gegen den Wechselrichter auslösen.
    mock_fronius_wr = Mock(side_effect=AssertionError("FroniusWR sollte ohne Zugangsdaten nicht erzeugt werden"))
    monkeypatch.setattr(bat, "FroniusWR", mock_fronius_wr)

    component_config = FroniusBatSetup()
    device_config = FroniusConfiguration()
    device_config.ip_address = SAMPLE_IP
    battery = bat.FroniusBat(component_config, device_config=dataclass_from_dict(
        FroniusConfiguration, device_config), device_id=0)
    battery.initialize()

    battery.set_power_limit(0)

    mock_fronius_wr.assert_not_called()


@pytest.mark.parametrize("power_limit, expected_call, expected_mode, repeats_call", [
    pytest.param(None, "set_mode_self_regulation", None, False, id="self_regulation"),
    pytest.param(0, "set_mode_avoid_discharge", "stop", False, id="stop"),
    pytest.param(-500, "set_mode_force_discharge", "discharge", True, id="discharge"),
    pytest.param(500, "set_mode_force_charge", "charge", True, id="charge"),
])
def test_set_power_limit_with_credentials(monkeypatch, power_limit, expected_call, expected_mode, repeats_call):
    mock_bat_api = Mock()
    mock_fronius_wr = Mock(return_value=mock_bat_api)
    monkeypatch.setattr(bat, "FroniusWR", mock_fronius_wr)

    component_config = FroniusBatSetup()
    component_config.configuration.username = "installer"
    component_config.configuration.password = "secret"
    device_config = FroniusConfiguration()
    device_config.ip_address = SAMPLE_IP
    battery = bat.FroniusBat(component_config, device_config=dataclass_from_dict(
        FroniusConfiguration, device_config), device_id=0)
    battery.initialize()

    battery.set_power_limit(power_limit)

    mock_fronius_wr.assert_called_once_with({
        'address': SAMPLE_IP,
        'user': "installer",
        'password': "secret",
    })
    getattr(mock_bat_api, expected_call).assert_called_once()
    assert battery.last_mode == expected_mode

    # Ein zweiter Aufruf muss die bestehende FroniusWR-Instanz wiederverwenden (nicht neu erzeugen).
    # Self-regulation/Stop dürfen dabei nicht erneut angestoßen werden, sobald der Modus schon aktiv
    # ist; Force-Charge/-Discharge werden hingegen bei jedem Aufruf erneut gesetzt, da sich die
    # gewünschte Lade-/Entladeleistung geändert haben könnte.
    battery.set_power_limit(power_limit)
    mock_fronius_wr.assert_called_once()
    expected_count = 2 if repeats_call else 1
    assert getattr(mock_bat_api, expected_call).call_count == expected_count
    mock_bat_api.set_config.assert_called_with(SAMPLE_IP, "installer", "secret")


json = {
    "Body": {
        "Data": {
            "Inverters": {
                "1": {
                    "Battery_Mode": "normal",
                    "DT": 1,
                    "E_Day": None,
                    "E_Total": 9805020.3608333338,
                    "E_Year": None,
                    "P": 2246.208984375,
                    "SOC": 60.799999999999997
                }
            },
            "Site": {
                "BackupMode": "false",
                "BatteryStandby": "true",
                "E_Day": None,
                "E_Total": 9805020.3608333338,
                "E_Year": None,
                "Meter_Location": "grid",
                "Mode": "bidirectional",
                "P_Akku": 2288.587158203125,
                "P_Grid": 280.39999999999998,
                "P_Load": -2938.6320312500002,
                "P_PV": 3.5314908027648926,
                "rel_Autonomy": 90.458145252002623,
                "rel_SelfConsumption": 100.0
            },
            "Smartloads": {
                "Ohmpilots": {}
            },
            "Version": "12"
        }
    },
    "Head": {
        "RequestArguments": {},
        "Status": {
            "Code": 0,
            "Reason": "",
            "UserMessage": ""
        },
        "Timestamp": "2022-01-03T17:17:36+00:00"
    }
}
