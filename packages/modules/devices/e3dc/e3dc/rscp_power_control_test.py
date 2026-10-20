from unittest.mock import Mock

import pytest

from modules.devices.e3dc.e3dc import rscp_power_control
from modules.devices.e3dc.e3dc.rscp_power_control import E3dcRscpBatControl


@pytest.fixture
def mock_e3dc(monkeypatch) -> Mock:
    mock_client = Mock()
    mock_e3dc_class = Mock(return_value=mock_client)
    monkeypatch.setattr(rscp_power_control, "E3DC", mock_e3dc_class)
    return mock_client


def _sent_mode_and_value(mock_client: Mock):
    request = mock_client.sendRequest.call_args[0][0]
    sub_tags = request[2]
    mode = next(value for tag, _, value in sub_tags if tag == rscp_power_control.RscpTag.EMS_REQ_SET_POWER_MODE)
    power_value = next(value for tag, _, value in sub_tags if tag == rscp_power_control.RscpTag.EMS_REQ_SET_POWER_VALUE)
    return mode, power_value


@pytest.mark.parametrize("power_limit, expected_mode, expected_value", [
    pytest.param(None, rscp_power_control.MODE_AUTO, 0, id="auto"),
    pytest.param(0, rscp_power_control.MODE_IDLE, 0, id="idle"),
    pytest.param(-2000, rscp_power_control.MODE_DISCH, 2000, id="discharge"),
    pytest.param(3000, rscp_power_control.MODE_CHRG, 3000, id="charge"),
])
def test_set_power_limit_translates_to_rscp_mode_and_value(mock_e3dc, power_limit, expected_mode, expected_value):
    control = E3dcRscpBatControl("192.0.2.50", "user", "secret", "key")

    control.set_power_limit(power_limit)

    mode, value = _sent_mode_and_value(mock_e3dc)
    assert mode == expected_mode
    assert value == expected_value


def test_connection_is_created_lazily_and_reused(monkeypatch):
    mock_client = Mock()
    mock_e3dc_class = Mock(return_value=mock_client)
    monkeypatch.setattr(rscp_power_control, "E3DC", mock_e3dc_class)
    control = E3dcRscpBatControl("192.0.2.50", "user", "secret", "key")
    mock_e3dc_class.assert_not_called()

    control.set_power_limit(1000)
    control.set_power_limit(2000)

    mock_e3dc_class.assert_called_once_with(
        mock_e3dc_class.CONNECT_LOCAL, username="user", password="secret", ipAddress="192.0.2.50", key="key")
    assert mock_client.sendRequest.call_count == 2
