from unittest.mock import Mock

import pytest
from modules.common import sdm
from modules.common.evse import Evse
from modules.internal_chargepoint_handler.clients import ClientHandler


@pytest.mark.parametrize(
    "evse_side_effect, evse_return_value, meter_side_effect, meter_return_value, expected_error_msg",
    [pytest.param(Exception("Modbus"), None, None, [230]*3, ClientHandler.EVSE_BROKEN, id="EVSE defekt"),
     pytest.param(None, 18, Exception("Modbus"), None, ClientHandler.METER_PROBLEM, id="Zähler verkonfiguriert"),
     pytest.param(None, 18, None, [230, 0, 230], ClientHandler.METER_BROKEN, id="Zähler defekt"),
     pytest.param(Exception("Modbus"), None, Exception("Modbus"), None, ClientHandler.USB_ADAPTER_BROKEN,
                  id="USB-Adapter defekt")
     ]
)
def test_hardware_check_fails(evse_side_effect,
                              evse_return_value,
                              meter_side_effect,
                              meter_return_value,
                              expected_error_msg,
                              monkeypatch):
    # setup
    mock_evse_client = Mock(spec=Evse, get_firmware_version=Mock(
        side_effect=evse_side_effect, return_value=evse_return_value))
    mock_evse_facotry = Mock(spec=Evse, return_value=mock_evse_client)
    monkeypatch.setattr(ClientHandler, "_evse_factory", mock_evse_facotry)

    mock_meter_client = Mock(spec=sdm.Sdm630, get_voltages=Mock(
        side_effect=meter_side_effect, return_value=meter_return_value))
    mock_find_meter_client = Mock(spec=sdm.Sdm630, return_value=mock_meter_client)
    monkeypatch.setattr(ClientHandler, "find_meter_client", mock_find_meter_client)

    # execution and evaluation
    with pytest.raises(Exception, match=expected_error_msg):
        ClientHandler(0, Mock(), [1])


def test_hardware_check_succeeds(monkeypatch):
    # setup
    mock_evse_client = Mock(spec=Evse, get_firmware_version=Mock(return_value=18))
    mock_evse_facotry = Mock(spec=Evse, return_value=mock_evse_client)
    monkeypatch.setattr(ClientHandler, "_evse_factory", mock_evse_facotry)

    mock_meter_client = Mock(spec=sdm.Sdm630, get_voltages=Mock(return_value=[230]*3))
    mock_find_meter_client = Mock(spec=sdm.Sdm630, return_value=mock_meter_client)
    monkeypatch.setattr(ClientHandler, "find_meter_client", mock_find_meter_client)

    # execution and evaluation
    # keine Exception
    ClientHandler(0, Mock(), [1])
