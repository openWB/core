from unittest.mock import Mock

import pytest
from modules.common import sdm
from modules.common.evse import Evse
from modules.common.hardware_check import (
    EVSE_BROKEN, LAN_ADAPTER_BROKEN, METER_BROKEN, METER_PROBLEM, USB_ADAPTER_BROKEN,
    SeriesHardwareCheckMixin, check_meter_values)
from modules.common.modbus import NO_CONNECTION, ModbusSerialClient_, ModbusTcpClient_
from modules.conftest import SAMPLE_IP, SAMPLE_PORT
from modules.internal_chargepoint_handler.clients import ClientHandler


@pytest.mark.parametrize(
    ("evse_side_effect, evse_return_value, meter_side_effect, meter_return_value, handle_exception_side_effect,"
     "handle_exception_return_value, client_spec, expected_error_msg"),
    [pytest.param(Exception("Modbus"), None, None, [230]*3, None, False, ModbusSerialClient_, EVSE_BROKEN,
                  id="EVSE defekt"),
     pytest.param(None, 18, Exception("Modbus"), None, None, None,
                  ModbusSerialClient_, METER_PROBLEM, id="Zähler verkonfiguriert"),
     pytest.param(Exception("Modbus"), None, Exception("Modbus"), None, None, False, ModbusSerialClient_,
                  USB_ADAPTER_BROKEN, id="USB-Adapter defekt"),
     pytest.param(Exception("Modbus"), None, Exception("Modbus"), None, None, False, ModbusTcpClient_,
                  LAN_ADAPTER_BROKEN, id="LAN-Adapter defekt"),
     pytest.param(Exception("Modbus"), None, Exception("Modbus"), None,
                  Exception(NO_CONNECTION.format(SAMPLE_IP, SAMPLE_PORT)), None, ModbusTcpClient_,
                  NO_CONNECTION.format(SAMPLE_IP, SAMPLE_PORT), id="LAN-Adapter nicht erreichbar"),
     ]
)
def test_hardware_check_fails(evse_side_effect,
                              evse_return_value,
                              meter_side_effect,
                              meter_return_value,
                              handle_exception_side_effect,
                              handle_exception_return_value,
                              client_spec,
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

    handle_exception_mock = Mock(side_effect=handle_exception_side_effect, return_value=handle_exception_return_value)
    monkeypatch.setattr(SeriesHardwareCheckMixin, "handle_exception", handle_exception_mock)

    # execution and evaluation
    with pytest.raises(Exception, match=expected_error_msg):
        ClientHandler(0, Mock(spec=client_spec, address=SAMPLE_IP, port=SAMPLE_PORT), [1], Mock())


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
    ClientHandler(0, Mock(), [1], Mock())


@pytest.mark.parametrize(
    "voltages, expected_msg",
    [pytest.param([230, 0, 0], None, id="einphasig oder zweiphasig L2 defekt (nicht erkennbar)"),
     pytest.param([0, 0, 0], METER_BROKEN, id="einphasig, L1 defekt"),
     pytest.param([230, 230, 0], None, id="zweiphasig oder dreiphasig, L3 defekt (nicht erkennbar)"),
     pytest.param([0, 230, 0], METER_BROKEN, id="zweiphasig, L1 defekt"),
     pytest.param([230, 230, 230], None, id="dreiphasig"),
     pytest.param([0, 230, 230], METER_BROKEN, id="dreiphasig, L1 defekt"),
     pytest.param([230, 0, 230], METER_BROKEN, id="dreiphasig, L2 defekt"),
     ]
)
def test_check_meter(voltages, expected_msg, monkeypatch):
    # setup & execution
    msg = check_meter_values(voltages)

    # assert
    assert msg == expected_msg
