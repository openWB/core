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
from modules.chargepoints.internal_openwb.config import InternalChargepointMode
from modules.internal_chargepoint_handler import chargepoint_module, clients, internal_chargepoint_handler
from modules.internal_chargepoint_handler.chargepoint_module import ChargepointModule
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import (
    GlobalHandlerData, InternalChargepoint)
from modules.internal_chargepoint_handler.internal_hardware_check import (
    EVSE_UNREACHABLE, METER_PROBLEM, METER_UNREACHABLE, READ_EVSE_AGAIN,
    READ_LAN_ADAPTER_AGAIN, READ_USB_ADAPTER_AGAIN, SeriesHardwareCheckMixin)
from modules.internal_chargepoint_handler.wallbox_socket_config import WallboxSocket


@pytest.mark.parametrize("tcp", [False, True])
@pytest.mark.parametrize("meter_available, evse_available", [(False, False), (False, True), (True, False)])
def test_hardware_error_message_after_timeout_and_recovery(
        tcp, meter_available, evse_available, monkeypatch, mock_pub, caplog):
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
    if not meter_available:
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
    if evse_available:
        retry_message, sustained_message = METER_PROBLEM, METER_UNREACHABLE
    elif meter_available:
        retry_message, sustained_message = READ_EVSE_AGAIN, EVSE_UNREACHABLE
    else:
        retry_message = sustained_message = READ_LAN_ADAPTER_AGAIN if tcp else READ_USB_ADAPTER_AGAIN

    def read():
        with SingleComponentUpdateContext(module.fault_state):
            module.get_values(False, None)

    for elapsed in (0, 59):
        clock.return_value = 1000 + elapsed
        caplog.clear()
        read()
        assert retry_message in caplog.text
        if retry_message != sustained_message:
            assert sustained_message not in caplog.text
        assert module.fault_state.fault_state.value == 0
        assert module.old_chargepoint_state.power == 100

    clock.return_value = 1061
    caplog.clear()
    read()
    assert sustained_message in caplog.text
    assert module.old_chargepoint_state.power == 0

    clock.return_value = 1071
    read()
    assert module.fault_state.fault_state.value == 2
    assert module.fault_state.fault_str == sustained_message
    mock_pub.pub.assert_any_call("openWB/set/internal_chargepoint/0/get/fault_str", module.fault_state.fault_str)
    mock_pub.pub.assert_any_call("openWB/set/chargepoint/3/get/fault_str", module.fault_state.fault_str)

    clock.return_value = 1200
    hardware.evse_client.get_evse_state.side_effect = None
    hardware.meter_client.get_counter_state.side_effect = None
    read()
    assert module.client_error_context.error_timestamp is None
    assert module.fault_state.fault_state.value == 0
    assert module.old_chargepoint_state.power == 100

    if not meter_available:
        hardware.meter_client.get_counter_state.side_effect = Exception("Meter read failed again")
    if not evse_available:
        hardware.evse_client.get_evse_state.side_effect = Exception("EVSE read failed again")
    caplog.clear()
    read()
    assert retry_message in caplog.text
    if retry_message != sustained_message:
        assert sustained_message not in caplog.text
    assert module.fault_state.fault_state.value == 0


@pytest.mark.parametrize("error_timestamp", [None, 1000])
@pytest.mark.parametrize("failed_hardware", ["meter", "evse"])
def test_handler_initialization_reports_hardware_error_immediately(
        error_timestamp, failed_hardware, monkeypatch, mock_pub):
    monkeypatch.setattr(ExceptionRegistry, "registry", [])
    clock = Mock(return_value=1000)
    monkeypatch.setattr(timecheck, "create_timestamp", clock)
    monkeypatch.setattr(chargepoint_module.time, "sleep", Mock())
    monkeypatch.setattr(internal_chargepoint_handler.InternalChargepointHandler, "init_gpio", Mock())
    client = MagicMock(spec=ModbusSerialClient_)
    get_modbus_client = Mock(return_value=(client, [11]))
    monkeypatch.setattr(clients, "get_modbus_client", get_modbus_client)
    monkeypatch.setattr(internal_chargepoint_handler, "get_modbus_client", get_modbus_client)
    evse = Mock(get_evse_state=Mock(return_value=EvseState(True, False, 6, 16)))
    meter = Mock(get_counter_state=Mock(return_value=CounterState(
        power=0, currents=[0]*3, voltages=[230]*3, serial_number="1234")))
    # Nach dem Neustart wird die ausgefallene Hardware nicht mehr erkannt.
    monkeypatch.setattr(clients.ClientHandler, "_evse_factory", Mock(
        return_value=None if failed_hardware == "evse" else evse))
    monkeypatch.setattr(clients.ClientHandler, "find_meter_client", Mock(
        return_value=None if failed_hardware == "meter" else meter))
    expected_message = METER_UNREACHABLE if failed_hardware == "meter" else EVSE_UNREACHABLE
    chargepoints = [InternalChargepoint(), InternalChargepoint()]
    for cp in chargepoints:
        cp.get.error_timestamp = error_timestamp
    for elapsed in (0, 59, 61, 71, 300):
        clock.return_value = 1000 + elapsed
        mock_pub.reset_mock()
        handler = internal_chargepoint_handler.InternalChargepointHandler(
            InternalChargepointMode.DUO, GlobalHandlerData(), chargepoints[0], 3, chargepoints[1], 4,
            WallboxSocket(), Mock(), Mock())
        assert handler.cp0 is None
        assert handler.cp1 is None
        for num in range(len(chargepoints)):
            mock_pub.pub.assert_any_call(f"openWB/set/internal_chargepoint/{num}/get/fault_str", expected_message)
            mock_pub.pub.assert_any_call(f"openWB/set/chargepoint/{num + 3}/get/fault_str", expected_message)
        assert not any(call.args[0].endswith("/error_timestamp") for call in mock_pub.pub.call_args_list)
