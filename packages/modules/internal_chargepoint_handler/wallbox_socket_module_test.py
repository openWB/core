from unittest.mock import MagicMock, Mock

import pytest

from helpermodules import timecheck
from helpermodules.exceptions.registry import ExceptionRegistry
from helpermodules.utils.error_handling import RetryableError
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CounterState, ConsumerState
from modules.common.store import _wallbox_socket
from modules.internal_chargepoint_handler import wallbox_socket
from modules.internal_chargepoint_handler.internal_hardware_check import (
    METER_PROBLEM, METER_UNREACHABLE, READ_USB_ADAPTER_AGAIN, USB_ADAPTER_UNREACHABLE)
from modules.internal_chargepoint_handler.wallbox_socket_config import WallboxSocket


@pytest.mark.parametrize("tag", ["0012345678", None])
def test_wallbox_socket_measurement_publishes_current_rfid_and_clears_previous_tag(tag, monkeypatch):
    publisher = Mock()
    monkeypatch.setattr(_wallbox_socket, "pub_to_broker", publisher)
    monkeypatch.setattr(wallbox_socket.time, "sleep", Mock())
    module = wallbox_socket.WallboxSocketModule.__new__(wallbox_socket.WallboxSocketModule)
    module._client = Mock()
    module._client = MagicMock()
    module.meter_client = Mock()
    module.meter_client.get_counter_state.return_value = CounterState(
        power=100, imported=20, exported=0, currents=[1, 0, 0], voltages=[230, 0, 0])
    module.client_error_context = MagicMock()
    module.client_error_context.error_counter_exceeded.return_value = False
    module.fault_state = Mock()
    module.current_state = False
    module.measurement_valid = False
    module.old_wallbox_socket_state = ConsumerState(power=0)
    module.store_wallbox_socket = _wallbox_socket.WallboxSocketValueStore()

    state = module.get_values(tag)

    assert isinstance(state, ConsumerState)
    assert state.rfid == tag
    assert state.power == 100
    publisher.assert_any_call("openWB/set/internal_socket/get/rfid", tag)
    publisher.reset_mock()

    state = module.get_values(None)

    assert state.rfid is None
    publisher.assert_any_call("openWB/set/internal_socket/get/rfid", None)


@pytest.mark.parametrize("chargepoint_meter_available", [False, True])
def test_wallbox_socket_bus_error_message_and_recovery(chargepoint_meter_available, monkeypatch, caplog):
    monkeypatch.setattr(ExceptionRegistry, "registry", [])
    clock = Mock(return_value=1000)
    monkeypatch.setattr(timecheck, "create_timestamp", clock)
    monkeypatch.setattr(wallbox_socket.time, "sleep", Mock())
    publisher = Mock()
    monkeypatch.setattr(_wallbox_socket, "pub_to_broker", publisher)
    counter_state = CounterState(
        power=100, imported=20, exported=0, currents=[1, 0, 0], voltages=[230]*3, serial_number="1234")
    socket_meter = Mock(get_counter_state=Mock(return_value=counter_state))
    diagnostic_meter = Mock(get_counter_state=Mock(return_value=counter_state))
    if not chargepoint_meter_available:
        diagnostic_meter.get_counter_state.side_effect = Exception("Bus read failed")
    monkeypatch.setattr(wallbox_socket, "WALLBOX_SOCKET_METERS", [(Mock(return_value=socket_meter), 8)])
    monkeypatch.setattr(wallbox_socket, "CP0_METERS", [(Mock(return_value=diagnostic_meter), 5)])
    client = MagicMock()
    module = wallbox_socket.WallboxSocketModule(client, WallboxSocket())
    assert module.get_values().power == 100
    socket_meter.get_counter_state.side_effect = Exception("Socket meter read failed")
    retry = METER_PROBLEM if chargepoint_meter_available else READ_USB_ADAPTER_AGAIN
    sustained = METER_UNREACHABLE if chargepoint_meter_available else USB_ADAPTER_UNREACHABLE

    def read() -> None:
        with SingleComponentUpdateContext(module.fault_state):
            module.get_values()

    for elapsed in (0, 59):
        clock.return_value = 1000 + elapsed
        caplog.clear()
        read()
        assert retry in caplog.text
        assert sustained not in caplog.text
        assert module.old_wallbox_socket_state.power == 100

    clock.return_value = 1061
    caplog.clear()
    read()
    assert sustained in caplog.text
    assert module.old_wallbox_socket_state.power == 0
    assert module.old_wallbox_socket_state.imported == 20
    publisher.assert_any_call("openWB/set/internal_socket/get/power", 0, 2)

    clock.return_value = 1071
    read()
    assert module.fault_state.fault_str == sustained
    assert module.fault_state.fault_state.value == 2

    clock.return_value = 1200
    socket_meter.get_counter_state.side_effect = None
    read()
    assert module.client_error_context.error_timestamp is None
    assert module.fault_state.fault_state.value == 0
    assert module.old_wallbox_socket_state.power == 100

    socket_meter.get_counter_state.side_effect = Exception("Socket meter read failed again")
    caplog.clear()
    read()
    assert retry in caplog.text
    assert sustained not in caplog.text
    with pytest.raises(RetryableError, match=sustained):
        wallbox_socket.WallboxSocketModule(client, WallboxSocket())
