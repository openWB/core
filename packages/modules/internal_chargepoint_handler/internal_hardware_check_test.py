from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pymodbus
import pytest

from helpermodules import timecheck
from helpermodules.exceptions.registry import ExceptionRegistry
from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState, CounterState, EvseState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusSerialClient_, ModbusTcpClient_
from modules.internal_chargepoint_handler import chargepoint_module
from modules.internal_chargepoint_handler.chargepoint_module import ChargepointModule
from modules.internal_chargepoint_handler.internal_hardware_check import (
    METER_PROBLEM, METER_UNREACHABLE, READ_LAN_ADAPTER_AGAIN, READ_USB_ADAPTER_AGAIN, SeriesHardwareCheckMixin)


@pytest.mark.parametrize("tcp", [False, True])
@pytest.mark.parametrize("evse_available", [False, True])
def test_meter_error_message_after_timeout_and_recovery(tcp, evse_available, monkeypatch, mock_pub, caplog):
    monkeypatch.setattr(ExceptionRegistry, "registry", [])
    clock = Mock(return_value=1000)
    monkeypatch.setattr(timecheck, "create_timestamp", clock)
    monkeypatch.setattr(chargepoint_module.time, "sleep", Mock())
    monkeypatch.setattr(pymodbus, "exceptions", SimpleNamespace(
        ConnectionException=type("ConnectionException", (Exception,), {})), raising=False)
    hardware = SeriesHardwareCheckMixin()
    hardware.client = MagicMock(spec=ModbusTcpClient_ if tcp else ModbusSerialClient_)
    hardware.evse_client = Mock()
    hardware.evse_client.get_evse_state.return_value = EvseState(True, False, 6, 16)
    if not evse_available:
        hardware.evse_client.get_evse_state.side_effect = Exception("EVSE read failed")
    hardware.meter_client = Mock()
    hardware.meter_client.get_counter_state.side_effect = Exception("Meter read failed")
    hardware.meter_client.get_counter_state.return_value = CounterState(
        power=100, currents=[1, 0, 0], voltages=[230]*3, serial_number="1234")

    module = ChargepointModule.__new__(ChargepointModule)
    module._client = hardware
    module.fault_state = FaultState(ComponentInfo(0, "Ladepunkt 0", "internal_chargepoint", hierarchy_id=3))
    module.client_error_context = ErrorTimerContext("test/error_timestamp", CP_ERROR, hide_exception=True)
    module.old_chargepoint_state = ChargepointState(
        power=100, currents=[1, 0, 0], plug_state=True, charge_state=False,
        phases_in_use=1, imported=10, exported=0)
    module.old_plug_state = True
    module.old_phases_in_use = 1
    module.store = Mock()
    module.store_internal = Mock()
    module.version = module.current_branch = module.current_commit = "test"
    retry_message = METER_PROBLEM if evse_available else (
        READ_LAN_ADAPTER_AGAIN if tcp else READ_USB_ADAPTER_AGAIN)

    def read():
        with SingleComponentUpdateContext(module.fault_state):
            module.get_values(False, None)

    for elapsed in (0, 59):
        clock.return_value = 1000 + elapsed
        caplog.clear()
        read()
        assert retry_message in caplog.text
        assert METER_UNREACHABLE not in caplog.text
        assert module.fault_state.fault_state.value == 0
        assert module.old_chargepoint_state.power == 100

    clock.return_value = 1061
    caplog.clear()
    read()
    assert (METER_UNREACHABLE in caplog.text) is evse_available
    assert module.old_chargepoint_state.power == 0

    clock.return_value = 1071
    read()
    assert module.fault_state.fault_state.value == 2
    assert module.fault_state.fault_str == (METER_UNREACHABLE if evse_available else retry_message)
    mock_pub.pub.assert_any_call("openWB/set/internal_chargepoint/0/get/fault_str", module.fault_state.fault_str)
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/3/get/fault_str", module.fault_state.fault_str)

    clock.return_value = 1200
    hardware.evse_client.get_evse_state.side_effect = None
    hardware.meter_client.get_counter_state.side_effect = None
    read()
    assert module.client_error_context.error_timestamp is None
    assert module.fault_state.fault_state.value == 0
    assert module.old_chargepoint_state.power == 100

    hardware.meter_client.get_counter_state.side_effect = Exception("Meter read failed again")
    caplog.clear()
    read()
    assert METER_PROBLEM in caplog.text
    assert METER_UNREACHABLE not in caplog.text
    assert module.fault_state.fault_state.value == 0
