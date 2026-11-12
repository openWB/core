from unittest.mock import Mock

from control.bat import Set
from modules.devices.e3dc.e3dc import bat
from modules.devices.e3dc.e3dc.config import E3dcBatSetup, E3dcConfiguration


def _create_bat(**configuration_kwargs) -> bat.E3dcBat:
    component_config = E3dcBatSetup()
    component_config.configuration.__dict__.update(configuration_kwargs)
    battery = bat.E3dcBat(component_config, device_id=0, modbus_id=1, client=Mock(),
                          device_config=E3dcConfiguration(address="192.0.2.50"))
    battery.initialize()
    return battery


def test_power_limit_controllable_without_credentials():
    battery = _create_bat()

    assert battery.power_limit_controllable() is False


def test_power_limit_controllable_with_credentials():
    battery = _create_bat(portal_username="user", portal_password="secret", rscp_key="key")

    assert battery.power_limit_controllable() is True


def test_set_power_limit_without_credentials_does_not_connect(monkeypatch):
    mock_rscp_control = Mock(
        side_effect=AssertionError("E3dcRscpBatControl sollte ohne Zugangsdaten nicht erzeugt werden"))
    monkeypatch.setattr(bat, "E3dcRscpBatControl", mock_rscp_control)
    battery = _create_bat()

    battery.set_power_limit(Set(power_limit=0))

    mock_rscp_control.assert_not_called()


def test_set_power_limit_with_credentials_forwards_to_rscp_control(monkeypatch):
    mock_control = Mock()
    mock_rscp_control = Mock(return_value=mock_control)
    monkeypatch.setattr(bat, "E3dcRscpBatControl", mock_rscp_control)
    battery = _create_bat(portal_username="user", portal_password="secret", rscp_key="key")

    battery.set_power_limit(Set(power_limit=-2000))

    mock_rscp_control.assert_called_once_with("192.0.2.50", "user", "secret", "key")
    mock_control.set_power_limit.assert_called_once_with(-2000)

    # Ein zweiter Aufruf muss die bestehende E3dcRscpBatControl-Instanz wiederverwenden.
    battery.set_power_limit(Set(power_limit=3000))
    mock_rscp_control.assert_called_once()
    mock_control.set_power_limit.assert_called_with(3000)
