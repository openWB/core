from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CounterState, InternalSocketState
from modules.common.fault_state_level import FaultStateLevel
from modules.internal_chargepoint_handler import clients, local_socket as socket_module
from modules.internal_chargepoint_handler.internal_socket_config import InternalSocket


@pytest.fixture
def socket(monkeypatch):
    from modules.common import fault_state
    from helpermodules.utils import error_handling

    monkeypatch.setattr(socket_module, "GPIO", Mock(BOARD=10, OUT=0, HIGH=1, LOW=0), raising=False)
    monkeypatch.setattr(socket_module, "get_internal_socket_value_store", Mock(return_value=Mock()))
    publisher = Mock()
    monkeypatch.setattr(fault_state, "Pub", Mock(return_value=publisher))
    monkeypatch.setattr(error_handling, "Pub", Mock(return_value=publisher))
    chargepoint_client = Mock()
    chargepoint_client.client = Mock()
    chargepoint_client.request_and_check_hardware.return_value = (Mock(), CounterState(
        power=10, imported=1, exported=0, currents=[0, 0, 0], voltages=[230, 230, 230]))
    client = clients.SocketClientHandler(chargepoint_client)
    client.meter_client = Mock()
    client.meter_client.get_counter_state.return_value = CounterState(
        power=500, imported=1234, exported=0, currents=[2.2, 0, 0], voltages=[230, 0, 0])
    return socket_module.SocketModule(client, InternalSocket())


def read_values(socket):
    with SingleComponentUpdateContext(socket.fault_state, update_always=False):
        return socket.get_values()


def test_module_uses_client_handler_fault_state_and_internal_value_store(socket):
    state = read_values(socket)
    assert isinstance(state, InternalSocketState)
    assert state.power == 500
    assert state.imported == 1234
    assert socket.fault_state.fault_state == FaultStateLevel.NO_ERROR
    socket.store_internal.set.assert_called_once_with(state)
    socket.store_internal.update.assert_called_once()


def test_on_requires_measurement_and_uses_both_gpio_outputs(socket):
    socket.set_state(True)
    assert socket.old_socket_state.state is False
    assert not any(call.args[1] == 1 for call in socket_module.GPIO.output.call_args_list)
    read_values(socket)
    socket.set_state(True)
    assert socket.old_socket_state.state is True
    socket_module.GPIO.output.assert_any_call(23, 1)
    socket_module.GPIO.output.assert_called_with(26, 1)
    socket.set_state(False)
    assert socket.old_socket_state.state is False


def test_failed_measurement_switches_off_and_uses_error_timer_and_slow_retry(socket):
    read_values(socket)
    socket.set_state(True)
    socket._next_poll = 0
    socket._client.meter_client.get_counter_state.side_effect = TimeoutError("no response")
    read_values(socket)
    assert socket.old_socket_state.state is False
    assert socket.fault_state.fault_state == FaultStateLevel.NO_ERROR
    assert socket.client_error_context.error_timestamp is not None
    calls = socket._client.meter_client.get_counter_state.call_count
    read_values(socket)
    assert socket._client.meter_client.get_counter_state.call_count == calls
    assert socket.fault_state.fault_state == FaultStateLevel.NO_ERROR
    socket.set_state(False)
    assert socket.fault_state.fault_state == FaultStateLevel.NO_ERROR


def test_missing_meter_constructor_is_deferred_and_isolated(socket, monkeypatch):
    socket._client.meter_client = None
    socket._client.client.read_input_registers.return_value = 230
    constructor = Mock(side_effect=TimeoutError("serial number unavailable"))
    monkeypatch.setattr(clients.sdm, "Sdm120", constructor)
    read_values(socket)
    assert socket.fault_state.fault_state == FaultStateLevel.NO_ERROR
    assert socket._client.meter_client is None
    assert socket.old_socket_state.state is False
    constructor.assert_called_once_with(54, socket._client.client, socket.fault_state)


def test_socket_meter_error_is_distinguished_from_usb_adapter_error(socket):
    read_values(socket)
    socket._next_poll = 0
    socket._client.meter_client.get_counter_state.side_effect = TimeoutError("no response")
    read_values(socket)
    socket._client.chargepoint_client_handler.request_and_check_hardware.assert_called()
    assert socket.client_error_context.error_timestamp is not None
    socket._client.chargepoint_client_handler.request_and_check_hardware.side_effect = Exception(
        "Erneutes Auslesen des USB-Adapters")
    socket.client_error_context.error_timestamp = 0
    socket._next_poll = 0
    read_values(socket)
    assert socket.fault_state.fault_state == FaultStateLevel.ERROR
    assert "USB-Adapters" in socket.fault_state.fault_str


