import re
from typing import List, Optional, Tuple, Union
from unittest.mock import MagicMock, Mock, patch

import pytest
from modules.common import sdm
from modules.common.evse import Evse
from modules.common.hardware_check import (
    EVSE_BROKEN, LAN_ADAPTER_BROKEN, METER_BROKEN, METER_NO_SERIAL_NUMBER, METER_PROBLEM, OPEN_TICKET,
    USB_ADAPTER_BROKEN, SeriesHardwareCheckMixin, check_meter_values)
from modules.common.modbus import NO_CONNECTION, ModbusClient, ModbusSerialClient_, ModbusTcpClient_
from modules.conftest import SAMPLE_IP, SAMPLE_PORT
from modules.internal_chargepoint_handler.clients import ClientHandler


@pytest.mark.parametrize(
    ("evse_side_effect, evse_return_value, meter_side_effect, meter_return_value, handle_exception_side_effect,"
     "handle_exception_return_value, client_spec, expected_error_msg"),
    [pytest.param(Exception("Modbus"), None, None, [230]*3, None, False, ModbusSerialClient_, EVSE_BROKEN,
                  id="EVSE defekt"),
     pytest.param(Exception("Modbus"), None, None, [230, 0, 230], None, False, ModbusSerialClient_,
                  EVSE_BROKEN + " " + METER_BROKEN.format([230, 0, 230]) + OPEN_TICKET,
                  id="EVSE defekt und Zähler eine Phase defekt"),
     pytest.param(None, 18, Exception("Modbus"), None, None, None,
                  ModbusSerialClient_, METER_PROBLEM, id="Zähler falsch konfiguriert"),
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
    mock_evse_factory = Mock(spec=Evse, return_value=mock_evse_client)
    monkeypatch.setattr(ClientHandler, "_evse_factory", mock_evse_factory)

    mock_meter_client = Mock(spec=sdm.Sdm630_72, get_voltages=Mock(
        side_effect=meter_side_effect, return_value=meter_return_value))
    mock_find_meter_client = Mock(spec=sdm.Sdm630_72, return_value=mock_meter_client)
    monkeypatch.setattr(ClientHandler, "find_meter_client", mock_find_meter_client)

    handle_exception_mock = Mock(side_effect=handle_exception_side_effect, return_value=handle_exception_return_value)
    monkeypatch.setattr(SeriesHardwareCheckMixin, "handle_exception", handle_exception_mock)

    mock_modbus_client = MagicMock(spec=client_spec, address=SAMPLE_IP, port=SAMPLE_PORT)
    mock_modbus_client.__enter__.return_value = mock_modbus_client

    # execution and evaluation
    with pytest.raises(Exception, match=re.escape(expected_error_msg)):
        ClientHandler(0, mock_modbus_client, [1], Mock())


def test_hardware_check_succeeds(monkeypatch):
    # setup
    mock_evse_client = Mock(spec=Evse, get_firmware_version=Mock(return_value=18))
    mock_evse_factory = Mock(spec=Evse, return_value=mock_evse_client)
    monkeypatch.setattr(ClientHandler, "_evse_factory", mock_evse_factory)

    mock_meter_client = Mock(spec=sdm.Sdm630_72, get_voltages=Mock(return_value=[230]*3))
    mock_find_meter_client = Mock(spec=sdm.Sdm630_72, return_value=mock_meter_client)
    monkeypatch.setattr(ClientHandler, "find_meter_client", mock_find_meter_client)

    mock_modbus_client = MagicMock(spec=ModbusClient)
    mock_modbus_client.__enter__.return_value = mock_modbus_client

    # execution and evaluation
    # keine Exception
    ClientHandler(0, mock_modbus_client, [1], Mock())


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
def test_check_meter_values(voltages, expected_msg, monkeypatch):
    # setup & execution
    msg = check_meter_values(voltages)

    # assert
    assert msg == expected_msg if expected_msg is None else expected_msg.format(voltages)


@patch('modules.common.hardware_check.ClientHandlerProtocol')
@pytest.mark.parametrize("serial_number_return, voltages_return, expected",
                         [("0", [230]*3, (True, METER_NO_SERIAL_NUMBER)),
                          (12345, [230]*3, (True, None)),
                          (Exception(), [230]*3, (False, METER_PROBLEM))])
def test_check_meter(
    MockClientHandlerProtocol: Mock,
    serial_number_return: Union[int, Exception],
    voltages_return: List[int],
    expected: Tuple[bool, Optional[str]],
):
    # Arrange
    mock_meter_client = Mock()
    if isinstance(serial_number_return, Exception):
        mock_meter_client.get_serial_number.side_effect = serial_number_return
    else:
        mock_meter_client.get_serial_number.return_value = serial_number_return
    mock_meter_client.get_voltages.return_value = voltages_return
    MockClientHandlerProtocol.meter_client = mock_meter_client
    mixin = SeriesHardwareCheckMixin

    # Act
    result = mixin.check_meter(MockClientHandlerProtocol)

    # Assert
    assert result == expected
