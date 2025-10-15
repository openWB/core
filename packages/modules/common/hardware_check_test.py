import re
from typing import List, Optional, Tuple, Union
from unittest.mock import Mock, patch

import pytest
from modules.common import sdm
from modules.common import hardware_check
from modules.common.component_state import CounterState, EvseState
from modules.common.evse import Evse
from modules.common.hardware_check import (
    EVSE_BROKEN, LAN_ADAPTER_BROKEN, METER_BROKEN_VOLTAGES, METER_NO_SERIAL_NUMBER,
    METER_PROBLEM, OPEN_TICKET, USB_ADAPTER_BROKEN,
    SeriesHardwareCheckMixin, _check_meter_values)
from modules.common.modbus import NO_CONNECTION, ModbusSerialClient_, ModbusTcpClient_
from modules.conftest import SAMPLE_IP, SAMPLE_PORT
from modules.internal_chargepoint_handler.clients import ClientHandler


@pytest.mark.parametrize(
    ("evse_side_effect, meter_side_effect, meter_return_value, handle_exception_side_effect,"
     "handle_exception_return_value, client_spec, expected_error_msg"),
    [pytest.param(Exception("Modbus"), None, [230]*3, None, False, ModbusSerialClient_, EVSE_BROKEN,
                  id="EVSE defekt"),
     pytest.param(Exception("Modbus"), None, [230, 0, 230], None, False, ModbusSerialClient_,
                  EVSE_BROKEN + " " + METER_BROKEN_VOLTAGES.format([230, 0, 230]) + OPEN_TICKET,
                  id="EVSE defekt und Zähler eine Phase defekt"),
     pytest.param(None, Exception("Modbus"), None, None, None,
                  ModbusSerialClient_, METER_PROBLEM, id="Zähler falsch konfiguriert"),
     pytest.param(Exception("Modbus"), Exception("Modbus"), None, None, False, ModbusSerialClient_,
                  USB_ADAPTER_BROKEN, id="USB-Adapter defekt"),
     pytest.param(Exception("Modbus"), Exception("Modbus"), None, None, False, ModbusTcpClient_,
                  LAN_ADAPTER_BROKEN, id="LAN-Adapter defekt"),
     pytest.param(Exception("Modbus"), Exception("Modbus"), None,
                  Exception(NO_CONNECTION.format(SAMPLE_IP, SAMPLE_PORT)), None, ModbusTcpClient_,
                  NO_CONNECTION.format(SAMPLE_IP, SAMPLE_PORT), id="LAN-Adapter nicht erreichbar"),
     ]
)
def test_hardware_check_fails(evse_side_effect,
                              meter_side_effect,
                              meter_return_value,
                              handle_exception_side_effect,
                              handle_exception_return_value,
                              client_spec,
                              expected_error_msg,
                              monkeypatch):
    # setup
    mock_evse_client = Mock(spec=Evse, version=18, get_evse_state=Mock(side_effect=[evse_side_effect]))
    monkeypatch.setattr(ClientHandler, "_evse_factory", Mock(return_value=mock_evse_client))

    counter_state_mock = Mock(spec=CounterState,
                              voltages=meter_return_value,
                              currents=[0, 0, 0],
                              powers=[0, 0, 0],
                              power=0,
                              serial_number="1234")
    mock_meter_client = Mock(spec=sdm.Sdm630_72, get_counter_state=Mock(
        side_effect=meter_side_effect, return_value=counter_state_mock))
    monkeypatch.setattr(ClientHandler, "find_meter_client", Mock(return_value=mock_meter_client))

    monkeypatch.setattr(SeriesHardwareCheckMixin, "handle_exception", Mock(
        side_effect=handle_exception_side_effect, return_value=handle_exception_return_value))

    client = Mock(spec=client_spec, __enter__=Mock(return_value=None), __exit__=Mock(return_value=None))

    # execution and evaluation
    with pytest.raises(Exception, match=re.escape(expected_error_msg)):
        ClientHandler(0, client, [1], Mock())