def test_stale_measurement_cannot_enable_output(socket, monkeypatch):
    read_values(socket)
    socket.set_state(True)
    monkeypatch.setattr(socket_module.time, "monotonic", lambda: socket._measurement_time + 16)
    socket.set_state(True)
    assert socket.old_socket_state.state is False
    assert socket.fault_state.fault_state == FaultStateLevel.ERROR
    assert "veraltet" in socket.fault_state.fault_str


def test_warning_and_recovery_do_not_switch_on_without_control(socket):
    values = socket._client.meter_client.get_counter_state.return_value

    def warning():
        socket.fault_state.warning("Messwarnung")
        return values

    socket._client.meter_client.get_counter_state.side_effect = warning
    read_values(socket)
    assert socket.fault_state.fault_state == FaultStateLevel.WARNING
    socket.set_state(True)
    socket._next_poll = 0
    socket._client.meter_client.get_counter_state.side_effect = TimeoutError("no response")
    read_values(socket)
    socket._next_poll = 0
    socket._client.meter_client.get_counter_state.side_effect = None
    read_values(socket)
    assert socket.fault_state.fault_state == FaultStateLevel.NO_ERROR
    assert socket.old_socket_state.state is False
    assert socket.client_error_context.error_timestamp is None


def test_new_module_resets_output_and_does_not_restore_retained_on(socket):
    read_values(socket)
    socket.set_state(True)
    retained = InternalSocket()
    retained.get.state = True
    retained.data.set_state = True
    restarted = socket_module.SocketModule(socket._client, retained)
    assert restarted.old_socket_state.state is False
    assert restarted.old_socket_state.timestamp == 0
    socket_module.GPIO.setup.assert_any_call(26, 0, initial=0)
    socket_module.GPIO.setup.assert_any_call(23, 0, initial=0)


def test_update_state_rejects_old_on_and_turns_off_after_heartbeat_loss(socket, monkeypatch):
    from modules.internal_chargepoint_handler import internal_chargepoint_handler as handler

    now = 1000.0
    monkeypatch.setattr(handler.timecheck, "create_timestamp", lambda: now)
    update = handler.UpdateSocketState(socket)
    read_values(socket)
    data = SimpleNamespace(set_state=True, heartbeat=999.0)
    update.update_state(data)
    assert socket.old_socket_state.state is False
    data.heartbeat = 1001.0
    now = 1001.0
    update.update_state(data)
    assert socket.old_socket_state.state is True
    now = 1032.0
    update.update_state(data)
    assert socket.old_socket_state.state is False


def test_internal_value_store_publishes_the_regular_state_fields(monkeypatch):
    from modules.common.store import _socket_internal as store_module

    publish = Mock()
    monkeypatch.setattr(store_module, "pub_to_broker", publish)
    store = store_module.get_internal_socket_value_store()
    store.set(InternalSocketState(power=500, imported=1234, exported=0,
                                  voltages=[230, 0, 0], currents=[2.2, 0, 0], timestamp=1000, state=False))
    store.update()
    publish.assert_any_call("openWB/set/internal_socket/get/power", 500, 2)
    publish.assert_any_call("openWB/set/internal_socket/get/timestamp", 1000, 2)
    assert {call.args[0].rsplit("/", 1)[-1] for call in publish.call_args_list} == {
        "voltages", "currents", "imported", "exported", "power", "powers", "state", "timestamp"}


def test_single_se_does_not_create_unconfigured_second_chargepoint(monkeypatch):
    from modules.internal_chargepoint_handler import internal_chargepoint_handler as handler
    from modules.chargepoints.internal_openwb.config import InternalChargepointMode

    monkeypatch.setattr(handler.InternalChargepointHandler, "init_gpio", Mock())
    monkeypatch.setattr(handler, "SingleComponentUpdateContext", MagicMock())
    factory = Mock()
    monkeypatch.setattr(handler, "client_factory", factory)
    monkeypatch.setattr(handler, "HandlerChargepoint", Mock())
    instance = handler.InternalChargepointHandler(
        InternalChargepointMode.SE, Mock(), Mock(), 1, None, None, Mock(), Mock())
    assert factory.call_count == 1
    assert instance.cp1 is None
    assert instance.cp1_client_handler is None