def test_hardware_check_succeeds(monkeypatch):
    # setup
    mock_evse_client = Mock(spec=Evse, get_evse_state=Mock(return_value=Mock(spec=EvseState)), version=17)
    mock_evse_facotry = Mock(return_value=mock_evse_client)
    monkeypatch.setattr(ClientHandler, "_evse_factory", mock_evse_facotry)

    counter_state_mock = Mock(spec=CounterState, voltages=[
                              230]*3, currents=[0, 0, 0], powers=[0, 0, 0], power=0, serial_number="1234")
    mock_meter_client = Mock(spec=sdm.Sdm630_72, get_counter_state=Mock(return_value=counter_state_mock))
    mock_find_meter_client = Mock(spec=sdm.Sdm630_72, return_value=mock_meter_client)
    monkeypatch.setattr(ClientHandler, "find_meter_client", mock_find_meter_client)

    enter_mock = Mock(return_value=None)
    exit_mock = Mock(return_value=True)
    client = Mock(spec=ModbusTcpClient_, __enter__=enter_mock, __exit__=exit_mock)

    # execution and evaluation
    # keine Exception
    ClientHandler(0, client, [1], Mock())


@pytest.mark.parametrize(
    "voltages, power, expected_msg",
    [pytest.param([230, 0, 0], 0, None, id="einphasig oder zweiphasig L2 defekt (nicht erkennbar)"),
     pytest.param([0, 0, 0], 0, METER_BROKEN_VOLTAGES.format([0]*3), id="einphasig, L1 defekt"),
     pytest.param([230, 230, 0], 0, None, id="zweiphasig oder dreiphasig, L3 defekt (nicht erkennbar)"),
     pytest.param([0, 230, 0], 0, METER_BROKEN_VOLTAGES.format([0, 230, 0]), id="zweiphasig, L1 defekt"),
     pytest.param([230, 230, 230], 0, None, id="dreiphasig"),
     pytest.param([0, 230, 230], 0, METER_BROKEN_VOLTAGES.format([0, 230, 230]), id="dreiphasig, L1 defekt"),
     pytest.param([230, 0, 230], 0, METER_BROKEN_VOLTAGES.format([230, 0, 230]), id="dreiphasig, L2 defekt"),
     pytest.param([230]*3, 100, METER_PROBLEM, id="Phantom-Leistung"),
     ]
)
def test_check_meter_values_voltages(voltages, power, expected_msg, monkeypatch):
    # setup
    counter_state = Mock(voltages=voltages, currents=[0, 0, 0], powers=[0, 0, 0], power=power)
    # execution
    msg = _check_meter_values(counter_state)

    # assert
    assert msg == expected_msg if expected_msg is None else expected_msg.format(voltages)


@patch('modules.common.hardware_check.ClientHandlerProtocol')
@pytest.mark.parametrize("serial_number, voltages, expected",
                         [("0", [230]*3, (True, METER_NO_SERIAL_NUMBER, CounterState)),
                          (12345, [230]*3, (True, None, CounterState)),
                          (Exception(), [230]*3, (False, METER_PROBLEM, None))])
def test_check_meter(
    MockClientHandlerProtocol: Mock,
    serial_number: Union[int, Exception],
    voltages: List[int],
    expected: Tuple[bool, Optional[str]],
    monkeypatch,
):
    # Arrange

    if isinstance(serial_number, Exception):
        counter_state_mock = Mock(spec=CounterState, side_effect=serial_number)
    else:
        counter_state_mock = Mock(spec=CounterState, serial_number=serial_number,
                                  voltages=voltages, currents=[0, 0, 0], powers=[0, 0, 0], power=0)
    mock_meter_client = Mock()
    mock_meter_client.get_counter_state.return_value = counter_state_mock
    MockClientHandlerProtocol.meter_client = mock_meter_client
    mixin = SeriesHardwareCheckMixin
    mock_check_meter_values = Mock(return_value=expected[1])
    monkeypatch.setattr(hardware_check, "check_meter_values", mock_check_meter_values)

    # Act
    result = mixin.check_meter(MockClientHandlerProtocol)

    # Assert
    assert result[0] == expected[0]
    assert result[1] == expected[1]
    assert isinstance(result[2], expected[2] if expected[2] is not None else type(result[2]))
